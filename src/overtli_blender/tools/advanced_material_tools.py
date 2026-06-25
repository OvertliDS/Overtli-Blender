"""MCP tool registration for Phase 4A advanced material authoring tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_advanced_material_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register template, custom, procedural, variant, assignment, batch, and cleanup tools."""

    @mcp.tool()
    def create_material_from_template(ctx: Any, template_name: str, material_name: str, parameters: dict[str, Any] | None = None, map_slots: dict[str, str] | None = None, assign_to_object: str | None = None, replace_existing: bool = False, verify: bool = True) -> str:
        """Create a production material from a named Phase 4A template."""
        try:
            return _send(get_blender_connection, "create_material_from_template", locals())
        except Exception as e:
            return f"Error creating material from template: {str(e)}"

    @mcp.tool()
    def create_custom_material(ctx: Any, material_name: str, recipe: dict[str, Any] | None = None, replace_existing: bool = False, verify: bool = True) -> str:
        """Create a material from a flexible channel-aware custom recipe."""
        try:
            return _send(get_blender_connection, "create_custom_material", locals())
        except Exception as e:
            return f"Error creating custom material: {str(e)}"

    @mcp.tool()
    def create_procedural_material(ctx: Any, material_name: str, procedural_type: str = "noise", base_color: list[float] | None = None, secondary_color: list[float] | None = None, parameters: dict[str, Any] | None = None, assign_to_object: str | None = None, replace_existing: bool = False, verify: bool = True) -> str:
        """Create a procedural material with noise/bump channel metadata and verification."""
        try:
            return _send(get_blender_connection, "create_procedural_material", locals())
        except Exception as e:
            return f"Error creating procedural material: {str(e)}"

    @mcp.tool()
    def create_material_variant(ctx: Any, source_material_name: str, variant_name: str, overrides: dict[str, Any] | None = None, replace_existing: bool = False, verify: bool = True) -> str:
        """Copy an existing material and apply channel overrides as a variant."""
        try:
            return _send(get_blender_connection, "create_material_variant", locals())
        except Exception as e:
            return f"Error creating material variant: {str(e)}"

    @mcp.tool()
    def apply_material_to_objects(ctx: Any, material_name: str, object_names: list[str], slot_index: int | None = None, replace: bool = True, verify: bool = True) -> str:
        """Apply one material to explicitly named objects."""
        try:
            return _send(get_blender_connection, "apply_material_to_objects", locals())
        except Exception as e:
            return f"Error applying material to objects: {str(e)}"

    @mcp.tool()
    def run_material_workflow_batch(ctx: Any, operations: list[dict[str, Any]], label: str | None = None, artifact_root: str | None = None, verify: bool = True) -> str:
        """Run an allowlisted material workflow batch with before/after snapshots."""
        try:
            return _send(get_blender_connection, "run_material_workflow_batch", locals())
        except Exception as e:
            return f"Error running material workflow batch: {str(e)}"

    @mcp.tool()
    def delete_materials(ctx: Any, material_names: list[str], confirm: bool = False, allow_missing: bool = False, only_if_unused: bool = False) -> str:
        """Delete explicitly named materials only after confirmation."""
        try:
            return _send(get_blender_connection, "delete_materials", locals())
        except Exception as e:
            return f"Error deleting materials: {str(e)}"
