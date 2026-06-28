from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/workflow_intelligence_tools.py").read_text(encoding="utf-8")


EXPANDED_COMMANDS = [
    "get_method_plan",
    "list_operation_playbooks",
    "get_tricks_knowledge_base",
    "get_anti_pattern_rules",
    "get_modifier_recipes",
    "score_selection_confidence",
    "scan_blender_asset_libraries",
    "preview_asset",
    "import_texture_folder",
    "create_style_material",
    "create_paintable_texture",
    "delete_images",
    "list_uv_maps",
    "create_vertex_group_from_uv_island",
    "measure_object",
    "measure_distance",
    "create_proportional_deformation",
    "get_sculpt_status",
    "configure_sculpt_brush",
    "create_sculpt_mask_from_vertex_group",
    "run_shape_key_sculpt_workflow",
]


def test_expanded_phase4b_services_exist() -> None:
    for text in [
        "class MethodIntelligenceService",
        "class AssetMaterialWorkflowService",
        "class UVSelectionMeasurementService",
        "class SculptWorkflowService",
        "PLAYBOOKS",
        "ANTI_PATTERNS",
        "MODIFIER_RECIPES",
        "SUPPORTED_BRUSHES",
        "shape-key sculpt workflow",
    ]:
        assert text in ADDON_TEXT


def test_expanded_phase4b_commands_are_dispatched() -> None:
    for name in EXPANDED_COMMANDS:
        assert f"def {name}(" in ADDON_TEXT
        assert f'"{name}": self.{name}' in ADDON_TEXT


def test_expanded_phase4b_mcp_wrappers_exist() -> None:
    assert "def register_workflow_intelligence_tools" in TOOLS_TEXT
    for name in EXPANDED_COMMANDS:
        assert f"def {name}(" in TOOLS_TEXT


def test_expanded_phase4b_guards_are_present() -> None:
    for text in [
        "configure_sculpt_brush requires confirm=True",
        "create_sculpt_mask_from_vertex_group requires confirm=True",
        "run_shape_key_sculpt_workflow requires confirm=True",
        "create_vertex_group_from_uv_island requires confirm=True",
        "delete_images requires confirm=True",
        "island_seed_face_index is required for UV island traversal",
        "uv_edge_connectivity",
    ]:
        assert text in ADDON_TEXT
