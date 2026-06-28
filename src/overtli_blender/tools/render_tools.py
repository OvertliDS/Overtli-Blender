from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_render_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_render_settings() -> str:
        return _send(get_blender_connection, "get_render_settings")

    @mcp.tool()
    def get_supported_color_management() -> str:
        return _send(get_blender_connection, "get_supported_color_management")

    @mcp.tool()
    def set_render_settings(engine: str | None = None, resolution_x: int | None = None, resolution_y: int | None = None, resolution_percentage: int | None = None, samples: int | None = None, image_format: str | None = None, transparent: bool | None = None, color_management: dict[str, Any] | None = None, clamp_for_smoke: bool = False, auto_compatible: bool = False) -> str:
        return _send(get_blender_connection, "set_render_settings", locals())

    @mcp.tool()
    def set_output_path(output_path: str | None = None, artifact_root: str | None = None, subdir: str = "renders/stills", filename: str | None = None) -> str:
        return _send(get_blender_connection, "set_output_path", locals())

    @mcp.tool()
    def render_still(output_path: str | None = None, artifact_root: str | None = None, filename: str | None = None, camera_name: str | None = None, frame: int | None = None, clamp_for_smoke: bool = True, write_manifest: bool = True) -> str:
        return _send(get_blender_connection, "render_still", locals())

    @mcp.tool()
    def render_contact_sheet(object_names: list[str] | None = None, camera_name: str | None = None, views: list[str] | None = None, artifact_root: str | None = None, filename: str | None = None, clamp_for_smoke: bool = True) -> str:
        return _send(get_blender_connection, "render_contact_sheet", locals())

    @mcp.tool()
    def create_turntable_animation(object_name: str, frame_start: int = 1, frame_end: int = 48, axis: str = "Z", rotations: float = 1.0, empty_name: str | None = None, camera_name: str | None = None, confirm_clear_existing: bool = False) -> str:
        return _send(get_blender_connection, "create_turntable_animation", locals())

    @mcp.tool()
    def render_preview_animation(output_dir: str | None = None, artifact_root: str | None = None, frame_start: int | None = None, frame_end: int | None = None, step: int = 1, max_frames: int = 24, camera_name: str | None = None, clamp_for_smoke: bool = True) -> str:
        return _send(get_blender_connection, "render_preview_animation", locals())
