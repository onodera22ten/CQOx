"""
マーケティング分野の1万行データ生成スクリプト
前処理が必要な現実的なデータを生成
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

def generate_marketing_data_10k():
    """
    マーケティングキャンペーンデータを生成

    特徴:
    - 欠損値を含む（前処理が必要）
    - 異常値を含む
    - カテゴリカル変数の表記ゆれ
    - 因果推論に適した構造
    """
    n = 10000

    # 時系列データ
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=int(x)) for x in np.random.randint(0, 365, n)]

    # 顧客属性
    age = np.random.normal(40, 15, n).clip(18, 80)
    income = np.random.lognormal(10.5, 0.8, n).clip(10000, 200000)

    # 学歴（表記ゆれあり）
    education_categories = [
        'high_school', 'High School', 'hs',
        'bachelors', 'Bachelors', 'BA', 'B.A.',
        'masters', 'Masters', 'MA', 'M.A.',
        'phd', 'PhD', 'Ph.D.'
    ]
    education = np.random.choice(education_categories, n,
                                 p=[0.15, 0.10, 0.05,  # high school variations
                                   0.25, 0.15, 0.05, 0.03,  # bachelors variations
                                   0.12, 0.05, 0.03, 0.01,  # masters variations
                                   0.005, 0.004, 0.001])  # phd variations

    # 性別（表記ゆれあり）
    gender_categories = ['Male', 'M', 'male', 'Female', 'F', 'female', 'Other', 'O']
    gender_raw = np.random.choice(gender_categories, n,
                                  p=[0.25, 0.15, 0.10, 0.25, 0.15, 0.08, 0.015, 0.005])

    # 地域
    regions = ['north', 'south', 'east', 'west', 'central']
    region = np.random.choice(regions, n)

    # クラスター（地理的グループ）
    cluster_id = np.random.randint(0, 50, n)

    # ネットワーク露出
    neighbor_exposure = np.random.choice([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8], n)

    # 共変量
    w_continuous = np.random.normal(0, 1, n)
    w_neg = np.random.normal(0, 1, n)

    # Instrumental Variable
    z = np.random.binomial(1, 0.6, n)
    z_neg = np.random.normal(0, 1, n)

    # ドメイン（転移可能性分析用）
    domain = np.random.choice(['source', 'target'], n, p=[0.7, 0.3])

    # 傾向スコア（処置割り当て確率）
    # 共変量に基づく
    masters_phd = np.isin(education, ['masters', 'Masters', 'MA', 'M.A.', 'phd', 'PhD', 'Ph.D.']).astype(int)
    logit_propensity = (
        -0.5
        + 0.02 * (age - 40)
        + 0.00001 * (income - 50000)
        + 0.3 * masters_phd
        + 0.2 * w_continuous
        + 0.1 * z
    )
    propensity_score = 1 / (1 + np.exp(-logit_propensity))

    # 処置割り当て
    treatment = np.random.binomial(1, propensity_score)

    # 潜在的アウトカム（CATE - 条件付き平均処置効果）
    # 年齢と収入によって効果が異なる（異質性）
    masters_only = np.isin(education, ['masters', 'Masters', 'MA', 'M.A.']).astype(int)
    phd_only = np.isin(education, ['phd', 'PhD', 'Ph.D.']).astype(int)
    base_outcome = (
        300
        + 5 * age
        + 0.003 * income
        + 50 * masters_only
        + 100 * phd_only
        + 30 * w_continuous
    )

    # 処置効果（異質性あり）
    treatment_effect = (
        150  # 平均処置効果（ATE）
        + 2 * (age - 40)  # 年齢による異質性
        + 0.002 * (income - 50000)  # 収入による異質性
        + 50 * z  # IV効果
        + 30 * neighbor_exposure  # ネットワーク効果
    )

    # 観測されるアウトカム（購入金額など）
    y = base_outcome + treatment * treatment_effect + np.random.normal(0, 50, n)

    # コスト（マーケティング施策のコスト）
    cost = np.where(
        treatment == 1,
        np.random.lognormal(4, 0.5, n),  # 処置群のコスト
        np.random.lognormal(2, 0.3, n)   # 対照群のコスト
    )

    # Log propensity（推定器で使用）
    log_propensity = np.log(propensity_score / (1 - propensity_score))

    # チャネル（マーケティングチャネル）
    channels = ['email', 'social_media', 'paid_search', 'display_ads', 'direct_mail']
    channel = np.random.choice(channels, n)

    # 顧客セグメント
    segments = ['premium', 'standard', 'budget', 'vip']
    customer_segment = np.random.choice(segments, n, p=[0.15, 0.50, 0.30, 0.05])

    # 以前の購入履歴
    previous_purchases = np.random.poisson(3, n)

    # エンゲージメントスコア（0-100）
    engagement_score = np.random.beta(2, 5, n) * 100

    # データフレーム作成
    df = pd.DataFrame({
        'user_id': range(1, n + 1),
        'date': dates,
        'treatment': treatment,
        'y': y,
        'cost': cost,
        'log_propensity': log_propensity,
        'propensity_score': propensity_score,
        'age': age,
        'income': income,
        'education': education,
        'gender_raw': gender_raw,
        'region': region,
        'z': z,
        'domain': domain,
        'w_continuous': w_continuous,
        'w_neg': w_neg,
        'z_neg': z_neg,
        'cluster_id': cluster_id,
        'neighbor_exposure': neighbor_exposure,
        'channel': channel,
        'customer_segment': customer_segment,
        'previous_purchases': previous_purchases,
        'engagement_score': engagement_score
    })

    # 前処理が必要な欠損値を導入（MCAR: Missing Completely At Random）
    # 5%の欠損率
    missing_mask_y = np.random.random(n) < 0.05
    df.loc[missing_mask_y, 'y'] = np.nan

    missing_mask_age = np.random.random(n) < 0.03
    df.loc[missing_mask_age, 'age'] = np.nan

    missing_mask_income = np.random.random(n) < 0.04
    df.loc[missing_mask_income, 'income'] = np.nan

    missing_mask_engagement = np.random.random(n) < 0.08
    df.loc[missing_mask_engagement, 'engagement_score'] = np.nan

    # 異常値の導入
    outlier_idx = np.random.choice(n, size=int(n * 0.02), replace=False)
    df.loc[outlier_idx, 'y'] = df.loc[outlier_idx, 'y'] * np.random.uniform(3, 5, len(outlier_idx))

    # 日付でソート
    df = df.sort_values('date').reset_index(drop=True)

    return df

if __name__ == "__main__":
    print("マーケティング分野の1万行データを生成中...")
    df = generate_marketing_data_10k()

    # CSV保存
    output_path = "/home/hirokionodera/CQO/data/marketing_campaign_10k.csv"
    df.to_csv(output_path, index=False)
    print(f"✓ データ生成完了: {output_path}")
    print(f"  - 行数: {len(df):,}")
    print(f"  - 列数: {len(df.columns)}")
    print(f"  - 欠損値: {df.isnull().sum().sum():,}")
    print(f"\n列一覧:")
    for col in df.columns:
        missing_pct = (df[col].isnull().sum() / len(df)) * 100
        print(f"  - {col:25s} : {str(df[col].dtype):12s} (欠損率: {missing_pct:.1f}%)")

    print(f"\n基本統計:")
    print(df[['age', 'income', 'y', 'cost', 'treatment']].describe())
