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
    return {
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


def get_command_safety(command_type: str) -> CommandSafetyMetadata | None:
    return build_command_safety_map().get(command_type)
