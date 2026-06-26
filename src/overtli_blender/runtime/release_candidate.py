"""Release-candidate manifest helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def build_release_candidate_manifest(root: Path, checks: dict) -> dict:
    failed = [name for name, result in checks.items() if result.get("status") not in {"passed", "success"}]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": "10A",
        "checks": checks,
        "ship_decision": "ship_candidate" if not failed else "needs_fixes",
        "failed_checks": failed,
        "known_limitations": [
            "Packaged addon live verification requires a local Blender addon refresh and socket server.",
            "Packaged addon source is modularized by runtime, UI, registration, adapters, shared helpers, and service domains.",
        ],
    }


def write_release_candidate_manifest(root: Path, checks: dict) -> Path:
    output_dir = root / ".overtli_blender" / "release_candidate"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_release_candidate_manifest(root, checks)
    path = output_dir / "phase10a_release_candidate_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path
