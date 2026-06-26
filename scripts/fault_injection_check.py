from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_check() -> dict:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "src"))
    from overtli_blender.runtime.fault_injection import missing_package_probe, unknown_command_probe
    from overtli_blender_addon.runtime.dispatcher import PackagedDispatcher

    probes = {
        "unknown_command": unknown_command_probe(PackagedDispatcher()),
        "missing_package_message": missing_package_probe("Install the Overtli-Blender addon zip built by scripts/build_addon_zip.py."),
    }
    failed = [name for name, result in probes.items() if result["status"] != "passed"]
    return {"status": "passed" if not failed else "failed", "probes": probes, "failed": failed}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 10A fault-injection checks.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run_check()
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status: {report['status']}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
