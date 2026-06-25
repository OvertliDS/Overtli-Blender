from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_scene_kit_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_asset_preview(object_names: list[str] | None = None, label: str | None = None, artifact_root: str | None = None, camera_name: str | None = None, clamp_for_smoke: bool = True) -> str:
        return _send(get_blender_connection, "create_asset_preview", locals())

    @mcp.tool()
    def create_asset_contact_sheet(object_names: list[str] | None = None, label: str | None = None, artifact_root: str | None = None, views: list[str] | None = None, camera_name: str | None = None, clamp_for_smoke: bool = True) -> str:
        return _send(get_blender_connection, "create_asset_contact_sheet", locals())

    @mcp.tool()
    def create_scene_kit(kit_id: str | None = None, label: str | None = None, collection_name: str | None = None, object_names: list[str] | None = None, export_format: str = "glb", include_preview: bool = True, include_scene_export: bool = True, overwrite: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "create_scene_kit", locals())

    @mcp.tool()
    def import_scene_kit(kit_path: str, collection_name: str | None = None, rename_prefix: str | None = None) -> str:
        return _send(get_blender_connection, "import_scene_kit", locals())

    @mcp.tool()
    def validate_scene_kit(kit_path: str) -> str:
        return _send(get_blender_connection, "validate_scene_kit", locals())

    @mcp.tool()
    def list_scene_kits(artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "list_scene_kits", locals())
