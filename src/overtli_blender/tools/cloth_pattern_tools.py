"""MCP tools for cloth pattern panel workflows."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_cloth_pattern_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_cloth_pattern_panel(ctx: Any, panel_name: str, points: list[list[float]], thickness: float = 0.01, collection_name: str | None = None, material_name: str | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "create_cloth_pattern_panel", locals())

    @mcp.tool()
    def define_cloth_seam_pair(ctx: Any, panel_a: str, edge_a: list[int], panel_b: str, edge_b: list[int], seam_name: str | None = None) -> str:
        return _send(get_blender_connection, "define_cloth_seam_pair", locals())

    @mcp.tool()
    def create_cloth_setup(ctx: Any, object_name: str, quality: int = 3, mass: float = 0.3, pressure: float = 0.0, pin_group_name: str | None = None) -> str:
        return _send(get_blender_connection, "create_cloth_setup", locals())

    @mcp.tool()
    def create_cloth_pin_group(ctx: Any, object_name: str, vertex_indices: list[int] | None = None, group_name: str = "Overtli_Cloth_Pin", weight: float = 1.0) -> str:
        return _send(get_blender_connection, "create_cloth_pin_group", locals())

    @mcp.tool()
    def create_cloth_collision_setup(ctx: Any, object_name: str, thickness_outer: float = 0.02, thickness_inner: float = 0.01) -> str:
        return _send(get_blender_connection, "create_cloth_collision_setup", locals())

    @mcp.tool()
    def simulate_cloth_preview(ctx: Any, object_name: str, frame_start: int = 1, frame_end: int = 24, approval_id: str | None = None, max_frames: int = 48) -> str:
        return _send(get_blender_connection, "simulate_cloth_preview", locals())

    @mcp.tool()
    def bake_cloth_cache(ctx: Any, object_name: str, approval_id: str | None = None) -> str:
        return _send(get_blender_connection, "bake_cloth_cache", locals())

    @mcp.tool()
    def clear_cloth_cache(ctx: Any, object_name: str, approval_id: str | None = None) -> str:
        return _send(get_blender_connection, "clear_cloth_cache", locals())

    @mcp.tool()
    def convert_cloth_result(ctx: Any, object_name: str, new_object_name: str | None = None, approval_id: str | None = None) -> str:
        return _send(get_blender_connection, "convert_cloth_result", locals())
