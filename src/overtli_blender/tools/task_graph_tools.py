"""MCP wrappers for Phase 7C task graph and time/revision commands."""

from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    if params:
        params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_task_graph_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_task(ctx: Any, goal: str, priority: str = "normal", acceptance_criteria: list[str] | None = None) -> str:
        return _send(get_blender_connection, "create_task", locals())

    @mcp.tool()
    def update_task(ctx: Any, task_id: str, status: str | None = None, goal: str | None = None) -> str:
        return _send(get_blender_connection, "update_task", locals())

    @mcp.tool()
    def list_tasks(ctx: Any, status: str | None = None) -> str:
        return _send(get_blender_connection, "list_tasks", locals())

    @mcp.tool()
    def get_task(ctx: Any, task_id: str) -> str:
        return _send(get_blender_connection, "get_task", locals())

    @mcp.tool()
    def set_task_status(ctx: Any, task_id: str, status: str) -> str:
        return _send(get_blender_connection, "set_task_status", locals())

    @mcp.tool()
    def link_task_artifact(ctx: Any, task_id: str, artifact_path: str, artifact_type: str = "file") -> str:
        return _send(get_blender_connection, "link_task_artifact", locals())

    @mcp.tool()
    def link_task_target(ctx: Any, task_id: str, target_handle: str) -> str:
        return _send(get_blender_connection, "link_task_target", locals())

    @mcp.tool()
    def mark_task_verified(ctx: Any, task_id: str) -> str:
        return _send(get_blender_connection, "mark_task_verified", locals())

    @mcp.tool()
    def mark_task_stale(ctx: Any, task_id: str) -> str:
        return _send(get_blender_connection, "mark_task_stale", locals())

    @mcp.tool()
    def archive_tasks(ctx: Any, task_ids: list[str] | None = None) -> str:
        return _send(get_blender_connection, "archive_tasks", locals())

    @mcp.tool()
    def get_task_graph(ctx: Any) -> str:
        return _send(get_blender_connection, "get_task_graph", locals())

    @mcp.tool()
    def detect_stale_tasks(ctx: Any) -> str:
        return _send(get_blender_connection, "detect_stale_tasks", locals())

    @mcp.tool()
    def get_session_time(ctx: Any) -> str:
        return _send(get_blender_connection, "get_session_time", locals())

    @mcp.tool()
    def get_scene_revision(ctx: Any) -> str:
        return _send(get_blender_connection, "get_scene_revision", locals())

    @mcp.tool()
    def get_recent_operations(ctx: Any, limit: int = 20) -> str:
        return _send(get_blender_connection, "get_recent_operations", locals())

    @mcp.tool()
    def get_changes_since_revision(ctx: Any, revision: int) -> str:
        return _send(get_blender_connection, "get_changes_since_revision", locals())

    @mcp.tool()
    def get_operation_duration(ctx: Any, operation_id: str | None = None) -> str:
        return _send(get_blender_connection, "get_operation_duration", locals())

    @mcp.tool()
    def create_scene_revision_marker(ctx: Any, label: str | None = None, source: str = "overtli") -> str:
        return _send(get_blender_connection, "create_scene_revision_marker", locals())
