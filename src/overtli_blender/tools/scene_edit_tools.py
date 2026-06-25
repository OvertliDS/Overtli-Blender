"""MCP tool registration for Phase 3 scene edit tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    if params:
        params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_scene_edit_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register explicit-target scene edit MCP tools."""

    @mcp.tool()
    def get_supported_edit_operations(ctx: Any) -> str:
        """List supported Phase 3 edit operations and safety metadata."""
        try:
            return _send(get_blender_connection, "get_supported_edit_operations")
        except Exception as e:
            return f"Error getting supported edit operations: {str(e)}"

    @mcp.tool()
    def create_primitive_object(ctx: Any, primitive_type: str, name: str | None = None, location: list[float] | None = None, rotation: list[float] | None = None, scale: list[float] | None = None, collection_name: str | None = None, material_name: str | None = None, verify: bool = False) -> str:
        """Create a supported primitive object with explicit transform and collection parameters."""
        try:
            return _send(get_blender_connection, "create_primitive_object", locals())
        except Exception as e:
            return f"Error creating primitive object: {str(e)}"

    @mcp.tool()
    def transform_object(ctx: Any, object_name: str, location: list[float] | None = None, rotation: list[float] | None = None, scale: list[float] | None = None, relative: bool = False, verify: bool = False) -> str:
        """Transform one explicitly named object."""
        try:
            return _send(get_blender_connection, "transform_object", locals())
        except Exception as e:
            return f"Error transforming object: {str(e)}"

    @mcp.tool()
    def duplicate_object(ctx: Any, object_name: str, new_name: str | None = None, linked: bool = False, location_offset: list[float] | None = None, collection_name: str | None = None, verify: bool = False) -> str:
        """Duplicate one explicitly named object."""
        try:
            return _send(get_blender_connection, "duplicate_object", locals())
        except Exception as e:
            return f"Error duplicating object: {str(e)}"

    @mcp.tool()
    def delete_objects(ctx: Any, object_names: list[str], confirm: bool = False, allow_missing: bool = False, verify: bool = False) -> str:
        """Delete only explicitly named objects after confirmation."""
        try:
            return _send(get_blender_connection, "delete_objects", locals())
        except Exception as e:
            return f"Error deleting objects: {str(e)}"

    @mcp.tool()
    def set_object_visibility(ctx: Any, object_name: str, hide_viewport: bool | None = None, hide_render: bool | None = None, verify: bool = False) -> str:
        """Set visibility on one explicitly named object."""
        try:
            return _send(get_blender_connection, "set_object_visibility", locals())
        except Exception as e:
            return f"Error setting object visibility: {str(e)}"

    @mcp.tool()
    def run_verified_edit_batch(ctx: Any, label: str | None = None, operations: list[dict] | None = None, create_before_snapshot: bool = True, create_after_snapshot: bool = True, stop_on_error: bool = True, max_operations: int = 20, batch_allow_destructive: bool = False, artifact_root: str | None = None) -> str:
        """Run a controlled allowlisted edit batch with before/after verification."""
        try:
            return _send(get_blender_connection, "run_verified_edit_batch", locals())
        except Exception as e:
            return f"Error running verified edit batch: {str(e)}"
