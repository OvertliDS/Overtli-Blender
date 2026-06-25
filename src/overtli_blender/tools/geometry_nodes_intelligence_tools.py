"""MCP wrappers for Geometry Nodes inspection and capability tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_geometry_nodes_intelligence_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    def _send(command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return get_blender_connection().send_command(command, params or {})

    @mcp.tool()
    def get_geometry_nodes_capabilities(ctx: Any) -> dict[str, Any]:
        return _send("get_geometry_nodes_capabilities")

    @mcp.tool()
    def list_geometry_node_groups(ctx: Any, include_builtin: bool = False, include_users: bool = True, include_interface: bool = True, include_node_summary: bool = True, max_groups: int | None = None) -> dict[str, Any]:
        return _send("list_geometry_node_groups", {"include_builtin": include_builtin, "include_users": include_users, "include_interface": include_interface, "include_node_summary": include_node_summary, "max_groups": max_groups})

    @mcp.tool()
    def get_geometry_node_group_deep_info(ctx: Any, node_group_name: str, include_nodes: bool = True, include_links: bool = True, include_interface: bool = True, include_modifier_users: bool = True, max_nodes: int | None = None) -> dict[str, Any]:
        return _send("get_geometry_node_group_deep_info", {"node_group_name": node_group_name, "include_nodes": include_nodes, "include_links": include_links, "include_interface": include_interface, "include_modifier_users": include_modifier_users, "max_nodes": max_nodes})

    @mcp.tool()
    def list_geometry_nodes_modifiers(ctx: Any, object_name: str | None = None, include_inputs: bool = True, include_group_info: bool = True) -> dict[str, Any]:
        return _send("list_geometry_nodes_modifiers", {"object_name": object_name, "include_inputs": include_inputs, "include_group_info": include_group_info})

    @mcp.tool()
    def get_geometry_nodes_modifier_info(ctx: Any, object_name: str, modifier_name: str, include_inputs: bool = True, include_group_info: bool = True) -> dict[str, Any]:
        return _send("get_geometry_nodes_modifier_info", {"object_name": object_name, "modifier_name": modifier_name, "include_inputs": include_inputs, "include_group_info": include_group_info})
