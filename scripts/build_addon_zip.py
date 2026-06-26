from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC_INIT = ROOT / "src" / "overtli_blender" / "__init__.py"
DEFAULT_OUTPUT_ROOT = ROOT / ".overtli_blender" / "release" / "addon_zip"
PACKAGE_ROOT = ROOT / "overtli_blender_addon"
SHARED_RUNTIME_ROOT = ROOT / "src" / "overtli_blender"

EXCLUDED_PATTERNS = [
    "memory_bank/",
    ".overtli_blender/",
    "dist/",
    "build/",
    "*.egg-info/",
    "tests/",
    "docs/",
    "scripts/",
    "tools/",
    "AIReview.config.json",
    "Create_AI_Review_Zip.bat",
    "Configure_AI_Review_Zip.bat",
    "Overtli-Blender_AIReview_Drive/",
    "*.zip",
    "*.log",
    "__pycache__/",
    ".pytest_cache/",
    ".venv/",
    "AGENTS.md",
    ".env",
    "blender_python_reference_5_1_md/",
    "diagnostics/",
    "release_candidate/",
    "final_handoff/",
    "review_packages/",
    "api_docs/",
]

FORBIDDEN_ZIP_PARTS = {
    "memory_bank",
    ".overtli_blender",
    "tests",
    "scripts",
    "dist",
    "build",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "Overtli-Blender_AIReview_Drive",
    "release_candidate",
    "final_handoff",
    "review_packages",
    "diagnostics",
}
FORBIDDEN_ZIP_NAMES = {"AGENTS.md", ".env", "AIReview.config.json"}
REQUIRED_PACKAGE_FILES = {
    "overtli_blender_addon/__init__.py",
    "overtli_blender_addon/registration.py",
    "overtli_blender_addon/preferences.py",
    "overtli_blender_addon/runtime/dispatcher.py",
    "overtli_blender_addon/runtime/socket_server.py",
    "overtli_blender_addon/services/scene.py",
    "overtli_blender_addon/services/materials.py",
    "overtli_blender_addon/services/diagnostics.py",
}
SHARED_RUNTIME_MODULE_DIRS = ("common", "runtime")


