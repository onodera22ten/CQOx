"""
Test suite for backend/core/objective.py
"""
import pytest
from backend.core.objective import (
    ObjectiveSpec, eval_objective, digest_of, get_formula_latex
)


def test_objective_profit():
    """利益最大化目的関数"""
    spec = ObjectiveSpec("profit", {"value_per_y": 1000, "cost_per_treated": 50}, "¥")
    s0, s1, delta = eval_objective(100, 120, 50, 55, spec)

    # profit = v*Y - c*T
    assert s0 == 1000 * 100 - 50 * 50  # 97500
    assert s1 == 1000 * 120 - 50 * 55  # 117250
    assert delta == s1 - s0


def test_objective_roi():
    """ROI最大化目的関数"""
    spec = ObjectiveSpec("roi", {"value_per_y": 1000, "cost_per_treated": 50}, "unitless")
    s0, s1, delta = eval_objective(100, 120, 50, 55, spec)

    # roi = (v*Y - c*T) / (c*T)
    assert s1 > s0  # 収益率が上がる


def test_digest_consistency():
    """ダイジェストの一貫性"""
    spec = ObjectiveSpec("profit", {"value_per_y": 1000}, "¥")
    params = {"coverage": 0.8, "budget_cap": 100000}

    digest1 = digest_of("dataset_123", params, spec)
    digest2 = digest_of("dataset_123", params, spec)

    # 同じ入力から同じダイジェスト
    assert digest1 == digest2
    assert len(digest1) == 16  # 16文字のハッシュ


def test_digest_different_inputs():
    """異なる入力から異なるダイジェスト"""
    spec = ObjectiveSpec("profit", {"value_per_y": 1000}, "¥")
    params1 = {"coverage": 0.8}
    params2 = {"coverage": 0.9}  # 異なるパラメータ

    digest1 = digest_of("dataset_123", params1, spec)
    digest2 = digest_of("dataset_123", params2, spec)

    assert digest1 != digest2


def test_get_formula_latex():
    """LaTeX式の取得"""
    spec_profit = ObjectiveSpec("profit", {}, "¥")
    latex = get_formula_latex(spec_profit)
    assert "J =" in latex or "v" in latex

    spec_roi = ObjectiveSpec("roi", {}, "unitless")
    latex_roi = get_formula_latex(spec_roi)
    assert "ROI" in latex_roi or "frac" in latex_roi
