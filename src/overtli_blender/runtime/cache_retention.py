"""Managed cache retention planning."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .path_utils import canonical_path, is_relative_to


CACHE_CATEGORIES = ("temp", "derived_previews", "smoke_artifacts", "verification_snapshots", "logs", "diagnostics", "release_artifacts", "exports", "final_renders", "knowledge_indexes")


def cache_roots(base: str | Path) -> dict[str, Path]:
    root = canonical_path(base)
    return {
        "temp": root / "temp",
        "derived_previews": root / "previews",
        "smoke_artifacts": root / "smoke",
        "verification_snapshots": root / "verification",
        "logs": root / "logs",
        "diagnostics": root / "diagnostics",
        "release_artifacts": root / "release",
        "exports": root / "exports",
        "final_renders": root / "renders" / "finals",
        "knowledge_indexes": root / "knowledge",
    }


def get_cache_status(base: str | Path) -> dict[str, Any]:
    status = []
    for category, root in cache_roots(base).items():
        files = [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
        mtimes = [p.stat().st_mtime for p in files]
        status.append({"category": category, "path": str(root), "file_count": len(files), "bytes": sum(p.stat().st_size for p in files), "oldest": min(mtimes) if mtimes else None, "newest": max(mtimes) if mtimes else None, "pinned_count": len([p for p in files if p.name.endswith(".pinned")]), "cleanup_policy": "manual_approval_required" if category in {"exports", "final_renders"} else "age_based"})
    return {"status": "success", "categories": status}


def plan_cache_cleanup(base: str | Path, categories: list[str] | None = None, older_than_days: int | None = None) -> dict[str, Any]:
    roots = cache_roots(base)
    selected = categories or list(roots)
    cutoff = time.time() - older_than_days * 86400 if older_than_days is not None else None
    files = []
    for category in selected:
        root = roots.get(category)
        if not root or category == "final_renders":
            continue
        for path in root.rglob("*") if root.exists() else []:
            if not path.is_file() or path.name.endswith(".pinned"):
                continue
            if cutoff is not None and path.stat().st_mtime >= cutoff:
                continue
            if is_relative_to(path, root):
                files.append({"category": category, "path": str(path), "bytes": path.stat().st_size})
    return {"status": "requires_approval", "approval_id": f"cache_{len(files)}_{int(time.time())}", "files": files, "bytes": sum(item["bytes"] for item in files), "dry_run": True}
