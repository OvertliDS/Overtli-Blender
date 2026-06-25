"""MCP tool registration for Phase 3 modifier tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_modifier_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register allowlisted modifier management tools."""

    @mcp.tool()
    def add_object_modifier(ctx: Any, object_name: str, modifier_type: str, name: str | None = None, properties: dict | None = None, verify: bool = False) -> str:
        """Add an allowlisted modifier to one explicitly named object without applying it."""
        try:
            return _send(get_blender_connection, "add_object_modifier", locals())
        except Exception as e:
            return f"Error adding object modifier: {str(e)}"

    @mcp.tool()
    def update_object_modifier(ctx: Any, object_name: str, modifier_name: str, properties: dict, verify: bool = False) -> str:
        """Update allowlisted properties on an existing modifier."""
        try:
            return _send(get_blender_connection, "update_object_modifier", locals())
        except Exception as e:
            return f"Error updating object modifier: {str(e)}"

    @mcp.tool()
    def remove_object_modifier(ctx: Any, object_name: str, modifier_name: str, confirm: bool = False, verify: bool = False) -> str:
        """Remove one named modifier after explicit confirmation."""
        try:
            return _send(get_blender_connection, "remove_object_modifier", locals())
        except Exception as e:
            return f"Error removing object modifier: {str(e)}"
