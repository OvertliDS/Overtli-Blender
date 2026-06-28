from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / ".overtli_blender" / "release" / "public_repo_zip"

INCLUDE_DIRS = {
    ".github",
    "config",
    "docs",
    "overtli_blender_addon",
    "scripts",
    "src",
    "tests",
}

INCLUDE_FILES = {
    ".gitignore",
    ".python-version",
    "addon.py",
    "CHANGELOG.md",
    "LICENSE",
    "main.py",
    "pyproject.toml",
    "README.md",
    "Reset_ChatGPT_Connector_Credentials.bat",
    "Start_ChatGPT_Connector.bat",
    "Start_ChatGPT_MCP_Server.bat",
    "Start_ChatGPT_Server_URL.bat",
    "Start_OpenAI_MCP_Tunnel.bat",
    "uv.lock",
}

FORBIDDEN_PARTS = {
    ".agents",
    ".git",
    ".overtli_blender",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "assets",
    "build",
    "dist",
    "memory_bank",
    "Overtli-Blender_AIReview_Drive",
    "tools",
}

FORBIDDEN_NAMES = {
    ".ai_review_zip_cache.tsv",
    ".ai_review_zip_state.json",
    ".DS_Store",
    "AGENTS.md",
    "AIReview.config.json",
    "Configure_AI_Review_Zip.bat",
    "Create_AI_Review_Zip.bat",
    "Overtli-Blender.zip",
}


def source_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def iter_public_files() -> Iterable[tuple[Path, str]]:
    for name in sorted(INCLUDE_FILES):
        path = ROOT / name
        if path.is_file():
            yield path, name
    for dirname in sorted(INCLUDE_DIRS):
        base = ROOT / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if any(part in FORBIDDEN_PARTS for part in path.relative_to(ROOT).parts):
                continue
            if path.name in FORBIDDEN_NAMES or path.suffix in {".pyc", ".pyo"}:
                continue
            yield path, path.relative_to(ROOT).as_posix()


def validate_zip(zip_path: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
    if not any(name.startswith("overtli_blender_addon/") for name in names):
        errors.append("public repo zip is missing overtli_blender_addon/")
    if not any(name.startswith("src/overtli_blender/") for name in names):
        errors.append("public repo zip is missing src/overtli_blender/")
    for required in ["README.md", "pyproject.toml", "LICENSE", "scripts/build_addon_zip.py"]:
        if required not in names:
            errors.append(f"public repo zip is missing {required}")
    for name in names:
        path = Path(name)
        if any(part in FORBIDDEN_PARTS for part in path.parts):
            errors.append(f"forbidden private/generated path included: {name}")
        if path.name in FORBIDDEN_NAMES:
            errors.append(f"forbidden private/generated file included: {name}")
        if name.startswith("memory_bank/") or "blender_python_reference_5_1_md" in name:
            errors.append(f"private Memory Bank or API mirror included: {name}")
        if name.startswith(".overtli_blender/") or name.startswith("dist/") or name.startswith("tools/"):
            errors.append(f"generated/local artifact included: {name}")
    return {"status": "passed" if not errors else "failed", "errors": errors, "warnings": warnings, "file_count": len(names)}


def build_public_repo_zip(output_dir: Path = DEFAULT_OUTPUT_ROOT, overwrite: bool = True, verify: bool = True) -> tuple[Path, Path, dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "overtli_blender_public_repo.zip"
    manifest_path = output_dir / "overtli_blender_public_repo.manifest.json"
    if (zip_path.exists() or manifest_path.exists()) and not overwrite:
        raise FileExistsError(f"{zip_path} already exists; pass --overwrite")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, arcname in iter_public_files():
            archive.write(source, arcname)
    validation = validate_zip(zip_path)
    if verify and validation["status"] != "passed":
        raise RuntimeError(json.dumps(validation, indent=2))
    with zipfile.ZipFile(zip_path) as archive:
        included_files = archive.namelist()
    manifest = {
        "status": "success",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "commit": source_commit(),
        "zip_path": str(zip_path.relative_to(ROOT)),
        "included_files": included_files,
        "included_file_count": len(included_files),
        "include_dirs": sorted(INCLUDE_DIRS),
        "include_files": sorted(INCLUDE_FILES),
        "forbidden_parts": sorted(FORBIDDEN_PARTS),
        "forbidden_names": sorted(FORBIDDEN_NAMES),
        "validation_status": validation,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return zip_path, manifest_path, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a public-safe source zip for GitHub/review handoff.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--overwrite", action="store_true", default=True)
    parser.add_argument("--no-overwrite", action="store_false", dest="overwrite")
    parser.add_argument("--no-verify", action="store_false", dest="verify")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        zip_path, manifest_path, manifest = build_public_repo_zip(args.output_dir, args.overwrite, args.verify)
    except Exception as exc:
        if args.as_json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"FAIL build_public_repo_zip: {exc}", file=sys.stderr)
        return 1
    if args.as_json:
        print(json.dumps({"status": "success", "zip_path": str(zip_path), "manifest_path": str(manifest_path), "validation_status": manifest["validation_status"]}, indent=2))
    else:
        print(f"created {zip_path}")
        print(f"created {manifest_path}")
        print(f"validation {manifest['validation_status']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
