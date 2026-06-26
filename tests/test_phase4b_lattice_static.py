from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/lattice_tools.py").read_text(encoding="utf-8")


def test_lattice_service_creates_updates_applies_and_removes_without_apply_modifier() -> None:
    for text in [
        "class LatticeDeformationService",
        "def create_lattice_deformer(",
        "def update_lattice_deformer(",
        "def apply_lattice_to_object(",
        "def remove_lattice_deformer(",
        'type="LATTICE"',
        "update_lattice_deformer requires confirm=True",
        "remove_lattice_deformer requires confirm=True",
        "delete_lattice_object",
    ]:
        assert text in ADDON_TEXT


def test_lattice_mcp_tools_exist() -> None:
    for text in [
        "def register_lattice_tools",
        "def create_lattice_deformer(",
        "def update_lattice_deformer(",
        "def apply_lattice_to_object(",
        "def remove_lattice_deformer(",
    ]:
        assert text in TOOLS_TEXT
