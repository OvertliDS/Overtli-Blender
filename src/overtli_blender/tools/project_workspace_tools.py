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
    def resolve_project_workspace(ctx: Any, preferred_root: str | None = None, allow_repo_fallback: bool = True, create_if_missing: bool = False) -> str:
        return _send(get_blender_connection, "resolve_project_workspace", locals())

    @mcp.tool()
    def initialize_project_workspace(ctx: Any, project_root: str | None = None, project_name: str | None = None, create_standard_folders: bool = True, save_blend_if_unsaved: bool = False, blend_filename: str | None = None, confirm: bool = False) -> str:
        return _send(get_blender_connection, "initialize_project_workspace", locals())

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
    def save_project_as(ctx: Any, project_root: str, blend_filename: str, confirm: bool = False, overwrite: bool = False) -> str:
        return _send(get_blender_connection, "save_project_as", locals())

    @mcp.tool()
    def create_project_backup(ctx: Any, confirm: bool = False) -> str:
        return _send(get_blender_connection, "create_project_backup", locals())

    @mcp.tool()
    def restore_project_backup(ctx: Any, backup_id: str, confirm: bool = False) -> str:
        return _send(get_blender_connection, "restore_project_backup", locals())

    @mcp.tool()
    def collect_project_dependencies(ctx: Any) -> str:
        return _send(get_blender_connection, "collect_project_dependencies", locals())
