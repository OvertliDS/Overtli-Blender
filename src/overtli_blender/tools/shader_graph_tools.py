"""MCP tool registration for Phase 4A shader graph tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_shader_graph_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register shader graph inspection and allowlisted editing tools."""

    @mcp.tool()
    def get_shader_graph(ctx: Any, material_name: str, include_links: bool = True, include_node_inputs: bool = True, include_node_outputs: bool = True, include_texture_metadata: bool = True, max_nodes: int | None = None) -> str:
        """Return a bounded JSON-serializable shader node graph for one material."""
        try:
            return _send(get_blender_connection, "get_shader_graph", locals())
        except Exception as e:
            return f"Error getting shader graph: {str(e)}"

    @mcp.tool()
    def set_material_node_input(ctx: Any, material_name: str, node_name: str, input_name: str, value: Any) -> str:
        """Set an allowlisted material node input value."""
        try:
            return _send(get_blender_connection, "set_material_node_input", locals())
        except Exception as e:
            return f"Error setting material node input: {str(e)}"

    @mcp.tool()
    def add_material_node(ctx: Any, material_name: str, node_type: str, name: str | None = None, location: list[float] | None = None) -> str:
        """Add an allowlisted material shader node."""
        try:
            return _send(get_blender_connection, "add_material_node", locals())
        except Exception as e:
            return f"Error adding material node: {str(e)}"

    @mcp.tool()
    def connect_material_nodes(ctx: Any, material_name: str, from_node: str, from_socket: str, to_node: str, to_socket: str) -> str:
        """Connect two existing shader nodes by explicit socket names."""
        try:
            return _send(get_blender_connection, "connect_material_nodes", locals())
        except Exception as e:
            return f"Error connecting material nodes: {str(e)}"

    @mcp.tool()
    def remove_material_node(ctx: Any, material_name: str, node_name: str, confirm: bool = False) -> str:
        """Remove an Overtli-created allowlisted material node after confirmation."""
        try:
            return _send(get_blender_connection, "remove_material_node", locals())
        except Exception as e:
            return f"Error removing material node: {str(e)}"
