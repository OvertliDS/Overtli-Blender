"""Project workspace manifest and layout helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .path_utils import atomic_write_text, canonical_path


STANDARD_FOLDERS = (
    ".overtli",
    "assets",
    "textures/source",
    "textures/working",
    "textures/baked",
    "textures/packed",
    "references/images",
    "imports",
    "exports",
    "renders/previews",
    "renders/finals",
    "backups",
)


@dataclass(frozen=True)
class ProjectWorkspace:
    project_root: Path
    source: str = "explicit"

    @property
    def workspace_dir(self) -> Path:
        return self.project_root / ".overtli"

    @property
    def manifest_path(self) -> Path:
        return self.workspace_dir / "project.json"

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolved": True,
            "project_root": str(self.project_root),
            "workspace_dir": str(self.workspace_dir),
            "manifest_path": str(self.manifest_path),
            "source": self.source,
        }


def resolve_workspace(blend_filepath: str | None, preferred_root: str | None = None, repo_root: str | Path | None = None, allow_repo_fallback: bool = True) -> dict[str, Any]:
    if preferred_root:
        return {"status": "success", "workspace": ProjectWorkspace(canonical_path(preferred_root), "preferred_root").to_dict(), "options": []}
    if blend_filepath:
        blend_path = canonical_path(blend_filepath)
        return {"status": "success", "workspace": ProjectWorkspace(blend_path.parent, "blend_parent").to_dict(), "options": []}
    options = []
    if repo_root and allow_repo_fallback:
        options.append({"source": "repo_fallback", "project_root": str(canonical_path(repo_root))})
    return {"status": "unsaved_blend", "workspace": {"resolved": False, "source": "temporary"}, "options": options, "warnings": ["Unsaved .blend has no trusted project root."]}


def initialize_workspace(project_root: str | Path, project_name: str | None = None, create_standard_folders: bool = True, overwrite_manifest: bool = False) -> dict[str, Any]:
    workspace = ProjectWorkspace(canonical_path(project_root), "explicit")
    if create_standard_folders:
        for folder in STANDARD_FOLDERS:
            (workspace.project_root / folder).mkdir(parents=True, exist_ok=True)
    if workspace.manifest_path.exists() and not overwrite_manifest:
        return {"status": "requires_approval", "message": "Project manifest already exists.", "workspace": workspace.to_dict()}
    manifest = {
        "project_name": project_name or workspace.project_root.name,
        "project_root": str(workspace.project_root),
        "standard_folders": list(STANDARD_FOLDERS),
    }
    atomic_write_text(workspace.manifest_path, json.dumps(manifest, indent=2, sort_keys=True))
    return {"status": "success", "workspace": workspace.to_dict(), "manifest": manifest}


def validate_layout(project_root: str | Path) -> dict[str, Any]:
    root = canonical_path(project_root)
    missing = [folder for folder in STANDARD_FOLDERS if not (root / folder).exists()]
    return {"status": "success" if not missing else "warning", "project_root": str(root), "missing": missing, "standard_folders": list(STANDARD_FOLDERS)}
