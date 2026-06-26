"""Release-candidate manifest helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def build_release_candidate_manifest(root: Path, checks: dict) -> dict:
    failed = [name for name, result in checks.items() if result.get("status") not in {"passed", "success"}]
    ship_decision = "ship_candidate" if not failed else "needs_fixes"
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": "10B",
        "checks": checks,
        "ship_decision": ship_decision,
        "failed_checks": failed,
        "runtime_mode": "packaged_addon",
        "addon_package_path": "overtli_blender_addon",
        "addon_version": "0.1.0",
        "server_command_count": None,
        "tool_registry_count": None,
        "packaged_runtime_status": "PACKAGED_RUNTIME_STATIC_VERIFIED",
        "single_file_shim_status": "addon.py thin bootstrap only",
        "known_limitations": [
            "Packaged addon live verification requires a local Blender addon refresh and socket server; prior Phase 10A local evidence was live verified.",
            "Packaged addon source is modularized by runtime, UI, registration, adapters, shared helpers, and service domains.",
        ],
    }


def write_release_candidate_manifest(root: Path, checks: dict) -> Path:
    output_dir = root / ".overtli_blender" / "release_candidate"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_release_candidate_manifest(root, checks)
    path = output_dir / "phase10b_release_candidate_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path
