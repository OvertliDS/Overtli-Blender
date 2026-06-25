"""MCP wrappers for Phase 7C spatial measurement and rename commands."""

from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    if params:
        params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_spatial_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def calculate_distance(ctx: Any, from_object: str | None = None, to_object: str | None = None, point_a: list[float] | None = None, point_b: list[float] | None = None) -> str:
        return _send(get_blender_connection, "calculate_distance", locals())

    @mcp.tool()
    def calculate_angle(ctx: Any, point_a: list[float], point_b: list[float], point_c: list[float]) -> str:
        return _send(get_blender_connection, "calculate_angle", locals())

    @mcp.tool()
    def calculate_area(ctx: Any, object_name: str) -> str:
        return _send(get_blender_connection, "calculate_area", locals())

    @mcp.tool()
    def calculate_volume(ctx: Any, object_name: str) -> str:
        return _send(get_blender_connection, "calculate_volume", locals())

    @mcp.tool()
    def calculate_curve_length(ctx: Any, object_name: str) -> str:
        return _send(get_blender_connection, "calculate_curve_length", locals())

    @mcp.tool()
    def calculate_clearance(ctx: Any, object_a: str, object_b: str) -> str:
        return _send(get_blender_connection, "calculate_clearance", locals())

    @mcp.tool()
    def calculate_alignment(ctx: Any, object_names: list[str]) -> str:
        return _send(get_blender_connection, "calculate_alignment", locals())

    @mcp.tool()
    def convert_units(ctx: Any, value: float, from_unit: str = "BLENDER_UNIT", to_unit: str = "METERS") -> str:
        return _send(get_blender_connection, "convert_units", locals())

    @mcp.tool()
    def calculate_scale_ratio(ctx: Any, measured: float, expected: float) -> str:
        return _send(get_blender_connection, "calculate_scale_ratio", locals())

    @mcp.tool()
    def compare_measurements(ctx: Any, a: float, b: float) -> str:
        return _send(get_blender_connection, "compare_measurements", locals())

    @mcp.tool()
    def get_oriented_bounds(ctx: Any, object_name: str) -> str:
        return _send(get_blender_connection, "get_oriented_bounds", locals())

    @mcp.tool()
    def raycast_scene(ctx: Any, origin: list[float], direction: list[float], distance: float = 1000.0) -> str:
        return _send(get_blender_connection, "raycast_scene", locals())

    @mcp.tool()
    def find_nearest_objects(ctx: Any, point: list[float], limit: int = 5) -> str:
        return _send(get_blender_connection, "find_nearest_objects", locals())

    @mcp.tool()
    def detect_object_intersections(ctx: Any, object_names: list[str]) -> str:
        return _send(get_blender_connection, "detect_object_intersections", locals())

    @mcp.tool()
    def measure_object_to_reference(ctx: Any, object_name: str, reference_id: str) -> str:
        return _send(get_blender_connection, "measure_object_to_reference", locals())

    @mcp.tool()
    def plan_rename(ctx: Any, target_type: str, old_name: str, new_name: str) -> str:
        return _send(get_blender_connection, "plan_rename", locals())

    @mcp.tool()
    def execute_rename(ctx: Any, approval_id: str, confirm: bool = False) -> str:
        return _send(get_blender_connection, "execute_rename", locals())

    @mcp.tool()
    def batch_rename_datablocks(ctx: Any, renames: list[dict[str, str]], confirm: bool = False) -> str:
        return _send(get_blender_connection, "batch_rename_datablocks", locals())

    @mcp.tool()
    def batch_rename_files(ctx: Any, renames: list[dict[str, str]], confirm: bool = False) -> str:
        return _send(get_blender_connection, "batch_rename_files", locals())

    @mcp.tool()
    def rename_project(ctx: Any, new_name: str, confirm: bool = False) -> str:
        return _send(get_blender_connection, "rename_project", locals())

    @mcp.tool()
    def repair_references_after_rename(ctx: Any, confirm: bool = False) -> str:
        return _send(get_blender_connection, "repair_references_after_rename", locals())
