"""
Network Exposure Calculator - NASA/Google Standard

Purpose: Calculate exposure for network/geographic causal inference
Features:
- k-NN exposure calculation
- Distance-based decay
- Spatial lag computation
- Edge-based exposure mapping
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Literal
from scipy.spatial.distance import cdist


@dataclass
class ExposureSpec:
    """Specification for exposure calculation"""
    type: Literal["kNN", "radius", "edges"] = "kNN"
    k: int = 5
    radius_km: Optional[float] = None
    decay: Literal["exp", "pow", "uniform"] = "exp"
    alpha: float = 0.7


def calculate_knn_exposure(
    df: pd.DataFrame,
    k: int = 5,
    lat_col: str = "lat",
    lon_col: str = "lon",
    treatment_col: str = "treatment",
    decay: str = "exp",
    alpha: float = 0.7
) -> pd.DataFrame:
    """
    Calculate k-nearest neighbor exposure with distance decay

    Args:
        df: DataFrame with lat/lon and treatment
        k: Number of nearest neighbors
        lat_col: Latitude column name
        lon_col: Longitude column name
        treatment_col: Treatment column name
        decay: Decay function ('exp', 'pow', 'uniform')
        alpha: Decay parameter

    Returns:
        DataFrame with 'exposure' and 'weighted_degree' columns
    """
    # Extract coordinates
    coords = df[[lat_col, lon_col]].values
    treatments = df[treatment_col].values

    # Calculate pairwise distances (haversine approximation)
    # For simplicity, using Euclidean; in production use geopy or similar
    distances = cdist(coords, coords, metric='euclidean')

    exposures = []
    weighted_degrees = []

    for i in range(len(df)):
        # Get k nearest neighbors (excluding self)
        neighbor_indices = np.argsort(distances[i])[1:k+1]
        neighbor_distances = distances[i, neighbor_indices]
        neighbor_treatments = treatments[neighbor_indices]

        # Calculate weights based on decay
        if decay == "exp":
            weights = np.exp(-alpha * neighbor_distances)
        elif decay == "pow":
            weights = 1 / (1 + neighbor_distances) ** alpha
        else:  # uniform
            weights = np.ones(len(neighbor_distances))

        # Normalize weights
        weights = weights / weights.sum() if weights.sum() > 0 else weights

        # Calculate weighted exposure
        exposure = np.dot(weights, neighbor_treatments)
        weighted_degree = weights.sum()

        exposures.append(exposure)
        weighted_degrees.append(weighted_degree)

    df = df.copy()
    df["exposure"] = exposures
    df["weighted_degree"] = weighted_degrees
    df["degree"] = k  # Constant for k-NN

    return df


def calculate_radius_exposure(
    df: pd.DataFrame,
    radius_km: float = 2.0,
    lat_col: str = "lat",
    lon_col: str = "lon",
    treatment_col: str = "treatment",
    decay: str = "exp",
    alpha: float = 0.7
) -> pd.DataFrame:
    """
    Calculate radius-based exposure with distance decay

    Args:
        df: DataFrame with lat/lon and treatment
        radius_km: Radius in kilometers
        lat_col: Latitude column name
        lon_col: Longitude column name
        treatment_col: Treatment column name
        decay: Decay function
        alpha: Decay parameter

    Returns:
        DataFrame with 'exposure', 'degree', and 'weighted_degree' columns
    """
    # Extract coordinates
    coords = df[[lat_col, lon_col]].values
    treatments = df[treatment_col].values

    # Calculate pairwise distances
    distances = cdist(coords, coords, metric='euclidean')
    # Convert to km (rough approximation: 1 degree ≈ 111 km)
    distances_km = distances * 111

    exposures = []
    degrees = []
    weighted_degrees = []

    for i in range(len(df)):
        # Get neighbors within radius (excluding self)
        within_radius = (distances_km[i] < radius_km) & (np.arange(len(df)) != i)
        neighbor_indices = np.where(within_radius)[0]

        if len(neighbor_indices) == 0:
            exposures.append(0.0)
            degrees.append(0)
            weighted_degrees.append(0.0)
            continue

        neighbor_distances = distances_km[i, neighbor_indices]
        neighbor_treatments = treatments[neighbor_indices]

        # Calculate weights
        if decay == "exp":
            weights = np.exp(-alpha * neighbor_distances / radius_km)
        elif decay == "pow":
            weights = 1 / (1 + neighbor_distances / radius_km) ** alpha
        else:  # uniform
            weights = np.ones(len(neighbor_distances))

        # Normalize weights
        weights = weights / weights.sum() if weights.sum() > 0 else weights

        # Calculate weighted exposure
        exposure = np.dot(weights, neighbor_treatments)
        degree = len(neighbor_indices)
        weighted_degree = weights.sum()

        exposures.append(exposure)
        degrees.append(degree)
        weighted_degrees.append(weighted_degree)

    df = df.copy()
    df["exposure"] = exposures
    df["degree"] = degrees
    df["weighted_degree"] = weighted_degrees

    return df


def calculate_edges_exposure(
    df: pd.DataFrame,
    edges: pd.DataFrame,
    treatment_col: str = "treatment",
    unit_col: str = "unit_id",
    normalize: bool = True
) -> pd.DataFrame:
    """
    Calculate exposure from edges table

    Args:
        df: Main DataFrame
        edges: Edges DataFrame with columns [src, dst, weight]
        treatment_col: Treatment column name
        unit_col: Unit ID column name
        normalize: Whether to normalize by total weight

    Returns:
        DataFrame with 'exposure', 'degree', and 'weighted_degree' columns
    """
    # Create unit_id to treatment mapping
    unit_treatment = dict(zip(df[unit_col], df[treatment_col]))

    exposures = []
    degrees = []
    weighted_degrees = []

    for unit_id in df[unit_col]:
        # Get outgoing edges
        unit_edges = edges[edges["src"] == unit_id]

        if len(unit_edges) == 0:
            exposures.append(0.0)
            degrees.append(0)
            weighted_degrees.append(0.0)
            continue

        # Get neighbor treatments
        neighbor_ids = unit_edges["dst"].values
        neighbor_treatments = np.array([unit_treatment.get(nid, 0) for nid in neighbor_ids])

        # Get weights
        if "weight" in unit_edges.columns:
            weights = unit_edges["weight"].values
        else:
            weights = np.ones(len(neighbor_ids))

        # Normalize if requested
        if normalize and weights.sum() > 0:
            weights = weights / weights.sum()

        # Calculate exposure
        exposure = np.dot(weights, neighbor_treatments)
        degree = len(neighbor_ids)
        weighted_degree = weights.sum()

        exposures.append(exposure)
        degrees.append(degree)
        weighted_degrees.append(weighted_degree)

    df = df.copy()
    df["exposure"] = exposures
    df["degree"] = degrees
    df["weighted_degree"] = weighted_degrees

    return df


def calculate_spatial_lag(
    df: pd.DataFrame,
    W: np.ndarray,
    variable_col: str
) -> np.ndarray:
    """
    Calculate spatial lag: W * variable

    Args:
        df: DataFrame
        W: Spatial weights matrix (n x n)
        variable_col: Variable to lag

    Returns:
        Spatial lag as numpy array
    """
    variable = df[variable_col].values
    return W @ variable


def compute_exposure(
    df: pd.DataFrame,
    spec: ExposureSpec,
    edges: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Compute exposure based on specification

    Args:
        df: Main DataFrame
        spec: Exposure specification
        edges: Optional edges DataFrame

    Returns:
        DataFrame with exposure columns
    """
    if spec.type == "kNN":
        return calculate_knn_exposure(
            df,
            k=spec.k,
            decay=spec.decay,
            alpha=spec.alpha
        )
    elif spec.type == "radius":
        if spec.radius_km is None:
            raise ValueError("radius_km must be specified for radius-based exposure")
        return calculate_radius_exposure(
            df,
            radius_km=spec.radius_km,
            decay=spec.decay,
            alpha=spec.alpha
        )
    elif spec.type == "edges":
        if edges is None:
            raise ValueError("edges DataFrame must be provided for edge-based exposure")
        return calculate_edges_exposure(df, edges)
    else:
        raise ValueError(f"Unknown exposure type: {spec.type}")
