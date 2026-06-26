"""Phase 10A addon modularization audit helpers."""

from __future__ import annotations

from pathlib import Path


REQUIRED_PACKAGE_PATHS = [
    "overtli_blender_addon/__init__.py",
    "overtli_blender_addon/registration.py",
    "overtli_blender_addon/preferences.py",
    "overtli_blender_addon/runtime/dispatcher.py",
    "overtli_blender_addon/runtime/socket_server.py",
    "overtli_blender_addon/services/scene.py",
    "overtli_blender_addon/services/materials.py",
    "overtli_blender_addon/services/animation.py",
    "overtli_blender_addon/services/diagnostics.py",
]


def migration_audit(root: Path) -> dict:
    missing = [rel for rel in REQUIRED_PACKAGE_PATHS if not (root / rel).is_file()]
    addon_lines = len((root / "addon.py").read_text(encoding="utf-8").splitlines())
    largest_module = max(
        (
            len(path.read_text(encoding="utf-8").splitlines()),
            path.relative_to(root).as_posix(),
        )
        for path in (root / "overtli_blender_addon").rglob("*.py")
    )
    return {
        "status": "passed" if not missing and addon_lines <= 300 else "failed",
        "missing": missing,
        "addon_py_lines": addon_lines,
        "largest_module_lines": largest_module[0],
        "largest_module": largest_module[1],
        "canonical_runtime": "overtli_blender_addon/",
    }
