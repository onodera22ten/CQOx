"""
推奨にリスク帯・根拠を付与

目的: 「推奨 = 即実行」ではなく、効果分布と失敗確率を提示し、
      ワンクリックで実験化

理論: ブートストラップCI or ベイズ事後分布

Expert insight:
  「推奨の分布」を出せない最適化は、現場では採用されない
"""
from dataclasses import dataclass
from typing import List, Tuple, Literal


@dataclass
class Evidence:
    """推奨の根拠"""
    name: str
    link: str
    notes: str


@dataclass
class Recommendation:
    """推奨アクション"""
    action: str  # 例: "Search +15%, Display -10%"
    expected_lift: float  # 期待改善値
    ci: Tuple[float, float]  # (下限, 上限)
    risk_level: Literal["low", "medium", "high"]
    evidence: List[Evidence]  # 根拠リスト


def risk_from_ci(ci: Tuple[float, float]) -> str:
    """
    信頼区間からリスクレベルを判定

    Args:
        ci: (下限, 上限) のタプル

    Returns:
        "low", "medium", "high"

    Logic:
        - 下限が正 → low（改善がほぼ確実）
        - 下限が負だが上限が正 → medium（不確実）
        - 上限が負または0 → high（悪化の可能性）
    """
    lo, hi = ci

    if hi <= 0:
        return "high"  # 上限が0以下 → 確実に悪化
    elif lo < 0:
        return "medium"  # 下限が負 → 不確実性あり
    else:
        return "low"  # 下限が正 → ほぼ確実に改善


def create_recommendation(
    action: str,
    expected_lift: float,
    ci: Tuple[float, float],
    evidence: List[Evidence] = None
) -> Recommendation:
    """
    推奨アクションを生成

    Args:
        action: アクション記述
        expected_lift: 期待改善値
        ci: 信頼区間
        evidence: 根拠リスト

    Returns:
        Recommendation オブジェクト
    """
    risk_level = risk_from_ci(ci)

    if evidence is None:
        evidence = []

    return Recommendation(
        action=action,
        expected_lift=expected_lift,
        ci=ci,
        risk_level=risk_level,
        evidence=evidence
    )
