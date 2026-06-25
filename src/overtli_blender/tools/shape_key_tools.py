"""MCP tool registration for Phase 4B shape key tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_shape_key_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register Basis-preserving shape key inspection and deformation tools."""

    @mcp.tool()
    def create_shape_key(ctx: Any, object_name: str, shape_key_name: str, from_mix: bool = False, replace_existing: bool = False, value: float = 0.0) -> str:
        """Create a named shape key on one mesh object while preserving Basis."""
        try:
            return _send(get_blender_connection, "create_shape_key", locals())
        except Exception as e:
            return f"Error creating shape key: {str(e)}"

    @mcp.tool()
    def update_shape_key_value(ctx: Any, object_name: str, shape_key_name: str, value: float) -> str:
        """Set one shape key value on one mesh object."""
        try:
            return _send(get_blender_connection, "update_shape_key_value", locals())
        except Exception as e:
            return f"Error updating shape key value: {str(e)}"

    @mcp.tool()
    def edit_shape_key_offsets(ctx: Any, object_name: str, shape_key_name: str, offsets: list[dict[str, Any]] | None = None, vertex_group_name: str | None = None, deformation: dict[str, Any] | None = None, confirm: bool = False, verify: bool = False) -> str:
        """Write bounded reversible deformation offsets into a non-Basis shape key after confirmation."""
        try:
            return _send(get_blender_connection, "edit_shape_key_offsets", locals())
        except Exception as e:
            return f"Error editing shape key offsets: {str(e)}"

    @mcp.tool()
    def list_shape_keys(ctx: Any, object_name: str, include_stats: bool = True) -> str:
        """List shape keys for one mesh object."""
        try:
            return _send(get_blender_connection, "list_shape_keys", locals())
        except Exception as e:
            return f"Error listing shape keys: {str(e)}"

    @mcp.tool()
    def delete_shape_keys(ctx: Any, object_name: str, shape_key_names: list[str], confirm: bool = False, allow_basis: bool = False) -> str:
        """Delete explicitly named shape keys after confirmation, refusing Basis by default."""
        try:
            return _send(get_blender_connection, "delete_shape_keys", locals())
        except Exception as e:
            return f"Error deleting shape keys: {str(e)}"
