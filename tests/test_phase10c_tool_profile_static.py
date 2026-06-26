from __future__ import annotations


def test_chatgpt_browser_default_profile_exists_and_is_bounded() -> None:
    from overtli_blender.runtime.tool_profiles import get_profile

    profile = get_profile("chatgpt_browser_default")
    assert profile is not None
    assert profile.permission_profile == "remote_browser_safe"
    assert profile.max_visible_tools <= 100
    assert "core" in profile.enabled_tool_packs
    assert "scene_intelligence" in profile.enabled_tool_packs
    assert "product_ux" in profile.enabled_tool_packs


def test_chatgpt_browser_default_hides_high_risk_tools() -> None:
    from overtli_blender.runtime.tool_profiles import get_profile

    profile = get_profile("chatgpt_browser_default")
    hidden = set(profile.hidden_risky_tools)
    assert "execute_code" in hidden
    assert "execute_blender_code" in hidden
    assert "execute_approved_file_delete" in hidden
    assert "execute_approved_addon_operator" in hidden
    assert "download_polyhaven_asset" in hidden
    assert "create_rodin_job" in hidden
