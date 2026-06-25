"""MCP tool registration for Phase 4A material preview tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_material_preview_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register material preview artifact tools."""

    @mcp.tool()
    def create_material_preview(ctx: Any, material_name: str, preview_shape: str = "sphere", artifact_root: str | None = None, include_snapshot: bool = True) -> str:
        """Create a local material preview manifest and optional verification snapshot."""
        try:
            return _send(get_blender_connection, "create_material_preview", locals())
        except Exception as e:
            return f"Error creating material preview: {str(e)}"
