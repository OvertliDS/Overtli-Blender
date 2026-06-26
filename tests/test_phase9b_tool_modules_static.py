from pathlib import Path


def test_phase9b_tool_modules_exist_and_register_helpers():
    expected = {
        "preferences_tools.py": "register_preferences_tools",
        "tool_profile_tools.py": "register_tool_profile_tools",
        "bundled_skill_tools.py": "register_bundled_skill_tools",
        "addon_interop_tools.py": "register_addon_interop_tools",
        "error_catalog_tools.py": "register_error_catalog_tools",
        "onboarding_tools.py": "register_onboarding_tools",
        "ux_status_tools.py": "register_ux_status_tools",
    }
    for filename, helper in expected.items():
        text = Path("src/overtli_blender/tools", filename).read_text(encoding="utf-8")
        assert f"def {helper}" in text
        assert "send_command" in text


def test_phase9b_tools_registered_in_central_registry_and_package_init():
    registry_text = Path("src/overtli_blender/tools/registry.py").read_text(encoding="utf-8")
    init_text = Path("src/overtli_blender/tools/__init__.py").read_text(encoding="utf-8")
    for helper in [
        "register_preferences_tools", "register_tool_profile_tools", "register_bundled_skill_tools",
        "register_addon_interop_tools", "register_error_catalog_tools", "register_onboarding_tools",
        "register_ux_status_tools",
    ]:
        assert helper in registry_text
        assert helper in init_text
