"""MCP tool registration for Phase 8A texture baking workflows."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_bake_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register bake capability, preflight, execution, validation, and cleanup tools."""

    @mcp.tool()
    def get_bake_capabilities(ctx: Any) -> str:
        """Inspect runtime texture baking capabilities for the active Blender session."""
        return _send(get_blender_connection, "get_bake_capabilities", locals())

    @mcp.tool()
    def validate_bake_setup(ctx: Any, target_object_names: list[str], passes: list[str], source_object_names: list[str] | None = None, resolution: int | list[int] = 1024, uv_layer: str | None = None, output_dir: str | None = None, overwrite: bool = False, selected_to_active: bool = False, cage_object: str | None = None, max_ray_distance: float = 0.0, normal_space: str = "TANGENT", create_missing_targets: bool = False) -> str:
        """Validate objects, UVs, render setup, file paths, targets, and bake risks."""
        return _send(get_blender_connection, "validate_bake_setup", locals())

    @mcp.tool()
    def estimate_bake_cost(ctx: Any, passes: list[str], resolution: int | list[int] = 1024, target_object_names: list[str] | None = None) -> str:
        """Estimate bake pixel, memory, disk, and time cost."""
        return _send(get_blender_connection, "estimate_bake_cost", locals())

    @mcp.tool()
    def assign_bake_targets(ctx: Any, object_names: list[str], image_name: str, material_slot_mode: str = "all", set_active: bool = True) -> str:
        """Assign an existing image to material image texture nodes for baking."""
        return _send(get_blender_connection, "assign_bake_targets", locals())

    @mcp.tool()
    def list_bake_targets(ctx: Any) -> str:
        """List active and available bake target image nodes."""
        return _send(get_blender_connection, "list_bake_targets", locals())

    @mcp.tool()
    def bake_material_maps(ctx: Any, target_object_names: list[str], passes: list[str], resolution: int | list[int] = 1024, output_dir: str | None = None, uv_layer: str | None = None, overwrite: bool = False, save_outputs: bool = True, create_material_variant: bool = False, verify: bool = True) -> str:
        """Bake native material maps when runtime support is available."""
        return _send(get_blender_connection, "bake_material_maps", locals())

    @mcp.tool()
    def bake_selected_to_active(ctx: Any, source_object_names: list[str], target_object_name: str, passes: list[str], resolution: int | list[int] = 1024, cage_object: str | None = None, cage_extrusion: float = 0.0, max_ray_distance: float = 0.0, normal_space: str = "TANGENT", output_dir: str | None = None, overwrite: bool = False, verify: bool = True) -> str:
        """Bake maps from exact source meshes to an exact active target mesh."""
        return _send(get_blender_connection, "bake_selected_to_active", locals())

    @mcp.tool()
    def bake_procedural_material(ctx: Any, object_names: list[str], material_names: list[str] | None = None, channels: list[str] = ["base_color", "roughness", "metallic", "normal"], resolution: int | list[int] = 1024, output_dir: str | None = None, overwrite: bool = False, verify: bool = True) -> str:
        """Bake procedural material channels to texture targets."""
        return _send(get_blender_connection, "bake_procedural_material", locals())

    @mcp.tool()
    def bake_derived_map(ctx: Any, object_names: list[str], derived_type: str, resolution: int | list[int] = 1024, method: str | None = None, output_dir: str | None = None, overwrite: bool = False, verify: bool = True) -> str:
        """Bake or approximate a derived map with honest classification."""
        return _send(get_blender_connection, "bake_derived_map", locals())

    @mcp.tool()
    def bake_curvature_map(ctx: Any, object_names: list[str], resolution: int | list[int] = 1024, method: str | None = None, output_dir: str | None = None, overwrite: bool = False, verify: bool = True) -> str:
        """Approximate curvature map generation when supported by the runtime workflow."""
        return _send(get_blender_connection, "bake_curvature_map", locals())

    @mcp.tool()
    def bake_thickness_map(ctx: Any, object_names: list[str], resolution: int | list[int] = 1024, method: str | None = None, output_dir: str | None = None, overwrite: bool = False, verify: bool = True) -> str:
        """Approximate thickness map generation when supported by the runtime workflow."""
        return _send(get_blender_connection, "bake_thickness_map", locals())

    @mcp.tool()
    def validate_baked_textures(ctx: Any, image_names_or_paths: list[str], check_files: bool = True, check_dimensions: bool = True, check_non_empty: bool = True, check_color_space: bool = True) -> str:
        """Validate baked image datablocks or files."""
        return _send(get_blender_connection, "validate_baked_textures", locals())

    @mcp.tool()
    def relink_baked_textures(ctx: Any, material_name: str, texture_bindings: dict, create_missing_nodes: bool = True) -> str:
        """Relink baked texture maps into a material graph."""
        return _send(get_blender_connection, "relink_baked_textures", locals())

    @mcp.tool()
    def create_baked_material(ctx: Any, new_material_name: str, texture_bindings: dict, source_material_name: str | None = None, assign_to_objects: list[str] | None = None) -> str:
        """Create a baked material variant without destroying the source material."""
        return _send(get_blender_connection, "create_baked_material", locals())

    @mcp.tool()
    def plan_bake_cleanup(ctx: Any, workflow_id: str | None = None, include_temp_nodes: bool = True, include_temp_images: bool = True, include_unsaved_images: bool = False, include_files: bool = False) -> str:
        """Plan exact cleanup of tracked bake temporary nodes, images, and artifacts."""
        return _send(get_blender_connection, "plan_bake_cleanup", locals())

    @mcp.tool()
    def execute_bake_cleanup(ctx: Any, approval_id: str, workflow_id: str | None = None, include_files: bool = False) -> str:
        """Execute approved cleanup of tracked temporary bake artifacts."""
        return _send(get_blender_connection, "execute_bake_cleanup", locals())

    @mcp.tool()
    def run_verified_bake_workflow(ctx: Any, target_object_names: list[str], passes: list[str], workflow_name: str | None = None, source_object_names: list[str] | None = None, resolution: int | list[int] = 512, include_derived: bool = False, include_channel_pack: bool = False, output_dir: str | None = None, overwrite: bool = False, create_baked_material: bool = True, verify: bool = True, cleanup_temp: bool = True) -> str:
        """Run the Phase 8A verified bake workflow envelope."""
        return _send(get_blender_connection, "run_verified_bake_workflow", locals())
