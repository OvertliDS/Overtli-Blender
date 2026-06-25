from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_motion_validation_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_motion_path_preview(object_name: str, frame_start: int | None = None, frame_end: int | None = None) -> str: return _send(get_blender_connection, "create_motion_path_preview", locals())
    @mcp.tool()
    def validate_motion(object_names: list[str] | None = None, include_rig: bool = True, include_drivers: bool = True, include_nla: bool = True, include_simulation: bool = True) -> str: return _send(get_blender_connection, "validate_motion", locals())
    @mcp.tool()
    def run_animation_rigging_workflow_batch(label: str | None = None, operations: list[dict[str, Any]] | None = None, stop_on_error: bool = True, max_operations: int = 40, allow_high_risk: bool = False) -> str: return _send(get_blender_connection, "run_animation_rigging_workflow_batch", locals())
