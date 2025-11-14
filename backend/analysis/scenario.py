"""
Scenario Heatmap Base=1.00 正規化

目的: Heatmapの色=倍率が一貫。凡例「1.00=Base」をUIに表示可能
設計: Base行は1.00、各シナリオは metric_scenario/metric_base

Expert insight:
  倍率正規化は部署横断の意思決定（">1なら上振れ"）を最短化する
"""
from typing import Dict


def normalize_heatmap(
    scenarios: Dict[str, Dict[str, float]]
) -> Dict[str, Dict[str, float]]:
    """
    シナリオ比較ヒートマップをBase=1.00で正規化

    Args:
        scenarios: {scenario_name: {metric_name: value}}
                  "Base" または "base" という名前のシナリオが必須

    Returns:
        正規化されたヒートマップ
        {scenario_name: {metric_name: normalized_ratio}}

    Raises:
        AssertionError: Baseシナリオが存在しない場合

    Example:
        >>> scenarios = {
        ...     "Base": {"roi": 100, "revenue": 5000},
        ...     "Scenario_A": {"roi": 120, "revenue": 6000}
        ... }
        >>> norm = normalize_heatmap(scenarios)
        >>> norm["Base"]["roi"]
        1.0
        >>> norm["Scenario_A"]["roi"]
        1.2
    """
    # Baseシナリオを探す（大文字小文字を許容）
    base = None
    for key in ["Base", "base", "BASE"]:
        if key in scenarios:
            base = scenarios[key]
            break

    assert base is not None, "Base row required for normalization"

    # 正規化
    normalized = {}
    for scenario_name, metrics in scenarios.items():
        normalized[scenario_name] = {}
        for metric_name, value in metrics.items():
            base_value = base.get(metric_name, 0)
            if base_value != 0:
                ratio = value / base_value
            else:
                ratio = float("nan")
            normalized[scenario_name][metric_name] = ratio

    return normalized


def validate_heatmap_ratios(
    heatmap: Dict[str, Dict[str, float]],
    base_name: str = "Base"
) -> None:
    """
    ヒートマップの比率が正しいことを検証

    Args:
        heatmap: 正規化済みヒートマップ
        base_name: ベースシナリオの名前

    Raises:
        ValueError: ベース行が1.0でない、または負の値が含まれる場合
    """
    from ..core.invariants import assert_heatmap_base_is_one

    # 行列形式に変換
    scenarios_list = sorted(heatmap.keys())
    if base_name not in scenarios_list:
        raise ValueError(f"Base scenario '{base_name}' not found")

    base_idx = scenarios_list.index(base_name)

    # 全メトリクスを取得
    all_metrics = set()
    for metrics in heatmap.values():
        all_metrics.update(metrics.keys())
    metrics_list = sorted(all_metrics)

    # 行列を構築
    matrix = []
    for scenario in scenarios_list:
        row = []
        for metric in metrics_list:
            value = heatmap[scenario].get(metric, float("nan"))
            row.append(value)
        matrix.append(row)

    # 不変条件チェック
    assert_heatmap_base_is_one(matrix, base_idx)
