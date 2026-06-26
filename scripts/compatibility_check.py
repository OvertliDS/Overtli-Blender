from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_check() -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    from overtli_blender.runtime.compatibility_matrix import compatibility_report

    report = compatibility_report()
    required = {"addon_registration", "addon_install", "runtime_paths", "animation_apis", "geometry_nodes_apis"}
    missing = sorted(required - set(report["matrix"]))
    return {"status": "failed" if missing else report["status"], "missing": missing, **report}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 10A compatibility checks.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run_check()
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status: {report['status']}")
        for name in report.get("checked_surfaces", []):
            print(f"checked: {name}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
