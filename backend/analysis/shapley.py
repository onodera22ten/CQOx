"""
Shapley値の正規化と検証

目的: Shapley Radarの総和=1を保証
理論: シンプルな制約（総和=1）は議論の土台を作る
"""
from typing import List
from ..core.invariants import assert_shapley_simplex


def normalize_to_simplex(vals: List[float]) -> List[float]:
    """
    Shapley値を総和=1に正規化

    Args:
        vals: Shapley値のリスト

    Returns:
        正規化されたShapley値（総和=1）

    Raises:
        AssertionError: 正規化後の検証に失敗した場合
    """
    s = sum(vals)
    if s > 0:
        out = [v / s for v in vals]
    else:
        # 全てゼロの場合は均等分配
        out = [1.0 / len(vals)] * len(vals)

    # 不変条件チェック
    assert_shapley_simplex(out)

    return out


def shapley_to_percentage(vals: List[float]) -> List[float]:
    """
    Shapley値をパーセンテージ（合計100）に変換

    Args:
        vals: 正規化済みShapley値（合計=1）

    Returns:
        パーセンテージ値（合計=100）
    """
    return [v * 100.0 for v in vals]
