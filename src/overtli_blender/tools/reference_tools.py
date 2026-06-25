"""MCP wrappers for Phase 7C reference image commands."""

from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    if params:
        params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_reference_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def import_reference_image(ctx: Any, source_path: str, reference_type: str = "empty_image", copy_into_project: bool = True, name: str | None = None) -> str:
        return _send(get_blender_connection, "import_reference_image", locals())

    @mcp.tool()
    def create_reference_set(ctx: Any, name: str, reference_ids: list[str] | None = None) -> str:
        return _send(get_blender_connection, "create_reference_set", locals())

    @mcp.tool()
    def place_reference_view(ctx: Any, reference_id: str, view: str = "front_orthographic", scale: float = 1.0) -> str:
        return _send(get_blender_connection, "place_reference_view", locals())

    @mcp.tool()
    def calibrate_reference_scale(ctx: Any, reference_id: str, known_distance: float, unit: str = "METERS") -> str:
        return _send(get_blender_connection, "calibrate_reference_scale", locals())

    @mcp.tool()
    def set_reference_opacity(ctx: Any, reference_id: str, opacity: float) -> str:
        return _send(get_blender_connection, "set_reference_opacity", locals())

    @mcp.tool()
    def set_reference_depth(ctx: Any, reference_id: str, depth: str) -> str:
        return _send(get_blender_connection, "set_reference_depth", locals())

    @mcp.tool()
    def lock_reference(ctx: Any, reference_id: str, locked: bool = True) -> str:
        return _send(get_blender_connection, "lock_reference", locals())

    @mcp.tool()
    def set_reference_view_visibility(ctx: Any, reference_id: str, visible: bool = True) -> str:
        return _send(get_blender_connection, "set_reference_view_visibility", locals())

    @mcp.tool()
    def add_reference_landmark(ctx: Any, reference_id: str, name: str, point: list[float]) -> str:
        return _send(get_blender_connection, "add_reference_landmark", locals())

    @mcp.tool()
    def measure_reference_landmarks(ctx: Any, reference_id: str, from_landmark: str, to_landmark: str) -> str:
        return _send(get_blender_connection, "measure_reference_landmarks", locals())

    @mcp.tool()
    def capture_reference_overlay(ctx: Any, reference_id: str) -> str:
        return _send(get_blender_connection, "capture_reference_overlay", locals())

    @mcp.tool()
    def list_reference_images(ctx: Any) -> str:
        return _send(get_blender_connection, "list_reference_images", locals())

    @mcp.tool()
    def relink_reference_image(ctx: Any, reference_id: str, new_path: str) -> str:
        return _send(get_blender_connection, "relink_reference_image", locals())

    @mcp.tool()
    def remove_reference_image(ctx: Any, reference_id: str, delete_file: bool = False, confirm: bool = False) -> str:
        return _send(get_blender_connection, "remove_reference_image", locals())
