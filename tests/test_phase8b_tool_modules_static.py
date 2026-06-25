from pathlib import Path


def test_phase8b_tool_modules_exist_and_register_helpers():
    expected = {
        "modeling_schema_tools.py": "register_modeling_schema_tools",
        "profile_modeling_tools.py": "register_profile_modeling_tools",
        "modifier_construction_tools.py": "register_modifier_construction_tools",
        "reference_construction_tools.py": "register_reference_construction_tools",
        "sculpt_workflow_tools.py": "register_sculpt_workflow_tools",
        "cloth_pattern_tools.py": "register_cloth_pattern_tools",
        "construction_validation_tools.py": "register_construction_validation_tools",
    }
    for filename, helper in expected.items():
        text = Path("src/overtli_blender/tools", filename).read_text(encoding="utf-8")
        assert f"def {helper}" in text
        assert "send_command" in text


def test_phase8b_tools_registered_in_central_registry():
    text = Path("src/overtli_blender/tools/registry.py").read_text(encoding="utf-8")
    for helper in [
        "register_modeling_schema_tools",
        "register_profile_modeling_tools",
        "register_modifier_construction_tools",
        "register_reference_construction_tools",
        "register_sculpt_workflow_tools",
        "register_cloth_pattern_tools",
        "register_construction_validation_tools",
    ]:
        assert helper in text
