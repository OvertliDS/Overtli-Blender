from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_driver_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def validate_driver_dsl(dsl: dict[str, Any]) -> str: return _send(get_blender_connection, "validate_driver_dsl", locals())
    @mcp.tool()
    def create_driver_from_dsl(target_type: str, target_name: str, data_path: str, dsl: dict[str, Any], array_index: int = -1, confirm: bool = False) -> str: return _send(get_blender_connection, "create_driver_from_dsl", locals())
    @mcp.tool()
    def list_drivers(target_type: str | None = None, target_name: str | None = None) -> str: return _send(get_blender_connection, "list_drivers", locals())
    @mcp.tool()
    def get_driver_info(target_type: str, target_name: str, data_path: str, array_index: int = -1) -> str: return _send(get_blender_connection, "get_driver_info", locals())
    @mcp.tool()
    def remove_drivers(target_type: str, target_name: str, data_paths: list[dict[str, Any]], confirm: bool = False) -> str: return _send(get_blender_connection, "remove_drivers", locals())
