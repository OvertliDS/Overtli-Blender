from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(args: list[str]) -> dict:
    proc = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {"status": "passed" if proc.returncode == 0 else "failed", "returncode": proc.returncode, "output": proc.stdout[-4000:]}


def run_check() -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    from overtli_blender.runtime.migration_audit import migration_audit
    from overtli_blender.runtime.release_candidate import write_release_candidate_manifest

    checks = {
        "migration_audit": migration_audit(ROOT),
        "addon_zip_package_verify": run_script(["scripts/build_addon_zip.py", "--mode", "package", "--verify", "--json"]),
        "compatibility": run_script(["scripts/compatibility_check.py", "--json"]),
        "performance": run_script(["scripts/performance_check.py", "--fast", "--json"]),
        "security": run_script(["scripts/security_audit.py", "--json"]),
        "fault_injection": run_script(["scripts/fault_injection_check.py", "--json"]),
        "docs_lockdown": run_script(["scripts/docs_lockdown_check.py", "--json"]),
    }
    manifest_path = write_release_candidate_manifest(ROOT, checks)
    failed = [name for name, result in checks.items() if result.get("status") not in {"passed", "success", "warning"}]
    return {"status": "passed" if not failed else "failed", "manifest_path": str(manifest_path), "failed": failed, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 10A release candidate checks.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run_check()
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status: {report['status']}")
        print(f"manifest: {report['manifest_path']}")
        for failed in report["failed"]:
            print(f"failed: {failed}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
