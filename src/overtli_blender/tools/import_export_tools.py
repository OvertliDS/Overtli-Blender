from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_import_export_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def append_blend_asset(blend_file_path: str, datablock_type: str, datablock_names: list[str], collection_name: str | None = None, link: bool = False, rename_prefix: str | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "append_blend_asset", locals())

    @mcp.tool()
    def import_model_file(file_path: str, format_hint: str | None = None, collection_name: str | None = None, rename_prefix: str | None = None, import_materials: bool = True, import_animations: bool = True, import_cameras_lights: bool = True, verify: bool = True) -> str:
        return _send(get_blender_connection, "import_model_file", locals())

    @mcp.tool()
    def export_selected_objects(output_path: str | None = None, format_hint: str = "glb", object_names: list[str] | None = None, overwrite: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "export_selected_objects", locals())

    @mcp.tool()
    def export_scene(output_path: str | None = None, format_hint: str = "glb", overwrite: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "export_scene", locals())
