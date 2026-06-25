from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/compositor_tools.py").read_text(encoding="utf-8")


def test_phase5a_compositor_service_and_wrappers_exist() -> None:
    for text in [
        "class CompositorPassService",
        "self.compositor_pass_service = CompositorPassService(self)",
        "get_compositor_status",
        "set_compositor_preset",
        "set_render_passes",
        "def register_compositor_tools",
    ]:
        assert text in ADDON_TEXT or text in TOOLS_TEXT


def test_phase5a_compositor_is_preset_only() -> None:
    assert "basic_viewer" in ADDON_TEXT
    assert "confirm_replace" in ADDON_TEXT
    assert "arbitrary" not in TOOLS_TEXT.lower()
