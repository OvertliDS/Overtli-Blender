from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_action_library_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def list_actions() -> str: return _send(get_blender_connection, "list_actions")
    @mcp.tool()
    def get_action_deep_info(action_name: str, include_keyframes: bool = False, max_keyframes: int = 200) -> str: return _send(get_blender_connection, "get_action_deep_info", locals())
    @mcp.tool()
    def create_action(action_name: str, object_name: str | None = None, frame_start: int | None = None, frame_end: int | None = None, assign_to_object: bool = False) -> str: return _send(get_blender_connection, "create_action", locals())
    @mcp.tool()
    def duplicate_action(source_action_name: str, new_action_name: str, assign_to_object: str | None = None) -> str: return _send(get_blender_connection, "duplicate_action", locals())
    @mcp.tool()
    def rename_action(action_name: str, new_action_name: str, confirm: bool = False) -> str: return _send(get_blender_connection, "rename_action", locals())
    @mcp.tool()
    def assign_action(object_name: str, action_name: str, create_animation_data: bool = True) -> str: return _send(get_blender_connection, "assign_action", locals())
    @mcp.tool()
    def delete_actions(action_names: list[str], allow_used: bool = False, confirm: bool = False) -> str: return _send(get_blender_connection, "delete_actions", locals())
