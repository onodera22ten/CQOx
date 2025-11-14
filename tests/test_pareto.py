"""
Test suite for backend/analysis/pareto.py
"""
import pytest
from backend.analysis.pareto import pareto_front, is_dominated


def test_pareto_front_basic():
    """Pareto最適フロンティアの基本テスト"""
    pts = [(10, 20), (12, 25), (12, 22), (9, 18)]
    out = pareto_front(pts)

    # (9, 18), (10, 20), (12, 25) がPareto最適
    assert (9, 18) in out
    assert (10, 20) in out
    assert (12, 25) in out
    assert (12, 22) not in out  # (12, 25)に支配される


def test_pareto_front_all_dominated_except_one():
    """1点のみがPareto最適"""
    pts = [(10, 10), (11, 9), (12, 8), (5, 15)]
    out = pareto_front(pts)
    assert out == [(5, 15)]  # コスト最小かつベネフィット最大


def test_is_dominated():
    """支配関係の判定"""
    assert is_dominated((10, 20), (9, 21))  # otherがコスト小・ベネフィット大
    assert not is_dominated((10, 20), (11, 19))  # pointの方が優位
    assert not is_dominated((10, 20), (10, 20))  # 同一点は支配されない
