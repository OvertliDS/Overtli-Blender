from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / ".overtli_blender" / "diagnostics"
EXCLUDED_NAMES = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    ".overtli_blender",
    "memory_bank",
    "tools",
    "dist",
    "build",
    "AGENTS.md",
}
SECRET_TERMS = ("api_key", "secret", "token", "password", ".env", "credential")


def run_text(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return f"command failed: {' '.join(args)}\n{exc}\n"


def pyproject_summary() -> dict:
    import tomllib

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project", {})
    return {
        "name": project.get("name"),
        "version": project.get("version"),
        "requires_python": project.get("requires-python"),
        "scripts": project.get("scripts", {}),
        "optional_dependencies": sorted((project.get("optional-dependencies") or {}).keys()),
    }


def public_file_manifest() -> list[dict]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        parts = set(rel.split("/"))
        if parts & EXCLUDED_NAMES:
            continue
        if "blender_python_reference_5_1_md" in parts:
            continue
        if path.suffix.lower() in {".pyc", ".zip"}:
            continue
        files.append({"path": rel, "size": path.stat().st_size})
    return files


def privacy_report(files: list[dict]) -> dict:
    forbidden_hits = []
    for item in files:
        lower = item["path"].lower()
        if any(term in lower for term in SECRET_TERMS):
            forbidden_hits.append(item["path"])
    return {
        "memory_bank_excluded": True,
        "docs_mirror_excluded": True,
        "env_excluded": True,
        "agents_md_excluded": True,
        "forbidden_path_hits": forbidden_hits,
        "status": "passed" if not forbidden_hits else "failed",
    }


def export_bundle(output_root: Path = DEFAULT_OUTPUT_ROOT, bundle_id: str | None = None) -> Path:
    bundle_id = bundle_id or datetime.now(timezone.utc).strftime("diagnostic_%Y%m%dT%H%M%SZ")
    bundle_dir = output_root / bundle_id
    bundle_dir.mkdir(parents=True, exist_ok=False)
    files = public_file_manifest()

    (bundle_dir / "git_status.txt").write_text(run_text(["git", "status", "--short", "--untracked-files=all"]), encoding="utf-8")
    (bundle_dir / "python_env.txt").write_text(
        "\n".join([sys.version, platform.platform(), f"executable={sys.executable}"]) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "pyproject_summary.json").write_text(json.dumps(pyproject_summary(), indent=2) + "\n", encoding="utf-8")
    (bundle_dir / "test_summary.json").write_text(json.dumps({"pytest": "not run by diagnostic export"}, indent=2) + "\n", encoding="utf-8")
    (bundle_dir / "smoke_script_summary.json").write_text(json.dumps({"script": "scripts/smoke_blender_addon_socket.py", "live_blender_required": True}, indent=2) + "\n", encoding="utf-8")
    (bundle_dir / "public_docs_summary.json").write_text(json.dumps({"docs": [item["path"] for item in files if item["path"].startswith("docs/") or item["path"] in {"README.md", "CHANGELOG.md"}]}, indent=2) + "\n", encoding="utf-8")
    (bundle_dir / "file_manifest_public.json").write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8")
    report = privacy_report(files)
    (bundle_dir / "privacy_exclusion_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "bundle_id": bundle_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "public_safe": report["status"] == "passed",
        "files": sorted(path.name for path in bundle_dir.iterdir()),
    }
    (bundle_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return bundle_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a public-safe diagnostic bundle.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--bundle-id")
    args = parser.parse_args()
    try:
        bundle = export_bundle(args.output_root, args.bundle_id)
    except Exception as exc:
        print(f"FAIL export_diagnostic_bundle: {exc}", file=sys.stderr)
        return 1
    print(f"created {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
