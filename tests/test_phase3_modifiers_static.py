from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/modifier_tools.py").read_text(encoding="utf-8")


def test_phase3_modifier_allowlists_are_present() -> None:
    for text in [
        "SUPPORTED_MODIFIERS",
        "ALLOWED_PROPERTIES",
        "BEVEL",
        "SUBSURF",
        "SOLIDIFY",
        "MIRROR",
        "ARRAY",
        "WEIGHTED_NORMAL",
        "TRIANGULATE",
        "DECIMATE",
        "Unsupported modifier property skipped",
        "remove_object_modifier requires confirm=True",
    ]:
        assert text in ADDON_TEXT


def test_phase3_modifier_mcp_wrappers_exist() -> None:
    assert "def register_modifier_tools" in TOOLS_TEXT
    for name in ["add_object_modifier", "update_object_modifier", "remove_object_modifier"]:
        assert f"def {name}(" in TOOLS_TEXT
        assert f'"{name}"' in TOOLS_TEXT
