from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


PHASE6A_SERVICES = [
    "GeometryNodesIntelligenceService",
    "GeometryNodesTemplateService",
    "GeometryNodesRecipeService",
    "GeometryNodesModifierService",
    "ProceduralAssetGeneratorService",
    "GeometryNodesValidationService",
    "GeometryNodesPreviewService",
    "GeometryNodesWorkflowBatchService",
]


PHASE6A_COMMANDS = [
    "get_geometry_nodes_capabilities",
    "list_geometry_node_groups",
    "get_geometry_node_group_deep_info",
    "list_geometry_nodes_modifiers",
    "get_geometry_nodes_modifier_info",
    "get_supported_geometry_node_templates",
    "create_geometry_node_group_from_template",
    "create_custom_geometry_node_recipe",
    "apply_geometry_nodes_modifier",
    "set_geometry_nodes_modifier_input",
    "create_procedural_asset",
    "create_scatter_system",
    "create_curve_generator",
    "create_radial_array_system",
    "create_panel_generator",
    "create_cable_or_rope_generator",
    "create_terrain_noise_system",
    "validate_geometry_node_group",
    "create_geometry_nodes_preview",
    "create_geometry_nodes_scene_kit",
    "delete_geometry_node_groups",
    "remove_geometry_nodes_modifiers",
    "run_geometry_nodes_workflow_batch",
]


def test_phase6a_addon_services_are_present_and_initialized() -> None:
    for service in PHASE6A_SERVICES:
        assert f"class {service}" in ADDON_TEXT
        snake = "".join([f"_{c.lower()}" if c.isupper() else c for c in service]).strip("_").replace("_service", "_service")
        assert service in ADDON_TEXT

    for assignment in [
        "self.geometry_nodes_intelligence_service = GeometryNodesIntelligenceService(self)",
        "self.geometry_nodes_template_service = GeometryNodesTemplateService(self)",
        "self.geometry_nodes_recipe_service = GeometryNodesRecipeService(self)",
        "self.geometry_nodes_modifier_service = GeometryNodesModifierService(self)",
        "self.procedural_asset_generator_service = ProceduralAssetGeneratorService(self)",
        "self.geometry_nodes_validation_service = GeometryNodesValidationService(self)",
        "self.geometry_nodes_preview_service = GeometryNodesPreviewService(self)",
        "self.geometry_nodes_workflow_batch_service = GeometryNodesWorkflowBatchService(self)",
    ]:
        assert assignment in ADDON_TEXT


def test_phase6a_commands_are_exposed_by_addon_handlers() -> None:
    for command in PHASE6A_COMMANDS:
        assert f'"{command}": self.{command}' in ADDON_TEXT

    assert '"complete_geometry_node": self.complete_geometry_node' in ADDON_TEXT
    assert '"get_geometry_nodes_status": self.get_geometry_nodes_status' in ADDON_TEXT


def test_phase6a_capability_and_intelligence_shapes_are_present() -> None:
    for text in [
        "supports_geometry_nodes",
        "supports_node_group_interface",
        "available_node_types",
        "modifier_input_api",
        "interface_inputs",
        "modifier_users",
        "node_count",
        "link_count",
    ]:
        assert text in ADDON_TEXT
