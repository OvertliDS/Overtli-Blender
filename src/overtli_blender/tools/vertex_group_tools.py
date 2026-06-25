"""MCP tool registration for Phase 4B vertex group tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_vertex_group_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register explicit-target vertex group creation, update, listing, and deletion tools."""

    @mcp.tool()
    def create_vertex_group(ctx: Any, object_name: str, group_name: str, selection_mode: str = "all", indices: list[int] | None = None, weight: float = 1.0, replace_existing: bool = False, rule: dict[str, Any] | None = None) -> str:
        """Create a vertex group from all vertices, indices, selection, bounds, axis, material slot, or proximity."""
        try:
            return _send(get_blender_connection, "create_vertex_group", locals())
        except Exception as e:
            return f"Error creating vertex group: {str(e)}"

    @mcp.tool()
    def update_vertex_group_weights(ctx: Any, object_name: str, group_name: str, indices: list[int] | None = None, weight: float = 1.0, mode: str = "replace", rule: dict[str, Any] | None = None) -> str:
        """Update weights in an existing vertex group with replace/add/subtract behavior."""
        try:
            return _send(get_blender_connection, "update_vertex_group_weights", locals())
        except Exception as e:
            return f"Error updating vertex group weights: {str(e)}"

    @mcp.tool()
    def list_vertex_groups(ctx: Any, object_name: str, include_weights_summary: bool = True, max_vertices_sample: int = 25) -> str:
        """List vertex groups and optional bounded weight summaries for one mesh object."""
        try:
            return _send(get_blender_connection, "list_vertex_groups", locals())
        except Exception as e:
            return f"Error listing vertex groups: {str(e)}"

    @mcp.tool()
    def delete_vertex_groups(ctx: Any, object_name: str, group_names: list[str], confirm: bool = False) -> str:
        """Delete explicitly named vertex groups after confirmation."""
        try:
            return _send(get_blender_connection, "delete_vertex_groups", locals())
        except Exception as e:
            return f"Error deleting vertex groups: {str(e)}"
