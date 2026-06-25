from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_nla_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_nla_track(object_name: str, track_name: str) -> str: return _send(get_blender_connection, "create_nla_track", locals())
    @mcp.tool()
    def add_action_to_nla(object_name: str, action_name: str, track_name: str | None = None, strip_name: str | None = None, frame_start: int = 1, frame_end: int | None = None, blend_type: str = "REPLACE") -> str: return _send(get_blender_connection, "add_action_to_nla", locals())
    @mcp.tool()
    def edit_nla_strip(object_name: str, track_name: str, strip_name: str, frame_start: float | None = None, frame_end: float | None = None, mute: bool | None = None, blend_type: str | None = None) -> str: return _send(get_blender_connection, "edit_nla_strip", locals())
    @mcp.tool()
    def mute_nla_track(object_name: str, track_name: str, mute: bool = True) -> str: return _send(get_blender_connection, "mute_nla_track", locals())
    @mcp.tool()
    def delete_nla_tracks(object_name: str, track_names: list[str], confirm: bool = False) -> str: return _send(get_blender_connection, "delete_nla_tracks", locals())
    @mcp.tool()
    def validate_nla_stack(object_name: str) -> str: return _send(get_blender_connection, "validate_nla_stack", locals())
