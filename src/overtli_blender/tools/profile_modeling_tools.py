"""MCP tools for profile, curve, extrude, lathe, and loft workflows."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_profile_modeling_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_profile_curve(ctx: Any, profile_name: str, points: list[list[float]], closed: bool = True, collection_name: str | None = None, material_name: str | None = None) -> str:
        return _send(get_blender_connection, "create_profile_curve", locals())

    @mcp.tool()
    def extrude_profile(ctx: Any, profile_object_name: str, extrude_vector: list[float], steps: int = 1, solidify: bool = True, bevel: float = 0.0, new_object_name: str | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "extrude_profile", locals())

    @mcp.tool()
    def lathe_profile(ctx: Any, profile_object_name: str, axis: str = "Z", angle_degrees: float = 360, segments: int = 32, new_object_name: str | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "lathe_profile", locals())

    @mcp.tool()
    def loft_profiles(ctx: Any, profile_object_names: list[str], new_object_name: str, segments_between: int = 1, closed_loop: bool = False, verify: bool = True) -> str:
        return _send(get_blender_connection, "loft_profiles", locals())

    @mcp.tool()
    def bridge_profile_loops(ctx: Any, object_name: str, loop_a: list[int] | None = None, loop_b: list[int] | None = None, new_object_name: str | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "bridge_profile_loops", locals())

    @mcp.tool()
    def create_curve_path_object(ctx: Any, name: str, points: list[list[float]], curve_type: str = "polyline", bevel_depth: float = 0.0, resolution: int = 12, collection_name: str | None = None, material_name: str | None = None) -> str:
        return _send(get_blender_connection, "create_curve_path_object", locals())

    @mcp.tool()
    def create_beveled_curve_object(ctx: Any, name: str, points: list[list[float]], radius: float = 0.05, resolution: int = 12, fill_caps: bool = True, material_name: str | None = None, collection_name: str | None = None) -> str:
        return _send(get_blender_connection, "create_beveled_curve_object", locals())
