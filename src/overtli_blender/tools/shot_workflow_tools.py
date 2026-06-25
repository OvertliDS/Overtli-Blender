from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_shot_workflow_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_shot_range(name: str, frame_start: int, frame_end: int, camera_name: str | None = None, set_scene_range: bool = False) -> str: return _send(get_blender_connection, "create_shot_range", locals())
    @mcp.tool()
    def create_camera_cut(name: str, frame: int, camera_name: str) -> str: return _send(get_blender_connection, "create_camera_cut", locals())
    @mcp.tool()
    def create_timeline_marker(name: str, frame: int, camera_name: str | None = None) -> str: return _send(get_blender_connection, "create_timeline_marker", locals())
    @mcp.tool()
    def create_shot_plan(plan_name: str, ranges: list[dict[str, Any]] | None = None, cuts: list[dict[str, Any]] | None = None, markers: list[dict[str, Any]] | None = None) -> str: return _send(get_blender_connection, "create_shot_plan", locals())
    @mcp.tool()
    def validate_shot_plan(plan_name: str | None = None, plan: dict[str, Any] | None = None) -> str: return _send(get_blender_connection, "validate_shot_plan", locals())
