"""MCP wrappers for Phase 7C file access policy commands."""

from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    if params:
        params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_file_access_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_file_access_policy(ctx: Any) -> str:
        return _send(get_blender_connection, "get_file_access_policy", locals())

    @mcp.tool()
    def set_file_access_policy(ctx: Any, approved_roots: list[str] | None = None, confirm: bool = False) -> str:
        return _send(get_blender_connection, "set_file_access_policy", locals())

    @mcp.tool()
    def validate_path_access(ctx: Any, path: str, access: str = "read") -> str:
        return _send(get_blender_connection, "validate_path_access", locals())

    @mcp.tool()
    def list_approved_roots(ctx: Any) -> str:
        return _send(get_blender_connection, "list_approved_roots", locals())

    @mcp.tool()
    def add_approved_root(ctx: Any, root: str, confirm: bool = False) -> str:
        return _send(get_blender_connection, "add_approved_root", locals())

    @mcp.tool()
    def remove_approved_root(ctx: Any, root: str, confirm: bool = False) -> str:
        return _send(get_blender_connection, "remove_approved_root", locals())

    @mcp.tool()
    def detect_drive_roots(ctx: Any, preferred_drives: list[str] | None = None) -> str:
        return _send(get_blender_connection, "detect_drive_roots", locals())

    @mcp.tool()
    def approve_drive_roots(ctx: Any, drives: list[str] | None = None, confirm: bool = False) -> str:
        return _send(get_blender_connection, "approve_drive_roots", locals())

    @mcp.tool()
    def scan_project_files(ctx: Any, root: str | None = None, limit: int = 200) -> str:
        return _send(get_blender_connection, "scan_project_files", locals())

    @mcp.tool()
    def read_project_text_file(ctx: Any, path: str, max_bytes: int = 200000) -> str:
        return _send(get_blender_connection, "read_project_text_file", locals())

    @mcp.tool()
    def write_project_text_file(ctx: Any, path: str, text: str, confirm: bool = False) -> str:
        return _send(get_blender_connection, "write_project_text_file", locals())

    @mcp.tool()
    def copy_file_into_project(ctx: Any, source: str, destination: str) -> str:
        return _send(get_blender_connection, "copy_file_into_project", locals())

    @mcp.tool()
    def plan_file_delete(ctx: Any, paths: list[str]) -> str:
        return _send(get_blender_connection, "plan_file_delete", locals())

    @mcp.tool()
    def execute_approved_file_delete(ctx: Any, approval_id: str, paths: list[str] | None = None, confirm: bool = False) -> str:
        return _send(get_blender_connection, "execute_approved_file_delete", locals())
