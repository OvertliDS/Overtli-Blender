from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_addon_management_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_addon_management_status() -> str:
        return _send(get_blender_connection, "get_addon_management_status")

    @mcp.tool()
    def list_blender_addons(include_enabled: bool = True, include_disabled: bool = True, include_paths: bool = True, include_version: bool = True, filter_text: str | None = None) -> str:
        return _send(get_blender_connection, "list_blender_addons", locals())

    @mcp.tool()
    def get_blender_addon_info(module_name: str, include_file_info: bool = True, include_preferences_summary: bool = True) -> str:
        return _send(get_blender_connection, "get_blender_addon_info", locals())

    @mcp.tool()
    def install_local_addon(addon_path: str, enable_after_install: bool = False, confirm: bool = False) -> str:
        return _send(get_blender_connection, "install_local_addon", locals())

    @mcp.tool()
    def enable_blender_addon(module_name: str, confirm: bool = False) -> str:
        return _send(get_blender_connection, "enable_blender_addon", locals())

    @mcp.tool()
    def disable_blender_addon(module_name: str, confirm: bool = False, allow_self_disable: bool = False) -> str:
        return _send(get_blender_connection, "disable_blender_addon", locals())

    @mcp.tool()
    def remove_blender_addon(module_name: str, confirm: bool = False, delete_files: bool = False) -> str:
        return _send(get_blender_connection, "remove_blender_addon", locals())
