from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_ENTRYPOINT = ROOT / "addon.py"
PACKAGE_ROOT = ROOT / "overtli_blender_addon"
TARGET_LINE_CAP = 300
HARD_LINE_CAP = 500

REQUIRED_FILES = [
    "overtli_blender_addon/__init__.py",
    "overtli_blender_addon/registration.py",
    "overtli_blender_addon/preferences.py",
    "overtli_blender_addon/operators.py",
    "overtli_blender_addon/runtime/dispatcher.py",
    "overtli_blender_addon/runtime/socket_server.py",
    "overtli_blender_addon/services/scene.py",
    "overtli_blender_addon/services/materials.py",
    "overtli_blender_addon/services/diagnostics.py",
    "overtli_blender_addon/ui/panels.py",
]

FORBIDDEN_ENTRYPOINT_MARKERS = [
    "class BlenderMCPServer",
    "socket.socket(",
    "ThreadingTCPServer",
    "COMMAND_HANDLERS",
    "_build_command_handlers",
]

FORBIDDEN_CLASS_SUFFIXES = (
    "Service",
    "Runtime",
    "Dispatcher",
    "Server",
)


def _syntax_check(path: Path) -> str | None:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return f"{path.relative_to(ROOT).as_posix()}: {exc}"
    return None


def run_check() -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    sys.path.insert(0, str(ROOT))

    if not ADDON_ENTRYPOINT.is_file():
        errors.append("addon.py is missing")
        return {"status": "failed", "errors": errors, "warnings": warnings}

    text = ADDON_ENTRYPOINT.read_text(encoding="utf-8")
    lines = text.splitlines()
    addon_line_count = len(lines)
    if addon_line_count > TARGET_LINE_CAP:
        warnings.append(f"addon.py exceeds target line cap {TARGET_LINE_CAP}: {addon_line_count}")
    if addon_line_count > HARD_LINE_CAP:
        errors.append(f"addon.py exceeds hard line cap {HARD_LINE_CAP}: {addon_line_count}")
    if "overtli_blender_addon" not in text or "importlib.import_module" not in text:
        errors.append("addon.py does not clearly delegate to overtli_blender_addon")

    tree = ast.parse(text, filename=str(ADDON_ENTRYPOINT))
    class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    service_like = [name for name in class_names if name.endswith(FORBIDDEN_CLASS_SUFFIXES)]
    if service_like:
        errors.append(f"addon.py defines service/runtime/server classes: {service_like}")
    for marker in FORBIDDEN_ENTRYPOINT_MARKERS:
        if marker in text:
            errors.append(f"addon.py contains forbidden runtime marker: {marker}")

    if not PACKAGE_ROOT.is_dir():
        errors.append("overtli_blender_addon package is missing")
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).is_file()]
    errors.extend(f"missing required package file: {rel}" for rel in missing)

    package_py_files = sorted(PACKAGE_ROOT.rglob("*.py")) if PACKAGE_ROOT.is_dir() else []
    syntax_errors = [error for path in package_py_files if (error := _syntax_check(path))]
    errors.extend(syntax_errors)

    importable_failures = []
    for path in package_py_files:
        rel = path.relative_to(ROOT).with_suffix("")
        module_name = ".".join(rel.parts)
        if importlib.util.find_spec(module_name) is None:
            importable_failures.append(module_name)
    if importable_failures:
        errors.append(f"package modules not import-resolvable: {importable_failures[:10]}")

    service_modules = [path.relative_to(ROOT).as_posix() for path in (PACKAGE_ROOT / "services").glob("*.py") if path.name != "__init__.py"]
    ui_modules = [path.relative_to(ROOT).as_posix() for path in (PACKAGE_ROOT / "ui").glob("*.py") if path.name != "__init__.py"]
    runtime_modules = [path.relative_to(ROOT).as_posix() for path in (PACKAGE_ROOT / "runtime").glob("*.py") if path.name != "__init__.py"]

    if not service_modules:
        errors.append("no service modules found under overtli_blender_addon/services")
    if not ui_modules:
        errors.append("no UI modules found under overtli_blender_addon/ui")
    if "overtli_blender_addon/runtime/socket_server.py" not in runtime_modules:
        errors.append("socket runtime module is missing")

    return {
        "status": "passed" if not errors else "failed",
        "addon_py_lines": addon_line_count,
        "target_line_cap": TARGET_LINE_CAP,
        "hard_line_cap": HARD_LINE_CAP,
        "delegates_to_package": "overtli_blender_addon" in text,
        "service_modules": service_modules,
        "runtime_modules": runtime_modules,
        "ui_modules": ui_modules,
        "required_files": REQUIRED_FILES,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Phase 10B addon modularity boundaries.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run_check()
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status: {report['status']}")
        print(f"addon.py lines: {report.get('addon_py_lines')}")
        for warning in report.get("warnings", []):
            print(f"warning: {warning}")
        for error in report.get("errors", []):
            print(f"error: {error}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
