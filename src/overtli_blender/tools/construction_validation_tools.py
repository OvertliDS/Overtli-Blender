"""MCP tools for construction validation and cleanup planning."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_construction_validation_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def validate_construction_geometry(ctx: Any, object_names: list[str], check_mesh_health: bool = True, check_normals: bool = True, check_bounds: bool = True, check_intersections: bool = True, check_scale: bool = True, reference_set_id: str | None = None) -> str:
        return _send(get_blender_connection, "validate_construction_geometry", locals())

    @mcp.tool()
    def plan_construction_cleanup(ctx: Any, workflow_id: str | None = None, target_prefix: str = "OVERTLI_PHASE8B_", include_temp_curves: bool = True, include_temp_modifiers: bool = True, include_cloth_caches: bool = True) -> str:
        return _send(get_blender_connection, "plan_construction_cleanup", locals())

    @mcp.tool()
    def execute_construction_cleanup(ctx: Any, approval_id: str, workflow_id: str | None = None, target_prefix: str = "OVERTLI_PHASE8B_", delete_final: bool = False) -> str:
        return _send(get_blender_connection, "execute_construction_cleanup", locals())

    @mcp.tool()
    def run_advanced_modeling_workflow_batch(ctx: Any, workflow_name: str | None = None, operations: list[dict] | None = None, create_before_snapshot: bool = True, create_after_snapshot: bool = True, stop_on_error: bool = True, max_operations: int = 50, allow_sculpt: bool = False, allow_simulation: bool = False, allow_destructive: bool = False) -> str:
        return _send(get_blender_connection, "run_advanced_modeling_workflow_batch", locals())
