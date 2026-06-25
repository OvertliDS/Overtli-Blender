"""MCP tools for non-destructive modifier construction workflows."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_modifier_construction_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_modifier_stack(ctx: Any, object_name: str, modifiers: list[dict], stack_name: str | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "create_modifier_stack", locals())

    @mcp.tool()
    def create_hard_surface_panel(ctx: Any, panel_name: str, size: list[float] = [2, 2, 0.05], bevel: float = 0.02, inset_count: int = 1, slot_count: int = 0, material_name: str | None = None, collection_name: str | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "create_hard_surface_panel", locals())

    @mcp.tool()
    def create_pipe_or_rail(ctx: Any, name: str, points: list[list[float]], radius: float = 0.05, support_posts: bool = False, post_spacing: float | None = None, material_name: str | None = None, collection_name: str | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "create_pipe_or_rail", locals())

    @mcp.tool()
    def create_modular_assembly(ctx: Any, assembly_name: str, module_specs: list[dict], collection_name: str | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "create_modular_assembly", locals())
