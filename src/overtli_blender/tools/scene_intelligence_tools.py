"""MCP tool registration for Phase 2 scene intelligence tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def register_scene_intelligence_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register rich read-only scene and selection inspection MCP tools."""

    @mcp.tool()
    def get_scene_index(
        ctx: Any,
        include_hidden: bool = True,
        include_materials: bool = True,
        include_modifiers: bool = True,
        include_constraints: bool = True,
        include_collections: bool = True,
        max_objects: int | None = None,
    ) -> str:
        """Get a bounded full-scene index with object transforms, hierarchy, materials, modifiers, and collections."""
        try:
            blender = get_blender_connection()
            result = blender.send_command(
                "get_scene_index",
                {
                    "include_hidden": include_hidden,
                    "include_materials": include_materials,
                    "include_modifiers": include_modifiers,
                    "include_constraints": include_constraints,
                    "include_collections": include_collections,
                    "max_objects": max_objects,
                },
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting scene index: {str(e)}"

    @mcp.tool()
    def get_object_deep_info(
        ctx: Any,
        object_name: str,
        include_mesh_stats: bool = True,
        include_material_slots: bool = True,
        include_modifiers: bool = True,
        include_constraints: bool = True,
        include_animation: bool = True,
        include_custom_properties: bool = True,
    ) -> str:
        """Get bounded deep inspection data for one object."""
        try:
            blender = get_blender_connection()
            result = blender.send_command(
                "get_object_deep_info",
                {
                    "object_name": object_name,
                    "include_mesh_stats": include_mesh_stats,
                    "include_material_slots": include_material_slots,
                    "include_modifiers": include_modifiers,
                    "include_constraints": include_constraints,
                    "include_animation": include_animation,
                    "include_custom_properties": include_custom_properties,
                },
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting object deep info: {str(e)}"

    @mcp.tool()
    def get_selection_info(ctx: Any) -> str:
        """Get active object and selection details without changing Blender mode or selection state."""
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_selection_info")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting selection info: {str(e)}"

    @mcp.tool()
    def get_scene_health(ctx: Any) -> str:
        """Get non-destructive scene metrics and health issues."""
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_scene_health")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting scene health: {str(e)}"
