from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .operation_types import OperationType
from .permissions import Reversibility, RiskLevel


SAFETY_MODE_COMPAT = "compatibility"
SAFETY_MODE_AUDIT = "audit"
SAFETY_MODE_STRICT = "strict"
SAFETY_POLICY_VERSION = "1.0"
DEFAULT_SAFETY_MODE = SAFETY_MODE_COMPAT
AVAILABLE_SAFETY_MODES = [SAFETY_MODE_COMPAT, SAFETY_MODE_AUDIT, SAFETY_MODE_STRICT]


@dataclass(frozen=True)
class CommandSafetyMetadata:
    command_type: str
    operation_type: OperationType
    risk_level: RiskLevel
    reversibility: Reversibility
    can_mutate_scene: bool = False
    can_execute_code: bool = False
    can_call_network: bool = False
    can_write_files: bool = False
    provider_api_key_involved: bool = False
    strict_blocked: bool = False
    default_action: str = "allow"
    strict_action: str = "block"
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["operation_type"] = self.operation_type.value
        data["risk_level"] = self.risk_level.value
        data["reversibility"] = self.reversibility.value
        data["warnings"] = list(self.warnings)
        return data


def _spec(command_type: str, operation_type: OperationType, risk_level: RiskLevel, reversibility: Reversibility, **kwargs: Any) -> CommandSafetyMetadata:
    return CommandSafetyMetadata(
        command_type=command_type,
        operation_type=operation_type,
        risk_level=risk_level,
        reversibility=reversibility,
        **kwargs,
    )


