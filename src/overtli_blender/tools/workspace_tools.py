"""MCP tool registration for Phase 3 workspace, journal, diff, and rollback tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    if params:
        params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_workspace_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register persistent task workspace, journal, scene diff, and rollback tools."""

    @mcp.tool()
    def get_task_workspace(ctx: Any, artifact_root: str | None = None) -> str:
        """Get the persistent task workspace summary."""
        return _send(get_blender_connection, "get_task_workspace", locals())

    @mcp.tool()
    def create_workspace_task(ctx: Any, title: str, goal: str | None = None, assumptions: list[str] | None = None, status: str = "pending", task_id: str | None = None, artifact_root: str | None = None) -> str:
        """Create a persistent task workspace entry."""
        return _send(get_blender_connection, "create_workspace_task", locals())

    @mcp.tool()
    def update_workspace_task(ctx: Any, task_id: str, status: str | None = None, goal: str | None = None, assumptions: list[str] | None = None, rollback_status: str | None = None, verification: dict | None = None, artifact_root: str | None = None) -> str:
        """Update a persistent task workspace entry."""
        return _send(get_blender_connection, "update_workspace_task", locals())

    @mcp.tool()
    def complete_workspace_task(ctx: Any, task_id: str, verified: bool = False, evidence: dict | None = None, artifact_root: str | None = None) -> str:
        """Mark a workspace task completed or verified with supporting evidence."""
        return _send(get_blender_connection, "complete_workspace_task", locals())

    @mcp.tool()
    def list_workspace_tasks(ctx: Any, status: str | None = None, artifact_root: str | None = None) -> str:
        """List persistent task workspace entries."""
        return _send(get_blender_connection, "list_workspace_tasks", locals())

    @mcp.tool()
    def create_scene_plan(ctx: Any, title: str, goal: str | None = None, steps: list[str] | None = None, assumptions: list[str] | None = None, task_id: str | None = None, artifact_root: str | None = None) -> str:
        """Create a task plus ordered todos for a scene-building plan."""
        return _send(get_blender_connection, "create_scene_plan", locals())

    @mcp.tool()
    def list_scene_plan(ctx: Any, task_id: str | None = None, artifact_root: str | None = None) -> str:
        """Return scene-plan tasks, todos, and journal context."""
        return _send(get_blender_connection, "list_scene_plan", locals())

    @mcp.tool()
    def add_workspace_todo(ctx: Any, text: str, task_id: str | None = None, state: str = "pending", todo_id: str | None = None, artifact_root: str | None = None) -> str:
        """Add a persistent todo entry."""
        return _send(get_blender_connection, "add_workspace_todo", locals())

    @mcp.tool()
    def update_workspace_todo(ctx: Any, todo_id: str, state: str | None = None, text: str | None = None, evidence: dict | None = None, artifact_root: str | None = None) -> str:
        """Update a persistent todo entry."""
        return _send(get_blender_connection, "update_workspace_todo", locals())

    @mcp.tool()
    def list_workspace_todos(ctx: Any, task_id: str | None = None, state: str | None = None, artifact_root: str | None = None) -> str:
        """List persistent todo entries."""
        return _send(get_blender_connection, "list_workspace_todos", locals())

    @mcp.tool()
    def record_operation_journal_entry(ctx: Any, operation_type: str, task_id: str | None = None, target: str | None = None, summary: str | None = None, risk_level: str = "LOW", rollback_status: str = "unknown", before_snapshot_id: str | None = None, after_snapshot_id: str | None = None, metadata: dict | None = None, artifact_root: str | None = None) -> str:
        """Record a durable operation journal entry."""
        return _send(get_blender_connection, "record_operation_journal_entry", locals())

    @mcp.tool()
    def get_operation_journal(ctx: Any, task_id: str | None = None, limit: int = 50, artifact_root: str | None = None) -> str:
        """Read durable operation journal entries."""
        return _send(get_blender_connection, "get_operation_journal", locals())

    @mcp.tool()
    def create_scene_snapshot(ctx: Any, label: str | None = None, task_id: str | None = None, include_verification_snapshot: bool = False, artifact_root: str | None = None) -> str:
        """Create a lightweight durable scene state snapshot."""
        return _send(get_blender_connection, "create_scene_snapshot", locals())

    @mcp.tool()
    def list_scene_snapshots(ctx: Any, artifact_root: str | None = None) -> str:
        """List durable scene state snapshots."""
        return _send(get_blender_connection, "list_scene_snapshots", locals())

    @mcp.tool()
    def diff_scene_snapshots(ctx: Any, before_snapshot_id: str, after_snapshot_id: str, artifact_root: str | None = None) -> str:
        """Diff two durable scene state snapshots."""
        return _send(get_blender_connection, "diff_scene_snapshots", locals())

    @mcp.tool()
    def detect_user_changes(ctx: Any, baseline_snapshot_id: str | None = None, artifact_root: str | None = None) -> str:
        """Detect scene changes relative to a baseline snapshot."""
        return _send(get_blender_connection, "detect_user_changes", locals())

    @mcp.tool()
    def rollback_to_scene_snapshot(ctx: Any, snapshot_id: str, confirm: bool = False, remove_new_objects: bool = False, verify: bool = True, artifact_root: str | None = None) -> str:
        """Rollback existing object transforms and visibility to a scene snapshot."""
        return _send(get_blender_connection, "rollback_to_scene_snapshot", locals())

    @mcp.tool()
    def undo_last_blender_operation(ctx: Any, confirm: bool = False) -> str:
        """Request Blender undo after explicit confirmation."""
        return _send(get_blender_connection, "undo_last_blender_operation", locals())
