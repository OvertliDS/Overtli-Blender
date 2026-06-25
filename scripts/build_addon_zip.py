from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_INIT = ROOT / "src" / "overtli_blender" / "__init__.py"
DEFAULT_OUTPUT_ROOT = ROOT / ".overtli_blender" / "release" / "addon_zip"


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


def source_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def build_addon_zip(output_dir: Path = DEFAULT_OUTPUT_ROOT, overwrite: bool = False) -> tuple[Path, Path]:
    addon = ROOT / "addon.py"
    if not addon.is_file():
        raise FileNotFoundError("addon.py not found")

    version = read_version()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"overtli_blender_addon_{version}.zip"
    manifest_path = zip_path.with_suffix(".manifest.json")
    if (zip_path.exists() or manifest_path.exists()) and not overwrite:
        raise FileExistsError(f"{zip_path} already exists; pass --overwrite")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(addon, "addon.py")
        readme = ROOT / "README.md"
        if readme.is_file():
            archive.write(readme, "README.md")
        install_doc = ROOT / "docs" / "addon_install.md"
        if install_doc.is_file():
            archive.write(install_doc, "addon_install.md")

    included = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            included.append({"path": info.filename, "size": info.file_size})

    manifest = {
        "artifact_type": "blender_addon_zip",
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit(),
        "zip_path": str(zip_path.relative_to(ROOT)),
        "zip_sha256": sha256(zip_path),
        "files_included": included,
        "excluded": [
            "memory_bank",
            ".overtli_blender",
            ".venv",
            "tests",
            "blender_python_reference_5_1_md",
            "AGENTS.md",
            ".env",
            "review artifacts",
            "caches",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return zip_path, manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the public-safe Overtli-Blender single-file addon zip.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        zip_path, manifest_path = build_addon_zip(args.output_dir, args.overwrite)
    except Exception as exc:
        print(f"FAIL build_addon_zip: {exc}", file=sys.stderr)
        return 1
    print(f"created {zip_path}")
    print(f"created {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
