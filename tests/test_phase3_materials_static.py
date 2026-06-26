from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/material_tools.py").read_text(encoding="utf-8")


def test_phase3_material_service_supports_required_commands() -> None:
    for name in [
        "def create_basic_material",
        "def assign_material",
        "def update_material_properties",
        "Principled BSDF",
        "base_color",
        "metallic",
        "roughness",
        "alpha",
    ]:
        assert name in ADDON_TEXT


def test_phase3_material_mcp_wrappers_exist() -> None:
    assert "def register_material_tools" in TOOLS_TEXT
    for name in ["create_basic_material", "assign_material", "update_material_properties"]:
        assert f"def {name}(" in TOOLS_TEXT
        assert f'"{name}"' in TOOLS_TEXT
