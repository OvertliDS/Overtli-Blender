from __future__ import annotations


def test_phase10d_preference_defaults_include_profiles_and_approval_modes() -> None:
    from overtli_blender.runtime.preferences_schema import APPROVAL_MODES, default_preferences, validate_preferences

    prefs = default_preferences()
    security = prefs["security"]
    tools = prefs["tool_profiles"]
    filesystem = prefs["filesystem"]
    assert tools["active_profile"] == "full_standard"
    assert filesystem["permission_profile"] == "standard"
    assert security["default_local_tool_profile"] == "full_standard"
    assert security["default_local_permission_profile"] == "standard"
    assert security["default_local_approval_mode"] == "ask_for_high_destructive"
    assert security["default_browser_tool_profile"] == "browser_full_standard"
    assert security["default_browser_permission_profile"] == "browser_standard"
    assert security["default_browser_approval_mode"] == "ask_for_destructive_only"
    assert security["approval_timeout_seconds"] == 900
    for key in [
        "require_approval_for_external_writes",
        "require_approval_for_file_delete",
        "require_approval_for_raw_python",
        "require_approval_for_provider_downloads",
        "require_approval_for_addon_lifecycle",
    ]:
        assert security[key] is True
    assert security["browser_connector_write_policy"] == "safe_structured_writes_enabled"
    assert {"always_ask", "ask_for_medium_high", "ask_for_high_destructive", "ask_for_destructive_only", "full_access_developer", "read_only"} <= APPROVAL_MODES
    assert validate_preferences(prefs)["status"] == "success"


def test_addon_preferences_expose_phase10d_fields() -> None:
    text = open("overtli_blender_addon/preferences.py", encoding="utf-8").read()
    for marker in [
        "browser_full_standard",
        "browser_standard",
        "ask_for_destructive_only",
        "ask_for_high_destructive",
        "browser_mutation_path_status",
        "require_approval_for_raw_python",
        "require_approval_for_provider_downloads",
        "require_approval_for_file_delete",
        "require_approval_for_external_writes",
    ]:
        assert marker in text
