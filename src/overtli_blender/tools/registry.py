"""Central MCP tool registry."""

from __future__ import annotations

from typing import Any

from .code_execution_tools import register_code_execution_tools
from .collection_tools import register_collection_tools
from .context_tools import register_context_tools
from .advanced_material_tools import register_advanced_material_tools
from .geometry_nodes_tools import register_geometry_nodes_tools
from .hyper3d_tools import register_hyper3d_tools
from .material_intelligence_tools import register_material_intelligence_tools
from .material_preview_tools import register_material_preview_tools
from .material_tools import register_material_tools
from .material_texture_tools import register_material_texture_tools
from .modifier_tools import register_modifier_tools
from .observation_tools import register_observation_tools
from .safety_tools import register_safety_tools
from .scene_intelligence_tools import register_scene_intelligence_tools
from .scene_edit_tools import register_scene_edit_tools
from .shader_graph_tools import register_shader_graph_tools
from .polyhaven_tools import register_polyhaven_tools
from .provider_status_tools import register_provider_status_tools
from .screenshot_tools import register_screenshot_tools
from .script_registry_tools import register_script_registry_tools
from .sketchfab_tools import register_sketchfab_tools
from .verification_tools import register_verification_tools
from .workspace_tools import register_workspace_tools


def register_all_tools(mcp: Any, get_blender_connection, *, image_type: Any | None = None) -> None:
    """Register all MCP tool groups."""

    register_context_tools(mcp, get_blender_connection)
    register_observation_tools(mcp, get_blender_connection)
    register_scene_intelligence_tools(mcp, get_blender_connection)
    register_scene_edit_tools(mcp, get_blender_connection)
    register_material_tools(mcp, get_blender_connection)
    register_material_intelligence_tools(mcp, get_blender_connection)
    register_advanced_material_tools(mcp, get_blender_connection)
    register_shader_graph_tools(mcp, get_blender_connection)
    register_material_texture_tools(mcp, get_blender_connection)
    register_material_preview_tools(mcp, get_blender_connection)
    register_modifier_tools(mcp, get_blender_connection)
    register_collection_tools(mcp, get_blender_connection)
    register_workspace_tools(mcp, get_blender_connection)
    register_screenshot_tools(mcp, get_blender_connection, image_type=image_type)
    register_verification_tools(mcp, get_blender_connection)
    register_script_registry_tools(mcp, get_blender_connection)
    register_provider_status_tools(mcp, get_blender_connection)
    register_safety_tools(mcp, get_blender_connection)
    register_polyhaven_tools(mcp, get_blender_connection)
    register_sketchfab_tools(mcp, get_blender_connection)
    register_hyper3d_tools(mcp, get_blender_connection)
    register_geometry_nodes_tools(mcp, get_blender_connection)
    register_code_execution_tools(mcp, get_blender_connection)
