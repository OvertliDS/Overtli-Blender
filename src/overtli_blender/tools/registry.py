"""Central MCP tool registry."""

from __future__ import annotations

from typing import Any

from .addon_development_tools import register_addon_development_tools
from .addon_management_tools import register_addon_management_tools
from .advanced_knowledge_workflow_tools import register_advanced_knowledge_workflow_tools
from .api_knowledge_tools import register_api_knowledge_tools
from .animation_tools import register_animation_tools
from .asset_library_tools import register_asset_library_tools
from .asset_workflow_tools import register_asset_workflow_tools
from .bake_tools import register_bake_tools
from .camera_tools import register_camera_tools
from .cache_tools import register_cache_tools
from .channel_packing_tools import register_channel_packing_tools
from .code_execution_tools import register_code_execution_tools
from .collection_tools import register_collection_tools
from .compositor_tools import register_compositor_tools
from .context_tools import register_context_tools
from .deformation_tools import register_deformation_tools
from .dependency_tools import register_dependency_tools
from .advanced_material_tools import register_advanced_material_tools
from .file_access_tools import register_file_access_tools
from .geometry_nodes_intelligence_tools import register_geometry_nodes_intelligence_tools
from .geometry_nodes_modifier_tools import register_geometry_nodes_modifier_tools
from .geometry_nodes_template_tools import register_geometry_nodes_template_tools
from .geometry_nodes_tools import register_geometry_nodes_tools
from .geometry_nodes_workflow_tools import register_geometry_nodes_workflow_tools
from .governance_tools import register_governance_tools
from .hyper3d_tools import register_hyper3d_tools
from .import_export_tools import register_import_export_tools
from .image_resource_tools import register_image_resource_tools
from .lattice_tools import register_lattice_tools
from .lighting_tools import register_lighting_tools
from .material_intelligence_tools import register_material_intelligence_tools
from .material_preview_tools import register_material_preview_tools
from .material_tools import register_material_tools
from .material_texture_tools import register_material_texture_tools
from .modifier_tools import register_modifier_tools
from .observation_tools import register_observation_tools
from .safety_tools import register_safety_tools
from .scene_intelligence_tools import register_scene_intelligence_tools
from .scene_edit_tools import register_scene_edit_tools
from .selection_tools import register_selection_tools
from .shape_key_tools import register_shape_key_tools
from .shader_graph_tools import register_shader_graph_tools
from .polyhaven_tools import register_polyhaven_tools
from .presentation_workflow_tools import register_presentation_workflow_tools
from .procedural_asset_tools import register_procedural_asset_tools
from .project_workspace_tools import register_project_workspace_tools
from .provider_status_tools import register_provider_status_tools
from .reference_tools import register_reference_tools
from .render_tools import register_render_tools
from .rigging_simulation_tools import register_rigging_simulation_tools
from .screenshot_tools import register_screenshot_tools
from .script_registry_tools import register_script_registry_tools
from .sketchfab_tools import register_sketchfab_tools
from .review_package_tools import register_review_package_tools
from .skill_pack_tools import register_skill_pack_tools
from .snippet_library_tools import register_snippet_library_tools
from .scene_kit_tools import register_scene_kit_tools
from .spatial_tools import register_spatial_tools
from .task_graph_tools import register_task_graph_tools
from .verification_tools import register_verification_tools
from .vertex_group_tools import register_vertex_group_tools
from .workflow_intelligence_tools import register_workflow_intelligence_tools
from .workspace_tools import register_workspace_tools


def register_all_tools(mcp: Any, get_blender_connection, *, image_type: Any | None = None) -> None:
    """Register all MCP tool groups."""

    register_context_tools(mcp, get_blender_connection)
    register_governance_tools(mcp, get_blender_connection)
    register_project_workspace_tools(mcp, get_blender_connection)
    register_file_access_tools(mcp, get_blender_connection)
    register_cache_tools(mcp, get_blender_connection)
    register_task_graph_tools(mcp, get_blender_connection)
    register_reference_tools(mcp, get_blender_connection)
    register_spatial_tools(mcp, get_blender_connection)
    register_observation_tools(mcp, get_blender_connection)
    register_scene_intelligence_tools(mcp, get_blender_connection)
    register_scene_edit_tools(mcp, get_blender_connection)
    register_material_tools(mcp, get_blender_connection)
    register_material_intelligence_tools(mcp, get_blender_connection)
    register_advanced_material_tools(mcp, get_blender_connection)
    register_shader_graph_tools(mcp, get_blender_connection)
    register_material_texture_tools(mcp, get_blender_connection)
    register_bake_tools(mcp, get_blender_connection)
    register_image_resource_tools(mcp, get_blender_connection)
    register_channel_packing_tools(mcp, get_blender_connection)
    register_material_preview_tools(mcp, get_blender_connection)
    register_selection_tools(mcp, get_blender_connection)
    register_vertex_group_tools(mcp, get_blender_connection)
    register_shape_key_tools(mcp, get_blender_connection)
    register_lattice_tools(mcp, get_blender_connection)
    register_deformation_tools(mcp, get_blender_connection)
    register_workflow_intelligence_tools(mcp, get_blender_connection)
    register_animation_tools(mcp, get_blender_connection)
    register_camera_tools(mcp, get_blender_connection)
    register_lighting_tools(mcp, get_blender_connection)
    register_render_tools(mcp, get_blender_connection)
    register_compositor_tools(mcp, get_blender_connection)
    register_presentation_workflow_tools(mcp, get_blender_connection)
    register_asset_library_tools(mcp, get_blender_connection)
    register_dependency_tools(mcp, get_blender_connection)
    register_import_export_tools(mcp, get_blender_connection)
    register_scene_kit_tools(mcp, get_blender_connection)
    register_asset_workflow_tools(mcp, get_blender_connection)
    register_rigging_simulation_tools(mcp, get_blender_connection)
    register_geometry_nodes_intelligence_tools(mcp, get_blender_connection)
    register_geometry_nodes_template_tools(mcp, get_blender_connection)
    register_geometry_nodes_modifier_tools(mcp, get_blender_connection)
    register_procedural_asset_tools(mcp, get_blender_connection)
    register_geometry_nodes_workflow_tools(mcp, get_blender_connection)
    register_addon_management_tools(mcp, get_blender_connection)
    register_addon_development_tools(mcp, get_blender_connection)
    register_api_knowledge_tools(mcp, get_blender_connection)
    register_snippet_library_tools(mcp, get_blender_connection)
    register_skill_pack_tools(mcp, get_blender_connection)
    register_review_package_tools(mcp, get_blender_connection)
    register_advanced_knowledge_workflow_tools(mcp, get_blender_connection)
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
