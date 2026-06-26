from __future__ import annotations

from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]


def test_import_boundary_check_exists() -> None:
    text = (ROOT / "scripts" / "import_boundary_check.py").read_text(encoding="utf-8")
    for marker in [
        "overtli_blender",
        "overtli_blender.server",
        "mcp_forbidden_imports",
        "addon_forbidden_imports",
        "addon_zip_boundary",
        "--json",
    ]:
        assert marker in text


def test_mcp_package_has_no_top_level_addon_or_bpy_imports() -> None:
    for path in (ROOT / "src" / "overtli_blender").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert "bpy" not in imports
        assert all(not name.startswith("overtli_blender_addon") for name in imports)
