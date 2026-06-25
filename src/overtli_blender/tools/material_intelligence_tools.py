"""MCP tool registration for Phase 4A material intelligence tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_material_intelligence_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register material schema, inventory, and deep inspection tools."""

    @mcp.tool()
    def get_material_channel_schema(ctx: Any) -> str:
        """Return the Phase 4A material channel, texture slot, and packed-map vocabulary."""
        try:
            return _send(get_blender_connection, "get_material_channel_schema", locals())
        except Exception as e:
            return f"Error getting material channel schema: {str(e)}"

    @mcp.tool()
    def get_supported_material_templates(ctx: Any) -> str:
        """Return supported production material templates and their channel plans."""
        try:
            return _send(get_blender_connection, "get_supported_material_templates", locals())
        except Exception as e:
            return f"Error getting material templates: {str(e)}"

    @mcp.tool()
    def list_materials_deep(ctx: Any, include_node_summary: bool = True, include_users: bool = True, include_objects: bool = True, include_texture_slots: bool = True, include_channel_summary: bool = True, max_materials: int | None = None) -> str:
        """List materials with user, channel, texture-slot, and bounded node summaries."""
        try:
            return _send(get_blender_connection, "list_materials_deep", locals())
        except Exception as e:
            return f"Error listing materials deeply: {str(e)}"

    @mcp.tool()
    def get_material_deep_info(ctx: Any, material_name: str, include_node_graph: bool = True, include_texture_slots: bool = True, include_channel_summary: bool = True, include_users: bool = True, include_preview_hints: bool = True) -> str:
        """Inspect one material with channel, texture, graph, user, and preview metadata."""
        try:
            return _send(get_blender_connection, "get_material_deep_info", locals())
        except Exception as e:
            return f"Error getting material deep info: {str(e)}"
