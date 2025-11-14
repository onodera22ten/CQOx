"""
Test suite for backend/core/mode.py
"""
import pytest
from backend.core.mode import decide_mode, validate_mode_consistency


def test_mode_sutva():
    """SUTVAモードの判定"""
    params = {"neighbor_boost": 0.0, "network_size": 0}
    assert decide_mode(params) == "sutva"


def test_mode_interference_with_neighbor_boost():
    """neighbor_boostによる干渉モード判定"""
    params = {"neighbor_boost": 0.1, "network_size": 0}
    assert decide_mode(params) == "interference"


def test_mode_interference_with_network_size():
    """network_sizeによる干渉モード判定"""
    params = {"neighbor_boost": 0.0, "network_size": 100}
    assert decide_mode(params) == "interference"


def test_validate_mode_consistency_valid():
    """モードとパラメータの整合性が取れている"""
    params = {"neighbor_boost": 0.1}
    validate_mode_consistency("interference", params)  # エラーなし


def test_validate_mode_consistency_invalid():
    """モードとパラメータが矛盾"""
    params = {"neighbor_boost": 0.1}
    with pytest.raises(ValueError, match="sutva"):
        validate_mode_consistency("sutva", params)
