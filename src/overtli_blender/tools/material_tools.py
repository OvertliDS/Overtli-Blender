"""MCP tool registration for Phase 3 material authoring tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_material_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register basic material creation and assignment tools."""

    @mcp.tool()
    def create_basic_material(ctx: Any, name: str, base_color: list[float] | None = None, metallic: float | None = None, roughness: float | None = None, alpha: float | None = None, use_nodes: bool = True, replace_existing: bool = False) -> str:
        """Create a basic material and configure Principled BSDF properties when nodes are enabled."""
        try:
            return _send(get_blender_connection, "create_basic_material", locals())
        except Exception as e:
            return f"Error creating material: {str(e)}"

    @mcp.tool()
    def assign_material(ctx: Any, object_name: str, material_name: str, slot_index: int | None = None, replace: bool = True, verify: bool = False) -> str:
        """Assign an existing material to one explicitly named object."""
        try:
            return _send(get_blender_connection, "assign_material", locals())
        except Exception as e:
            return f"Error assigning material: {str(e)}"

    @mcp.tool()
    def update_material_properties(ctx: Any, material_name: str, base_color: list[float] | None = None, metallic: float | None = None, roughness: float | None = None, alpha: float | None = None, verify: bool = False) -> str:
        """Update supported material properties without creating a shader graph."""
        try:
            return _send(get_blender_connection, "update_material_properties", locals())
        except Exception as e:
            return f"Error updating material properties: {str(e)}"
