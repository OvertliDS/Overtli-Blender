from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def has_build() -> bool:
    return importlib.util.find_spec("build") is not None


def build_package(allow_missing_build: bool = False) -> list[Path]:
    if not has_build():
        message = 'Python package "build" is not installed. Run: python -m pip install -e ".[dev]"'
        if allow_missing_build:
            print(f"WARN {message}")
            return []
        raise RuntimeError(message)
    if DIST.exists():
        shutil.rmtree(DIST)
    subprocess.run([sys.executable, "-m", "build"], cwd=ROOT, check=True)
    artifacts = sorted(DIST.glob("*"))
    if not artifacts:
        raise RuntimeError("python -m build completed but dist/ is empty")
    expected = re.compile(r"^overtli[_-]blender-")
    bad = [path.name for path in artifacts if not expected.match(path.name)]
    if bad:
        raise RuntimeError(f"unexpected package artifact names: {bad}")
    for artifact in artifacts:
        if artifact.suffix == ".whl":
            with zipfile.ZipFile(artifact) as archive:
                names = archive.namelist()
                if not any(name.startswith("overtli_blender/") for name in names):
                    raise RuntimeError(f"{artifact.name} does not contain overtli_blender package")
        elif artifact.name.endswith(".tar.gz"):
            with tarfile.open(artifact) as archive:
                names = archive.getnames()
                if not any("/src/overtli_blender/" in name for name in names):
                    raise RuntimeError(f"{artifact.name} does not contain src/overtli_blender")
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Overtli-Blender wheel and sdist locally.")
    parser.add_argument("--allow-missing-build", action="store_true")
    args = parser.parse_args()
    try:
        artifacts = build_package(args.allow_missing_build)
    except Exception as exc:
        print(f"FAIL build_python_package: {exc}", file=sys.stderr)
        return 1
    for artifact in artifacts:
        print(f"created {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
