import os
import sys


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def test_comprehensive_agent_uses_metaphysics_point_tiers():
    from comprehensive_ai import COMPREHENSIVE_READING_MODES, calculate_cost

    assert [mode["display_cost"] for mode in COMPREHENSIVE_READING_MODES] == [300, 800, 1500]
    assert calculate_cost("basic", ["liuyao"], reading_mode="concise") == 300
    assert calculate_cost("basic", ["bazi", "qimen"], reading_mode="standard") == 800
    assert calculate_cost("basic", ["bazi", "qimen", "ziwei"], reading_mode="standard") == 1500
    assert calculate_cost("basic", ["qimen"], reading_mode="deep") == 1500
    assert calculate_cost("basic", ["qimen"], is_followup=True, reading_mode="standard") == 100


def test_recharge_packages_match_agent_point_tiers():
    from recharge_routes import RECHARGE_PACKAGES
    from points_service import POINT_RULES

    packages = {pkg["id"]: pkg for pkg in RECHARGE_PACKAGES}

    assert POINT_RULES["sign_in"] == 300
    assert packages["starter"]["points"] == 3000
    assert packages["starter"]["price"] == 9.9
    assert packages["standard"]["points"] == 12000
    assert packages["standard"]["price"] == 36
    assert packages["premium"]["points"] == 30000
    assert packages["premium"]["price"] == 68
