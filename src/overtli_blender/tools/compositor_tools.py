from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_compositor_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_compositor_status() -> str:
        return _send(get_blender_connection, "get_compositor_status")

    @mcp.tool()
    def set_compositor_preset(preset: str = "basic_viewer", confirm_replace: bool = False) -> str:
        return _send(get_blender_connection, "set_compositor_preset", locals())

    @mcp.tool()
    def set_render_passes(use_pass_z: bool | None = None, use_pass_mist: bool | None = None, use_pass_normal: bool | None = None, use_pass_diffuse_color: bool | None = None) -> str:
        return _send(get_blender_connection, "set_render_passes", locals())
