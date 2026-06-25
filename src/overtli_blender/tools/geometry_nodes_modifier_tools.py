"""MCP wrappers for Geometry Nodes modifier workflows."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_geometry_nodes_modifier_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    def _send(command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return get_blender_connection().send_command(command, params or {})

    @mcp.tool()
    def apply_geometry_nodes_modifier(ctx: Any, object_name: str, node_group_name: str, modifier_name: str | None = None, input_values: dict[str, Any] | None = None, verify: bool = False) -> dict[str, Any]:
        return _send("apply_geometry_nodes_modifier", {"object_name": object_name, "node_group_name": node_group_name, "modifier_name": modifier_name, "input_values": input_values, "verify": verify})

    @mcp.tool()
    def set_geometry_nodes_modifier_input(ctx: Any, object_name: str, modifier_name: str, input_values: dict[str, Any]) -> dict[str, Any]:
        return _send("set_geometry_nodes_modifier_input", {"object_name": object_name, "modifier_name": modifier_name, "input_values": input_values})

    @mcp.tool()
    def remove_geometry_nodes_modifiers(ctx: Any, object_name: str | None = None, modifier_names: list[str] | None = None, prefix: str | None = None, confirm: bool = False) -> dict[str, Any]:
        return _send("remove_geometry_nodes_modifiers", {"object_name": object_name, "modifier_names": modifier_names, "prefix": prefix, "confirm": confirm})
