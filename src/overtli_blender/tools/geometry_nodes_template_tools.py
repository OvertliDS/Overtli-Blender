"""MCP wrappers for Geometry Nodes templates and safe recipes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_geometry_nodes_template_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    def _send(command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return get_blender_connection().send_command(command, params or {})

    @mcp.tool()
    def get_supported_geometry_node_templates(ctx: Any) -> dict[str, Any]:
        return _send("get_supported_geometry_node_templates")

    @mcp.tool()
    def create_geometry_node_group_from_template(ctx: Any, template_name: str, node_group_name: str, parameters: dict[str, Any] | None = None, material_name: str | None = None, replace_existing: bool = False, verify: bool = False) -> dict[str, Any]:
        return _send("create_geometry_node_group_from_template", {"template_name": template_name, "node_group_name": node_group_name, "parameters": parameters, "material_name": material_name, "replace_existing": replace_existing, "verify": verify})

    @mcp.tool()
    def create_custom_geometry_node_recipe(ctx: Any, node_group_name: str, recipe: dict[str, Any], replace_existing: bool = False, verify: bool = False) -> dict[str, Any]:
        return _send("create_custom_geometry_node_recipe", {"node_group_name": node_group_name, "recipe": recipe, "replace_existing": replace_existing, "verify": verify})
