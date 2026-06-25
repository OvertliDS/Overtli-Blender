from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_animation_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_timeline_info(include_markers: bool = True, include_playback: bool = True) -> str:
        return _send(get_blender_connection, "get_timeline_info", {"include_markers": include_markers, "include_playback": include_playback})

    @mcp.tool()
    def list_animated_objects(include_material_animation: bool = True, include_shape_key_animation: bool = True, include_drivers: bool = True, max_objects: int | None = None) -> str:
        return _send(get_blender_connection, "list_animated_objects", {"include_material_animation": include_material_animation, "include_shape_key_animation": include_shape_key_animation, "include_drivers": include_drivers, "max_objects": max_objects})

    @mcp.tool()
    def get_animation_deep_info(object_name: str | None = None, material_name: str | None = None, include_keyframes: bool = True, include_fcurves: bool = True, include_drivers: bool = True, max_keyframes: int = 200) -> str:
        return _send(get_blender_connection, "get_animation_deep_info", locals())

    @mcp.tool()
    def set_timeline_range(frame_start: int, frame_end: int, fps: int | None = None, current_frame: int | None = None) -> str:
        return _send(get_blender_connection, "set_timeline_range", locals())

    @mcp.tool()
    def set_current_frame(frame: int) -> str:
        return _send(get_blender_connection, "set_current_frame", {"frame": frame})

    @mcp.tool()
    def insert_transform_keyframes(object_name: str, frames: list[int], properties: list[str] | None = None) -> str:
        return _send(get_blender_connection, "insert_transform_keyframes", locals())

    @mcp.tool()
    def animate_object_transform(object_name: str, keyframes: list[dict[str, Any]], interpolation: str = "BEZIER", clear_existing: bool = False, confirm_clear_existing: bool = False, verify: bool = False) -> str:
        return _send(get_blender_connection, "animate_object_transform", locals())

    @mcp.tool()
    def animate_camera_transform(camera_name: str, keyframes: list[dict[str, Any]], interpolation: str = "BEZIER", clear_existing: bool = False, confirm_clear_existing: bool = False, verify: bool = False) -> str:
        return _send(get_blender_connection, "animate_camera_transform", locals())

    @mcp.tool()
    def animate_light_property(light_name: str, property_name: str, keyframes: list[dict[str, Any]], interpolation: str = "BEZIER") -> str:
        return _send(get_blender_connection, "animate_light_property", locals())

    @mcp.tool()
    def animate_material_property(material_name: str, channel: str, keyframes: list[dict[str, Any]], interpolation: str = "BEZIER") -> str:
        return _send(get_blender_connection, "animate_material_property", locals())

    @mcp.tool()
    def animate_shape_key_value(object_name: str, shape_key_name: str, keyframes: list[dict[str, Any]], interpolation: str = "BEZIER") -> str:
        return _send(get_blender_connection, "animate_shape_key_value", locals())

    @mcp.tool()
    def delete_animation_data(target_type: str, target_name: str, data_paths: list[str] | None = None, confirm: bool = False) -> str:
        return _send(get_blender_connection, "delete_animation_data", locals())
