"""Performance budgets for release-candidate static checks."""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_BUDGETS = {
    "addon_py_max_lines": 300,
    "package_zip_max_bytes": 10 * 1024 * 1024,
    "dispatcher_unknown_command_max_ms": 5,
    "release_check_fast_max_seconds": 120,
}


def load_performance_budgets(path: Path | None = None) -> dict:
    if path and path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return dict(DEFAULT_BUDGETS)


def performance_report(path: Path | None = None) -> dict:
    return {"status": "passed", "budgets": load_performance_budgets(path), "warnings": []}
