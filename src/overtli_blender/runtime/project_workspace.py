"""Project workspace manifest and layout helpers."""

from __future__ import annotations

import json
import os
import shutil
import uuid
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
    "blend",
    "screenshots",
    "verification",
    "logs",
    "tasks",
    "manifests",
)

RESOURCE_FOLDERS = {
    "assets": "assets",
    "texture_source": "textures/source",
    "texture_working": "textures/working",
    "texture_baked": "textures/baked",
    "texture_packed": "textures/packed",
    "references": "references/images",
    "imports": "imports",
    "exports": "exports",
    "render_previews": "renders/previews",
    "render_finals": "renders/finals",
    "backups": "backups",
    "tasks": ".overtli/tasks",
    "manifests": ".overtli/manifests",
    "blend": "blend",
    "screenshots": "screenshots",
    "verification": "verification",
    "logs": "logs",
}


def resource_folder_manifest(project_root: str | Path) -> dict[str, str]:
    root = canonical_path(project_root)
    return {name: str(root / rel_path) for name, rel_path in RESOURCE_FOLDERS.items()}


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


def temp_workspace_root(session_id: str | None = None) -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TMP") or os.environ.get("TEMP") or str(Path.home())
    safe_session = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(session_id or "").strip())
    if not safe_session:
        safe_session = f"session_{uuid.uuid4().hex[:12]}"
    return canonical_path(Path(base) / "Overtli-Blender" / "temp_workspaces" / safe_session)


def initialize_temp_workspace(session_id: str | None = None, project_name: str | None = None) -> dict[str, Any]:
    root = temp_workspace_root(session_id)
    result = repair_workspace_layout(root, project_name=project_name or root.name)
    result["temporary"] = True
    result["session_id"] = root.name
    result["warnings"] = ["Unsaved .blend artifacts are stored in a user-local Overtli-Blender temp workspace, not the addon installation folder."]
    return result


def resolve_artifact_workspace(
    blend_filepath: str | None,
    preferred_root: str | None = None,
    session_id: str | None = None,
    create_if_missing: bool = True,
) -> dict[str, Any]:
    resolved = resolve_workspace(blend_filepath, preferred_root=preferred_root, allow_repo_fallback=False)
    workspace = resolved.get("workspace", {})
    if workspace.get("resolved"):
        if create_if_missing:
            repair_workspace_layout(workspace["project_root"], blend_filepath=blend_filepath)
        return {**resolved, "temporary": False}
    temp = initialize_temp_workspace(session_id=session_id) if create_if_missing else {"workspace": ProjectWorkspace(temp_workspace_root(session_id), "temporary").to_dict()}
    return {
        "status": "success",
        "workspace": temp["workspace"],
        "temporary": True,
        "unsaved_blend": True,
        "warnings": ["Unsaved .blend has no trusted project root; using dedicated temp workspace."],
    }


def initialize_workspace(project_root: str | Path, project_name: str | None = None, create_standard_folders: bool = True, overwrite_manifest: bool = False) -> dict[str, Any]:
    workspace = ProjectWorkspace(canonical_path(project_root), "explicit")
    if create_standard_folders:
        for folder in sorted({*STANDARD_FOLDERS, *RESOURCE_FOLDERS.values()}):
            (workspace.project_root / folder).mkdir(parents=True, exist_ok=True)
    if workspace.manifest_path.exists() and not overwrite_manifest:
        return {"status": "requires_approval", "message": "Project manifest already exists.", "workspace": workspace.to_dict()}
    manifest = {
        "project_name": project_name or workspace.project_root.name,
        "project_root": str(workspace.project_root),
        "standard_folders": list(STANDARD_FOLDERS),
        "resource_folders": resource_folder_manifest(workspace.project_root),
        "storage_backend": "json_files",
        "persistence": {
            "project_manifest": ".overtli/project.json",
            "tasks": ".overtli/tasks/*.json",
            "operation_journal": ".overtli/operation_journal.json",
            "runtime_log": ".overtli_blender/logs/runtime_events.jsonl",
            "sqlite": False,
        },
    }
    atomic_write_text(workspace.manifest_path, json.dumps(manifest, indent=2, sort_keys=True))
    return {"status": "success", "workspace": workspace.to_dict(), "manifest": manifest}


