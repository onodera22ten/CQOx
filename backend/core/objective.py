"""
目的関数のSSOT化

目的: S0（観測）/S1（反実）/Δの式・単位・重みを一元化
設計境界:
  - 入力: ObjectiveSpec{name, weights, unit, constraints}
  - 出力: ObjectiveResult{S0, S1, Delta, unit, formula_latex, digest}
"""
from dataclasses import dataclass
from typing import Literal, Dict, Optional
import hashlib
import json


ObjectiveName = Literal["profit", "roi", "roas", "cac", "welfare"]


@dataclass(frozen=True)
class ObjectiveSpec:
    """目的関数の仕様"""
    name: ObjectiveName
    weights: Dict[str, float]  # {"value_per_y": 1000, "cost_per_treated": 50}
    unit: str  # "¥", "$", "unitless"
    constraints: Optional[Dict[str, float]] = None  # {"budget_cap": 1e6}


def digest_of(dataset_id: str, params: dict, spec: ObjectiveSpec) -> str:
    """
    シナリオのダイジェスト（SHA-256ハッシュ）を生成

    Args:
        dataset_id: データセットID
        params: パラメータ辞書
        spec: 目的関数仕様

    Returns:
        16文字のダイジェスト文字列（監査用）
    """
    payload = {
        "ds": dataset_id,
        "p": params,
        "spec": {
            "name": spec.name,
            "weights": spec.weights,
            "unit": spec.unit,
            "constraints": spec.constraints,
        }
    }
    s = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def eval_objective(
    y0: float,
    y1: float,
    t0: float,
    t1: float,
    spec: ObjectiveSpec
) -> tuple:
    """
    目的関数を評価してS0, S1, Δを計算

    Args:
        y0: S0のアウトカム
        y1: S1のアウトカム
        t0: S0の処置数
        t1: S1の処置数
        spec: 目的関数仕様

    Returns:
        (s0, s1, delta) のタプル

    Formulas:
        profit: v·Y - c·T
        roi: (v·Y - c·T) / (c·T)
        roas: (v·Y) / (c·T)
        cac: (c·T) / Y
        welfare: v·Y - c·T + w·(Y - T)
    """
    v = spec.weights.get("value_per_y", 1.0)
    c = spec.weights.get("cost_per_treated", 0.0)

    if spec.name == "profit":
        s0 = v * y0 - c * t0
        s1 = v * y1 - c * t1

    elif spec.name == "roi":
        cost0 = max(c * t0, 1e-9)
        cost1 = max(c * t1, 1e-9)
        s0 = (v * y0 - c * t0) / cost0
        s1 = (v * y1 - c * t1) / cost1

    elif spec.name == "roas":
        cost0 = max(c * t0, 1e-9)
        cost1 = max(c * t1, 1e-9)
        s0 = (v * y0) / cost0
        s1 = (v * y1) / cost1

    elif spec.name == "cac":
        y0_safe = max(y0, 1e-9)
        y1_safe = max(y1, 1e-9)
        s0 = (c * t0) / y0_safe
        s1 = (c * t1) / y1_safe

    elif spec.name == "welfare":
        w = spec.weights.get("welfare_weight", 1.0)
        s0 = v * y0 - c * t0 + w * (y0 - t0)
        s1 = v * y1 - c * t1 + w * (y1 - t1)

    else:
        raise ValueError(f"Unsupported objective: {spec.name}")

    delta = s1 - s0
    return s0, s1, delta


def get_formula_latex(spec: ObjectiveSpec) -> str:
    """
    目的関数のLaTeX式を取得

    Args:
        spec: 目的関数仕様

    Returns:
        LaTeX形式の数式文字列
    """
    formulas = {
        "profit": r"J = v \cdot Y - c \cdot T",
        "roi": r"\text{ROI} = \frac{v \cdot Y - c \cdot T}{c \cdot T}",
        "roas": r"\text{ROAS} = \frac{v \cdot Y}{c \cdot T}",
        "cac": r"\text{CAC} = \frac{c \cdot T}{Y}",
        "welfare": r"W = v \cdot Y - c \cdot T + w \cdot (Y - T)",
    }
    return formulas.get(spec.name, "")
