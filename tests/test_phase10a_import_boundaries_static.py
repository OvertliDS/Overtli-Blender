from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mcp_server_does_not_import_addon_or_bpy_at_startup() -> None:
    text = (ROOT / "src" / "overtli_blender" / "server.py").read_text(encoding="utf-8")
    assert "import bpy" not in text
    assert "overtli_blender_addon" not in text


def test_addon_package_does_not_import_mcp_server() -> None:
    for path in (ROOT / "overtli_blender_addon").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "overtli_blender.server" not in text
        assert "import mcp" not in text


def test_tests_do_not_import_bpy() -> None:
    for path in (ROOT / "tests").glob("test_*.py"):
        text = path.read_text(encoding="utf-8")
        assert "\nimport bpy" not in text
        assert "\nfrom bpy" not in text
