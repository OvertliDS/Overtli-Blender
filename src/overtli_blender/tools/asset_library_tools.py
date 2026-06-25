from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_asset_library_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_supported_asset_formats() -> str:
        return _send(get_blender_connection, "get_supported_asset_formats")

    @mcp.tool()
    def scan_asset_folder(folder_path: str, recursive: bool = True, include_textures: bool = True, include_blend_files: bool = True, include_model_files: bool = True, max_files: int = 1000, write_manifest: bool = True, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "scan_asset_folder", locals())

    @mcp.tool()
    def list_asset_libraries(artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "list_asset_libraries", locals())

    @mcp.tool()
    def list_scene_assets(include_objects: bool = True, include_meshes: bool = True, include_materials: bool = True, include_images: bool = True, include_libraries: bool = True, include_actions: bool = True, include_collections: bool = True) -> str:
        return _send(get_blender_connection, "list_scene_assets", locals())

    @mcp.tool()
    def get_asset_file_info(file_path: str, inspect_blend_contents: bool = True) -> str:
        return _send(get_blender_connection, "get_asset_file_info", locals())
