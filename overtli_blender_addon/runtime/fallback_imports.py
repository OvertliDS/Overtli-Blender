"""Import bootstrap helpers for development and bundled addon installs."""

from __future__ import annotations

import sys
from pathlib import Path


def add_runtime_search_paths(package_file: str) -> list[str]:
    package_root = Path(package_file).resolve().parent
    candidates = [package_root.parent / "src", package_root / "_shared_runtime"]
    added: list[str] = []
    for candidate in candidates:
        if candidate.is_dir():
            value = str(candidate)
            if value not in sys.path:
                sys.path.insert(0, value)
                added.append(value)
    return added
