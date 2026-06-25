from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_animation_intelligence_advanced_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_animation_system_capabilities() -> str:
        return _send(get_blender_connection, "get_animation_system_capabilities")
    @mcp.tool()
    def inspect_animation_system(object_names: list[str] | None = None, include_actions: bool = True, include_fcurves: bool = True, include_nla: bool = True, include_drivers: bool = True, include_constraints: bool = True, include_pose: bool = True, include_simulation: bool = True) -> str:
        return _send(get_blender_connection, "inspect_animation_system", locals())
