from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/animation_tools.py").read_text(encoding="utf-8")


def test_phase5a_animation_services_and_commands_exist() -> None:
    for text in [
        "class AnimationIntelligenceService",
        "class AnimationAuthoringService",
        "self.animation_intelligence_service = AnimationIntelligenceService(self)",
        "self.animation_authoring_service = AnimationAuthoringService(self)",
        "get_timeline_info",
        "list_animated_objects",
        "get_animation_deep_info",
        "set_timeline_range",
        "set_current_frame",
        "insert_transform_keyframes",
        "animate_object_transform",
        "animate_camera_transform",
        "animate_light_property",
        "animate_material_property",
        "animate_shape_key_value",
        "delete_animation_data",
    ]:
        assert text in ADDON_TEXT


def test_phase5a_animation_mcp_wrappers_exist() -> None:
    assert "def register_animation_tools" in TOOLS_TEXT
    for command in [
        "get_timeline_info",
        "list_animated_objects",
        "get_animation_deep_info",
        "set_timeline_range",
        "set_current_frame",
        "insert_transform_keyframes",
        "animate_object_transform",
        "animate_camera_transform",
        "animate_light_property",
        "animate_material_property",
        "animate_shape_key_value",
        "delete_animation_data",
    ]:
        assert f'"{command}"' in TOOLS_TEXT
