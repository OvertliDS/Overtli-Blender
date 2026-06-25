"""MCP tools for Phase 8B mesh schema construction."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_modeling_schema_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_modeling_capabilities(ctx: Any) -> str:
        return _send(get_blender_connection, "get_modeling_capabilities", locals())

    @mcp.tool()
    def validate_mesh_schema(ctx: Any, schema: dict, max_vertices: int = 10000, max_faces: int = 20000, check_non_manifold: bool = True) -> str:
        return _send(get_blender_connection, "validate_mesh_schema", locals())

    @mcp.tool()
    def create_mesh_from_schema(ctx: Any, object_name: str, schema: dict, collection_name: str | None = None, material_name: str | None = None, validate: bool = True, create_uvs: bool = True, verify: bool = True) -> str:
        return _send(get_blender_connection, "create_mesh_from_schema", locals())
