"""MCP tool registration for Phase 8A image resource operations."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_image_resource_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register image target, save, inventory, and rename tools."""

    @mcp.tool()
    def create_bake_target_images(ctx: Any, target_object_names: list[str], passes: list[str], resolution: int | list[int] = 1024, output_dir: str | None = None, image_format: str = "PNG", color_depth: str | None = None, overwrite: bool = False, prefix: str | None = None, create_nodes: bool = True, set_active: bool = True) -> str:
        """Create project-scoped bake target images and optional image texture nodes."""
        return _send(get_blender_connection, "create_bake_target_images", locals())

    @mcp.tool()
    def save_baked_textures(ctx: Any, image_names: list[str], output_dir: str | None = None, overwrite: bool = False) -> str:
        """Save baked texture images under approved project texture folders."""
        return _send(get_blender_connection, "save_baked_textures", locals())

    @mcp.tool()
    def list_project_images(ctx: Any, include_paths: bool = True) -> str:
        """List project image resources and Blender image datablocks."""
        return _send(get_blender_connection, "list_project_images", locals())

    @mcp.tool()
    def get_image_resource_info(ctx: Any, image_name_or_path: str) -> str:
        """Inspect a Blender image datablock or project image file."""
        return _send(get_blender_connection, "get_image_resource_info", locals())

    @mcp.tool()
    def rename_image_resource(ctx: Any, image_name_or_path: str, new_name: str, overwrite: bool = False) -> str:
        """Plan or perform a safe project-scoped image resource rename."""
        return _send(get_blender_connection, "rename_image_resource", locals())
