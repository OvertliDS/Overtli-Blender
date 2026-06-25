from __future__ import annotations

import argparse
import importlib
import json
import py_compile
import re
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIVACY_SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "pyproject.toml",
    ROOT / "addon.py",
    ROOT / "main.py",
    ROOT / "src",
    ROOT / "docs",
    ROOT / "tests",
    ROOT / "scripts",
    ROOT / ".github",
]
PRIVATE_ALLOWED = {
    "memory_bank/research/blender_python_reference_5_1_md",
    "blender_python_reference_5_1_md",
    "memory_bank_excluded",
    "include_memory_bank",
    "memory_bank/",
}
STALE_ALLOWED_FILES = {
    "docs/architecture_refactor_plan.md",
    "docs/current_tool_inventory.md",
    "docs/phase_0_repo_orientation.md",
    "docs/rebrand_plan.md",
    "docs/upstream_diff_plan.md",
    "tests/test_repo_baseline.py",
    "tests/test_phase7a_release_hardening_static.py",
    "scripts/check_install_docs.py",
    "scripts/release_check.py",
}
SECRET_ALLOWED_FILES = {
    "addon.py",
    "src/overtli_blender/common/safety.py",
    "src/overtli_blender/tools/addon_development_tools.py",
    "docs/release_check.md",
    "docs/review_package_protocol.md",
    "tests/test_phase7a_ci_static.py",
    "scripts/release_check.py",
    "scripts/export_diagnostic_bundle.py",
}
SECRET_RE = re.compile(r"(api[_-]?key|secret|token|password|credential|\\.env)", re.IGNORECASE)


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def record(checks: dict[str, str], name: str, fn) -> None:
    try:
        fn()
    except Exception as exc:
        checks[name] = f"failed: {exc}"
    else:
        checks[name] = "passed"


def require_command(args: list[str]) -> None:
    proc = run(args)
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout.strip() or f"command failed: {' '.join(args)}")


def check_git_status() -> None:
    proc = run(["git", "status", "--short", "--untracked-files=all"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout.strip())


def check_pyproject() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    if project["name"] != "overtli-blender":
        raise RuntimeError("project.name must be overtli-blender")
    if project["scripts"].get("overtli-blender") != "overtli_blender.server:main":
        raise RuntimeError("overtli-blender console script must point to overtli_blender.server:main")
    namespace: dict[str, str] = {}
    exec((ROOT / "src" / "overtli_blender" / "__init__.py").read_text(encoding="utf-8"), namespace)
    if project["version"] != namespace.get("__version__"):
        raise RuntimeError("pyproject version and overtli_blender.__version__ differ")


def check_import() -> None:
    module = importlib.import_module("overtli_blender")
    if module.__name__ != "overtli_blender":
        raise RuntimeError("unexpected import package")


def iter_scan_files():
    for root in PRIVACY_SCAN_PATHS:
        if not root.exists():
            continue
        if root.is_file():
            yield root
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".md", ".toml", ".yml", ".yaml", ".json"}:
                parts = set(path.relative_to(ROOT).as_posix().split("/"))
                if parts & {"__pycache__", ".pytest_cache"}:
                    continue
                yield path


def check_privacy_scan() -> None:
    hits = []
    for path in iter_scan_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in SECRET_ALLOWED_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in SECRET_RE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            context = text[max(0, match.start() - 80): match.end() + 80]
            if "subtype=\"PASSWORD\"" in context or "PHASE6B_SECRET_RE" in context or "SECRET_RE" in context or "REDACTION_KEYS" in context:
                continue
            hits.append(f"{rel}:{line}:{match.group(0)}")
    if hits:
        raise RuntimeError("; ".join(hits[:20]))


def check_stale_identity_scan() -> None:
    hits = []
    for path in iter_scan_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for stale in ["blender-mcp-enhanced", "BlenderMCP Enhanced", "src/blender_mcp", "uvx install blender-mcp-enhanced"]:
            if stale in text and rel not in STALE_ALLOWED_FILES:
                hits.append(f"{rel}:{stale}")
    if hits:
        raise RuntimeError("; ".join(hits[:20]))


def check_addon_entrypoint() -> None:
    py_compile.compile(str(ROOT / "addon.py"), doraise=True)
    text = (ROOT / "addon.py").read_text(encoding="utf-8")
    if "bl_info" not in text or "Overtli-Blender" not in text:
        raise RuntimeError("addon.py missing bl_info or Overtli-Blender identity")


def check_smoke_script_static() -> None:
    py_compile.compile(str(ROOT / "scripts" / "smoke_blender_addon_socket.py"), doraise=True)
    text = (ROOT / "scripts" / "smoke_blender_addon_socket.py").read_text(encoding="utf-8")
    if "import bpy" in text:
        raise RuntimeError("smoke script must not import bpy")


