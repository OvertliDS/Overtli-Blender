from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/material_texture_tools.py").read_text(encoding="utf-8")


def test_texture_map_slot_awareness_and_color_space_rules_exist() -> None:
    for text in [
        "MATERIAL_MAP_KINDS",
        "base_color_map",
        "roughness_map",
        "metallic_map",
        "ambient_occlusion_map",
        "metallic_roughness_map",
        "normal_map",
        "orm_map",
        "rma_map",
        "mra_map",
        "color_space_intent",
        "Non-Color",
        "sRGB",
        "automatic packed/AO channel mixing is not blindly connected",
    ]:
        assert text in ADDON_TEXT


def test_material_texture_mcp_tool_exists() -> None:
    assert "def register_material_texture_tools" in TOOLS_TEXT
    assert "def bind_material_texture_map(" in TOOLS_TEXT
