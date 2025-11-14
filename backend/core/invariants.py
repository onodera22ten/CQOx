"""
図の不変条件チェック - Fail Fast before Plot

目的: 壊れた結果を描画前にFailさせる
設計境界: 入力=各図用の配列/DF、出力=None（例外throw）

What this does:
  - Shapley=総和1（総和=1または100）
  - Sankey=流量保存
  - Heatmap=Base=1.0
  - Survival=単調減少

Expert insight:
  描画前ブレーキは、監視やSLOより先に誤検知を物理的に止める最小コスト
"""
import math
from typing import List, Dict


def assert_shapley_simplex(values: List[float], tol: float = 1e-6):
    """
    Shapley値が総和=1または100であることを確認

    Args:
        values: Shapley値のリスト
        tol: 許容誤差

    Raises:
        ValueError: 総和が1でも100でもない、またはNaNが含まれる場合
    """
    s = sum(values)
    if not (abs(s - 1.0) <= tol or abs(s - 100.0) <= tol):
        raise ValueError(f"Shapley sum {s} not in {{1, 100}} (tolerance={tol})")

    if any(math.isnan(v) for v in values):
        raise ValueError("NaN in Shapley values")


def assert_sankey_conservation(
    layer_in: List[float],
    layer_out: List[float],
    tol: float = 1e-6
):
    """
    Sankeyダイアグラムの流量保存則を確認

    Args:
        layer_in: 入力層の流量リスト
        layer_out: 出力層の流量リスト
        tol: 許容誤差

    Raises:
        ValueError: 入出力の総和が一致しない場合
    """
    sum_in = sum(layer_in)
    sum_out = sum(layer_out)

    if abs(sum_in - sum_out) > tol:
        raise ValueError(
            f"Sankey flow not conserved: in={sum_in}, out={sum_out}, "
            f"diff={abs(sum_in - sum_out)}"
        )


def assert_heatmap_base_is_one(
    matrix: List[List[float]],
    base_row: int,
    tol: float = 0.3
):
    """
    Heatmapのベース行が1.0であることを確認

    Args:
        matrix: ヒートマップの行列（各行がシナリオ、各列が指標）
        base_row: ベース行のインデックス
        tol: ベース行の値が1.0からどれだけずれを許容するか

    Raises:
        ValueError: 負の値が含まれる、またはベース行が~1.0でない場合
    """
    # 比率は正
    for row in matrix:
        for v in row:
            if v <= 0:
                raise ValueError("Heatmap values must be positive ratios")

    # ベース行は ≈1.0
    base_values = matrix[base_row]
    for v in base_values:
        if abs(v - 1.0) > tol:
            raise ValueError(
                f"Heatmap base row must be ~1.0 (found {v}, tolerance={tol})"
            )


def assert_survival_monotone_down(surv: List[float], tol: float = 1e-9):
    """
    Survival曲線が単調減少であることを確認

    Args:
        surv: 生存率の時系列リスト
        tol: 許容誤差

    Raises:
        ValueError: 単調減少でない場合
    """
    for i in range(len(surv) - 1):
        if surv[i] < surv[i + 1] - tol:
            raise ValueError(
                f"Survival must be non-increasing: surv[{i}]={surv[i]}, "
                f"surv[{i+1}]={surv[i+1]}"
            )


def assert_positive_values(values: List[float], name: str = "values"):
    """
    全ての値が正であることを確認

    Args:
        values: 確認する値のリスト
        name: 値の名前（エラーメッセージ用）

    Raises:
        ValueError: 負の値またはNaNが含まれる場合
    """
    for i, v in enumerate(values):
        if math.isnan(v):
            raise ValueError(f"{name}[{i}] is NaN")
        if v < 0:
            raise ValueError(f"{name}[{i}]={v} is negative")


def assert_ci_order(ci_low: float, ci_high: float, name: str = "CI"):
    """
    信頼区間の順序が正しいことを確認

    Args:
        ci_low: 信頼区間の下限
        ci_high: 信頼区間の上限
        name: CI名（エラーメッセージ用）

    Raises:
        ValueError: 下限が上限より大きい場合
    """
    if ci_low >= ci_high:
        raise ValueError(
            f"{name}: lower bound ({ci_low}) must be < upper bound ({ci_high})"
        )


def assert_probability_range(probs: List[float], name: str = "probabilities"):
    """
    確率値が[0, 1]の範囲にあることを確認

    Args:
        probs: 確率値のリスト
        name: 確率名（エラーメッセージ用）

    Raises:
        ValueError: 範囲外の値が含まれる場合
    """
    for i, p in enumerate(probs):
        if math.isnan(p):
            raise ValueError(f"{name}[{i}] is NaN")
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"{name}[{i}]={p} out of range [0, 1]")
