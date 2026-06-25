from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/selection_tools.py").read_text(encoding="utf-8")


def test_selection_intelligence_service_and_commands_exist() -> None:
    for text in [
        "class SelectionIntelligenceService",
        "def get_selection_deep_info(",
        "def get_mesh_component_summary(",
        '"get_selection_deep_info": self.get_selection_deep_info',
        '"get_mesh_component_summary": self.get_mesh_component_summary',
        "component_selection",
        "material_slots",
        "vertex_groups",
        "triangles_estimate",
    ]:
        assert text in ADDON_TEXT


def test_selection_mcp_tools_exist() -> None:
    for text in [
        "def register_selection_tools",
        "def get_selection_deep_info(",
        "def get_mesh_component_summary(",
        '"get_selection_deep_info"',
        '"get_mesh_component_summary"',
    ]:
        assert text in TOOLS_TEXT
