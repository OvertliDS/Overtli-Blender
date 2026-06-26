from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_check() -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    from overtli_blender.runtime.performance_budgets import load_performance_budgets

    budgets = load_performance_budgets(ROOT / "config" / "performance_budgets.json")
    addon_lines = len((ROOT / "addon.py").read_text(encoding="utf-8").splitlines())
    package_files = list((ROOT / "overtli_blender_addon").rglob("*.py"))
    largest = max((len(path.read_text(encoding="utf-8").splitlines()), path.relative_to(ROOT).as_posix()) for path in package_files)
    warnings = []
    if addon_lines > budgets["addon_py_max_lines"]:
        warnings.append(f"addon.py line budget exceeded: {addon_lines}")
    status = "passed" if not warnings else "warning"
    return {"status": status, "budgets": budgets, "addon_py_lines": addon_lines, "largest_module": largest[1], "largest_module_lines": largest[0], "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 10A performance budget checks.")
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run_check()
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status: {report['status']}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
    return 0 if report["status"] in {"passed", "warning"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