def read_version() -> str:
    namespace: dict[str, str] = {}
    exec(SRC_INIT.read_text(encoding="utf-8"), namespace)
    return namespace.get("__version__", "0.0.0")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def iter_package_files() -> Iterable[tuple[Path, str]]:
    if not PACKAGE_ROOT.is_dir():
        raise FileNotFoundError("overtli_blender_addon package not found")
    for path in sorted(PACKAGE_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.name == "README.md":
            continue
        rel = path.relative_to(ROOT).as_posix()
        if path.suffix == ".py" or path.name == "blender_manifest.toml":
            yield path, rel


def iter_shared_runtime_files() -> Iterable[tuple[Path, str]]:
    for dirname in SHARED_RUNTIME_MODULE_DIRS:
        base = SHARED_RUNTIME_ROOT / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(SHARED_RUNTIME_ROOT).as_posix()
            yield path, f"overtli_blender_addon/_shared_runtime/overtli_blender/{rel}"
    init_path = SHARED_RUNTIME_ROOT / "__init__.py"
    if init_path.is_file():
        yield init_path, "overtli_blender_addon/_shared_runtime/overtli_blender/__init__.py"


def _zip_name(version: str, mode: str) -> str:
    return f"overtli_blender_addon_{version}.zip"


def validate_zip(zip_path: Path, mode: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
    root_entries = sorted({name.split("/", 1)[0] for name in names})
    if mode == "package":
        if root_entries != ["overtli_blender_addon"]:
            errors.append(f"package zip must have one root folder overtli_blender_addon, got {root_entries}")
        missing = sorted(REQUIRED_PACKAGE_FILES - set(names))
        if missing:
            errors.append(f"missing required package files: {missing}")
    for name in names:
        path = Path(name)
        if not name.startswith("overtli_blender_addon/"):
            errors.append(f"zip entry is outside addon package root: {name}")
        if any(part in FORBIDDEN_ZIP_PARTS for part in path.parts):
            errors.append(f"forbidden path included: {name}")
        if path.name in FORBIDDEN_ZIP_NAMES:
            errors.append(f"forbidden file included: {name}")
        if "blender_python_reference_5_1_md" in name or "API docs mirror" in name:
            errors.append(f"API docs mirror included: {name}")
        if name.startswith("docs/") and name != "ADDON_INSTALL.md":
            errors.append(f"bulk docs included: {name}")
    return {"status": "passed" if not errors else "failed", "errors": errors, "warnings": warnings, "root_entries": root_entries}


def _write_manifest(zip_path: Path, manifest_path: Path, version: str, mode: str, included_hashes: dict[str, str]) -> dict:
    included_files = []
    total_bytes = 0
    with zipfile.ZipFile(zip_path) as archive:
        root_entries = sorted({info.filename.split("/", 1)[0] for info in archive.infolist()})
        for info in archive.infolist():
            included_files.append(info.filename)
            total_bytes += info.file_size
    validation = validate_zip(zip_path, mode)
    manifest = {
        "version": version,
        "commit": source_commit(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "included_files": included_files,
        "excluded_patterns": EXCLUDED_PATTERNS,
        "file_hashes": included_hashes,
        "total_bytes": total_bytes,
        "root_entries": root_entries,
        "install_layout": "package-root",
        "validation_status": validation,
        "zip_sha256": sha256(zip_path),
        "zip_path": str(zip_path.relative_to(ROOT)),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_addon_zip(
    output_dir: Path = DEFAULT_OUTPUT_ROOT,
    overwrite: bool = False,
    mode: str = "package",
    verify: bool = False,
) -> tuple[Path, Path, dict]:
    if mode != "package":
        raise ValueError(f"unsupported mode for single build: {mode}")
    version = read_version()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / _zip_name(version, mode)
    manifest_path = zip_path.with_suffix(".zip.manifest.json")
    if (zip_path.exists() or manifest_path.exists()) and not overwrite:
        raise FileExistsError(f"{zip_path} already exists; pass --overwrite")

    included_hashes: dict[str, str] = {}
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, arcname in iter_package_files():
            archive.write(source, arcname)
            included_hashes[arcname] = sha256(source)
        for source, arcname in iter_shared_runtime_files():
            archive.write(source, arcname)
            included_hashes[arcname] = sha256(source)

    manifest = _write_manifest(zip_path, manifest_path, version, mode, included_hashes)
    if verify and manifest["validation_status"]["status"] != "passed":
        raise RuntimeError(json.dumps(manifest["validation_status"], indent=2))
    return zip_path, manifest_path, manifest


def build_modes(output_dir: Path, overwrite: bool, mode: str, verify: bool) -> list[tuple[Path, Path, dict]]:
    modes = ["package"] if mode == "both" else [mode]
    return [build_addon_zip(output_dir=output_dir, overwrite=overwrite, mode=item, verify=verify) for item in modes]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build clean Overtli-Blender addon zips.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--overwrite", action="store_true", default=True, help="Overwrite generated addon zips; default for repeatable validation.")
    parser.add_argument("--no-overwrite", action="store_false", dest="overwrite")
    parser.add_argument("--mode", choices=["package", "both"], default="package")
    parser.add_argument("--layout", choices=["legacy", "packaged", "both"], help="Deprecated alias for --mode.")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--list", action="store_true", dest="show_list")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    mode = args.mode
    if args.layout:
        mode = {"legacy": "package", "packaged": "package", "both": "both"}[args.layout]

    try:
        built = build_modes(args.output_dir, args.overwrite, mode, args.verify)
    except Exception as exc:
        if args.as_json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"FAIL build_addon_zip: {exc}", file=sys.stderr)
        return 1

    payload = {"status": "success", "artifacts": []}
    for zip_path, manifest_path, manifest in built:
        item = {
            "zip_path": str(zip_path),
            "manifest_path": str(manifest_path),
            "mode": manifest["mode"],
            "validation_status": manifest["validation_status"],
            "included_files": manifest["included_files"],
        }
        payload["artifacts"].append(item)

    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        for item in payload["artifacts"]:
            print(f"created {item['zip_path']}")
            print(f"created {item['manifest_path']}")
            print(f"validation {item['validation_status']['status']}")
            if args.show_list:
                for name in item["included_files"]:
                    print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
