"""
干渉（interference）モード切替

目的: Neighbor Boost/Network Size が正なら干渉ありモードへ自動切替
理論: SUTVA違反の検出と適切な推定器の選択

Expert insight:
  仮定の明示と計算系の切替がない因果UIは、「見栄え重視ツール」で終わる
"""
from typing import Literal, Dict


InterferenceMode = Literal["sutva", "interference"]


def decide_mode(params: Dict[str, float]) -> InterferenceMode:
    """
    パラメータから干渉モードを判定

    Args:
        params: シナリオパラメータ辞書
                例: {"neighbor_boost": 0.1, "network_size": 100}

    Returns:
        "sutva" または "interference"

    Logic:
        - neighbor_boost > 0 または network_size > 0 → interference
        - それ以外 → sutva
    """
    nb = params.get("neighbor_boost", 0.0)
    ns = params.get("network_size", 0)

    if nb > 0 or ns > 0:
        return "interference"
    else:
        return "sutva"


def validate_mode_consistency(
    mode: InterferenceMode,
    params: Dict[str, float]
) -> None:
    """
    モードとパラメータの整合性を検証

    Args:
        mode: 指定されたモード
        params: パラメータ辞書

    Raises:
        ValueError: モードとパラメータが矛盾している場合

    Examples:
        - mode="sutva" だが neighbor_boost>0 → エラー
        - mode="interference" だが干渉パラメータが全て0 → 警告
    """
    detected_mode = decide_mode(params)

    if mode == "sutva" and detected_mode == "interference":
        raise ValueError(
            "モード'sutva'が指定されていますが、干渉パラメータ"
            "（neighbor_boost または network_size）が正の値です。"
            "SUTVAモードでは干渉パラメータは0でなければなりません。"
        )

    if mode == "interference" and detected_mode == "sutva":
        import warnings
        warnings.warn(
            "モード'interference'が指定されていますが、"
            "干渉パラメータがすべて0です。"
        )


def get_estimator_for_mode(mode: InterferenceMode) -> str:
    """
    モードに応じた推定器を取得

    Args:
        mode: 干渉モード

    Returns:
        推定器名

    Mapping:
        - sutva: "DR-Learner" (Doubly Robust)
        - interference: "Exposure-Mapping" (簡易版)
    """
    if mode == "sutva":
        return "DR-Learner"
    else:
        return "Exposure-Mapping"
