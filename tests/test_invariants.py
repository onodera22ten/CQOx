"""
Test suite for backend/core/invariants.py
"""
import pytest
from backend.core.invariants import (
    assert_shapley_simplex,
    assert_sankey_conservation,
    assert_heatmap_base_is_one,
    assert_survival_monotone_down,
    assert_ci_order,
    assert_probability_range,
)


def test_shapley_simplex_valid():
    """有効なShapley値"""
    assert_shapley_simplex([0.3, 0.5, 0.2])  # 合計=1
    assert_shapley_simplex([30.0, 50.0, 20.0])  # 合計=100


def test_shapley_simplex_invalid():
    """無効なShapley値"""
    with pytest.raises(ValueError, match="not in"):
        assert_shapley_simplex([0.3, 0.5, 0.3])  # 合計=1.1

    with pytest.raises(ValueError, match="NaN"):
        assert_shapley_simplex([0.5, float("nan"), 0.5])


def test_sankey_conservation_valid():
    """有効なSankey流量"""
    assert_sankey_conservation([100, 200], [150, 150])  # 合計一致


def test_sankey_conservation_invalid():
    """無効なSankey流量"""
    with pytest.raises(ValueError, match="not conserved"):
        assert_sankey_conservation([100, 200], [100, 150])  # 合計不一致


def test_heatmap_base_valid():
    """有効なHeatmapベース行"""
    matrix = [
        [1.0, 1.0, 1.0],  # Base行
        [1.2, 0.9, 1.1],  # Scenario A
    ]
    assert_heatmap_base_is_one(matrix, base_row=0)


def test_heatmap_negative_values():
    """負の値を含むHeatmap"""
    matrix = [
        [1.0, -0.5, 1.0],  # 負の値
    ]
    with pytest.raises(ValueError, match="positive"):
        assert_heatmap_base_is_one(matrix, base_row=0)


def test_survival_monotone_valid():
    """有効なSurvival曲線"""
    assert_survival_monotone_down([1.0, 0.9, 0.8, 0.7, 0.6])


def test_survival_monotone_invalid():
    """無効なSurvival曲線（増加）"""
    with pytest.raises(ValueError, match="non-increasing"):
        assert_survival_monotone_down([1.0, 0.9, 0.95, 0.7])


def test_ci_order_valid():
    """有効な信頼区間"""
    assert_ci_order(10.0, 20.0)


def test_ci_order_invalid():
    """無効な信頼区間（逆順）"""
    with pytest.raises(ValueError, match="must be <"):
        assert_ci_order(20.0, 10.0)


def test_probability_range_valid():
    """有効な確率値"""
    assert_probability_range([0.0, 0.5, 1.0])


def test_probability_range_invalid():
    """範囲外の確率値"""
    with pytest.raises(ValueError, match="out of range"):
        assert_probability_range([0.5, 1.5])