def build_command_safety_map() -> dict[str, CommandSafetyMetadata]:
    command_map = {
        "get_scene_info": _spec("get_scene_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_object_info": _spec("get_object_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_shared_context": _spec("get_shared_context", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_operation_history": _spec("get_operation_history", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_object_handles": _spec("list_object_handles", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_material_handles": _spec("list_material_handles", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_context_scripts": _spec("list_context_scripts", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_polyhaven_status": _spec("get_polyhaven_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_hyper3d_status": _spec("get_hyper3d_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE, provider_api_key_involved=True),
        "get_sketchfab_status": _spec("get_sketchfab_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE, provider_api_key_involved=True),
        "get_geometry_nodes_status": _spec("get_geometry_nodes_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_addon_management_status": _spec("get_addon_management_status", OperationType.INSTALL_ADDON, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_blender_addons": _spec("list_blender_addons", OperationType.INSTALL_ADDON, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_blender_addon_info": _spec("get_blender_addon_info", OperationType.INSTALL_ADDON, RiskLevel.LOW, Reversibility.REVERSIBLE, warnings=("preference-secret-fields-redacted",)),
        "inspect_blender_api_docs": _spec("inspect_blender_api_docs", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW, Reversibility.REVERSIBLE, warnings=("local-private-docs-summary-only",)),
        "search_blender_api_docs": _spec("search_blender_api_docs", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_blender_api_topic": _spec("get_blender_api_topic", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_verified_snippets": _spec("list_verified_snippets", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "search_verified_snippets": _spec("search_verified_snippets", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_verified_snippet": _spec("get_verified_snippet", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "validate_verified_snippet": _spec("validate_verified_snippet", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_skill_packs": _spec("list_skill_packs", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_skill_pack": _spec("get_skill_pack", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "validate_skill_pack": _spec("validate_skill_pack", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "validate_review_package": _spec("validate_review_package", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "create_addon_skeleton": _spec("create_addon_skeleton", OperationType.INSTALL_ADDON, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-addon-dev-artifacts",)),
        "validate_addon_skeleton": _spec("validate_addon_skeleton", OperationType.VERIFY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, warnings=("static-validation-only",)),
        "package_addon_zip": _spec("package_addon_zip", OperationType.EXPORT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("excludes-private-generated-and-secret-files",)),
        "build_blender_api_index": _spec("build_blender_api_index", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("indexes-local-private-docs-with-public-safe-summary",)),
        "create_verified_snippet": _spec("create_verified_snippet", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("metadata-first-validation-first",)),
        "create_skill_pack": _spec("create_skill_pack", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("local-manifest-based-skill-pack",)),
        "export_project_review_package": _spec("export_project_review_package", OperationType.EXPORT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("privacy-exclusions-by-default",)),
        "run_advanced_knowledge_workflow_batch": _spec("run_advanced_knowledge_workflow_batch", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_write_files=True, warnings=("allowlisted-knowledge-batch",)),
        "install_local_addon": _spec("install_local_addon", OperationType.INSTALL_ADDON, RiskLevel.HIGH, Reversibility.PARTIAL, can_execute_code=True, can_write_files=True, strict_blocked=True, warnings=("explicit-confirmation-required", "local-addon-only")),
        "enable_blender_addon": _spec("enable_blender_addon", OperationType.INSTALL_ADDON, RiskLevel.HIGH, Reversibility.PARTIAL, can_execute_code=True, strict_blocked=True, warnings=("explicit-confirmation-required", "executes-addon-register-code")),
        "disable_blender_addon": _spec("disable_blender_addon", OperationType.INSTALL_ADDON, RiskLevel.HIGH, Reversibility.PARTIAL, can_execute_code=True, strict_blocked=True, warnings=("explicit-confirmation-required",)),
        "remove_blender_addon": _spec("remove_blender_addon", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_write_files=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-module-only")),
        "run_verified_snippet_smoke": _spec("run_verified_snippet_smoke", OperationType.UPDATE_KNOWLEDGE, RiskLevel.HIGH, Reversibility.UNKNOWN, can_execute_code=True, can_write_files=True, strict_blocked=True, warnings=("explicit-confirmation-required", "not-run-in-default-smoke")),
        "delete_verified_snippets": _spec("delete_verified_snippets", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_write_files=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-snippet-ids-only")),
        "run_skill_pack": _spec("run_skill_pack", OperationType.UPDATE_KNOWLEDGE, RiskLevel.HIGH, Reversibility.PARTIAL, can_write_files=True, strict_blocked=True, warnings=("explicit-confirmation-required", "manifest-operations-only")),
        "delete_skill_packs": _spec("delete_skill_packs", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_write_files=True, strict_blocked=True, warnings=("explicit-confirmation-required", "workspace-scope-only")),
        "get_geometry_nodes_capabilities": _spec("get_geometry_nodes_capabilities", OperationType.GEOMETRY_NODES, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_geometry_node_groups": _spec("list_geometry_node_groups", OperationType.GEOMETRY_NODES, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_geometry_node_group_deep_info": _spec("get_geometry_node_group_deep_info", OperationType.GEOMETRY_NODES, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_geometry_nodes_modifiers": _spec("list_geometry_nodes_modifiers", OperationType.GEOMETRY_NODES, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_geometry_nodes_modifier_info": _spec("get_geometry_nodes_modifier_info", OperationType.GEOMETRY_NODES, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_supported_geometry_node_templates": _spec("get_supported_geometry_node_templates", OperationType.GEOMETRY_NODES, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "validate_geometry_node_group": _spec("validate_geometry_node_group", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_safety_status": _spec("get_safety_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_viewport_screenshot": _spec(
            "get_viewport_screenshot",
            OperationType.CAMERA,
            RiskLevel.MEDIUM,
            Reversibility.REVERSIBLE,
            can_mutate_scene=False,
            warnings=("viewport-context-dependent",),
        ),
        "get_scene_index": _spec("get_scene_index", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_object_deep_info": _spec("get_object_deep_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_selection_info": _spec("get_selection_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_scene_health": _spec("get_scene_health", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "capture_viewport_pack": _spec(
            "capture_viewport_pack",
            OperationType.CAMERA,
            RiskLevel.MEDIUM,
            Reversibility.REVERSIBLE,
            can_write_files=True,
            warnings=("writes-local-verification-artifacts", "viewport-context-dependent"),
        ),
        "create_verification_snapshot": _spec(
            "create_verification_snapshot",
            OperationType.VERIFY,
            RiskLevel.MEDIUM,
            Reversibility.REVERSIBLE,
            can_write_files=True,
            warnings=("writes-local-verification-artifacts",),
        ),
        "list_verification_snapshots": _spec("list_verification_snapshots", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_supported_edit_operations": _spec("get_supported_edit_operations", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "create_primitive_object": _spec("create_primitive_object", OperationType.CREATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "transform_object": _spec("transform_object", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "duplicate_object": _spec("duplicate_object", OperationType.CREATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "delete_objects": _spec("delete_objects", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required",)),
        "set_object_visibility": _spec("set_object_visibility", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_basic_material": _spec("create_basic_material", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "assign_material": _spec("assign_material", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "update_material_properties": _spec("update_material_properties", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "get_material_channel_schema": _spec("get_material_channel_schema", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_supported_material_templates": _spec("get_supported_material_templates", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_materials_deep": _spec("list_materials_deep", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_material_deep_info": _spec("get_material_deep_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_shader_graph": _spec("get_shader_graph", OperationType.SHADER, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "create_material_from_template": _spec("create_material_from_template", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_custom_material": _spec("create_custom_material", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_procedural_material": _spec("create_procedural_material", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_material_variant": _spec("create_material_variant", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "apply_material_to_objects": _spec("apply_material_to_objects", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "bind_material_texture_map": _spec("bind_material_texture_map", OperationType.TEXTURE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("non-color-map-intent-preserved",)),
        "set_material_node_input": _spec("set_material_node_input", OperationType.SHADER, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("allowlisted-node-inputs-only",)),
        "add_material_node": _spec("add_material_node", OperationType.SHADER, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("allowlisted-node-types-only",)),
        "connect_material_nodes": _spec("connect_material_nodes", OperationType.SHADER, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("explicit-node-socket-links-only",)),
        "create_material_preview": _spec("create_material_preview", OperationType.VERIFY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-material-preview-artifacts",)),
        "run_material_workflow_batch": _spec("run_material_workflow_batch", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("allowlisted-material-workflow-batch", "writes-local-verification-artifacts")),
        "remove_material_node": _spec("remove_material_node", OperationType.SHADER, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "overtli-created-allowlisted-nodes-only")),
        "delete_materials": _spec("delete_materials", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "explicit-material-names-only")),
        "get_selection_deep_info": _spec("get_selection_deep_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_mesh_component_summary": _spec("get_mesh_component_summary", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_vertex_groups": _spec("list_vertex_groups", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_shape_keys": _spec("list_shape_keys", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "create_vertex_group": _spec("create_vertex_group", OperationType.SELECT_REGION, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("explicit-mesh-target-required",)),
        "update_vertex_group_weights": _spec("update_vertex_group_weights", OperationType.SELECT_REGION, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("explicit-mesh-target-required",)),
        "create_shape_key": _spec("create_shape_key", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("basis-preserved",)),
        "update_shape_key_value": _spec("update_shape_key_value", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_lattice_deformer": _spec("create_lattice_deformer", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "apply_lattice_to_object": _spec("apply_lattice_to_object", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("does-not-apply-modifier",)),
        "add_deformation_modifier": _spec("add_deformation_modifier", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("allowlisted-modifier-types-only", "does-not-apply-modifier")),
        "update_deformation_modifier": _spec("update_deformation_modifier", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("allowlisted-modifier-properties-only",)),
        "create_region_deformation": _spec("create_region_deformation", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("explicit-region-required", "confirmation-required")),
        "run_deformation_workflow_batch": _spec("run_deformation_workflow_batch", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("allowlisted-deformation-workflow-batch", "writes-local-verification-artifacts")),
        "edit_shape_key_offsets": _spec("edit_shape_key_offsets", OperationType.DEFORM, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "basis-preserved", "bounded-target-required")),
        "update_lattice_deformer": _spec("update_lattice_deformer", OperationType.DEFORM, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-lattice-name-only")),
        "delete_vertex_groups": _spec("delete_vertex_groups", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-group-names-only")),
        "delete_shape_keys": _spec("delete_shape_keys", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "basis-refused-by-default")),
        "remove_lattice_deformer": _spec("remove_lattice_deformer", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-lattice-name-only")),
        "get_method_plan": _spec("get_method_plan", OperationType.PLAN, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_operation_playbooks": _spec("list_operation_playbooks", OperationType.PLAN, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_tricks_knowledge_base": _spec("get_tricks_knowledge_base", OperationType.PLAN, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_anti_pattern_rules": _spec("get_anti_pattern_rules", OperationType.PLAN, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_modifier_recipes": _spec("get_modifier_recipes", OperationType.MODIFIER, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "score_selection_confidence": _spec("score_selection_confidence", OperationType.SELECT_REGION, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "scan_blender_asset_libraries": _spec("scan_blender_asset_libraries", OperationType.ASSET_LIBRARY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "preview_asset": _spec("preview_asset", OperationType.VERIFY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-verification-artifacts",)),
        "import_texture_folder": _spec("import_texture_folder", OperationType.TEXTURE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("local-files-only", "color-space-intent-preserved")),
        "create_style_material": _spec("create_style_material", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_paintable_texture": _spec("create_paintable_texture", OperationType.TEXTURE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("creates-in-memory-image",)),
        "delete_images": _spec("delete_images", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-image-names-only")),
        "list_uv_maps": _spec("list_uv_maps", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "measure_object": _spec("measure_object", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "measure_distance": _spec("measure_distance", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "create_vertex_group_from_uv_island": _spec("create_vertex_group_from_uv_island", OperationType.SELECT_REGION, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "uv-island-approximation")),
        "create_proportional_deformation": _spec("create_proportional_deformation", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("explicit-region-required", "shape-key-or-lattice-preferred")),
        "get_sculpt_status": _spec("get_sculpt_status", OperationType.SCULPT, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "configure_sculpt_brush": _spec("configure_sculpt_brush", OperationType.SCULPT, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "session-local-brush-settings")),
        "create_sculpt_mask_from_vertex_group": _spec("create_sculpt_mask_from_vertex_group", OperationType.SCULPT, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "vertex-group-backed-mask-intent")),
        "run_shape_key_sculpt_workflow": _spec("run_shape_key_sculpt_workflow", OperationType.SCULPT, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, strict_blocked=True, warnings=("explicit-confirmation-required", "basis-preserved", "shape-key-sculpt-workflow")),
        "get_timeline_info": _spec("get_timeline_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_animated_objects": _spec("list_animated_objects", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_animation_deep_info": _spec("get_animation_deep_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_render_settings": _spec("get_render_settings", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_compositor_status": _spec("get_compositor_status", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "set_current_frame": _spec("set_current_frame", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("mutates-current-frame-state",)),
        "set_timeline_range": _spec("set_timeline_range", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "insert_transform_keyframes": _spec("insert_transform_keyframes", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("explicit-target-required",)),
        "animate_object_transform": _spec("animate_object_transform", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("explicit-target-required",)),
        "animate_camera_transform": _spec("animate_camera_transform", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("explicit-camera-required",)),
        "animate_light_property": _spec("animate_light_property", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("allowlisted-light-properties-only",)),
        "animate_material_property": _spec("animate_material_property", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("allowlisted-material-channels-only",)),
        "animate_shape_key_value": _spec("animate_shape_key_value", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("shape-key-value-only",)),
        "create_camera": _spec("create_camera", OperationType.CAMERA, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "frame_camera_to_objects": _spec("frame_camera_to_objects", OperationType.CAMERA, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("explicit-targets-required",)),
        "set_active_camera": _spec("set_active_camera", OperationType.CAMERA, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_light": _spec("create_light", OperationType.LIGHTING, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_lighting_setup": _spec("create_lighting_setup", OperationType.LIGHTING, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "update_light": _spec("update_light", OperationType.LIGHTING, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "set_world_lighting": _spec("set_world_lighting", OperationType.LIGHTING, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "set_render_settings": _spec("set_render_settings", OperationType.RENDER, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "set_output_path": _spec("set_output_path", OperationType.RENDER, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True, warnings=("workspace-output-default",)),
        "render_still": _spec("render_still", OperationType.RENDER, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-render-artifacts",)),
        "render_contact_sheet": _spec("render_contact_sheet", OperationType.RENDER, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-render-artifacts",)),
        "create_turntable_animation": _spec("create_turntable_animation", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("bounded-frame-range-required",)),
        "render_preview_animation": _spec("render_preview_animation", OperationType.RENDER, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("bounded-preview-frames",)),
        "set_compositor_preset": _spec("set_compositor_preset", OperationType.RENDER, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("preset-only-compositor-editing",)),
        "set_render_passes": _spec("set_render_passes", OperationType.RENDER, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "run_presentation_workflow_batch": _spec("run_presentation_workflow_batch", OperationType.RENDER, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("allowlisted-presentation-batch", "writes-local-verification-artifacts")),
        "delete_animation_data": _spec("delete_animation_data", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-target-only")),
        "cleanup_presentation_artifacts": _spec("cleanup_presentation_artifacts", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, strict_blocked=True, warnings=("explicit-confirmation-required", "prefix-bound-cleanup-only")),
        "get_supported_asset_formats": _spec("get_supported_asset_formats", OperationType.ASSET_LIBRARY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "scan_asset_folder": _spec("scan_asset_folder", OperationType.ASSET_LIBRARY, RiskLevel.LOW, Reversibility.REVERSIBLE, warnings=("bounded-local-scan-only",)),
        "list_asset_libraries": _spec("list_asset_libraries", OperationType.ASSET_LIBRARY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_scene_assets": _spec("list_scene_assets", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_asset_file_info": _spec("get_asset_file_info", OperationType.ASSET_LIBRARY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_asset_dependency_report": _spec("get_asset_dependency_report", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "validate_external_dependencies": _spec("validate_external_dependencies", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "validate_scene_kit": _spec("validate_scene_kit", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_scene_kits": _spec("list_scene_kits", OperationType.ASSET_LIBRARY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "create_asset_manifest": _spec("create_asset_manifest", OperationType.ASSET_LIBRARY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-manifest-artifacts",)),
        "append_blend_asset": _spec("append_blend_asset", OperationType.IMPORT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("exact-datablock-names-only", "local-blend-files-only")),
        "import_model_file": _spec("import_model_file", OperationType.IMPORT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("local-files-only", "writes-local-import-manifest")),
        "export_selected_objects": _spec("export_selected_objects", OperationType.EXPORT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("overwrite-disabled-by-default",)),
        "export_scene": _spec("export_scene", OperationType.EXPORT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("overwrite-disabled-by-default",)),
        "create_asset_preview": _spec("create_asset_preview", OperationType.VERIFY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-preview-artifacts",)),
        "create_asset_contact_sheet": _spec("create_asset_contact_sheet", OperationType.VERIFY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-preview-artifacts",)),
        "collect_external_dependencies": _spec("collect_external_dependencies", OperationType.EXPORT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("copies-local-dependencies-only",)),
        "create_scene_kit": _spec("create_scene_kit", OperationType.EXPORT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-scene-kit-artifacts",)),
        "import_scene_kit": _spec("import_scene_kit", OperationType.IMPORT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("imports-local-scene-kit-export",)),
        "run_asset_workflow_batch": _spec("run_asset_workflow_batch", OperationType.ASSET_LIBRARY, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("allowlisted-asset-workflow-batch",)),
        "inspect_rigging": _spec("inspect_rigging", OperationType.RIG, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "create_armature": _spec("create_armature", OperationType.RIG, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "parent_mesh_to_armature": _spec("parent_mesh_to_armature", OperationType.RIG, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "pose_bone_transform": _spec("pose_bone_transform", OperationType.RIG, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "add_driver": _spec("add_driver", OperationType.ANIMATE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("scripted-driver-expression",)),
        "add_physics_basic": _spec("add_physics_basic", OperationType.DEFORM, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("simulation-cache-not-baked",)),
        "create_geometry_node_group_from_template": _spec("create_geometry_node_group_from_template", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True, warnings=("template-first-geometry-nodes", "writes-local-recipe-manifest")),
        "create_custom_geometry_node_recipe": _spec("create_custom_geometry_node_recipe", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True, warnings=("allowlisted-node-types-only", "writes-local-recipe-manifest")),
        "apply_geometry_nodes_modifier": _spec("apply_geometry_nodes_modifier", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, warnings=("does-not-apply-modifier-destructively", "explicit-target-required")),
        "set_geometry_nodes_modifier_input": _spec("set_geometry_nodes_modifier_input", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("modifier-id-properties-only",)),
        "create_procedural_asset": _spec("create_procedural_asset", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True, warnings=("template-first-procedural-asset",)),
        "create_scatter_system": _spec("create_scatter_system", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True),
        "create_curve_generator": _spec("create_curve_generator", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True),
        "create_radial_array_system": _spec("create_radial_array_system", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True),
        "create_panel_generator": _spec("create_panel_generator", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True),
        "create_cable_or_rope_generator": _spec("create_cable_or_rope_generator", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True),
        "create_terrain_noise_system": _spec("create_terrain_noise_system", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True, can_write_files=True),
        "create_geometry_nodes_preview": _spec("create_geometry_nodes_preview", OperationType.VERIFY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-geometry-nodes-preview-artifacts",)),
        "create_geometry_nodes_scene_kit": _spec("create_geometry_nodes_scene_kit", OperationType.EXPORT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-scene-kit-artifacts",)),
        "run_geometry_nodes_workflow_batch": _spec("run_geometry_nodes_workflow_batch", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("allowlisted-geometry-nodes-workflow-batch",)),
        "delete_geometry_node_groups": _spec("delete_geometry_node_groups", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-node-group-names-or-prefix-only")),
        "remove_geometry_nodes_modifiers": _spec("remove_geometry_nodes_modifiers", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-modifier-names-or-prefix-only")),
        "pack_external_data": _spec("pack_external_data", OperationType.EXPORT, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "mutates-blend-packed-data-state")),
        "make_paths_relative": _spec("make_paths_relative", OperationType.EXPORT, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "mutates-blend-path-state")),
        "cleanup_asset_artifacts": _spec("cleanup_asset_artifacts", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, strict_blocked=True, warnings=("explicit-confirmation-required", "prefix-bound-cleanup-only")),
        "remove_driver": _spec("remove_driver", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "exact-driver-target-only")),
        "add_object_modifier": _spec("add_object_modifier", OperationType.MODIFIER, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "update_object_modifier": _spec("update_object_modifier", OperationType.MODIFIER, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "remove_object_modifier": _spec("remove_object_modifier", OperationType.MODIFIER, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required",)),
        "create_collection": _spec("create_collection", OperationType.CREATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "move_objects_to_collection": _spec("move_objects_to_collection", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "delete_collection": _spec("delete_collection", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "empty-collection-only-by-default")),
        "run_verified_edit_batch": _spec("run_verified_edit_batch", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("writes-local-verification-artifacts",)),
        "get_task_workspace": _spec("get_task_workspace", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE, can_write_files=True),
        "create_workspace_task": _spec("create_workspace_task", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True),
        "update_workspace_task": _spec("update_workspace_task", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True),
        "list_workspace_tasks": _spec("list_workspace_tasks", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "add_workspace_todo": _spec("add_workspace_todo", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True),
        "update_workspace_todo": _spec("update_workspace_todo", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True),
        "list_workspace_todos": _spec("list_workspace_todos", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "record_operation_journal_entry": _spec("record_operation_journal_entry", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True),
        "get_operation_journal": _spec("get_operation_journal", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "create_scene_snapshot": _spec("create_scene_snapshot", OperationType.VERIFY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("writes-local-workspace-artifacts",)),
        "list_scene_snapshots": _spec("list_scene_snapshots", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "diff_scene_snapshots": _spec("diff_scene_snapshots", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "detect_user_changes": _spec("detect_user_changes", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "rollback_to_scene_snapshot": _spec("rollback_to_scene_snapshot", OperationType.ROLLBACK, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "existing-objects-only")),
        "undo_last_blender_operation": _spec("undo_last_blender_operation", OperationType.ROLLBACK, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required",)),
        "create_object_handle": _spec("create_object_handle", OperationType.CREATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_material_handle": _spec("create_material_handle", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "register_context_script": _spec("register_context_script", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True),
        "execute_context_script": _spec(
            "execute_context_script",
            OperationType.UPDATE_KNOWLEDGE,
            RiskLevel.HIGH,
            Reversibility.UNKNOWN,
            can_execute_code=True,
            can_write_files=True,
            strict_blocked=True,
            warnings=("executes-user-registered-python",),
        ),
        "clear_context_scripts": _spec(
            "clear_context_scripts",
            OperationType.CLEANUP,
            RiskLevel.MEDIUM,
            Reversibility.PARTIAL,
            can_write_files=True,
            strict_blocked=True,
        ),
        "clear_shared_context": _spec(
            "clear_shared_context",
            OperationType.CLEANUP,
            RiskLevel.MEDIUM,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            strict_blocked=True,
        ),
        "get_polyhaven_categories": _spec("get_polyhaven_categories", OperationType.ASSET_LIBRARY, RiskLevel.LOW, Reversibility.REVERSIBLE, can_call_network=True),
        "search_polyhaven_assets": _spec("search_polyhaven_assets", OperationType.ASSET_LIBRARY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_call_network=True),
        "download_polyhaven_asset": _spec(
            "download_polyhaven_asset",
            OperationType.ASSET_LIBRARY,
            RiskLevel.HIGH,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            can_call_network=True,
            can_write_files=True,
            strict_blocked=True,
        ),
        "set_texture": _spec(
            "set_texture",
            OperationType.TEXTURE,
            RiskLevel.MEDIUM,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
        ),
        "search_sketchfab_models": _spec("search_sketchfab_models", OperationType.ASSET_LIBRARY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_call_network=True, provider_api_key_involved=True),
        "download_sketchfab_model": _spec(
            "download_sketchfab_model",
            OperationType.ASSET_LIBRARY,
            RiskLevel.HIGH,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            can_call_network=True,
            can_write_files=True,
            provider_api_key_involved=True,
            strict_blocked=True,
        ),
        "create_rodin_job": _spec(
            "create_rodin_job",
            OperationType.ASSET_LIBRARY,
            RiskLevel.HIGH,
            Reversibility.UNKNOWN,
            can_call_network=True,
            provider_api_key_involved=True,
            strict_blocked=True,
        ),
        "poll_rodin_job_status": _spec("poll_rodin_job_status", OperationType.VERIFY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_call_network=True, provider_api_key_involved=True),
        "import_generated_asset": _spec(
            "import_generated_asset",
            OperationType.IMPORT,
            RiskLevel.HIGH,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            can_call_network=True,
            can_write_files=True,
            provider_api_key_involved=True,
            strict_blocked=True,
        ),
        "complete_geometry_node": _spec(
            "complete_geometry_node",
            OperationType.GEOMETRY_NODES,
            RiskLevel.HIGH,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            strict_blocked=True,
        ),
        "get_system_status": _spec("get_system_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_project_status": _spec("get_project_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "discover_tool_packs": _spec("discover_tool_packs", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_tool_pack": _spec("get_tool_pack", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "search_tools": _spec("search_tools", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_tool_spec": _spec("get_tool_spec", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_recommended_tools_for_task": _spec("get_recommended_tools_for_task", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "prepare_operation": _spec("prepare_operation", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_pending_approvals": _spec("get_pending_approvals", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "approve_operation": _spec("approve_operation", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "deny_operation": _spec("deny_operation", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "execute_approved_operation": _spec("execute_approved_operation", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.PARTIAL, warnings=("executes-only-with-approval-record",)),
        "expire_approval": _spec("expire_approval", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_operation_status": _spec("get_operation_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_recent_operations": _spec("list_recent_operations", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "cancel_operation": _spec("cancel_operation", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_operation_log": _spec("get_operation_log", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_permission_profile": _spec("get_permission_profile", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "set_permission_profile": _spec("set_permission_profile", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.PARTIAL, warnings=("permission-expansion-confirmation-required",)),
        "get_capability_policy": _spec("get_capability_policy", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "validate_command_capabilities": _spec("validate_command_capabilities", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_log_status": _spec("get_log_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "export_operation_log": _spec("export_operation_log", OperationType.EXPORT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True, warnings=("redacted-operation-log-export",)),
        "get_command_registry_report": _spec("get_command_registry_report", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "execute_code": _spec(
            "execute_code",
            OperationType.VERIFY,
            RiskLevel.HIGH,
            Reversibility.UNKNOWN,
            can_execute_code=True,
            strict_blocked=True,
            warnings=("arbitrary-python-execution",),
        ),
    }
    command_map.update(_phase7c_safety_map())
    command_map.update(_phase8a_safety_map())
    command_map.update(_phase8b_safety_map())
    command_map.update(_phase9a_safety_map())
    return command_map


def _phase9a_safety_map() -> dict[str, CommandSafetyMetadata]:
    low = [
        "get_animation_system_capabilities", "inspect_animation_system", "list_actions",
        "get_action_deep_info", "validate_fcurves", "validate_nla_stack", "validate_driver_dsl",
        "list_drivers", "get_driver_info", "validate_rig", "inspect_pose", "list_pose_assets",
        "compare_poses", "validate_shot_plan", "create_motion_path_preview", "validate_motion",
        "get_simulation_capabilities", "inspect_simulation_state", "get_simulation_cache_status",
    ]
    medium = [
        "create_action", "duplicate_action", "rename_action", "assign_action",
        "insert_keyframe_batch", "set_fcurve_interpolation", "add_fcurve_modifier",
        "create_nla_track", "add_action_to_nla", "edit_nla_strip", "mute_nla_track",
        "create_driver_from_dsl", "create_rig_template", "create_control_bones",
        "create_ik_chain", "add_rig_constraint", "add_custom_rig_properties",
        "create_pose_snapshot", "create_pose_asset", "create_shot_range", "create_camera_cut",
        "create_timeline_marker", "create_shot_plan", "configure_rigidbody_basic",
        "configure_cloth_simulation_advanced", "configure_softbody_basic",
        "configure_hair_curve_dynamics_basic", "run_animation_rigging_workflow_batch",
    ]
    high = [
        "delete_actions", "edit_keyframes", "retime_action", "remove_fcurve_modifier",
        "delete_nla_tracks", "remove_drivers", "remove_rig_constraints", "apply_pose_snapshot",
        "delete_pose_assets", "simulate_preview_range", "bake_simulation_cache",
        "clear_simulation_cache",
    ]
    specs: dict[str, CommandSafetyMetadata] = {}
    for name in low:
        specs[name] = _spec(name, OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE, warnings=("phase9a-motion-workflow",))
    for name in medium:
        operation = OperationType.ANIMATE
        if any(marker in name for marker in ("rig", "ik", "constraint", "custom_rig")):
            operation = OperationType.RIG
        elif any(marker in name for marker in ("shot", "camera_cut", "timeline_marker", "motion_path")):
            operation = OperationType.CAMERA
        elif any(marker in name for marker in ("simulation", "rigidbody", "cloth", "softbody", "hair")):
            operation = OperationType.EDIT
        specs[name] = _spec(name, operation, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, warnings=("phase9a-structured-workflow", "exact-target-required"))
    for name in high:
        specs[name] = _spec(name, OperationType.CLEANUP if any(marker in name for marker in ("delete", "remove", "clear")) else OperationType.ANIMATE, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-approval-required", "phase9a-high-risk", "exact-target-only"))
    return specs


def _phase8b_safety_map() -> dict[str, CommandSafetyMetadata]:
    low = [
        "get_modeling_capabilities", "validate_mesh_schema", "plan_reference_construction",
        "validate_reference_alignment", "validate_sculpt_result", "validate_construction_geometry",
        "plan_construction_cleanup",
    ]
    medium = [
        "create_mesh_from_schema", "create_profile_curve", "extrude_profile", "lathe_profile",
        "loft_profiles", "bridge_profile_loops", "create_curve_path_object",
        "create_beveled_curve_object", "create_modifier_stack", "create_hard_surface_panel",
        "create_pipe_or_rail", "create_modular_assembly", "run_reference_construction_step",
        "configure_sculpt_session", "create_sculpt_mask", "create_face_set",
        "create_shape_key_sculpt_variant", "create_cloth_pattern_panel", "define_cloth_seam_pair",
        "create_cloth_setup", "create_cloth_pin_group", "create_cloth_collision_setup",
        "run_advanced_modeling_workflow_batch",
    ]
    high = [
        "apply_sculpt_stroke_batch", "simulate_cloth_preview", "bake_cloth_cache",
        "clear_cloth_cache", "convert_cloth_result", "execute_construction_cleanup",
    ]
    specs: dict[str, CommandSafetyMetadata] = {}
    for name in low:
        specs[name] = _spec(name, OperationType.VERIFY if "plan" not in name else OperationType.PLAN, RiskLevel.LOW, Reversibility.REVERSIBLE, warnings=("phase8b-advanced-modeling",))
    for name in medium:
        operation = OperationType.SCULPT if "sculpt" in name or "face_set" in name else OperationType.EDIT
        if "cloth" in name:
            operation = OperationType.EDIT
        if "modifier" in name:
            operation = OperationType.MODIFIER
        if any(marker in name for marker in ("mesh", "profile", "curve", "panel", "pipe", "assembly", "lathe", "loft", "bridge", "extrude")):
            operation = OperationType.CREATE
        specs[name] = _spec(name, operation, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=name == "run_advanced_modeling_workflow_batch", warnings=("phase8b-structured-workflow", "non-destructive-default"))
    for name in high:
        specs[name] = _spec(name, OperationType.CLEANUP if "cleanup" in name or "cache" in name else OperationType.SCULPT if "sculpt" in name else OperationType.EDIT, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-approval-required", "phase8b-high-risk"))
    return specs


def _phase8a_safety_map() -> dict[str, CommandSafetyMetadata]:
    low = [
        "get_bake_capabilities", "validate_bake_setup", "estimate_bake_cost", "list_bake_targets",
        "validate_packed_texture", "validate_baked_textures", "plan_bake_cleanup",
        "list_project_images", "get_image_resource_info",
    ]
    medium_scene = [
        "create_bake_target_images", "assign_bake_targets", "bake_material_maps",
        "bake_selected_to_active", "bake_procedural_material", "bake_derived_map",
        "bake_curvature_map", "bake_thickness_map", "relink_baked_textures",
        "create_baked_material", "run_verified_bake_workflow",
    ]
    medium_files = [
        "pack_texture_channels", "unpack_texture_channels", "save_baked_textures",
        "rename_image_resource",
    ]
    high = ["execute_bake_cleanup"]
    specs: dict[str, CommandSafetyMetadata] = {}
    for name in low:
        specs[name] = _spec(name, OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE, warnings=("phase8a-texture-baking",))
    for name in medium_scene:
        specs[name] = _spec(name, OperationType.TEXTURE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=name not in {"assign_bake_targets", "relink_baked_textures", "create_baked_material"}, warnings=("phase8a-texture-baking", "project-workspace-required"))
    for name in medium_files:
        specs[name] = _spec(name, OperationType.TEXTURE, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_write_files=True, warnings=("phase8a-texture-baking", "no-overwrite-without-approval"))
    for name in high:
        specs[name] = _spec(name, OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, strict_blocked=True, warnings=("explicit-approval-required", "tracked-bake-artifacts-only"))
    return specs


def _phase7c_safety_map() -> dict[str, CommandSafetyMetadata]:
    low = [
        "get_project_status", "resolve_project_workspace", "get_file_access_policy", "validate_path_access",
        "list_approved_roots", "scan_project_files", "get_cache_status", "list_tasks", "get_task",
        "get_task_graph", "detect_stale_tasks", "get_session_time", "get_scene_revision",
        "get_recent_operations", "get_changes_since_revision", "list_reference_images",
        "calculate_distance", "calculate_angle", "calculate_area", "calculate_volume", "convert_units",
        "get_oriented_bounds",
    ]
    medium = [
        "initialize_project_workspace", "validate_project_layout", "repair_project_layout", "register_blend_file",
        "create_project_backup", "collect_project_dependencies", "add_approved_root", "remove_approved_root",
        "write_project_text_file", "copy_file_into_project", "read_project_text_file", "plan_file_delete",
        "plan_cache_cleanup", "pin_artifact", "unpin_artifact", "find_orphaned_artifacts",
        "compact_operation_history", "create_task", "update_task", "set_task_status", "link_task_artifact",
        "link_task_target", "mark_task_verified", "mark_task_stale", "archive_tasks",
        "get_operation_duration", "create_scene_revision_marker", "import_reference_image",
        "create_reference_set", "place_reference_view", "calibrate_reference_scale", "set_reference_opacity",
        "set_reference_depth", "lock_reference", "set_reference_view_visibility", "add_reference_landmark",
        "measure_reference_landmarks", "capture_reference_overlay", "relink_reference_image",
        "calculate_curve_length", "calculate_clearance", "calculate_alignment", "calculate_scale_ratio",
        "compare_measurements", "raycast_scene", "find_nearest_objects", "detect_object_intersections",
        "measure_object_to_reference", "plan_rename", "batch_rename_datablocks",
    ]
    high = [
        "save_project_as", "restore_project_backup", "set_file_access_policy", "execute_approved_file_delete",
        "execute_cache_cleanup", "remove_reference_image", "execute_rename", "batch_rename_files",
        "rename_project", "repair_references_after_rename",
    ]
    specs: dict[str, CommandSafetyMetadata] = {}
    for name in low:
        specs[name] = _spec(name, OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE)
    for name in medium:
        specs[name] = _spec(name, OperationType.UPDATE_KNOWLEDGE if "task" in name else OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=name in {"place_reference_view", "create_scene_revision_marker", "batch_rename_datablocks"}, can_write_files=any(marker in name for marker in ("workspace", "file", "cache", "task", "reference", "backup", "project", "artifact", "root")), warnings=("phase7c-project-scoped",))
    for name in high:
        specs[name] = _spec(name, OperationType.CLEANUP if "delete" in name or "cleanup" in name or "remove" in name else OperationType.EDIT, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=name in {"execute_rename", "rename_project", "repair_references_after_rename", "save_project_as", "restore_project_backup"}, can_write_files=True, strict_blocked=True, warnings=("explicit-approval-required", "phase7c-high-risk"))
    return specs


def get_command_safety(command_type: str) -> CommandSafetyMetadata | None:
    return build_command_safety_map().get(command_type)
