from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/shape_key_tools.py").read_text(encoding="utf-8")


def test_shape_key_service_preserves_basis_and_requires_confirmation_for_offsets() -> None:
    for text in [
        "class ShapeKeyService",
        "def create_shape_key(",
        "def update_shape_key_value(",
        "def edit_shape_key_offsets(",
        "def list_shape_keys(",
        "def delete_shape_keys(",
        'obj.shape_key_add(name="Basis"',
        "Refusing to edit Basis shape key",
        "edit_shape_key_offsets requires confirm=True",
        "inflate_along_normals",
        "scale_from_center",
        "bend_approx",
    ]:
        assert text in ADDON_TEXT


def test_shape_key_mcp_tools_exist() -> None:
    for text in [
        "def register_shape_key_tools",
        "def create_shape_key(",
        "def update_shape_key_value(",
        "def edit_shape_key_offsets(",
        "def list_shape_keys(",
        "def delete_shape_keys(",
    ]:
        assert text in TOOLS_TEXT
