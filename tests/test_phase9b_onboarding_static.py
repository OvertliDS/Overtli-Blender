from overtli_blender.runtime.onboarding import CHECKS, run_setup_checks


def test_phase9b_onboarding_checks_are_structured():
    result = run_setup_checks({"filesystem": {}, "tool_profiles": {"active_profile": "safe_scene"}})
    assert result["status"] == "success"
    assert set(CHECKS) == set(result["checks"])
    assert isinstance(result["next_actions"], list)
