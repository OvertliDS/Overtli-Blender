from overtli_blender.runtime.tool_profiles import BUILTIN_TOOL_PROFILES, preview_profile_change, recommend_profile


def test_phase9b_tool_profiles_exist():
    for name in ["minimal", "safe_scene", "materials", "modeling", "animation", "full_standard", "developer", "read_only_review"]:
        assert name in BUILTIN_TOOL_PROFILES
        assert BUILTIN_TOOL_PROFILES[name].enabled_tool_packs


def test_phase9b_profile_preview_and_recommendation():
    preview = preview_profile_change("safe_scene", "developer")
    assert preview["requires_approval"] is True
    assert recommend_profile("bake a pbr material")["recommended_profile"]["name"] == "materials"