def check_phase7b_governance_static() -> None:
    from overtli_blender.runtime.command_registry import build_command_registry, command_registry_report
    from overtli_blender.runtime.tool_packs import TOOL_PACK_DEFINITIONS

    registry = build_command_registry()
    required = [
        "discover_tool_packs",
        "search_tools",
        "get_tool_spec",
        "prepare_operation",
        "get_pending_approvals",
        "approve_operation",
        "deny_operation",
        "execute_approved_operation",
        "get_operation_status",
        "list_recent_operations",
        "cancel_operation",
        "get_permission_profile",
        "get_capability_policy",
        "validate_command_capabilities",
        "get_log_status",
    ]
    missing = [name for name in required if name not in registry]
    if missing:
        raise RuntimeError(f"missing governance command specs: {missing}")
    if "core" not in TOOL_PACK_DEFINITIONS or "geometry_nodes" not in TOOL_PACK_DEFINITIONS:
        raise RuntimeError("tool pack definitions incomplete")
    if not (ROOT / "src" / "overtli_blender" / "runtime" / "approval.py").is_file():
        raise RuntimeError("approval runtime missing")
    if not (ROOT / "src" / "overtli_blender" / "runtime" / "operation_response.py").is_file():
        raise RuntimeError("operation response helper missing")
    if not (ROOT / "overtli_blender_addon" / "registration.py").is_file():
        raise RuntimeError("packaged addon scaffold missing")
    if not (ROOT / "docs" / "packaged_addon_migration.md").is_file():
        raise RuntimeError("packaged addon migration docs missing")
    registry_text = (ROOT / "src" / "overtli_blender" / "tools" / "registry.py").read_text(encoding="utf-8")
    if "register_governance_tools" not in registry_text:
        raise RuntimeError("governance tools are not registered")
    report = command_registry_report()
    if report["command_count"] < 100:
        raise RuntimeError("command registry unexpectedly small")


def run_full_checks(checks: dict[str, str], args: argparse.Namespace, warnings: list[str]) -> None:
    if not args.skip_build:
        def build_package() -> None:
            from build_python_package import has_build, build_package as build_python_package

            if not has_build():
                warnings.append('build package missing; install with python -m pip install -e ".[dev]"')
                raise RuntimeError("missing build dependency")
            build_python_package()
        record(checks, "python_package_build", build_package)

    if not args.skip_package:
        def addon_zip() -> None:
            from build_addon_zip import build_addon_zip

            build_addon_zip(overwrite=True)
        record(checks, "addon_zip_build", addon_zip)

        def diagnostic_bundle() -> None:
            from export_diagnostic_bundle import export_bundle

            export_bundle()
        record(checks, "diagnostic_bundle", diagnostic_bundle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Overtli-Blender release readiness checks.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fast", action="store_true", help="Run static release checks only.")
    mode.add_argument("--full", action="store_true", help="Run static checks plus package/artifact checks.")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-package", action="store_true")
    parser.add_argument("--skip-privacy", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    if not args.fast and not args.full:
        args.fast = True

    checks: dict[str, str] = {}
    warnings: list[str] = []
    record(checks, "python_version", lambda: sys.version_info >= (3, 10) or (_ for _ in ()).throw(RuntimeError("Python >=3.10 required")))
    record(checks, "git_status", check_git_status)
    record(checks, "compileall", lambda: require_command([sys.executable, "-m", "compileall", "addon.py", "main.py", "src", "scripts", "tests"]))
    record(checks, "pytest", lambda: require_command([sys.executable, "-m", "pytest"]))
    record(checks, "import_overtli_blender", check_import)
    record(checks, "pyproject", check_pyproject)
    record(checks, "console_script_metadata", check_pyproject)
    if not args.skip_privacy:
        record(checks, "privacy_scan", check_privacy_scan)
        record(checks, "stale_identity_scan", check_stale_identity_scan)
    record(checks, "addon_entrypoint", check_addon_entrypoint)
    record(checks, "smoke_script_static", check_smoke_script_static)
    record(checks, "phase7b_governance_static", check_phase7b_governance_static)
    if args.full:
        run_full_checks(checks, args, warnings)

    failed = {name: status for name, status in checks.items() if status != "passed"}
    summary = {"status": "failed" if failed else "success", "checks": checks, "warnings": warnings}
    if args.as_json:
        print(json.dumps(summary, indent=2))
    else:
        for name, status in checks.items():
            print(f"{name}: {status}")
        for warning in warnings:
            print(f"warning: {warning}")
        print(f"status: {summary['status']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
