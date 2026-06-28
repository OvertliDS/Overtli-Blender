from __future__ import annotations


def test_chatgpt_browser_default_profile_exists_and_is_bounded() -> None:
    from overtli_blender.runtime.tool_profiles import get_profile

    profile = get_profile("browser_full_standard")
    legacy = get_profile("chatgpt_browser_default")
    assert profile is not None
    assert legacy is not None
    assert legacy.to_dict() == profile.to_dict()
    assert profile.permission_profile == "browser_standard"
    assert profile.max_visible_tools >= 500
    from overtli_blender.runtime.tool_packs import TOOL_PACK_DEFINITIONS
    assert set(TOOL_PACK_DEFINITIONS) <= set(profile.enabled_tool_packs)


def test_chatgpt_browser_default_hides_no_tools() -> None:
    from overtli_blender.runtime.tool_profiles import get_profile

    profile = get_profile("browser_full_standard")
    assert profile is not None
    assert profile.hidden_risky_tools == ()
