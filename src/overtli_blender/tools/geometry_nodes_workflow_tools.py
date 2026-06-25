"""MCP wrappers for Geometry Nodes validation, previews, scene kits, cleanup, and batches."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_geometry_nodes_workflow_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    def _send(command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return get_blender_connection().send_command(command, params or {})

    @mcp.tool()
    def validate_geometry_node_group(ctx: Any, node_group_name: str, expected_template: str | None = None) -> dict[str, Any]:
        return _send("validate_geometry_node_group", {"node_group_name": node_group_name, "expected_template": expected_template})

    @mcp.tool()
    def create_geometry_nodes_preview(ctx: Any, node_group_name: str | None = None, object_name: str | None = None, label: str | None = None, include_scene_snapshot: bool = True) -> dict[str, Any]:
        return _send("create_geometry_nodes_preview", {"node_group_name": node_group_name, "object_name": object_name, "label": label, "include_scene_snapshot": include_scene_snapshot})

    @mcp.tool()
    def create_geometry_nodes_scene_kit(ctx: Any, kit_id: str | None = None, label: str | None = None, object_names: list[str] | None = None, node_group_names: list[str] | None = None, include_preview: bool = True, overwrite: bool = True) -> dict[str, Any]:
        return _send("create_geometry_nodes_scene_kit", {"kit_id": kit_id, "label": label, "object_names": object_names, "node_group_names": node_group_names, "include_preview": include_preview, "overwrite": overwrite})

    @mcp.tool()
    def delete_geometry_node_groups(ctx: Any, node_group_names: list[str] | None = None, prefix: str | None = None, confirm: bool = False) -> dict[str, Any]:
        return _send("delete_geometry_node_groups", {"node_group_names": node_group_names, "prefix": prefix, "confirm": confirm})

    @mcp.tool()
    def run_geometry_nodes_workflow_batch(ctx: Any, label: str | None = None, operations: list[dict[str, Any]] | None = None, create_before_snapshot: bool = True, create_after_snapshot: bool = True, stop_on_error: bool = True, max_operations: int = 40, batch_allow_destructive: bool = False) -> dict[str, Any]:
        return _send("run_geometry_nodes_workflow_batch", {"label": label, "operations": operations, "create_before_snapshot": create_before_snapshot, "create_after_snapshot": create_after_snapshot, "stop_on_error": stop_on_error, "max_operations": max_operations, "batch_allow_destructive": batch_allow_destructive})
