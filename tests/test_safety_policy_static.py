from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
SAFETY_TEXT = (ROOT / "src/overtli_blender/common/safety.py").read_text(encoding="utf-8")
SMOKE_TEXT = (ROOT / "scripts" / "smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_addon_defines_safety_policy_service() -> None:
    for text in [
        "class SafetyPolicyService",
        "self.safety_policy_service = SafetyPolicyService(self)",
        "self.get_safety_status = self.safety_policy_service.get_safety_status",
        "def get_safety_status(self):",
        '"get_safety_status": self.get_safety_status',
    ]:
        assert text in ADDON_TEXT


def test_addon_dispatch_evaluates_safety_before_execution() -> None:
    for text in [
        "safety_decision = self.safety_policy_service.evaluate_command(cmd_type, params)",
        "Command blocked by safety policy",
        "self.safety_policy_service.mode == SAFETY_MODE_AUDIT",
        "if cmd_type == \"get_safety_status\":",
    ]:
        assert text in ADDON_TEXT


def test_common_safety_module_defines_policy_metadata() -> None:
    for text in [
        "SAFETY_MODE_COMPAT = \"compatibility\"",
        "SAFETY_MODE_AUDIT = \"audit\"",
        "SAFETY_MODE_STRICT = \"strict\"",
        "SAFETY_POLICY_VERSION = \"1.0\"",
        "CommandSafetyMetadata",
        "build_command_safety_map",
    ]:
        assert text in SAFETY_TEXT


def test_common_safety_module_classifies_high_risk_commands() -> None:
    for text in [
        '"execute_code"',
        '"execute_context_script"',
        '"complete_geometry_node"',
        '"download_polyhaven_asset"',
        '"download_sketchfab_model"',
        '"create_rodin_job"',
        '"import_generated_asset"',
        '"clear_context_scripts"',
    ]:
        assert text in SAFETY_TEXT


def test_common_safety_module_classifies_phase2_commands() -> None:
    for text in [
        '"get_scene_index", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_object_deep_info", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_selection_info", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_scene_health", OperationType.VERIFY, RiskLevel.LOW',
        '"capture_viewport_pack"',
        '"create_verification_snapshot"',
        '"list_verification_snapshots", OperationType.VERIFY, RiskLevel.LOW',
        "can_write_files=True",
        '"writes-local-verification-artifacts"',
    ]:
        assert text in SAFETY_TEXT


def test_phase2_strict_mode_behavior_is_documented_in_policy() -> None:
    for command in [
        "get_scene_index",
        "get_object_deep_info",
        "get_selection_info",
        "get_scene_health",
        "capture_viewport_pack",
        "create_verification_snapshot",
    ]:
        command_index = SAFETY_TEXT.index(f'"{command}"')
        command_block = SAFETY_TEXT[command_index:command_index + 500]
        assert "strict_blocked=True" not in command_block


def test_common_safety_module_classifies_phase3_commands() -> None:
    for text in [
        '"get_supported_edit_operations", OperationType.OBSERVE, RiskLevel.LOW',
        '"create_primitive_object", OperationType.CREATE, RiskLevel.MEDIUM',
        '"transform_object", OperationType.EDIT, RiskLevel.MEDIUM',
        '"duplicate_object", OperationType.CREATE, RiskLevel.MEDIUM',
        '"create_basic_material", OperationType.MATERIAL, RiskLevel.MEDIUM',
        '"add_object_modifier", OperationType.MODIFIER, RiskLevel.MEDIUM',
        '"create_collection", OperationType.CREATE, RiskLevel.MEDIUM',
        '"run_verified_edit_batch", OperationType.EDIT, RiskLevel.MEDIUM',
        '"delete_objects", OperationType.CLEANUP, RiskLevel.HIGH',
        '"remove_object_modifier", OperationType.MODIFIER, RiskLevel.HIGH',
        '"delete_collection", OperationType.CLEANUP, RiskLevel.HIGH',
        '"rollback_to_scene_snapshot", OperationType.ROLLBACK, RiskLevel.HIGH',
        '"undo_last_blender_operation", OperationType.ROLLBACK, RiskLevel.HIGH',
        "explicit-confirmation-required",
    ]:
        assert text in SAFETY_TEXT


def test_phase3_destructive_commands_are_strict_blocked() -> None:
    for command in ["delete_objects", "remove_object_modifier", "delete_collection", "rollback_to_scene_snapshot", "undo_last_blender_operation"]:
        command_index = SAFETY_TEXT.index(f'"{command}"')
        command_block = SAFETY_TEXT[command_index:command_index + 500]
        assert "strict_blocked=True" in command_block


def test_common_safety_module_classifies_phase3_master_workspace_commands() -> None:
    for text in [
        '"get_task_workspace", OperationType.VERIFY, RiskLevel.LOW',
        '"create_workspace_task", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM',
        '"add_workspace_todo", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM',
        '"record_operation_journal_entry", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM',
        '"create_scene_snapshot", OperationType.VERIFY, RiskLevel.MEDIUM',
        '"diff_scene_snapshots", OperationType.VERIFY, RiskLevel.LOW',
        '"detect_user_changes", OperationType.VERIFY, RiskLevel.LOW',
    ]:
        assert text in SAFETY_TEXT


def test_common_safety_module_classifies_phase4a_material_commands() -> None:
    for text in [
        '"get_material_channel_schema", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_supported_material_templates", OperationType.OBSERVE, RiskLevel.LOW',
        '"list_materials_deep", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_material_deep_info", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_shader_graph", OperationType.SHADER, RiskLevel.LOW',
        '"create_material_from_template", OperationType.MATERIAL, RiskLevel.MEDIUM',
        '"create_custom_material", OperationType.MATERIAL, RiskLevel.MEDIUM',
        '"create_procedural_material", OperationType.MATERIAL, RiskLevel.MEDIUM',
        '"bind_material_texture_map", OperationType.TEXTURE, RiskLevel.MEDIUM',
        '"run_material_workflow_batch", OperationType.MATERIAL, RiskLevel.MEDIUM',
        '"remove_material_node", OperationType.SHADER, RiskLevel.HIGH',
        '"delete_materials", OperationType.CLEANUP, RiskLevel.HIGH',
    ]:
        assert text in SAFETY_TEXT


def test_phase4a_destructive_material_commands_are_strict_blocked() -> None:
    for command in ["remove_material_node", "delete_materials"]:
        command_index = SAFETY_TEXT.index(f'"{command}"')
        command_block = SAFETY_TEXT[command_index:command_index + 500]
        assert "strict_blocked=True" in command_block


def test_common_safety_module_classifies_phase4b_deformation_commands() -> None:
    for text in [
        '"get_selection_deep_info", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_mesh_component_summary", OperationType.OBSERVE, RiskLevel.LOW',
        '"list_vertex_groups", OperationType.OBSERVE, RiskLevel.LOW',
        '"list_shape_keys", OperationType.OBSERVE, RiskLevel.LOW',
        '"create_vertex_group", OperationType.SELECT_REGION, RiskLevel.MEDIUM',
        '"update_vertex_group_weights", OperationType.SELECT_REGION, RiskLevel.MEDIUM',
        '"create_shape_key", OperationType.DEFORM, RiskLevel.MEDIUM',
        '"update_shape_key_value", OperationType.DEFORM, RiskLevel.MEDIUM',
        '"create_lattice_deformer", OperationType.DEFORM, RiskLevel.MEDIUM',
        '"apply_lattice_to_object", OperationType.DEFORM, RiskLevel.MEDIUM',
        '"add_deformation_modifier", OperationType.DEFORM, RiskLevel.MEDIUM',
        '"update_deformation_modifier", OperationType.DEFORM, RiskLevel.MEDIUM',
        '"create_region_deformation", OperationType.DEFORM, RiskLevel.MEDIUM',
        '"run_deformation_workflow_batch", OperationType.DEFORM, RiskLevel.MEDIUM',
        '"edit_shape_key_offsets", OperationType.DEFORM, RiskLevel.HIGH',
        '"update_lattice_deformer", OperationType.DEFORM, RiskLevel.HIGH',
        '"delete_vertex_groups", OperationType.CLEANUP, RiskLevel.HIGH',
        '"delete_shape_keys", OperationType.CLEANUP, RiskLevel.HIGH',
        '"remove_lattice_deformer", OperationType.CLEANUP, RiskLevel.HIGH',
        '"get_method_plan", OperationType.PLAN, RiskLevel.LOW',
        '"list_operation_playbooks", OperationType.PLAN, RiskLevel.LOW',
        '"get_tricks_knowledge_base", OperationType.PLAN, RiskLevel.LOW',
        '"get_anti_pattern_rules", OperationType.PLAN, RiskLevel.LOW',
        '"score_selection_confidence", OperationType.SELECT_REGION, RiskLevel.LOW',
        '"scan_blender_asset_libraries", OperationType.ASSET_LIBRARY, RiskLevel.LOW',
        '"preview_asset", OperationType.VERIFY, RiskLevel.MEDIUM',
        '"import_texture_folder", OperationType.TEXTURE, RiskLevel.MEDIUM',
        '"create_style_material", OperationType.MATERIAL, RiskLevel.MEDIUM',
        '"create_paintable_texture", OperationType.TEXTURE, RiskLevel.MEDIUM',
        '"list_uv_maps", OperationType.OBSERVE, RiskLevel.LOW',
        '"measure_object", OperationType.VERIFY, RiskLevel.LOW',
        '"measure_distance", OperationType.VERIFY, RiskLevel.LOW',
        '"create_proportional_deformation", OperationType.DEFORM, RiskLevel.MEDIUM',
        '"get_sculpt_status", OperationType.SCULPT, RiskLevel.LOW',
        '"create_vertex_group_from_uv_island", OperationType.SELECT_REGION, RiskLevel.HIGH',
        '"configure_sculpt_brush", OperationType.SCULPT, RiskLevel.HIGH',
        '"create_sculpt_mask_from_vertex_group", OperationType.SCULPT, RiskLevel.HIGH',
        '"run_shape_key_sculpt_workflow", OperationType.SCULPT, RiskLevel.HIGH',
        '"delete_images", OperationType.CLEANUP, RiskLevel.HIGH',
    ]:
        assert text in SAFETY_TEXT


def test_phase4b_high_risk_commands_are_strict_blocked() -> None:
    for command in ["edit_shape_key_offsets", "update_lattice_deformer", "delete_vertex_groups", "delete_shape_keys", "remove_lattice_deformer", "create_vertex_group_from_uv_island", "configure_sculpt_brush", "create_sculpt_mask_from_vertex_group", "run_shape_key_sculpt_workflow", "delete_images"]:
        command_index = SAFETY_TEXT.index(f'"{command}"')
        command_block = SAFETY_TEXT[command_index:command_index + 500]
        assert "strict_blocked=True" in command_block


def test_common_safety_module_classifies_phase6b_commands() -> None:
    for text in [
        '"get_addon_management_status", OperationType.INSTALL_ADDON, RiskLevel.LOW',
        '"list_blender_addons", OperationType.INSTALL_ADDON, RiskLevel.LOW',
        '"get_blender_addon_info", OperationType.INSTALL_ADDON, RiskLevel.LOW',
        '"inspect_blender_api_docs", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW',
        '"search_blender_api_docs", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW',
        '"get_blender_api_topic", OperationType.UPDATE_KNOWLEDGE, RiskLevel.LOW',
        '"create_addon_skeleton", OperationType.INSTALL_ADDON, RiskLevel.MEDIUM',
        '"validate_addon_skeleton", OperationType.VERIFY, RiskLevel.MEDIUM',
        '"package_addon_zip", OperationType.EXPORT, RiskLevel.MEDIUM',
        '"build_blender_api_index", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM',
        '"create_verified_snippet", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM',
        '"create_skill_pack", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM',
        '"export_project_review_package", OperationType.EXPORT, RiskLevel.MEDIUM',
        '"install_local_addon", OperationType.INSTALL_ADDON, RiskLevel.HIGH',
        '"enable_blender_addon", OperationType.INSTALL_ADDON, RiskLevel.HIGH',
        '"disable_blender_addon", OperationType.INSTALL_ADDON, RiskLevel.HIGH',
        '"remove_blender_addon", OperationType.CLEANUP, RiskLevel.HIGH',
        '"run_verified_snippet_smoke", OperationType.UPDATE_KNOWLEDGE, RiskLevel.HIGH',
        '"delete_verified_snippets", OperationType.CLEANUP, RiskLevel.HIGH',
        '"run_skill_pack", OperationType.UPDATE_KNOWLEDGE, RiskLevel.HIGH',
        '"delete_skill_packs", OperationType.CLEANUP, RiskLevel.HIGH',
    ]:
        assert text in SAFETY_TEXT


def test_phase6b_high_risk_commands_are_strict_blocked() -> None:
    for command in ["install_local_addon", "enable_blender_addon", "disable_blender_addon", "remove_blender_addon", "run_verified_snippet_smoke", "delete_verified_snippets", "run_skill_pack", "delete_skill_packs"]:
        command_index = SAFETY_TEXT.index(f'"{command}"')
        command_block = SAFETY_TEXT[command_index:command_index + 600]
        assert "strict_blocked=True" in command_block


def test_smoke_script_exposes_safety_mode_flags() -> None:
    for text in [
        "--include-safety-status",
        "--expect-strict-blocks",
        "run_optional_safety_status_smoke",
        "run_optional_strict_block_smoke",
        "execute_code",
        "get_safety_status",
    ]:
        assert text in SMOKE_TEXT

