"""
Test suite for backend/core/reco.py
"""
import pytest
from backend.core.reco import risk_from_ci, create_recommendation, Evidence


def test_risk_from_ci_low():
    """低リスク（下限が正）"""
    assert risk_from_ci((5.0, 10.0)) == "low"


def test_risk_from_ci_medium():
    """中リスク（下限が負、上限が正）"""
    assert risk_from_ci((-2.0, 5.0)) == "medium"


def test_risk_from_ci_high():
    """高リスク（上限が負または0）"""
    assert risk_from_ci((-10.0, -5.0)) == "high"
    assert risk_from_ci((-5.0, 0.0)) == "high"


def test_create_recommendation():
    """推奨の生成"""
    evidence = [Evidence("Model A", "https://...", "ベースライン実験")]
    reco = create_recommendation(
        action="Search +15%",
        expected_lift=1200.0,
        ci=(800.0, 1600.0),
        evidence=evidence
    )

    assert reco.action == "Search +15%"
    assert reco.expected_lift == 1200.0
    assert reco.ci == (800.0, 1600.0)
    assert reco.risk_level == "low"  # 下限が正
    assert len(reco.evidence) == 1
