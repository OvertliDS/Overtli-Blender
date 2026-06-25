from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_fcurve_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def insert_keyframe_batch(object_name: str, keyframes: list[dict[str, Any]], create_action: bool = True, action_name: str | None = None) -> str: return _send(get_blender_connection, "insert_keyframe_batch", locals())
    @mcp.tool()
    def edit_keyframes(action_name: str, edits: list[dict[str, Any]], confirm: bool = False) -> str: return _send(get_blender_connection, "edit_keyframes", locals())
    @mcp.tool()
    def retime_action(action_name: str, frame_start: float, frame_end: float, new_start: float, new_end: float, confirm: bool = False) -> str: return _send(get_blender_connection, "retime_action", locals())
    @mcp.tool()
    def set_fcurve_interpolation(action_name: str, fcurves: list[dict[str, Any]] | None = None, interpolation: str = "BEZIER", easing: str | None = None) -> str: return _send(get_blender_connection, "set_fcurve_interpolation", locals())
    @mcp.tool()
    def add_fcurve_modifier(action_name: str, data_path: str, array_index: int = 0, modifier_type: str = "CYCLES", settings: dict[str, Any] | None = None) -> str: return _send(get_blender_connection, "add_fcurve_modifier", locals())
    @mcp.tool()
    def remove_fcurve_modifier(action_name: str, data_path: str, array_index: int = 0, modifier_name: str | None = None, modifier_type: str | None = None, confirm: bool = False) -> str: return _send(get_blender_connection, "remove_fcurve_modifier", locals())
    @mcp.tool()
    def validate_fcurves(action_name: str) -> str: return _send(get_blender_connection, "validate_fcurves", locals())
