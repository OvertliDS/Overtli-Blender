from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def test_phase4a_material_services_are_defined_and_wired() -> None:
    for text in [
        "class MaterialIntelligenceService",
        "class MaterialTemplateService",
        "class AdvancedMaterialAuthoringService",
        "class ShaderGraphService",
        "class MaterialTextureSlotService",
        "class ProceduralTextureService",
        "class MaterialPreviewService",
        "class MaterialWorkflowBatchService",
        "self.material_intelligence_service = MaterialIntelligenceService(self)",
        "self.material_template_service = MaterialTemplateService(self)",
        "self.advanced_material_authoring_service = AdvancedMaterialAuthoringService(self)",
        "self.shader_graph_service = ShaderGraphService(self)",
        "self.material_texture_slot_service = MaterialTextureSlotService(self)",
        "self.procedural_texture_service = ProceduralTextureService(self)",
        "self.material_preview_service = MaterialPreviewService(self)",
        "self.material_workflow_batch_service = MaterialWorkflowBatchService(self)",
    ]:
        assert text in ADDON_TEXT


def test_phase4a_commands_are_mapped_in_addon_dispatch() -> None:
    for name in [
        "get_material_channel_schema",
        "get_supported_material_templates",
        "list_materials_deep",
        "get_material_deep_info",
        "get_shader_graph",
        "create_material_from_template",
        "create_custom_material",
        "create_procedural_material",
        "create_material_variant",
        "apply_material_to_objects",
        "bind_material_texture_map",
        "set_material_node_input",
        "add_material_node",
        "connect_material_nodes",
        "remove_material_node",
        "create_material_preview",
        "run_material_workflow_batch",
        "delete_materials",
        "create_basic_material",
        "assign_material",
        "update_material_properties",
    ]:
        assert f'"{name}": self.{name}' in ADDON_TEXT


def test_phase4a_channel_and_map_vocabulary_is_present() -> None:
    for text in [
        "MATERIAL_CHANNEL_SCHEMA",
        "base_color",
        "albedo",
        "roughness",
        "metallic",
        "normal",
        "bump",
        "height",
        "displacement",
        "ambient_occlusion",
        "emission_color",
        "alpha",
        "ORM",
        "RMA",
        "MRA",
        "glTF_metallic_roughness",
        "Non-Color",
        "sRGB",
    ]:
        assert text in ADDON_TEXT
