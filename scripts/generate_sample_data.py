"""
Sample Data Generator - NASA/Google Standard+

Purpose: Generate realistic sample datasets with network and geographic effects
Features:
- Social network marketing campaign (network spillover)
- Geographic store expansion (distance-based effects)
- Hybrid social + geo (location-aware social network)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List
import json


def generate_network_adjacency(n: int, avg_degree: int = 5, seed: int = 42) -> np.ndarray:
    """
    Generate realistic social network adjacency matrix

    Uses preferential attachment (Barabási-Albert model) for realistic structure
    """
    np.random.seed(seed)

    # Start with small complete graph
    m0 = min(3, avg_degree)
    adjacency = np.zeros((n, n))

    # Initial complete graph
    for i in range(m0):
        for j in range(i + 1, m0):
            adjacency[i, j] = 1
            adjacency[j, i] = 1

    # Preferential attachment
    degrees = adjacency.sum(axis=1)

    for i in range(m0, n):
        # Probability proportional to degree
        probs = degrees / degrees.sum() if degrees.sum() > 0 else np.ones(i) / i

        # Add m edges
        m = min(avg_degree, i)
        targets = np.random.choice(i, size=m, replace=False, p=probs)

        for target in targets:
            adjacency[i, target] = 1
            adjacency[target, i] = 1
            degrees[target] += 1

        degrees[i] = m

    return adjacency


def generate_geo_coords(n: int, n_clusters: int = 5, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate realistic geographic coordinates with clustering

    Simulates cities/regions with local concentrations
    """
    np.random.seed(seed)

    # Generate cluster centers (cities)
    cluster_lats = np.random.uniform(35, 45, n_clusters)  # Japan-like latitude range
    cluster_lons = np.random.uniform(135, 145, n_clusters)  # Japan-like longitude range

    # Assign each unit to a cluster
    cluster_assignments = np.random.choice(n_clusters, n)

    # Generate coordinates around cluster centers
    lats = np.zeros(n)
    lons = np.zeros(n)

    for i in range(n):
        cluster = cluster_assignments[i]
        # Add noise (~ 0.5 degree = ~50km)
        lats[i] = cluster_lats[cluster] + np.random.normal(0, 0.5)
        lons[i] = cluster_lons[cluster] + np.random.normal(0, 0.5)

    return lats, lons


