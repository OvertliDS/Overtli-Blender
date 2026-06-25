from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_addon_development_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_addon_skeleton(addon_name: str, module_name: str | None = None, output_dir: str | None = None, include_operator: bool = True, include_panel: bool = True, include_preferences: bool = True, include_property_group: bool = True, include_readme: bool = True, include_manifest: bool = True) -> str:
        return _send(get_blender_connection, "create_addon_skeleton", locals())

    @mcp.tool()
    def validate_addon_skeleton(addon_dir_or_file: str, check_register_functions: bool = True, check_bl_info: bool = True, check_operator_ids: bool = True, check_no_secrets: bool = True) -> str:
        return _send(get_blender_connection, "validate_addon_skeleton", locals())

    @mcp.tool()
    def package_addon_zip(addon_dir_or_file: str, output_path: str | None = None, overwrite: bool = False) -> str:
        return _send(get_blender_connection, "package_addon_zip", locals())
