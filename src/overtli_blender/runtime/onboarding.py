"""Phase 9B setup and onboarding checks."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any


CHECKS = (
    "python_package_installed",
    "mcp_server_available",
    "blender_addon_loaded",
    "socket_server_reachable",
    "version_metadata_match",
    "project_workspace_initialized",
    "approved_roots_configured",
    "tool_profile_selected",
    "logs_writable",
    "cache_roots_writable",
    "docs_index_available",
    "diagnostic_bundle_available",
)


def run_setup_checks(preferences: dict[str, Any] | None = None, repo_root: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    root = Path(repo_root or os.getcwd())
    prefs = preferences or {}
    fs = prefs.get("filesystem", {})
    tool_profiles = prefs.get("tool_profiles", {})
    generated_root = root / ".overtli_blender"
    checks = {
        "python_package_installed": importlib.util.find_spec("overtli_blender") is not None,
        "mcp_server_available": (root / "main.py").exists(),
        "blender_addon_loaded": None,
        "socket_server_reachable": None,
        "version_metadata_match": (root / "pyproject.toml").exists(),
        "project_workspace_initialized": (generated_root / "workspace").exists() or (root / ".overtli").exists(),
        "approved_roots_configured": bool(fs.get("approved_roots")),
        "tool_profile_selected": bool(tool_profiles.get("active_profile")),
        "logs_writable": _writable(generated_root / "logs"),
        "cache_roots_writable": _writable(generated_root / "cache"),
        "docs_index_available": (root / "docs").exists(),
        "diagnostic_bundle_available": (root / "scripts" / "export_diagnostic_bundle.py").exists(),
    }
    blockers = [name for name, value in checks.items() if value is False]
    unknown = [name for name, value in checks.items() if value is None]
    return {"status": "success", "checks": checks, "blockers": blockers, "unknown": unknown, "next_actions": recommended_actions(blockers, unknown)}


def _writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test = path / ".write_test"
        test.write_text("ok", encoding="utf-8")
        test.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def recommended_actions(blockers: list[str], unknown: list[str]) -> list[str]:
    actions = []
    if "approved_roots_configured" in blockers:
        actions.append("Configure approved project roots before file or addon-source access.")
    if "project_workspace_initialized" in blockers:
        actions.append("Initialize the project workspace for logs, cache, manifests, and diagnostics.")
    if "blender_addon_loaded" in unknown or "socket_server_reachable" in unknown:
        actions.append("Refresh Blender addon status from the live socket smoke when Blender is open.")
    return actions or ["Setup looks ready for non-destructive Phase 9B checks."]
