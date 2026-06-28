"""MCP tool registration for Phase 3 scene edit tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_scene_edit_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register explicit-target scene edit MCP tools."""

    @mcp.tool()
    def get_supported_edit_operations(ctx: Any) -> str:
        """List supported Phase 3 edit operations and safety metadata."""
        try:
            return _send(get_blender_connection, "get_supported_edit_operations")
        except Exception as e:
            return f"Error getting supported edit operations: {str(e)}"

    @mcp.tool()
    def create_primitive_object(ctx: Any, primitive_type: str, name: str | None = None, location: list[float] | None = None, rotation: list[float] | None = None, scale: list[float] | None = None, collection_name: str | None = None, material_name: str | None = None, verify: bool = False, dimensions: list[float] | None = None, anchor: str = "center", origin_mode: str | None = None, snap_to: dict[str, Any] | str | None = None, clearance: float = 0.0) -> str:
        """Create a supported primitive with optional final dimensions, anchor placement, and contact snapping."""
        try:
            return _send(
                get_blender_connection,
                "create_primitive_object",
                {
                    "primitive_type": primitive_type,
                    "name": name,
                    "location": location,
                    "rotation": rotation,
                    "scale": scale,
                    "collection_name": collection_name,
                    "material_name": material_name,
                    "verify": verify,
                    "dimensions": dimensions,
                    "anchor": anchor,
                    "origin_mode": origin_mode,
                    "snap_to": snap_to,
                    "clearance": clearance,
                },
            )
        except Exception as e:
            return f"Error creating primitive object: {str(e)}"

    @mcp.tool()
    def create_box(ctx: Any, name: str | None = None, dimensions: list[float] | None = None, location: list[float] | None = None, anchor: str = "bottom_center", collection_name: str | None = None, material_name: str | None = None, verify: bool = False) -> str:
        """Create a box using final dimensions instead of scale."""
        try:
            return _send(
                get_blender_connection,
                "create_box",
                {
                    "name": name,
                    "dimensions": dimensions,
                    "location": location,
                    "anchor": anchor,
                    "collection_name": collection_name,
                    "material_name": material_name,
                    "verify": verify,
                },
            )
        except Exception as e:
            return f"Error creating box: {str(e)}"

    @mcp.tool()
    def transform_object(ctx: Any, object_name: str, location: list[float] | None = None, rotation: list[float] | None = None, scale: list[float] | None = None, relative: bool = False, verify: bool = False, dimensions: list[float] | None = None, anchor: str | None = None, preserve_anchor: bool = True) -> str:
        """Transform one explicitly named object, optionally setting final dimensions while preserving an anchor."""
        try:
            return _send(
                get_blender_connection,
                "transform_object",
                {
                    "object_name": object_name,
                    "location": location,
                    "rotation": rotation,
                    "scale": scale,
                    "relative": relative,
                    "verify": verify,
                    "dimensions": dimensions,
                    "anchor": anchor,
                    "preserve_anchor": preserve_anchor,
                },
            )
        except Exception as e:
            return f"Error transforming object: {str(e)}"

    @mcp.tool()
    def transform_object_dimensions(ctx: Any, object_name: str, dimensions: list[float], preserve_anchor: bool = True, anchor: str = "bottom_center", verify: bool = False) -> str:
        """Set final object dimensions without relying on ambiguous scale values."""
        try:
            return _send(
                get_blender_connection,
                "transform_object_dimensions",
                {
                    "object_name": object_name,
                    "dimensions": dimensions,
                    "preserve_anchor": preserve_anchor,
                    "anchor": anchor,
                    "verify": verify,
                },
            )
        except Exception as e:
            return f"Error transforming object dimensions: {str(e)}"

    @mcp.tool()
    def duplicate_object(ctx: Any, object_name: str, new_name: str | None = None, linked: bool = False, location_offset: list[float] | None = None, collection_name: str | None = None, verify: bool = False) -> str:
        """Duplicate one explicitly named object."""
        try:
            return _send(
                get_blender_connection,
                "duplicate_object",
                {
                    "object_name": object_name,
                    "new_name": new_name,
                    "linked": linked,
                    "location_offset": location_offset,
                    "collection_name": collection_name,
                    "verify": verify,
                },
            )
        except Exception as e:
            return f"Error duplicating object: {str(e)}"

    @mcp.tool()
    def delete_objects(ctx: Any, object_names: list[str], confirm: bool = False, allow_missing: bool = False, verify: bool = False) -> str:
        """Delete only explicitly named objects after confirmation."""
        try:
            return _send(
                get_blender_connection,
                "delete_objects",
                {
                    "object_names": object_names,
                    "confirm": confirm,
                    "allow_missing": allow_missing,
                    "verify": verify,
                },
            )
        except Exception as e:
            return f"Error deleting objects: {str(e)}"

    @mcp.tool()
    def clear_scene(ctx: Any, scope: str = "prefix", prefix: str = "OVERTLI_", collection_name: str | None = None, delete_objects: bool = True, delete_empty_collections: bool = True, delete_unused_materials: bool = True, delete_unused_images: bool = False, delete_cameras_lights: bool = False, dry_run: bool = True, confirm: bool = False, create_before_snapshot: bool = True) -> str:
        """Plan or execute a scoped scene cleanup. Defaults to dry-run and generated OVERTLI_* assets only."""
        try:
            return _send(
                get_blender_connection,
                "clear_scene",
                {
                    "scope": scope,
                    "prefix": prefix,
                    "collection_name": collection_name,
                    "delete_objects": delete_objects,
                    "delete_empty_collections": delete_empty_collections,
                    "delete_unused_materials": delete_unused_materials,
                    "delete_unused_images": delete_unused_images,
                    "delete_cameras_lights": delete_cameras_lights,
                    "dry_run": dry_run,
                    "confirm": confirm,
                    "create_before_snapshot": create_before_snapshot,
                },
            )
        except Exception as e:
            return f"Error clearing scene: {str(e)}"

    @mcp.tool()
    def scene_cleanup_plan(ctx: Any, scope: str = "prefix", prefix: str = "OVERTLI_", collection_name: str | None = None, delete_objects: bool = True, delete_empty_collections: bool = True, delete_unused_materials: bool = True, delete_unused_images: bool = False, delete_cameras_lights: bool = False, create_before_snapshot: bool = True) -> str:
        """Return a non-mutating scene cleanup plan with approval details."""
        try:
            return _send(
                get_blender_connection,
                "scene_cleanup_plan",
                {
                    "scope": scope,
                    "prefix": prefix,
                    "collection_name": collection_name,
                    "delete_objects": delete_objects,
                    "delete_empty_collections": delete_empty_collections,
                    "delete_unused_materials": delete_unused_materials,
                    "delete_unused_images": delete_unused_images,
                    "delete_cameras_lights": delete_cameras_lights,
                    "create_before_snapshot": create_before_snapshot,
                },
            )
        except Exception as e:
            return f"Error planning scene cleanup: {str(e)}"

    @mcp.tool()
    def validate_ground_contact(ctx: Any, object_name: str, ground_z: float = 0.0, tolerance: float = 0.01) -> str:
        """Verify that an object's bottom bounds are in contact with the expected ground plane."""
        try:
            return _send(
                get_blender_connection,
                "validate_ground_contact",
                {
                    "object_name": object_name,
                    "ground_z": ground_z,
                    "tolerance": tolerance,
                },
            )
        except Exception as e:
            return f"Error validating ground contact: {str(e)}"

    @mcp.tool()
    def align_object_to_surface(ctx: Any, object_name: str, target_object_name: str | None = None, target_z: float | None = None, clearance: float = 0.0, anchor: str = "bottom_center", verify: bool = True) -> str:
        """Move an object so its anchor rests on a target object's top surface or an explicit Z plane."""
        try:
            return _send(
                get_blender_connection,
                "align_object_to_surface",
                {
                    "object_name": object_name,
                    "target_object_name": target_object_name,
                    "target_z": target_z,
                    "clearance": clearance,
                    "anchor": anchor,
                    "verify": verify,
                },
            )
        except Exception as e:
            return f"Error aligning object to surface: {str(e)}"

    @mcp.tool()
    def validate_scene_composition(ctx: Any, object_names: list[str] | None = None, require_ground_contact: bool = False, ground_z: float = 0.0, tolerance: float = 0.01) -> str:
        """Run lightweight composition checks for dimensions, visibility, bounds, and optional ground contact."""
        try:
            return _send(
                get_blender_connection,
                "validate_scene_composition",
                {
                    "object_names": object_names,
                    "require_ground_contact": require_ground_contact,
                    "ground_z": ground_z,
                    "tolerance": tolerance,
                },
            )
        except Exception as e:
            return f"Error validating scene composition: {str(e)}"

    @mcp.tool()
    def set_object_visibility(ctx: Any, object_name: str, hide_viewport: bool | None = None, hide_render: bool | None = None, verify: bool = False) -> str:
        """Set visibility on one explicitly named object."""
        try:
            return _send(
                get_blender_connection,
                "set_object_visibility",
                {
                    "object_name": object_name,
                    "hide_viewport": hide_viewport,
                    "hide_render": hide_render,
                    "verify": verify,
                },
            )
        except Exception as e:
            return f"Error setting object visibility: {str(e)}"

    @mcp.tool()
    def run_verified_edit_batch(ctx: Any, label: str | None = None, operations: list[dict] | None = None, create_before_snapshot: bool = True, create_after_snapshot: bool = True, stop_on_error: bool = True, max_operations: int = 20, batch_allow_destructive: bool = False, artifact_root: str | None = None, prevalidate_only: bool = False, prevalidate_all: bool = True) -> str:
        """Run a controlled allowlisted edit batch with command_name/params operations and before/after verification."""
        try:
            return _send(
                get_blender_connection,
                "run_verified_edit_batch",
                {
                    "label": label,
                    "operations": operations,
                    "create_before_snapshot": create_before_snapshot,
                    "create_after_snapshot": create_after_snapshot,
                    "stop_on_error": stop_on_error,
                    "max_operations": max_operations,
                    "batch_allow_destructive": batch_allow_destructive,
                    "artifact_root": artifact_root,
                    "prevalidate_only": prevalidate_only,
                    "prevalidate_all": prevalidate_all,
                },
            )
        except Exception as e:
            return f"Error running verified edit batch: {str(e)}"
