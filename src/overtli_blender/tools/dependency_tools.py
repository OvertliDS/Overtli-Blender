from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_dependency_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_asset_dependency_report(include_images: bool = True, include_libraries: bool = True, include_fonts: bool = True, include_movie_clips: bool = True, include_sounds: bool = True, write_manifest: bool = True, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "get_asset_dependency_report", locals())

    @mcp.tool()
    def create_asset_manifest(label: str | None = None, include_scene_index: bool = True, include_scene_assets: bool = True, include_dependencies: bool = True, include_materials: bool = True, include_animation: bool = True, include_render_settings: bool = True, include_previews: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "create_asset_manifest", locals())

    @mcp.tool()
    def collect_external_dependencies(target_dir: str | None = None, overwrite: bool = False, include_packed: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "collect_external_dependencies", locals())

    @mcp.tool()
    def validate_external_dependencies() -> str:
        return _send(get_blender_connection, "validate_external_dependencies")

    @mcp.tool()
    def pack_external_data(confirm: bool = False) -> str:
        return _send(get_blender_connection, "pack_external_data", locals())

    @mcp.tool()
    def make_paths_relative(confirm: bool = False) -> str:
        return _send(get_blender_connection, "make_paths_relative", locals())
