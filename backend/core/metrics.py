"""
KPI/通貨のSSOT (Single Source of Truth)

目的: ROI/ROAS/LTV等の定義・通貨・丸めをENVで統一し、
      UI/最適化/ログで一貫した計算を保証する

設計境界:
  - ENV: CURRENCY={USD|JPY}, DECIMAL_PLACES=2, ROI_DEF={roi|roas}
  - I/O: メトリクス関数は純粋関数、副作用なし
"""
import os
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MoneyFmt:
    """通貨フォーマット設定"""
    currency: str = os.getenv("CURRENCY", "USD")
    decimals: int = int(os.getenv("DECIMAL_PLACES", "2"))


def roi(revenue: float, cost: float) -> float:
    """
    ROI = (Revenue - Cost) / Cost

    Returns:
        ROI value, or nan if cost <= 0
    """
    if cost <= 0:
        return float("nan")
    return (revenue - cost) / cost


def roas(revenue: float, cost: float) -> float:
    """
    ROAS = Revenue / Cost

    Returns:
        ROAS value, or nan if cost <= 0
    """
    if cost <= 0:
        return float("nan")
    return revenue / cost


def choose_roi(revenue: float, cost: float) -> float:
    """
    ENVのROI_DEFに基づいてROIまたはROASを計算

    Returns:
        ROI or ROAS based on ROI_DEF environment variable
    """
    roi_def = os.getenv("ROI_DEF", "roi")
    if roi_def == "roi":
        return roi(revenue, cost)
    else:
        return roas(revenue, cost)


def money_tick(v: float, fmt: MoneyFmt = None) -> str:
    """
    通貨表示フォーマット

    Args:
        v: 金額
        fmt: MoneyFmt設定（デフォルトはENVから取得）

    Returns:
        "¥1,234" or "$1,234.56" 形式の文字列

    Examples:
        >>> money_tick(1234.567, MoneyFmt("USD", 2))
        '$1234.57'
        >>> money_tick(1234.567, MoneyFmt("JPY", 0))
        '¥1235'
    """
    if fmt is None:
        fmt = MoneyFmt()

    # 丸め
    rounded = round(v, fmt.decimals)

    # フォーマット
    s = f"{rounded:.{fmt.decimals}f}"

    # 通貨記号
    symbol = "$" if fmt.currency == "USD" else "¥"

    return symbol + s


def cac(cost: float, acquisitions: float) -> float:
    """
    CAC = Customer Acquisition Cost = Cost / Acquisitions

    Returns:
        CAC value, or nan if acquisitions <= 0
    """
    if acquisitions <= 0:
        return float("nan")
    return cost / acquisitions


def ltv_simple(revenue_per_customer: float, churn_rate: float) -> float:
    """
    Simplified LTV = Revenue per Customer / Churn Rate

    Returns:
        LTV value, or nan if churn_rate <= 0
    """
    if churn_rate <= 0:
        return float("nan")
    return revenue_per_customer / churn_rate
