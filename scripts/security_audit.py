from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_check() -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    from overtli_blender.runtime.security_audit import audit_paths

    findings = []
    for path in (ROOT / "overtli_blender_addon").rglob("*"):
        if path.is_file():
            rel = path.relative_to(ROOT).as_posix()
            findings.extend(audit_paths([rel])["findings"])
    latest_zip = ROOT / ".overtli_blender" / "release" / "addon_zip" / "overtli_blender_addon_0.1.0.zip"
    if latest_zip.is_file():
        with zipfile.ZipFile(latest_zip) as archive:
            findings.extend(audit_paths(archive.namelist())["findings"])
    return {"status": "passed" if not findings else "failed", "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 10A static security audit.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run_check()
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status: {report['status']}")
        for finding in report["findings"]:
            print(f"{finding['severity']}: {finding['path']}: {finding['message']}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
