"""MCP tools for safe sculpt workflow setup."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_sculpt_workflow_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def configure_sculpt_session(ctx: Any, object_name: str, brush: str = "SMOOTH", use_shape_key: bool = True, symmetry: list[bool] | None = None, radius: int = 50, strength: float = 0.25) -> str:
        return _send(get_blender_connection, "configure_sculpt_session", locals())

    @mcp.tool()
    def create_sculpt_mask(ctx: Any, object_name: str, mask_name: str = "Overtli_Sculpt_Mask", vertex_indices: list[int] | None = None, weight: float = 1.0) -> str:
        return _send(get_blender_connection, "create_sculpt_mask", locals())

    @mcp.tool()
    def create_face_set(ctx: Any, object_name: str, face_indices: list[int] | None = None, face_set_name: str = "Overtli_Face_Set") -> str:
        return _send(get_blender_connection, "create_face_set", locals())

    @mcp.tool()
    def apply_sculpt_stroke_batch(ctx: Any, object_name: str, strokes: list[dict], approval_id: str | None = None, max_strokes: int = 32) -> str:
        return _send(get_blender_connection, "apply_sculpt_stroke_batch", locals())

    @mcp.tool()
    def create_shape_key_sculpt_variant(ctx: Any, object_name: str, shape_key_name: str = "Overtli_Sculpt_Variant", value: float = 0.0) -> str:
        return _send(get_blender_connection, "create_shape_key_sculpt_variant", locals())

    @mcp.tool()
    def validate_sculpt_result(ctx: Any, object_name: str, shape_key_name: str | None = None) -> str:
        return _send(get_blender_connection, "validate_sculpt_result", locals())
