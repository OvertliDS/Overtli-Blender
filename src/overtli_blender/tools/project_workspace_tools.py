"""MCP wrappers for Phase 7C project workspace commands."""

from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    if params:
        params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_project_workspace_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_project_status(ctx: Any) -> str:
        return _send(get_blender_connection, "get_project_status", locals())

    @mcp.tool()
    def get_loaded_project_folder(ctx: Any, preferred_root: str | None = None) -> str:
        return _send(get_blender_connection, "get_loaded_project_folder", locals())

    @mcp.tool()
    def resolve_project_workspace(ctx: Any, preferred_root: str | None = None, allow_repo_fallback: bool = True, create_if_missing: bool = False) -> str:
        return _send(get_blender_connection, "resolve_project_workspace", locals())

    @mcp.tool()
    def initialize_project_workspace(ctx: Any, project_root: str | None = None, project_name: str | None = None, create_standard_folders: bool = True, save_blend_if_unsaved: bool = False, blend_filename: str | None = None, confirm: bool = False) -> str:
        return _send(get_blender_connection, "initialize_project_workspace", locals())

    @mcp.tool()
    def initialize_temp_workspace(ctx: Any, session_id: str | None = None, project_name: str | None = None) -> str:
        """Create or return a user-local temporary project workspace for unsaved .blend sessions."""
        return _send(get_blender_connection, "initialize_temp_workspace", locals())

    @mcp.tool()
    def promote_temp_workspace_to_project(ctx: Any, project_root: str, session_id: str | None = None, blend_filename: str | None = None, project_name: str | None = None, confirm: bool = False, overwrite: bool = False, collect_external_images: bool = True, make_paths_relative: bool = True) -> str:
        """Copy a temporary workspace into a real project folder and save the .blend there after confirmation."""
        return _send(get_blender_connection, "promote_temp_workspace_to_project", locals())

    @mcp.tool()
    def validate_project_layout(ctx: Any, project_root: str | None = None) -> str:
        return _send(get_blender_connection, "validate_project_layout", locals())

    @mcp.tool()
    def repair_project_layout(ctx: Any, project_root: str | None = None, confirm: bool = False) -> str:
        return _send(get_blender_connection, "repair_project_layout", locals())

    @mcp.tool()
    def register_blend_file(ctx: Any, filepath: str | None = None, confirm: bool = False) -> str:
        return _send(get_blender_connection, "register_blend_file", locals())

    @mcp.tool()
    def save_project_as(ctx: Any, project_root: str, blend_filename: str, confirm: bool = False, overwrite: bool = False, collect_external_images: bool = False, make_paths_relative: bool = True) -> str:
        return _send(get_blender_connection, "save_project_as", locals())

    @mcp.tool()
    def resave_project_folder(ctx: Any, project_root: str | None = None, blend_filename: str | None = None, project_name: str | None = None, create_standard_folders: bool = True, update_manifest: bool = True, confirm: bool = False, overwrite: bool = False, collect_external_images: bool = True, make_paths_relative: bool = True) -> str:
        return _send(get_blender_connection, "resave_project_folder", locals())

    @mcp.tool()
    def plan_project_folder_move(ctx: Any, destination_root: str, new_project_name: str | None = None, source_project_root: str | None = None, copy_mode: str = "copy") -> str:
        return _send(get_blender_connection, "plan_project_folder_move", locals())

    @mcp.tool()
    def move_project_folder(ctx: Any, destination_root: str, new_project_name: str | None = None, source_project_root: str | None = None, copy_mode: str = "copy", confirm: bool = False, overwrite: bool = False, save_after_move: bool = True, delete_original: bool = False, collect_external_images: bool = True, make_paths_relative: bool = True) -> str:
        return _send(get_blender_connection, "move_project_folder", locals())

    @mcp.tool()
    def create_project_backup(ctx: Any, confirm: bool = False) -> str:
        return _send(get_blender_connection, "create_project_backup", locals())

    @mcp.tool()
    def restore_project_backup(ctx: Any, backup_id: str, confirm: bool = False) -> str:
        return _send(get_blender_connection, "restore_project_backup", locals())

    @mcp.tool()
    def collect_project_dependencies(ctx: Any, project_root: str | None = None, copy_external_images: bool = False, overwrite: bool = False, make_paths_relative: bool = True, confirm: bool = False) -> str:
        return _send(get_blender_connection, "collect_project_dependencies", locals())
