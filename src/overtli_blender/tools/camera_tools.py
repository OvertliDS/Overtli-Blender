from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params), indent=2)


def register_camera_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_camera(camera_name: str | None = None, location: list[float] | None = None, rotation: list[float] | None = None, lens: float | None = None, sensor_width: float | None = None, clip_start: float | None = None, clip_end: float | None = None, collection_name: str | None = None, set_active: bool = False, verify: bool = False) -> str:
        return _send(get_blender_connection, "create_camera", locals())

    @mcp.tool()
    def frame_camera_to_objects(camera_name: str, object_names: list[str], view: str = "front_perspective", margin: float = 1.25, distance_multiplier: float = 1.0, look_at: bool = True, set_active: bool = True, verify: bool = False) -> str:
        return _send(get_blender_connection, "frame_camera_to_objects", locals())

    @mcp.tool()
    def set_active_camera(camera_name: str) -> str:
        return _send(get_blender_connection, "set_active_camera", {"camera_name": camera_name})
