"""MCP tool registration for Phase 4B selection intelligence tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_selection_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register deep selection and mesh component inspection tools."""

    @mcp.tool()
    def get_selection_deep_info(ctx: Any, include_components: bool = True, include_bounds: bool = True, include_material_slots: bool = True, include_vertex_groups: bool = True, max_components: int = 500) -> str:
        """Return active/selected object state plus bounded edit-mode component selection details."""
        try:
            return _send(get_blender_connection, "get_selection_deep_info", locals())
        except Exception as e:
            return f"Error getting selection deep info: {str(e)}"

    @mcp.tool()
    def get_mesh_component_summary(ctx: Any, object_name: str, include_bounds: bool = True, include_material_faces: bool = True, include_vertex_group_stats: bool = True, include_shape_key_stats: bool = True) -> str:
        """Return bounded mesh statistics, bounds, material face counts, vertex groups, and shape key counts."""
        try:
            return _send(get_blender_connection, "get_mesh_component_summary", locals())
        except Exception as e:
            return f"Error getting mesh component summary: {str(e)}"
