"""MCP tools for reference-driven construction."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_reference_construction_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def plan_reference_construction(ctx: Any, reference_set_id: str | None = None, target_description: str = "", measurement_ids: list[str] | None = None, method_preference: str | None = None) -> str:
        return _send(get_blender_connection, "plan_reference_construction", locals())

    @mcp.tool()
    def run_reference_construction_step(ctx: Any, step: str, reference_set_id: str | None = None, target_object_name: str | None = None, params: dict | None = None, verify: bool = True) -> str:
        return _send(get_blender_connection, "run_reference_construction_step", locals())

    @mcp.tool()
    def validate_reference_alignment(ctx: Any, object_names: list[str], reference_set_id: str | None = None, tolerance: float = 0.05) -> str:
        return _send(get_blender_connection, "validate_reference_alignment", locals())
