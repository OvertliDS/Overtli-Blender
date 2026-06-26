from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/render_tools.py").read_text(encoding="utf-8")
SMOKE_TEXT = (ROOT / "scripts/smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_phase5a_render_services_and_wrappers_exist() -> None:
    for text in [
        "class RenderSettingsService",
        "class RenderArtifactService",
        "self.render_settings_service = RenderSettingsService(self)",
        "self.render_artifact_service = RenderArtifactService(self)",
        "def register_render_tools",
        "get_render_settings",
        "set_render_settings",
        "set_output_path",
        "render_still",
        "render_contact_sheet",
        "create_turntable_animation",
        "render_preview_animation",
    ]:
        assert text in ADDON_TEXT or text in TOOLS_TEXT


def test_phase5a_render_cost_limits_are_in_smoke() -> None:
    phase5a = SMOKE_TEXT[SMOKE_TEXT.index("def run_phase5a_full_smoke"):SMOKE_TEXT.index("def run_optional_modifier_ops_smoke")]
    for text in ["BLENDER_WORKBENCH", '"resolution_x": 320', '"resolution_y": 320', '"samples": 8', '"max_frames": 4', '"clamp_for_smoke": True']:
        assert text in phase5a
