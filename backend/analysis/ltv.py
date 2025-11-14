"""
LTV信頼区間 - ブートストラップ実装

目的: 「95%CI」表記の根拠を最小コストで実装
理論: ブートストラップ・パーセンタイル法

Expert insight:
  CIの手法を明記しないBIは監査で一発NG（特に収益系）
"""
import numpy as np
from typing import Tuple


def ltv_ci(
    samples: np.ndarray,
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    LTVサンプルから信頼区間を計算（ブートストラップ・パーセンタイル法）

    Args:
        samples: LTVサンプルの配列
        alpha: 有意水準（デフォルト0.05で95%CI）

    Returns:
        (lower_bound, upper_bound) のタプル

    Example:
        >>> np.random.seed(42)
        >>> samples = np.random.gamma(2.0, 150.0, 1000)
        >>> lo, hi = ltv_ci(samples)
        >>> assert lo < hi
        >>> assert lo > 0
    """
    # パーセンタイル法
    low = alpha / 2
    high = 1 - alpha / 2

    lower_bound, upper_bound = np.quantile(samples, [low, high])

    return float(lower_bound), float(upper_bound)


def bootstrap_ltv(
    revenue_per_customer: np.ndarray,
    churn_events: np.ndarray,
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    random_state: int = None
) -> Tuple[float, float, float]:
    """
    LTVのブートストラップ推定

    Args:
        revenue_per_customer: 顧客あたり収益の配列
        churn_events: チャーンイベント（0/1）の配列
        n_bootstrap: ブートストラップ反復回数
        alpha: 有意水準
        random_state: 乱数シード

    Returns:
        (mean_ltv, ci_low, ci_high) のタプル
    """
    rng = np.random.RandomState(random_state)
    n = len(revenue_per_customer)

    ltv_samples = []

    for _ in range(n_bootstrap):
        # リサンプリング
        indices = rng.choice(n, size=n, replace=True)
        rev_sample = revenue_per_customer[indices]
        churn_sample = churn_events[indices]

        # LTV推定
        churn_rate = churn_sample.mean()
        if churn_rate > 0:
            mean_rev = rev_sample.mean()
            ltv = mean_rev / churn_rate
        else:
            ltv = float("nan")

        ltv_samples.append(ltv)

    # NaNを除外
    ltv_samples = np.array([x for x in ltv_samples if not np.isnan(x)])

    if len(ltv_samples) == 0:
        return float("nan"), float("nan"), float("nan")

    mean_ltv = float(np.mean(ltv_samples))
    ci_low, ci_high = ltv_ci(ltv_samples, alpha)

    return mean_ltv, ci_low, ci_high
