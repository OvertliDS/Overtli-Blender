"""MCP tool registration for Phase 4B method, asset, UV, measurement, and sculpt workflows."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_workflow_intelligence_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register method planning, asset/material, UV/measurement, and sculpt-safe workflow tools."""

    @mcp.tool()
    def get_method_plan(ctx: Any, intent: str, object_name: str | None = None, region: dict[str, Any] | None = None, constraints: list[str] | None = None, verify: bool = True) -> str:
        """Plan a safe Blender method sequence for a user intent."""
        try:
            return _send(get_blender_connection, "get_method_plan", locals())
        except Exception as e:
            return f"Error getting method plan: {str(e)}"

    @mcp.tool()
    def list_operation_playbooks(ctx: Any, category: str | None = None) -> str:
        """List reusable operation playbooks."""
        try:
            return _send(get_blender_connection, "list_operation_playbooks", locals())
        except Exception as e:
            return f"Error listing operation playbooks: {str(e)}"

    @mcp.tool()
    def get_tricks_knowledge_base(ctx: Any, category: str | None = None) -> str:
        """Return concise Blender workflow tricks grouped by category."""
        try:
            return _send(get_blender_connection, "get_tricks_knowledge_base", locals())
        except Exception as e:
            return f"Error getting tricks knowledge base: {str(e)}"

    @mcp.tool()
    def get_anti_pattern_rules(ctx: Any) -> str:
        """Return safety and workflow anti-pattern rules."""
        try:
            return _send(get_blender_connection, "get_anti_pattern_rules", locals())
        except Exception as e:
            return f"Error getting anti-pattern rules: {str(e)}"

    @mcp.tool()
    def get_modifier_recipes(ctx: Any, recipe_name: str | None = None) -> str:
        """Return non-destructive modifier recipes."""
        try:
            return _send(get_blender_connection, "get_modifier_recipes", locals())
        except Exception as e:
            return f"Error getting modifier recipes: {str(e)}"

    @mcp.tool()
    def score_selection_confidence(ctx: Any, object_name: str | None = None, region: dict[str, Any] | None = None) -> str:
        """Score whether a target region has enough evidence for deformation or sculpt workflows."""
        try:
            return _send(get_blender_connection, "score_selection_confidence", locals())
        except Exception as e:
            return f"Error scoring selection confidence: {str(e)}"

    @mcp.tool()
    def scan_blender_asset_libraries(ctx: Any, include_current_file: bool = True, max_items: int = 200) -> str:
        """Scan current-file Blender data-blocks as local asset-library candidates."""
        try:
            return _send(get_blender_connection, "scan_blender_asset_libraries", locals())
        except Exception as e:
            return f"Error scanning Blender asset libraries: {str(e)}"

    @mcp.tool()
    def preview_asset(ctx: Any, asset_name: str, asset_type: str = "material", artifact_root: str | None = None, include_snapshot: bool = True) -> str:
        """Create a local preview/verification artifact for an asset."""
        try:
            return _send(get_blender_connection, "preview_asset", locals())
        except Exception as e:
            return f"Error previewing asset: {str(e)}"

    @mcp.tool()
    def import_texture_folder(ctx: Any, folder_path: str, material_name: str | None = None, assign_to_object: str | None = None, strict_file_exists: bool = True, verify: bool = True) -> str:
        """Create a material from local texture folder maps without downloads."""
        try:
            return _send(get_blender_connection, "import_texture_folder", locals())
        except Exception as e:
            return f"Error importing texture folder: {str(e)}"

    @mcp.tool()
    def create_style_material(ctx: Any, style_name: str, material_name: str, parameters: dict[str, Any] | None = None, assign_to_object: str | None = None, verify: bool = True) -> str:
        """Create a style-aware material through existing templates."""
        try:
            return _send(get_blender_connection, "create_style_material", locals())
        except Exception as e:
            return f"Error creating style material: {str(e)}"

    @mcp.tool()
    def create_paintable_texture(ctx: Any, object_name: str, material_name: str | None = None, image_name: str | None = None, width: int = 1024, height: int = 1024, base_color: list[float] | None = None, verify: bool = True) -> str:
        """Create an in-memory paintable image and assign a material to a mesh object."""
        try:
            return _send(get_blender_connection, "create_paintable_texture", locals())
        except Exception as e:
            return f"Error creating paintable texture: {str(e)}"

    @mcp.tool()
    def delete_images(ctx: Any, image_names: list[str], confirm: bool = False, allow_missing: bool = False) -> str:
        """Delete explicitly named images after confirmation."""
        try:
            return _send(get_blender_connection, "delete_images", locals())
        except Exception as e:
            return f"Error deleting images: {str(e)}"

    @mcp.tool()
    def list_uv_maps(ctx: Any, object_name: str, include_island_estimate: bool = True) -> str:
        """List UV maps for one mesh object."""
        try:
            return _send(get_blender_connection, "list_uv_maps", locals())
        except Exception as e:
            return f"Error listing UV maps: {str(e)}"

    @mcp.tool()
    def create_vertex_group_from_uv_island(ctx: Any, object_name: str, group_name: str, uv_map_name: str | None = None, island_seed_face_index: int | None = None, weight: float = 1.0, confirm: bool = False) -> str:
        """Create a vertex group from a UV island approximation after confirmation."""
        try:
            return _send(get_blender_connection, "create_vertex_group_from_uv_island", locals())
        except Exception as e:
            return f"Error creating vertex group from UV island: {str(e)}"

    @mcp.tool()
    def measure_object(ctx: Any, object_name: str, include_bounds: bool = True) -> str:
        """Measure object dimensions, location, and bounds."""
        try:
            return _send(get_blender_connection, "measure_object", locals())
        except Exception as e:
            return f"Error measuring object: {str(e)}"

    @mcp.tool()
    def measure_distance(ctx: Any, object_a: str, object_b: str) -> str:
        """Measure distance between two object origins."""
        try:
            return _send(get_blender_connection, "measure_distance", locals())
        except Exception as e:
            return f"Error measuring distance: {str(e)}"

    @mcp.tool()
    def create_proportional_deformation(ctx: Any, object_name: str, region: dict[str, Any], deformation: dict[str, Any], method: str = "shape_key", name: str | None = None, confirm: bool = False, verify: bool = True) -> str:
        """Create a bounded proportional-style deformation through a non-destructive method."""
        try:
            return _send(get_blender_connection, "create_proportional_deformation", locals())
        except Exception as e:
            return f"Error creating proportional deformation: {str(e)}"

    @mcp.tool()
    def get_sculpt_status(ctx: Any, object_name: str | None = None) -> str:
        """Inspect sculpt mode and supported structured sculpt workflows."""
        try:
            return _send(get_blender_connection, "get_sculpt_status", locals())
        except Exception as e:
            return f"Error getting sculpt status: {str(e)}"

    @mcp.tool()
    def configure_sculpt_brush(ctx: Any, brush_name: str = "grab", radius: int = 50, strength: float = 0.25, symmetry: dict[str, Any] | None = None, confirm: bool = False) -> str:
        """Configure supported sculpt brush settings after confirmation."""
        try:
            return _send(get_blender_connection, "configure_sculpt_brush", locals())
        except Exception as e:
            return f"Error configuring sculpt brush: {str(e)}"

    @mcp.tool()
    def create_sculpt_mask_from_vertex_group(ctx: Any, object_name: str, vertex_group_name: str, mask_name: str | None = None, confirm: bool = False) -> str:
        """Record sculpt mask intent backed by an existing vertex group."""
        try:
            return _send(get_blender_connection, "create_sculpt_mask_from_vertex_group", locals())
        except Exception as e:
            return f"Error creating sculpt mask from vertex group: {str(e)}"

    @mcp.tool()
    def run_shape_key_sculpt_workflow(ctx: Any, object_name: str, vertex_group_name: str, shape_key_name: str, brush_action: str = "inflate", amount: float = 0.05, confirm: bool = False, verify: bool = True) -> str:
        """Run a safe sculpt-like workflow by writing to a non-Basis shape key."""
        try:
            return _send(get_blender_connection, "run_shape_key_sculpt_workflow", locals())
        except Exception as e:
            return f"Error running shape key sculpt workflow: {str(e)}"
