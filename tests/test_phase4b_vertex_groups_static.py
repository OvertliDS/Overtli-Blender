from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/vertex_group_tools.py").read_text(encoding="utf-8")


def test_vertex_group_service_supports_required_modes_and_guards() -> None:
    for text in [
        "class VertexGroupService",
        "def create_vertex_group(",
        "def update_vertex_group_weights(",
        "def list_vertex_groups(",
        "def delete_vertex_groups(",
        "by_axis",
        "by_bounds",
        "by_material_slot",
        "by_proximity_to_object",
        "selected_vertices",
        "delete_vertex_groups requires confirm=True",
    ]:
        assert text in ADDON_TEXT


def test_vertex_group_mcp_tools_exist() -> None:
    for text in [
        "def register_vertex_group_tools",
        "def create_vertex_group(",
        "def update_vertex_group_weights(",
        "def list_vertex_groups(",
        "def delete_vertex_groups(",
    ]:
        assert text in TOOLS_TEXT
