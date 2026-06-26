from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / ".overtli_blender" / "final_handoff"


def _run(args: list[str]) -> dict:
    proc = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {
        "status": "passed" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "command": [sys.executable, *args],
        "output_tail": proc.stdout[-6000:],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _latest_path(pattern: str) -> str | None:
    matches = sorted(ROOT.glob(pattern), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
    if not matches:
        return None
    return matches[0].relative_to(ROOT).as_posix()


def _ship_decision(checks: dict) -> str:
    failed = [name for name, result in checks.items() if result.get("status") not in {"passed", "success", "warning"}]
    if any(name in failed for name in ["security_audit", "build_addon_zip", "import_boundary_check"]):
        return "blocked"
    return "ship_candidate" if not failed else "needs_fixes"


def build_handoff(handoff_id: str | None = None) -> tuple[Path, dict]:
    handoff_id = handoff_id or datetime.now(timezone.utc).strftime("handoff_%Y%m%dT%H%M%SZ")
    handoff_dir = OUTPUT_ROOT / handoff_id
    handoff_dir.mkdir(parents=True, exist_ok=False)

    checks = {
        "release_check_fast": _run(["scripts/release_check.py", "--fast"]),
        "release_candidate_check": _run(["scripts/release_candidate_check.py", "--json"]),
        "addon_modularity_check": _run(["scripts/addon_modularity_check.py", "--json"]),
        "build_addon_zip": _run(["scripts/build_addon_zip.py", "--mode", "package", "--verify", "--json"]),
        "import_boundary_check": _run(["scripts/import_boundary_check.py", "--json"]),
        "docs_lockdown_check": _run(["scripts/docs_lockdown_check.py", "--json"]),
        "security_audit": _run(["scripts/security_audit.py", "--json"]),
        "compatibility_check": _run(["scripts/compatibility_check.py", "--json"]),
        "performance_check": _run(["scripts/performance_check.py", "--fast", "--json"]),
        "fault_injection_check": _run(["scripts/fault_injection_check.py", "--json"]),
        "diagnostic_bundle_export": _run(["scripts/export_diagnostic_bundle.py"]),
    }

    failed = [name for name, result in checks.items() if result.get("status") not in {"passed", "success", "warning"}]
    decision = _ship_decision(checks)
    created_at = datetime.now(timezone.utc).isoformat()
    addon_zip = _latest_path(".overtli_blender/release/addon_zip/*.zip")
    addon_manifest = _latest_path(".overtli_blender/release/addon_zip/*.manifest.json")
    diagnostic_manifest = _latest_path(".overtli_blender/diagnostics/*/manifest.json")

    ship_payload = {
        "handoff_id": handoff_id,
        "created_at": created_at,
        "decision": decision,
        "failed_checks": failed,
        "rules": {
            "ship_candidate": "all required gates pass",
            "needs_fixes": "non-blocking release gaps remain",
            "blocked": "install/package/security/privacy failure remains",
        },
    }

    artifact_payload = {
        "addon_zip": addon_zip,
        "addon_zip_manifest": addon_manifest,
        "diagnostic_bundle_manifest": diagnostic_manifest,
        "final_handoff_dir": handoff_dir.relative_to(ROOT).as_posix(),
        "generated_artifacts_are_ignored": True,
    }

    test_summary = {
        "pytest": "covered by release_check_fast in this aggregate",
        "static_phase10b_scripts": ["addon_modularity_check", "import_boundary_check", "final_release_handoff"],
        "checks": {name: result["status"] for name, result in checks.items()},
    }
    smoke_summary = {
        "packaged_runtime_status": "PACKAGED_RUNTIME_STATIC_VERIFIED",
        "live_smoke": "not run by final_release_handoff.py; run smoke_blender_addon_socket.py against Blender socket",
        "commands": [
            ".\\.venv\\Scripts\\python scripts\\smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status",
            ".\\.venv\\Scripts\\python scripts\\smoke_blender_addon_socket.py --timeout 30 --release-candidate-full",
        ],
    }

    _write_json(handoff_dir / "ship_decision.json", ship_payload)
    _write_json(handoff_dir / "artifact_manifest.json", artifact_payload)
    _write_json(handoff_dir / "addon_zip_manifest_pointer.json", {"manifest_path": addon_manifest, "zip_path": addon_zip})
    _write_json(handoff_dir / "diagnostic_bundle_pointer.json", {"manifest_path": diagnostic_manifest})
    _write_json(handoff_dir / "test_summary.json", test_summary)
    _write_json(handoff_dir / "smoke_summary.json", smoke_summary)
    _write_text(
        handoff_dir / "known_limitations.md",
        [
            "# Known Limitations",
            "",
            "- Live Blender socket verification is local/manual and is not run by CI.",
            "- `overtli_blender_addon/runtime/socket_server.py` remains the largest runtime module, though root `addon.py` is a thin entrypoint.",
            "- Provider downloads and raw Python execution remain opt-in/high-risk surfaces.",
        ],
    )
    _write_text(
        handoff_dir / "next_steps.md",
        [
            "# Next Steps",
            "",
            "- If decision is `ship_candidate`, draft the v0.1.0 tag/release only after explicit user approval.",
            "- If decision is `needs_fixes`, resolve failed gates before release prep.",
            "- If decision is `blocked`, stop feature work and resolve package/security/privacy blockers.",
        ],
    )

    manifest = {
        "handoff_id": handoff_id,
        "created_at": created_at,
        "phase": "10B",
        "status": "passed" if decision == "ship_candidate" else decision,
        "ship_decision": decision,
        "checks": checks,
        "artifacts": artifact_payload,
        "files": sorted(path.name for path in handoff_dir.iterdir()),
    }
    _write_json(handoff_dir / "handoff_manifest.json", manifest)
    return handoff_dir, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 10B final release handoff.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--handoff-id")
    args = parser.parse_args()
    try:
        handoff_dir, manifest = build_handoff(args.handoff_id)
    except Exception as exc:
        if args.as_json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"FAIL final_release_handoff: {exc}", file=sys.stderr)
        return 1
    payload = {
        "status": manifest["status"],
        "ship_decision": manifest["ship_decision"],
        "handoff_dir": str(handoff_dir),
        "handoff_manifest": str(handoff_dir / "handoff_manifest.json"),
        "failed_checks": [name for name, result in manifest["checks"].items() if result.get("status") not in {"passed", "success", "warning"}],
    }
    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"created {handoff_dir}")
        print(f"ship_decision: {manifest['ship_decision']}")
    return 0 if manifest["ship_decision"] == "ship_candidate" else 1


if __name__ == "__main__":
    raise SystemExit(main())
