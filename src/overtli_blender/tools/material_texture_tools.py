"""MCP tool registration for Phase 4A material texture slot tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_material_texture_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register texture/map slot binding tools."""

    @mcp.tool()
    def bind_material_texture_map(ctx: Any, material_name: str, map_kind: str, texture_path: str, strict_file_exists: bool = True, connect: bool = True, packed_convention: str | None = None, verify: bool = True) -> str:
        """Bind or validate a texture map slot with color-space intent and packed-map metadata."""
        try:
            return _send(get_blender_connection, "bind_material_texture_map", locals())
        except Exception as e:
            return f"Error binding material texture map: {str(e)}"
