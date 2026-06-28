from __future__ import annotations


def test_chatgpt_browser_default_profile_exists_and_is_bounded() -> None:
    from overtli_blender.runtime.tool_profiles import get_profile

    profile = get_profile("browser_full_standard")
    legacy = get_profile("chatgpt_browser_default")
    assert profile is not None
    assert legacy is not None
    assert legacy.to_dict() == profile.to_dict()
    assert profile.permission_profile == "browser_standard"
    assert profile.max_visible_tools <= 160
    assert "core" in profile.enabled_tool_packs
    assert "scene_intelligence" in profile.enabled_tool_packs
    assert "verified_editing" in profile.enabled_tool_packs
    assert "materials" in profile.enabled_tool_packs
    assert "animation_presentation" in profile.enabled_tool_packs
    assert "product_ux" in profile.enabled_tool_packs


def test_chatgpt_browser_default_hides_high_risk_tools() -> None:
    from overtli_blender.runtime.tool_profiles import get_profile

    profile = get_profile("browser_full_standard")
    hidden = set(profile.hidden_risky_tools)
    assert "execute_code" in hidden
    assert "execute_blender_code" in hidden
    assert "execute_approved_file_delete" in hidden
    assert "execute_approved_addon_operator" in hidden
    assert "download_polyhaven_asset" in hidden
    assert "create_rodin_job" in hidden
