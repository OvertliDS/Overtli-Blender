"""MCP wrappers for Phase 7C cache retention commands."""

from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    if params:
        params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_cache_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_cache_status(ctx: Any) -> str:
        return _send(get_blender_connection, "get_cache_status", locals())

    @mcp.tool()
    def plan_cache_cleanup(ctx: Any, categories: list[str] | None = None, older_than_days: int | None = None, dry_run: bool = True) -> str:
        return _send(get_blender_connection, "plan_cache_cleanup", locals())

    @mcp.tool()
    def execute_cache_cleanup(ctx: Any, approval_id: str, confirm: bool = False) -> str:
        return _send(get_blender_connection, "execute_cache_cleanup", locals())

    @mcp.tool()
    def pin_artifact(ctx: Any, path: str) -> str:
        return _send(get_blender_connection, "pin_artifact", locals())

    @mcp.tool()
    def unpin_artifact(ctx: Any, path: str) -> str:
        return _send(get_blender_connection, "unpin_artifact", locals())

    @mcp.tool()
    def find_orphaned_artifacts(ctx: Any) -> str:
        return _send(get_blender_connection, "find_orphaned_artifacts", locals())

    @mcp.tool()
    def compact_operation_history(ctx: Any, confirm: bool = False) -> str:
        return _send(get_blender_connection, "compact_operation_history", locals())
