from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase8a_tool_modules_exist_and_register_helpers():
    expected = {
        "src/overtli_blender/tools/bake_tools.py": "register_bake_tools",
        "src/overtli_blender/tools/image_resource_tools.py": "register_image_resource_tools",
        "src/overtli_blender/tools/channel_packing_tools.py": "register_channel_packing_tools",
    }
    for rel, helper in expected.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert f"def {helper}" in text
        assert "bpy" not in text


def test_phase8a_tools_registered_in_central_registry():
    text = (ROOT / "src/overtli_blender/tools/registry.py").read_text(encoding="utf-8")
    for helper in ("register_bake_tools", "register_image_resource_tools", "register_channel_packing_tools"):
        assert helper in text
