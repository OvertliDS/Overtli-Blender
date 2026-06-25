from pathlib import Path


def test_phase9a_tool_modules_exist_and_register_helpers():
    expected = {
        "animation_intelligence_advanced_tools.py": "register_animation_intelligence_advanced_tools",
        "action_library_tools.py": "register_action_library_tools",
        "fcurve_tools.py": "register_fcurve_tools",
        "nla_tools.py": "register_nla_tools",
        "driver_tools.py": "register_driver_tools",
        "rig_template_tools.py": "register_rig_template_tools",
        "rig_validation_tools.py": "register_rig_validation_tools",
        "pose_library_tools.py": "register_pose_library_tools",
        "shot_workflow_tools.py": "register_shot_workflow_tools",
        "simulation_workflow_tools.py": "register_simulation_workflow_tools",
        "motion_validation_tools.py": "register_motion_validation_tools",
    }
    for filename, helper in expected.items():
        text = Path("src/overtli_blender/tools", filename).read_text(encoding="utf-8")
        assert f"def {helper}" in text
        assert "send_command" in text


def test_phase9a_tools_registered_in_central_registry_and_package_init():
    registry_text = Path("src/overtli_blender/tools/registry.py").read_text(encoding="utf-8")
    init_text = Path("src/overtli_blender/tools/__init__.py").read_text(encoding="utf-8")
    for helper in [
        "register_animation_intelligence_advanced_tools",
        "register_action_library_tools",
        "register_fcurve_tools",
        "register_nla_tools",
        "register_driver_tools",
        "register_rig_template_tools",
        "register_rig_validation_tools",
        "register_pose_library_tools",
        "register_shot_workflow_tools",
        "register_simulation_workflow_tools",
        "register_motion_validation_tools",
    ]:
        assert helper in registry_text
        assert helper in init_text