def calculate_distance_matrix(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """Calculate pairwise Haversine distances (km)"""
    n = len(lats)
    distances = np.zeros((n, n))

    # Haversine formula
    R = 6371  # Earth radius in km

    lat1 = np.radians(lats[:, np.newaxis])
    lat2 = np.radians(lats[np.newaxis, :])
    lon1 = np.radians(lons[:, np.newaxis])
    lon2 = np.radians(lons[np.newaxis, :])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    distances = R * c

    return distances


def generate_sample1_social_marketing(n: int = 2000, seed: int = 42) -> pd.DataFrame:
    """
    Sample 1: Social Network Marketing Campaign

    Scenario: SNS広告キャンペーンの効果測定
    - Network spillover: 友人が広告を見ると自分も影響を受ける
    - Treatment: 広告配信の有無
    - Outcome: 購入金額
    """
    np.random.seed(seed)

    # Generate network
    adjacency = generate_network_adjacency(n, avg_degree=8, seed=seed)

    # User characteristics
    age = np.random.normal(35, 12, n).clip(18, 70)
    income = np.random.lognormal(11, 0.5, n).clip(3_000_000, 20_000_000)
    engagement_score = np.random.beta(2, 5, n) * 100  # 0-100, right-skewed

    # Network centrality (degree)
    degree = adjacency.sum(axis=1)

    # Treatment assignment (biased by engagement - confounding!)
    propensity = 0.3 + 0.4 * (engagement_score / 100)
    treatment = np.random.binomial(1, propensity)

    # Calculate network exposure (# of treated friends)
    network_exposure = adjacency @ treatment

    # Outcome generation
    # Base: income effect
    base_outcome = 10000 + 0.5 * (income / 10000)

    # Direct treatment effect
    direct_effect = treatment * (5000 + 200 * (engagement_score / 100) * np.random.normal(1, 0.2, n))

    # Network spillover effect (NASA/Google+: realistic heterogeneous spillover)
    spillover_effect = network_exposure * (800 + 100 * (engagement_score / 100)) * np.random.normal(1, 0.15, n)

    # Noise
    noise = np.random.normal(0, 2000, n)

    outcome = base_outcome + direct_effect + spillover_effect + noise
    outcome = outcome.clip(0, None)

    # Create dataframe
    df = pd.DataFrame({
        'unit_id': [f'user_{i:05d}' for i in range(n)],
        'treatment': treatment,
        'outcome': outcome,
        'age': age,
        'income': income,
        'engagement_score': engagement_score,
        'network_degree': degree,
        'network_exposure': network_exposure,
        # Add network edges as separate columns for analysis
        'neighbor_ids': [','.join([f'user_{j:05d}' for j in range(n) if adjacency[i, j] == 1]) for i in range(n)]
    })

    # Save adjacency matrix separately
    return df, adjacency


def generate_sample2_geo_store_expansion(n: int = 1500, seed: int = 43) -> pd.DataFrame:
    """
    Sample 2: Geographic Store Expansion

    Scenario: 新店舗オープンによる既存店への影響
    - Geographic spillover: 近隣店舗の売上への影響（カニバリゼーション vs シナジー）
    - Treatment: 新店舗オープン
    - Outcome: 月間売上
    """
    np.random.seed(seed)

    # Generate geographic coordinates
    lats, lons = generate_geo_coords(n, n_clusters=8, seed=seed)

    # Calculate distances
    distances = calculate_distance_matrix(lats, lons)

    # Store characteristics
    store_size = np.random.lognormal(6, 0.4, n).clip(50, 500)  # m²
    population_density = np.random.lognormal(8, 0.6, n).clip(500, 20000)  # people/km²
    competition_index = np.random.beta(2, 3, n) * 10  # 0-10

    # Treatment assignment (new store opening - based on population density)
    propensity = 0.2 + 0.3 * (population_density / population_density.max())
    treatment = np.random.binomial(1, propensity)

    # Calculate geographic exposure (weighted by inverse distance)
    # Stores within 5km affect each other
    distance_weights = np.exp(-distances / 2.0)  # Exponential decay
    distance_weights[distances > 10] = 0  # Cut-off at 10km
    np.fill_diagonal(distance_weights, 0)  # Exclude self

    geo_exposure = distance_weights @ treatment

    # Outcome generation
    # Base: size and population effect
    base_outcome = 5_000_000 + 50_000 * store_size + 500 * population_density

    # Direct treatment effect (new store boost)
    direct_effect = treatment * (1_500_000 + 20_000 * store_size * np.random.normal(1, 0.2, n))

    # Geographic spillover effect (NASA/Google+: distance-dependent cannibalization)
    # Negative effect (cannibalization) for nearby stores
    cannibalization = -geo_exposure * (300_000 + 5_000 * store_size) * np.random.normal(1, 0.15, n)

    # Positive effect (synergy) for distant stores (brand awareness)
    synergy_weights = (distances > 5) & (distances < 15)
    synergy_exposure = synergy_weights.sum(axis=1)
    synergy_effect = synergy_exposure * 50_000 * np.random.normal(1, 0.1, n)

    # Noise
    noise = np.random.normal(0, 500_000, n)

    outcome = base_outcome + direct_effect + cannibalization + synergy_effect + noise
    outcome = outcome.clip(0, None)

    # Create dataframe
    df = pd.DataFrame({
        'unit_id': [f'store_{i:05d}' for i in range(n)],
        'treatment': treatment,
        'outcome': outcome,
        'lat': lats,
        'lon': lons,
        'store_size': store_size,
        'population_density': population_density,
        'competition_index': competition_index,
        'geo_exposure': geo_exposure,
        'nearby_stores_count': (distances < 5).sum(axis=1) - 1  # Exclude self
    })

    return df, distances


def generate_sample3_hybrid_social_geo(n: int = 3000, seed: int = 44) -> pd.DataFrame:
    """
    Sample 3: Hybrid Social + Geographic (NASA/Google++ level)

    Scenario: 位置情報ベースのソーシャルアプリでのプロモーション
    - Dual spillover: ソーシャルネットワーク + 地理的近接性
    - Treatment: プレミアム機能の無料トライアル提供
    - Outcome: 月間アクティブ時間（分）

    This is the most advanced: captures both network and geographic interference
    """
    np.random.seed(seed)

    # Generate both network and geography
    adjacency = generate_network_adjacency(n, avg_degree=12, seed=seed)
    lats, lons = generate_geo_coords(n, n_clusters=10, seed=seed)
    distances = calculate_distance_matrix(lats, lons)

    # User characteristics
    age = np.random.normal(28, 8, n).clip(18, 60)
    usage_frequency = np.random.beta(3, 3, n) * 100  # 0-100
    social_activity = np.random.beta(2, 3, n) * 100  # 0-100

    # Network and geo metrics
    network_degree = adjacency.sum(axis=1)
    nearby_users = (distances < 2).sum(axis=1) - 1  # Within 2km

    # Treatment assignment (biased by social activity)
    propensity = 0.25 + 0.35 * (social_activity / 100)
    treatment = np.random.binomial(1, propensity)

    # Calculate exposures
    # Social network exposure
    network_exposure = adjacency @ treatment

    # Geographic exposure (exponential decay)
    geo_weights = np.exp(-distances / 1.0)
    geo_weights[distances > 5] = 0
    np.fill_diagonal(geo_weights, 0)
    geo_exposure = geo_weights @ treatment

    # Outcome generation
    # Base: usage frequency and social activity
    base_outcome = 120 + 2.5 * usage_frequency + 1.5 * social_activity

    # Direct treatment effect
    direct_effect = treatment * (180 + 3 * social_activity * np.random.normal(1, 0.2, n))

    # Network spillover (friend effect)
    network_spillover = network_exposure * (15 + 0.5 * social_activity) * np.random.normal(1, 0.15, n)

    # Geographic spillover (local trend effect)
    geo_spillover = geo_exposure * (8 + 0.3 * usage_frequency) * np.random.normal(1, 0.12, n)

    # Interaction effect (NASA/Google++: network × geo synergy)
    # Users with both friend influence AND local influence get extra boost
    interaction = (network_exposure > 0) & (geo_exposure > 0.5)
    interaction_effect = interaction * 25 * np.random.normal(1, 0.2, n)

    # Noise
    noise = np.random.normal(0, 30, n)

    outcome = base_outcome + direct_effect + network_spillover + geo_spillover + interaction_effect + noise
    outcome = outcome.clip(0, None)

    # Create dataframe
    df = pd.DataFrame({
        'unit_id': [f'user_{i:05d}' for i in range(n)],
        'treatment': treatment,
        'outcome': outcome,
        'lat': lats,
        'lon': lons,
        'age': age,
        'usage_frequency': usage_frequency,
        'social_activity': social_activity,
        'network_degree': network_degree,
        'network_exposure': network_exposure,
        'nearby_users': nearby_users,
        'geo_exposure': geo_exposure,
        'has_interaction': interaction.astype(int),
        'neighbor_ids': [','.join([f'user_{j:05d}' for j in range(n) if adjacency[i, j] == 1]) for i in range(n)]
    })

    return df, adjacency, distances


def save_sample_data():
    """Generate and save all sample datasets"""
    data_dir = Path("data/samples")
    data_dir.mkdir(parents=True, exist_ok=True)

    print("[Sample Data] Generating 3 sample datasets...")

    # Sample 1: Social Marketing
    print("[1/3] Generating social_marketing dataset (n=2000)...")
    df1, adj1 = generate_sample1_social_marketing(n=2000)
    df1.to_csv(data_dir / "social_marketing.csv", index=False)
    np.save(data_dir / "social_marketing_adjacency.npy", adj1)

    metadata1 = {
        "name": "social_marketing",
        "description": "SNS広告キャンペーンの効果測定（ネットワーク波及効果）",
        "n": len(df1),
        "treatment_rate": float(df1['treatment'].mean()),
        "avg_outcome_treated": float(df1[df1['treatment']==1]['outcome'].mean()),
        "avg_outcome_control": float(df1[df1['treatment']==0]['outcome'].mean()),
        "naive_ate": float(df1[df1['treatment']==1]['outcome'].mean() - df1[df1['treatment']==0]['outcome'].mean()),
        "features": {
            "network": True,
            "geographic": False,
            "spillover_type": "social_network"
        }
    }

    # Sample 2: Geographic Store
    print("[2/3] Generating geo_store_expansion dataset (n=1500)...")
    df2, dist2 = generate_sample2_geo_store_expansion(n=1500)
    df2.to_csv(data_dir / "geo_store_expansion.csv", index=False)
    np.save(data_dir / "geo_store_distances.npy", dist2)

    metadata2 = {
        "name": "geo_store_expansion",
        "description": "新店舗オープンによる既存店への影響（地理的カニバリゼーション）",
        "n": len(df2),
        "treatment_rate": float(df2['treatment'].mean()),
        "avg_outcome_treated": float(df2[df2['treatment']==1]['outcome'].mean()),
        "avg_outcome_control": float(df2[df2['treatment']==0]['outcome'].mean()),
        "naive_ate": float(df2[df2['treatment']==1]['outcome'].mean() - df2[df2['treatment']==0]['outcome'].mean()),
        "features": {
            "network": False,
            "geographic": True,
            "spillover_type": "geographic_distance"
        }
    }

    # Sample 3: Hybrid
    print("[3/3] Generating hybrid_social_geo dataset (n=3000)...")
    df3, adj3, dist3 = generate_sample3_hybrid_social_geo(n=3000)
    df3.to_csv(data_dir / "hybrid_social_geo.csv", index=False)
    np.save(data_dir / "hybrid_adjacency.npy", adj3)
    np.save(data_dir / "hybrid_distances.npy", dist3)

    metadata3 = {
        "name": "hybrid_social_geo",
        "description": "位置情報ベースのソーシャルアプリ（ネットワーク×地理のハイブリッド波及）",
        "n": len(df3),
        "treatment_rate": float(df3['treatment'].mean()),
        "avg_outcome_treated": float(df3[df3['treatment']==1]['outcome'].mean()),
        "avg_outcome_control": float(df3[df3['treatment']==0]['outcome'].mean()),
        "naive_ate": float(df3[df3['treatment']==1]['outcome'].mean() - df3[df3['treatment']==0]['outcome'].mean()),
        "features": {
            "network": True,
            "geographic": True,
            "spillover_type": "hybrid_network_geographic"
        }
    }

    # Save metadata
    with open(data_dir / "metadata.json", "w") as f:
        json.dump({
            "samples": [metadata1, metadata2, metadata3],
            "generated_at": pd.Timestamp.now().isoformat()
        }, f, indent=2)

    print("\n[Sample Data] ✓ All datasets generated successfully!")
    print(f"[Sample Data] Location: {data_dir.absolute()}")
    print("\n[Sample Data] Summary:")
    print(f"  1. social_marketing.csv: {len(df1):,} rows, Network spillover")
    print(f"     Naive ATE: ¥{metadata1['naive_ate']:,.0f}")
    print(f"  2. geo_store_expansion.csv: {len(df2):,} rows, Geographic spillover")
    print(f"     Naive ATE: ¥{metadata2['naive_ate']:,.0f}")
    print(f"  3. hybrid_social_geo.csv: {len(df3):,} rows, Hybrid spillover")
    print(f"     Naive ATE: {metadata3['naive_ate']:.1f} minutes")

    return metadata1, metadata2, metadata3


if __name__ == "__main__":
    save_sample_data()
