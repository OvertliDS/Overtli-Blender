from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/material_intelligence_tools.py").read_text(encoding="utf-8")


def test_required_phase4a_templates_exist() -> None:
    for name in [
        "pbr_metal_gold",
        "pbr_metal_brushed",
        "pbr_plastic",
        "pbr_rubber",
        "pbr_ceramic",
        "pbr_clay",
        "glass_clear",
        "glass_frosted",
        "water_basic",
        "emission_neon",
        "toon_flat",
        "toon_rim",
        "fabric_woven",
        "leather_grain",
        "skin_basic",
        "stone_rough",
        "concrete_rough",
        "wood_procedural",
        "marble_procedural",
        "brick_procedural",
        "sci_fi_panel",
        "painted_metal",
        "car_paint_basic",
    ]:
        assert name in ADDON_TEXT


def test_template_recipe_fields_are_structured() -> None:
    for text in [
        "supported_parameters",
        "default_parameters",
        "channel_plan",
        "node_plan",
        "map_slots",
        "procedural_slots",
        "preview_shape",
        "risk_level",
        "known_limitations",
    ]:
        assert text in ADDON_TEXT
    assert "def get_supported_material_templates(" in TOOLS_TEXT
