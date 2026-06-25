"""MCP wrappers for template-backed procedural Geometry Nodes assets."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_procedural_asset_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    def _send(command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return get_blender_connection().send_command(command, params or {})

    @mcp.tool()
    def create_procedural_asset(ctx: Any, asset_type: str = "curve_rope", asset_name: str | None = None, template_name: str | None = None, parameters: dict[str, Any] | None = None, collection_name: str | None = None, material_name: str | None = None, verify: bool = False) -> dict[str, Any]:
        return _send("create_procedural_asset", {"asset_type": asset_type, "asset_name": asset_name, "template_name": template_name, "parameters": parameters, "collection_name": collection_name, "material_name": material_name, "verify": verify})

    @mcp.tool()
    def create_scatter_system(ctx: Any, target_object_name: str | None = None, asset_name: str | None = None, template_name: str = "scatter_on_surface", parameters: dict[str, Any] | None = None, collection_name: str | None = None, material_name: str | None = None, verify: bool = False) -> dict[str, Any]:
        return _send("create_scatter_system", {"target_object_name": target_object_name, "asset_name": asset_name, "template_name": template_name, "parameters": parameters, "collection_name": collection_name, "material_name": material_name, "verify": verify})

    @mcp.tool()
    def create_curve_generator(ctx: Any, asset_name: str | None = None, template_name: str = "beveled_curve_path", parameters: dict[str, Any] | None = None, collection_name: str | None = None, material_name: str | None = None, verify: bool = False) -> dict[str, Any]:
        return _send("create_curve_generator", {"asset_name": asset_name, "template_name": template_name, "parameters": parameters, "collection_name": collection_name, "material_name": material_name, "verify": verify})

    @mcp.tool()
    def create_radial_array_system(ctx: Any, source_object_name: str | None = None, asset_name: str | None = None, parameters: dict[str, Any] | None = None, collection_name: str | None = None, material_name: str | None = None, verify: bool = False) -> dict[str, Any]:
        return _send("create_radial_array_system", {"source_object_name": source_object_name, "asset_name": asset_name, "parameters": parameters, "collection_name": collection_name, "material_name": material_name, "verify": verify})

    @mcp.tool()
    def create_panel_generator(ctx: Any, asset_name: str | None = None, template_name: str = "panel_grid", parameters: dict[str, Any] | None = None, collection_name: str | None = None, material_name: str | None = None, verify: bool = False) -> dict[str, Any]:
        return _send("create_panel_generator", {"asset_name": asset_name, "template_name": template_name, "parameters": parameters, "collection_name": collection_name, "material_name": material_name, "verify": verify})

    @mcp.tool()
    def create_cable_or_rope_generator(ctx: Any, asset_name: str | None = None, template_name: str = "curve_rope", parameters: dict[str, Any] | None = None, collection_name: str | None = None, material_name: str | None = None, verify: bool = False) -> dict[str, Any]:
        return _send("create_cable_or_rope_generator", {"asset_name": asset_name, "template_name": template_name, "parameters": parameters, "collection_name": collection_name, "material_name": material_name, "verify": verify})

    @mcp.tool()
    def create_terrain_noise_system(ctx: Any, asset_name: str | None = None, parameters: dict[str, Any] | None = None, collection_name: str | None = None, material_name: str | None = None, verify: bool = False) -> dict[str, Any]:
        return _send("create_terrain_noise_system", {"asset_name": asset_name, "parameters": parameters, "collection_name": collection_name, "material_name": material_name, "verify": verify})
