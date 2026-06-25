from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
CAMERA_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/camera_tools.py").read_text(encoding="utf-8")
LIGHTING_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/lighting_tools.py").read_text(encoding="utf-8")


def test_phase5a_camera_lighting_services_exist() -> None:
    for text in [
        "class CameraCompositionService",
        "class LightingSetupService",
        "self.camera_composition_service = CameraCompositionService(self)",
        "self.lighting_setup_service = LightingSetupService(self)",
        "create_camera",
        "frame_camera_to_objects",
        "set_active_camera",
        "create_light",
        "create_lighting_setup",
        "update_light",
        "set_world_lighting",
    ]:
        assert text in ADDON_TEXT


def test_phase5a_camera_lighting_mcp_wrappers_exist() -> None:
    assert "def register_camera_tools" in CAMERA_TOOLS_TEXT
    assert "def register_lighting_tools" in LIGHTING_TOOLS_TEXT
    for command in ["create_camera", "frame_camera_to_objects", "set_active_camera"]:
        assert f'"{command}"' in CAMERA_TOOLS_TEXT
    for command in ["create_light", "create_lighting_setup", "update_light", "set_world_lighting"]:
        assert f'"{command}"' in LIGHTING_TOOLS_TEXT
