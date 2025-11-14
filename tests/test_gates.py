"""
Test suite for backend/core/gates.py
"""
import pytest
from backend.core.gates import check_gates, get_gate_remediation


def test_gates_all_pass():
    """すべてのゲートを通過"""
    diag = {
        "overlap_rate": 0.95,
        "t_stat": 3.0,
        "se": 0.1,
        "tau": 1.0,
        "ci_width": 0.5,
        "did_trend_p": 0.5,
        "iv_first_stage_F": 15.0,
        "rosenbaum_gamma": 1.5,
        "smd_max": 0.12,
        "vif_max": 5.0,
        "mape": 10.0,
    }
    result = check_gates(diag)
    assert result.ok
    assert len(result.reasons) == 0


def test_gates_overlap_fail():
    """Overlap不足で失敗"""
    diag = {"overlap_rate": 0.05}
    result = check_gates(diag)
    assert not result.ok
    assert "POOR_OVERLAP" in result.reasons


def test_gates_iv_weak():
    """IV First-stage F が弱い"""
    diag = {"iv_first_stage_F": 8.0}
    result = check_gates(diag)
    assert not result.ok
    assert "IV_WEAK_F" in result.reasons


def test_gate_remediation():
    """改善アクションの取得"""
    remedy = get_gate_remediation("POOR_OVERLAP")
    assert "action" in remedy
    assert "description" in remedy
    assert len(remedy["action"]) > 0
