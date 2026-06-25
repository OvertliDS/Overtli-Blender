"""MCP tool registration for Phase 4B lattice deformation tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_lattice_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register non-applied lattice deformer creation, update, binding, and removal tools."""

    @mcp.tool()
    def create_lattice_deformer(ctx: Any, target_object_name: str, lattice_name: str | None = None, resolution: list[int] | None = None, padding: float = 0.25, collection_name: str | None = None, add_modifier: bool = True, verify: bool = False) -> str:
        """Create a lattice cage around an explicitly named target object."""
        try:
            return _send(get_blender_connection, "create_lattice_deformer", locals())
        except Exception as e:
            return f"Error creating lattice deformer: {str(e)}"

    @mcp.tool()
    def update_lattice_deformer(ctx: Any, lattice_name: str, control_point_offsets: list[dict[str, Any]] | None = None, deformation: dict[str, Any] | None = None, confirm: bool = False, verify: bool = False) -> str:
        """Update exact lattice control points or a bounded lattice deformation after confirmation."""
        try:
            return _send(get_blender_connection, "update_lattice_deformer", locals())
        except Exception as e:
            return f"Error updating lattice deformer: {str(e)}"

    @mcp.tool()
    def apply_lattice_to_object(ctx: Any, target_object_name: str, lattice_name: str, modifier_name: str | None = None, create_if_missing: bool = True) -> str:
        """Add or update a Lattice modifier on one target object without applying it destructively."""
        try:
            return _send(get_blender_connection, "apply_lattice_to_object", locals())
        except Exception as e:
            return f"Error applying lattice to object: {str(e)}"

    @mcp.tool()
    def remove_lattice_deformer(ctx: Any, lattice_name: str, target_object_name: str | None = None, remove_modifier: bool = True, delete_lattice_object: bool = True, confirm: bool = False) -> str:
        """Remove an exact lattice deformer and associated modifiers after confirmation."""
        try:
            return _send(get_blender_connection, "remove_lattice_deformer", locals())
        except Exception as e:
            return f"Error removing lattice deformer: {str(e)}"
