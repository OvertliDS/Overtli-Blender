"""Path helpers for project-scoped filesystem operations."""

from __future__ import annotations

import os
from pathlib import Path


def canonical_path(path: str | Path) -> Path:
    """Return a resolved absolute path without requiring the target to exist."""

    return Path(path).expanduser().resolve(strict=False)


def is_relative_to(child: str | Path, parent: str | Path) -> bool:
    child_path = canonical_path(child)
    parent_path = canonical_path(parent)
    try:
        child_path.relative_to(parent_path)
        return True
    except ValueError:
        return False


def has_symlink_escape(path: str | Path, approved_roots: list[str | Path]) -> bool:
    """Detect whether an existing path resolves outside every approved root."""

    path_obj = Path(path).expanduser()
    existing = path_obj if path_obj.exists() else next((p for p in [path_obj, *path_obj.parents] if p.exists()), path_obj)
    resolved = canonical_path(existing)
    return not any(is_relative_to(resolved, root) for root in approved_roots)


def safe_join(root: str | Path, *parts: str) -> Path:
    candidate = canonical_path(Path(root).joinpath(*parts))
    if not is_relative_to(candidate, root):
        raise ValueError(f"Path escapes root: {candidate}")
    return candidate


def atomic_write_text(path: str | Path, text: str, encoding: str = "utf-8") -> Path:
    target = canonical_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target.with_name(f".{target.name}.tmp")
    temp_path.write_text(text, encoding=encoding)
    os.replace(temp_path, target)
    return target
