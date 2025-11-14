"""
Pareto Frontier の正規実装

目的: コスト↓・便益↑の非支配集合のみを表示
理論: Paretoの支配定義を明示

Expert insight:
  Paretoの支配定義を明示しないと、「きれいな散布図」≠「最適候補」になりやすい
"""
from typing import Iterable, Tuple, List


def pareto_front(points: Iterable[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Pareto最適フロンティアを計算

    Args:
        points: (cost, benefit) のタプルのリスト
                cost: コスト（小さいほど良い）
                benefit: 便益（大きいほど良い）

    Returns:
        Pareto最適な点のリスト（非支配集合）
        cost昇順でソート済み

    Algorithm:
        1. costで昇順ソート（同じcostならbenefit降順）
        2. 左から走査し、benefitが今までの最大より大きい点のみを採用

    Example:
        >>> pareto_front([(10, 20), (12, 25), (12, 22), (9, 18)])
        [(9, 18), (10, 20), (12, 25)]
    """
    # (cost, benefit) でソート: cost昇順、同じならbenefit降順
    pts = sorted(points, key=lambda x: (x[0], -x[1]))

    front = []
    best_benefit = -1e18

    for cost, benefit in pts:
        if benefit > best_benefit:
            front.append((cost, benefit))
            best_benefit = benefit

    return front


def is_dominated(
    point: Tuple[float, float],
    other: Tuple[float, float]
) -> bool:
    """
    pointがotherに支配されているかを判定

    Args:
        point: (cost, benefit)
        other: (cost, benefit)

    Returns:
        True if other dominates point
        （otherのcostが小さく、benefitが大きい場合）
    """
    cost_p, benefit_p = point
    cost_o, benefit_o = other

    # otherがpointを支配: cost_o <= cost_p AND benefit_o >= benefit_p
    # かつ、少なくとも一方で厳密に優位
    return (
        cost_o <= cost_p
        and benefit_o >= benefit_p
        and (cost_o < cost_p or benefit_o > benefit_p)
    )


def filter_non_dominated(
    points: List[Tuple[float, float]]
) -> List[Tuple[float, float]]:
    """
    非支配解のみをフィルタリング

    Args:
        points: (cost, benefit) のリスト

    Returns:
        どの他の点にも支配されていない点のリスト
    """
    non_dominated = []

    for i, point in enumerate(points):
        dominated = False
        for j, other in enumerate(points):
            if i != j and is_dominated(point, other):
                dominated = True
                break
        if not dominated:
            non_dominated.append(point)

    return non_dominated
