"""MCP tool registration for Phase 8A channel packing."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_channel_packing_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register packed texture creation, unpacking, and validation tools."""

    @mcp.tool()
    def pack_texture_channels(ctx: Any, source_images: dict, layout: str = "ORM", output_name: str | None = None, output_path: str | None = None, overwrite: bool = False, color_space: str = "Non-Color") -> str:
        """Pack source texture channels into ORM/RMA/MRA/glTF-style maps."""
        return _send(get_blender_connection, "pack_texture_channels", locals())

    @mcp.tool()
    def unpack_texture_channels(ctx: Any, packed_image_name_or_path: str, layout: str, output_dir: str | None = None, overwrite: bool = False) -> str:
        """Unpack known packed texture layouts into separate channel images."""
        return _send(get_blender_connection, "unpack_texture_channels", locals())

    @mcp.tool()
    def validate_packed_texture(ctx: Any, packed_image_name_or_path: str, layout: str) -> str:
        """Validate dimensions, color-space intent, source manifest, and layout metadata."""
        return _send(get_blender_connection, "validate_packed_texture", locals())
