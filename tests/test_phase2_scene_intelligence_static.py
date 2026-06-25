from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
SCENE_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/scene_intelligence_tools.py").read_text(encoding="utf-8")


PHASE2_SCENE_COMMANDS = [
    "get_scene_index",
    "get_object_deep_info",
    "get_selection_info",
    "get_scene_health",
]


def test_addon_defines_scene_intelligence_service() -> None:
    assert "class SceneIntelligenceService" in ADDON_TEXT
    assert "self.scene_intelligence_service = SceneIntelligenceService(self)" in ADDON_TEXT


def test_addon_maps_phase2_scene_commands() -> None:
    for command in PHASE2_SCENE_COMMANDS:
        assert f'"{command}": self.{command}' in ADDON_TEXT
        assert f"def {command}(" in ADDON_TEXT


def test_scene_index_source_contains_expected_shape_keys() -> None:
    for key in [
        '"frame_current"',
        '"unit_system"',
        '"render_engine"',
        '"bound_box_world"',
        '"material_names"',
        '"modifier_names"',
        '"constraint_names"',
        '"truncated"',
    ]:
        assert key in ADDON_TEXT


def test_deep_object_source_contains_bounded_inspection_keys() -> None:
    for key in [
        '"mesh_stats"',
        '"triangles_estimate"',
        '"matrix_world"',
        '"type_specific"',
        '"custom_properties"',
        '"Object not found:',
    ]:
        assert key in ADDON_TEXT


def test_selection_and_health_source_contains_expected_keys() -> None:
    for key in [
        '"active_object"',
        '"selected_objects"',
        '"selection_bounds"',
        '"objects_with_negative_scale"',
        '"objects_with_unapplied_scale"',
        '"NO_CAMERA"',
        '"MISSING_MATERIALS"',
    ]:
        assert key in ADDON_TEXT


def test_scene_intelligence_tool_module_registers_phase2_tools() -> None:
    assert "def register_scene_intelligence_tools" in SCENE_TOOLS_TEXT
    for command in PHASE2_SCENE_COMMANDS:
        assert f"def {command}(" in SCENE_TOOLS_TEXT
        assert f'"{command}"' in SCENE_TOOLS_TEXT
