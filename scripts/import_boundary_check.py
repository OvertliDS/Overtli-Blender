from __future__ import annotations

import argparse
import ast
import importlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
ADDON_ROOT = ROOT / "overtli_blender_addon"
ZIP_PATH = ROOT / ".overtli_blender" / "release" / "addon_zip" / "overtli_blender_addon_0.1.0.zip"


def _run_import(module_name: str) -> dict:
    code = (
        "import importlib, sys; "
        f"importlib.import_module({module_name!r}); "
        "print('ok')"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return {"status": "passed" if proc.returncode == 0 else "failed", "returncode": proc.returncode, "output": proc.stdout.strip()}


def _imports_from_file(path: Path) -> list[str]:
    imports: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _scan_imports(root: Path, forbidden: tuple[str, ...]) -> list[dict]:
    findings: list[dict] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for module in _imports_from_file(path):
            if any(module == item or module.startswith(f"{item}.") for item in forbidden):
                findings.append({"path": path.relative_to(ROOT).as_posix(), "import": module})
    return findings


def _zip_boundary_report() -> dict:
    if not ZIP_PATH.is_file():
        return {"status": "missing", "zip_path": str(ZIP_PATH.relative_to(ROOT)), "root_entries": [], "forbidden": []}
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = archive.namelist()
    root_entries = sorted({name.split("/", 1)[0] for name in names})
    forbidden = [
        name
        for name in names
        if name.startswith(("src/", "tests/", "scripts/", "docs/", "memory_bank/", ".overtli_blender/"))
        or name in {"addon.py", "AGENTS.md", ".env", "AIReview.config.json"}
    ]
    return {
        "status": "passed" if root_entries == ["overtli_blender_addon"] and not forbidden else "failed",
        "zip_path": str(ZIP_PATH.relative_to(ROOT)),
        "root_entries": root_entries,
        "forbidden": forbidden,
    }


def run_check() -> dict:
    sys.path.insert(0, str(SRC_ROOT))
    sys.path.insert(0, str(ROOT))
    mcp_import = _run_import("overtli_blender")
    server_import = _run_import("overtli_blender.server")
    mcp_findings = _scan_imports(SRC_ROOT / "overtli_blender", ("bpy", "overtli_blender_addon"))
    addon_findings = _scan_imports(ADDON_ROOT, ("overtli_blender.server", "mcp"))
    zip_report = _zip_boundary_report()

    package_import = {"status": "failed", "module": "overtli_blender_addon", "output": ""}
    try:
        importlib.import_module("overtli_blender_addon")
    except Exception as exc:
        package_import["output"] = str(exc)
    else:
        package_import["status"] = "passed"
        package_import["output"] = "ok"

    errors = []
    if mcp_import["status"] != "passed":
        errors.append("import overtli_blender failed")
    if server_import["status"] != "passed":
        errors.append("import overtli_blender.server failed")
    if mcp_findings:
        errors.append("MCP package imports Blender/addon modules at top level")
    if addon_findings:
        errors.append("addon package imports MCP/server modules at top level")
    if zip_report["status"] == "failed":
        errors.append("addon zip boundary failed")

    return {
        "status": "passed" if not errors else "failed",
        "mcp_import": mcp_import,
        "server_import": server_import,
        "addon_package_import": package_import,
        "mcp_forbidden_imports": mcp_findings,
        "addon_forbidden_imports": addon_findings,
        "addon_zip_boundary": zip_report,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Phase 10B import boundaries.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run_check()
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status: {report['status']}")
        for error in report["errors"]:
            print(f"error: {error}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