def repair_workspace_layout(project_root: str | Path, project_name: str | None = None, blend_filepath: str | None = None) -> dict[str, Any]:
    workspace = ProjectWorkspace(canonical_path(project_root), "explicit")
    created = []
    for folder in sorted({*STANDARD_FOLDERS, *RESOURCE_FOLDERS.values()}):
        path = workspace.project_root / folder
        if not path.exists():
            created.append(folder)
        path.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {}
    if workspace.manifest_path.exists():
        try:
            manifest = json.loads(workspace.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {"previous_manifest_unreadable": True}
    manifest.update(
        {
            "project_name": project_name or manifest.get("project_name") or workspace.project_root.name,
            "project_root": str(workspace.project_root),
            "standard_folders": list(STANDARD_FOLDERS),
            "resource_folders": resource_folder_manifest(workspace.project_root),
            "storage_backend": "json_files",
            "persistence": {
                "project_manifest": ".overtli/project.json",
                "tasks": ".overtli/tasks/*.json",
                "operation_journal": ".overtli/operation_journal.json",
                "runtime_log": ".overtli_blender/logs/runtime_events.jsonl",
                "sqlite": False,
            },
        }
    )
    if blend_filepath:
        blend_path = canonical_path(blend_filepath)
        blends = [item for item in manifest.get("blend_files", []) if item.get("filepath") != str(blend_path)]
        blends.append({"filepath": str(blend_path), "name": blend_path.name, "registered_from": "repair_workspace_layout"})
        manifest["blend_files"] = blends
        manifest["active_blend_file"] = str(blend_path)
    atomic_write_text(workspace.manifest_path, json.dumps(manifest, indent=2, sort_keys=True))
    return {"status": "success", "workspace": workspace.to_dict(), "created_folders": created, "manifest": manifest}


def validate_layout(project_root: str | Path) -> dict[str, Any]:
    root = canonical_path(project_root)
    expected = tuple(sorted({*STANDARD_FOLDERS, *RESOURCE_FOLDERS.values()}))
    missing = [folder for folder in expected if not (root / folder).exists()]
    return {
        "status": "success" if not missing else "warning",
        "project_root": str(root),
        "missing": missing,
        "standard_folders": list(STANDARD_FOLDERS),
        "resource_folders": resource_folder_manifest(root),
    }


def get_loaded_project_folder(blend_filepath: str | None, preferred_root: str | None = None) -> dict[str, Any]:
    resolved = resolve_workspace(blend_filepath, preferred_root=preferred_root, allow_repo_fallback=False)
    workspace = resolved.get("workspace", {})
    if not workspace.get("resolved"):
        return {**resolved, "project_folder": None, "layout": None}
    layout = validate_layout(workspace["project_root"])
    return {
        "status": "success",
        "blend_filepath": str(canonical_path(blend_filepath)) if blend_filepath else None,
        "project_folder": workspace["project_root"],
        "workspace": workspace,
        "layout": layout,
    }


def detect_drive_roots(preferred: tuple[str, ...] = ("C", "D")) -> dict[str, Any]:
    roots = []
    if os.name == "nt":
        for drive in preferred:
            letter = str(drive).rstrip(":\\/").upper()
            root = Path(f"{letter}:\\")
            if root.exists():
                roots.append(str(root))
    else:
        roots.append(str(Path("/")))
    return {"status": "success", "drive_roots": sorted(set(roots)), "platform": os.name}


def plan_project_folder_move(
    source_project_root: str | Path,
    destination_root: str | Path,
    new_project_name: str | None = None,
    blend_filepath: str | None = None,
    copy_mode: str = "copy",
) -> dict[str, Any]:
    source = canonical_path(source_project_root)
    destination_base = canonical_path(destination_root)
    target_name = new_project_name or source.name
    target = canonical_path(destination_base / target_name)
    if target == source:
        return {"status": "error", "message": "Target project folder is the same as source.", "source_project_root": str(source), "target_project_root": str(target)}
    if target in source.parents or source in target.parents:
        return {"status": "error", "message": "Project move target must not be nested inside the source or vice versa.", "source_project_root": str(source), "target_project_root": str(target)}
    blend_path = canonical_path(blend_filepath) if blend_filepath else None
    target_blend = target / (blend_path.name if blend_path else f"{target_name}.blend")
    conflicts = []
    if target.exists():
        conflicts.append({"path": str(target), "type": "directory_exists", "empty": not any(target.iterdir()) if target.is_dir() else False})
    missing_layout = validate_layout(source).get("missing", []) if source.exists() else list(STANDARD_FOLDERS)
    return {
        "status": "requires_approval",
        "source_project_root": str(source),
        "target_project_root": str(target),
        "destination_root": str(destination_base),
        "new_project_name": target_name,
        "blend_filepath": str(blend_path) if blend_path else None,
        "target_blend_filepath": str(target_blend),
        "copy_mode": copy_mode,
        "conflicts": conflicts,
        "source_missing_standard_folders": missing_layout,
        "steps": [
            "repair source project layout if requested",
            "copy project folder to target",
            "save current .blend to target blend path",
            "repair target project layout and manifest",
            "optionally delete original only when explicitly requested",
        ],
    }


def copy_project_folder(source_project_root: str | Path, target_project_root: str | Path, overwrite: bool = False) -> dict[str, Any]:
    source = canonical_path(source_project_root)
    target = canonical_path(target_project_root)
    if not source.exists() or not source.is_dir():
        return {"status": "error", "message": "Source project root is not a directory.", "source_project_root": str(source)}
    if target.exists() and any(target.iterdir()) and not overwrite:
        return {"status": "error", "message": "Target project root exists and is not empty.", "target_project_root": str(target)}
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, dirs_exist_ok=True)
    return {"status": "success", "source_project_root": str(source), "target_project_root": str(target)}
