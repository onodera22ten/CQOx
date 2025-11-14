"""
Test suite for backend/core/metrics.py
"""
import pytest
from backend.core.metrics import (
    roi, roas, choose_roi, money_tick, MoneyFmt, cac, ltv_simple
)


def test_roi_basic():
    """ROI計算の基本テスト"""
    assert roi(1200, 1000) == 0.2  # (1200-1000)/1000 = 0.2
    assert roi(1000, 1000) == 0.0  # 損益分岐
    assert roi(800, 1000) == -0.2  # 赤字


def test_roi_edge_cases():
    """ROIのエッジケース"""
    import math
    assert math.isnan(roi(100, 0))  # コストゼロ
    assert math.isnan(roi(100, -10))  # 負のコスト


def test_roas_basic():
    """ROAS計算の基本テスト"""
    assert roas(1200, 1000) == 1.2  # 1200/1000
    assert roas(2000, 1000) == 2.0


def test_choose_roi_with_env(monkeypatch):
    """環境変数によるROI/ROAS切替"""
    # ROIモード
    monkeypatch.setenv("ROI_DEF", "roi")
    assert choose_roi(1200, 1000) == 0.2

    # ROASモード
    monkeypatch.setenv("ROI_DEF", "roas")
    assert choose_roi(1200, 1000) == 1.2


def test_money_tick_usd():
    """USD通貨フォーマット"""
    fmt = MoneyFmt("USD", 2)
    assert money_tick(1234.567, fmt) == "$1234.57"
    assert money_tick(1000.0, fmt) == "$1000.00"


def test_money_tick_jpy():
    """JPY通貨フォーマット"""
    fmt = MoneyFmt("JPY", 0)
    assert money_tick(1234.567, fmt) == "¥1235"
    assert money_tick(1000.4, fmt) == "¥1000"


def test_cac():
    """CAC計算"""
    assert cac(10000, 100) == 100.0  # 10000/100
    assert cac(5000, 50) == 100.0


def test_ltv_simple():
    """簡易LTV計算"""
    assert ltv_simple(100, 0.1) == 1000.0  # 100/0.1
    assert ltv_simple(50, 0.05) == 1000.0
