"""MCP tool registration for Phase 4B deformation modifier and workflow tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_deformation_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register allowlisted deformation modifiers, region deformation, and workflow batches."""

    @mcp.tool()
    def add_deformation_modifier(ctx: Any, object_name: str, modifier_type: str, name: str | None = None, properties: dict[str, Any] | None = None, vertex_group_name: str | None = None, verify: bool = False) -> str:
        """Add an allowlisted non-applied deformation modifier to one object."""
        try:
            return _send(get_blender_connection, "add_deformation_modifier", locals())
        except Exception as e:
            return f"Error adding deformation modifier: {str(e)}"

    @mcp.tool()
    def update_deformation_modifier(ctx: Any, object_name: str, modifier_name: str, properties: dict[str, Any], vertex_group_name: str | None = None, verify: bool = False) -> str:
        """Update allowlisted properties on an existing deformation modifier."""
        try:
            return _send(get_blender_connection, "update_deformation_modifier", locals())
        except Exception as e:
            return f"Error updating deformation modifier: {str(e)}"

    @mcp.tool()
    def create_region_deformation(ctx: Any, object_name: str, region: dict[str, Any], deformation: dict[str, Any], method: str = "shape_key", name: str | None = None, verify: bool = True, confirm: bool = False) -> str:
        """Create an agent-friendly bounded region deformation using shape key, lattice, or modifier method."""
        try:
            return _send(get_blender_connection, "create_region_deformation", locals())
        except Exception as e:
            return f"Error creating region deformation: {str(e)}"

    @mcp.tool()
    def run_deformation_workflow_batch(ctx: Any, operations: list[dict[str, Any]], label: str | None = None, create_before_snapshot: bool = True, create_after_snapshot: bool = True, stop_on_error: bool = True, max_operations: int = 30, batch_allow_destructive: bool = False) -> str:
        """Run an allowlisted deformation workflow batch with optional before/after snapshots."""
        try:
            return _send(get_blender_connection, "run_deformation_workflow_batch", locals())
        except Exception as e:
            return f"Error running deformation workflow batch: {str(e)}"
