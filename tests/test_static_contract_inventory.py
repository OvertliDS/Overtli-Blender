from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER_TEXT = (ROOT / "src/overtli_blender/server.py").read_text(encoding="utf-8")
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
CONTEXT_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/context_tools.py").read_text(encoding="utf-8")
COLLECTION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/collection_tools.py").read_text(encoding="utf-8")
OBSERVATION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/observation_tools.py").read_text(encoding="utf-8")
MATERIAL_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/material_tools.py").read_text(encoding="utf-8")
MATERIAL_INTELLIGENCE_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/material_intelligence_tools.py").read_text(encoding="utf-8")
ADVANCED_MATERIAL_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/advanced_material_tools.py").read_text(encoding="utf-8")
SHADER_GRAPH_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/shader_graph_tools.py").read_text(encoding="utf-8")
MATERIAL_TEXTURE_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/material_texture_tools.py").read_text(encoding="utf-8")
MATERIAL_PREVIEW_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/material_preview_tools.py").read_text(encoding="utf-8")
MODIFIER_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/modifier_tools.py").read_text(encoding="utf-8")
SCREENSHOT_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/screenshot_tools.py").read_text(encoding="utf-8")
SCENE_EDIT_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/scene_edit_tools.py").read_text(encoding="utf-8")
SCENE_INTELLIGENCE_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/scene_intelligence_tools.py").read_text(encoding="utf-8")
VERIFICATION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/verification_tools.py").read_text(encoding="utf-8")
WORKSPACE_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/workspace_tools.py").read_text(encoding="utf-8")
SCRIPT_REGISTRY_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/script_registry_tools.py").read_text(encoding="utf-8")
CODE_EXECUTION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/code_execution_tools.py").read_text(encoding="utf-8")
REGISTRY_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/registry.py").read_text(encoding="utf-8")
PROVIDER_STATUS_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/provider_status_tools.py").read_text(encoding="utf-8")
POLYHAVEN_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/polyhaven_tools.py").read_text(encoding="utf-8")
SKETCHFAB_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/sketchfab_tools.py").read_text(encoding="utf-8")
HYPER3D_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/hyper3d_tools.py").read_text(encoding="utf-8")
GEOMETRY_NODES_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/geometry_nodes_tools.py").read_text(encoding="utf-8")


def _has_def(source: str, name: str) -> bool:
    pattern = rf"^\s*def\s+{re.escape(name)}\s*\("
    return re.search(pattern, source, flags=re.MULTILINE) is not None


def test_server_static_surface_includes_expected_wrappers() -> None:
    expected = [
    ]

    missing = [name for name in expected if not _has_def(SERVER_TEXT, name)]
    assert missing == [], f"Missing server wrappers: {missing}"


def test_server_no_longer_defines_execute_blender_code() -> None:
    assert not _has_def(SERVER_TEXT, "execute_blender_code")


def test_observation_tool_module_includes_extracted_wrappers() -> None:
    observation_text = (ROOT / "src/overtli_blender/tools/observation_tools.py").read_text(encoding="utf-8")
    expected = [
        "get_scene_info",
        "get_object_info",
    ]

    missing = [name for name in expected if f"def {name}(" not in observation_text]
    assert missing == [], f"Missing extracted observation tools: {missing}"


def test_screenshot_tool_module_includes_extracted_wrapper() -> None:
    screenshot_text = (ROOT / "src/overtli_blender/tools/screenshot_tools.py").read_text(encoding="utf-8")
    assert "def get_viewport_screenshot(" in screenshot_text


def test_scene_intelligence_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "get_scene_index",
        "get_object_deep_info",
        "get_selection_info",
        "get_scene_health",
    ]

    missing = [name for name in expected if f"def {name}(" not in SCENE_INTELLIGENCE_TOOLS_TEXT]
    assert missing == [], f"Missing extracted scene intelligence tools: {missing}"


def test_verification_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "capture_viewport_pack",
        "create_verification_snapshot",
        "list_verification_snapshots",
    ]

    missing = [name for name in expected if f"def {name}(" not in VERIFICATION_TOOLS_TEXT]
    assert missing == [], f"Missing extracted verification tools: {missing}"


def test_script_registry_tool_module_includes_extracted_wrappers() -> None:
    script_registry_text = (ROOT / "src/overtli_blender/tools/script_registry_tools.py").read_text(encoding="utf-8")
    expected = [
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "clear_context_scripts",
    ]

    missing = [name for name in expected if f"def {name}(" not in script_registry_text]
    assert missing == [], f"Missing extracted script registry tools: {missing}"


def test_code_execution_tool_module_includes_extracted_wrapper() -> None:
    assert "def register_code_execution_tools" in CODE_EXECUTION_TOOLS_TEXT
    assert "def execute_blender_code(" in CODE_EXECUTION_TOOLS_TEXT
    assert '"execute_code"' in CODE_EXECUTION_TOOLS_TEXT


def test_registry_tool_module_includes_all_registrations() -> None:
    assert "def register_all_tools" in REGISTRY_TOOLS_TEXT
    for name in [
        "register_context_tools",
        "register_observation_tools",
        "register_scene_intelligence_tools",
        "register_scene_edit_tools",
        "register_material_tools",
        "register_material_intelligence_tools",
        "register_advanced_material_tools",
        "register_shader_graph_tools",
        "register_material_texture_tools",
        "register_material_preview_tools",
        "register_modifier_tools",
        "register_collection_tools",
        "register_workspace_tools",
        "register_screenshot_tools",
        "register_verification_tools",
        "register_script_registry_tools",
        "register_provider_status_tools",
        "register_safety_tools",
        "register_polyhaven_tools",
        "register_sketchfab_tools",
        "register_hyper3d_tools",
        "register_geometry_nodes_tools",
        "register_code_execution_tools",
    ]:
        assert name in REGISTRY_TOOLS_TEXT


def test_provider_status_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
    ]

    missing = [name for name in expected if f"def {name}(" not in PROVIDER_STATUS_TOOLS_TEXT]
    assert missing == [], f"Missing extracted provider status tools: {missing}"


def test_polyhaven_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "get_polyhaven_categories",
        "search_polyhaven_assets",
        "download_polyhaven_asset",
        "set_texture",
    ]

    missing = [name for name in expected if f"def {name}(" not in POLYHAVEN_TOOLS_TEXT]
    assert missing == [], f"Missing extracted PolyHaven tools: {missing}"


def test_sketchfab_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "search_sketchfab_models",
        "download_sketchfab_model",
    ]

    missing = [name for name in expected if f"def {name}(" not in SKETCHFAB_TOOLS_TEXT]
    assert missing == [], f"Missing extracted Sketchfab tools: {missing}"


def test_hyper3d_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "generate_hyper3d_model_via_text",
        "generate_hyper3d_model_via_images",
        "poll_rodin_job_status",
        "import_generated_asset",
    ]

    missing = [name for name in expected if f"def {name}(" not in HYPER3D_TOOLS_TEXT]
    assert missing == [], f"Missing extracted Hyper3D tools: {missing}"


def test_geometry_nodes_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "complete_geometry_node",
        "get_geometry_nodes_status",
    ]

    missing = [name for name in expected if f"def {name}(" not in GEOMETRY_NODES_TOOLS_TEXT]
    assert missing == [], f"Missing extracted geometry nodes tools: {missing}"


def test_phase3_tool_modules_include_extracted_wrappers() -> None:
    expected = {
        SCENE_EDIT_TOOLS_TEXT: ["get_supported_edit_operations", "create_primitive_object", "transform_object", "duplicate_object", "delete_objects", "set_object_visibility", "run_verified_edit_batch"],
        MATERIAL_TOOLS_TEXT: ["create_basic_material", "assign_material", "update_material_properties"],
        MODIFIER_TOOLS_TEXT: ["add_object_modifier", "update_object_modifier", "remove_object_modifier"],
        COLLECTION_TOOLS_TEXT: ["create_collection", "move_objects_to_collection", "delete_collection"],
        WORKSPACE_TOOLS_TEXT: ["get_task_workspace", "create_workspace_task", "add_workspace_todo", "record_operation_journal_entry", "create_scene_snapshot", "diff_scene_snapshots", "rollback_to_scene_snapshot"],
    }
    for source, names in expected.items():
        missing = [name for name in names if f"def {name}(" not in source]
        assert missing == [], f"Missing Phase 3 tools: {missing}"


def test_phase4a_tool_modules_include_wrappers() -> None:
    expected = {
        MATERIAL_INTELLIGENCE_TOOLS_TEXT: ["get_material_channel_schema", "get_supported_material_templates", "list_materials_deep", "get_material_deep_info"],
        ADVANCED_MATERIAL_TOOLS_TEXT: ["create_material_from_template", "create_custom_material", "create_procedural_material", "create_material_variant", "apply_material_to_objects", "run_material_workflow_batch", "delete_materials"],
        SHADER_GRAPH_TOOLS_TEXT: ["get_shader_graph", "set_material_node_input", "add_material_node", "connect_material_nodes", "remove_material_node"],
        MATERIAL_TEXTURE_TOOLS_TEXT: ["bind_material_texture_map"],
        MATERIAL_PREVIEW_TOOLS_TEXT: ["create_material_preview"],
    }
    for source, names in expected.items():
        missing = [name for name in names if f"def {name}(" not in source]
        assert missing == [], f"Missing Phase 4A tools: {missing}"


def test_context_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
    ]

    missing = [name for name in expected if f"def {name}(" not in CONTEXT_TOOLS_TEXT]
    assert missing == [], f"Missing extracted context tools: {missing}"


def test_addon_static_surface_includes_dispatch_helpers() -> None:
    for name in [
        "def _build_command_handlers(",
        "def _dispatch_command(",
    ]:
        assert name in ADDON_TEXT


def test_addon_static_surface_includes_internal_service_classes() -> None:
    for name in [
        "class SharedContextService",
        "class ScriptRegistryService",
        "class SceneObservationService",
        "class ViewportScreenshotService",
        "class SceneIntelligenceService",
        "class VerificationArtifactService",
        "class SceneEditService",
        "class MaterialAuthoringService",
        "class ModifierService",
        "class CollectionOrganizationService",
        "class VerifiedEditBatchService",
        "class WorkspaceSafetyDiffService",
        "class ProviderStatusService",
        "class PolyHavenService",
        "class SketchfabService",
        "class Hyper3DService",
        "class SafetyPolicyService",
        "class RawCodeExecutionService",
        "class GeometryNodesService",
        "self.shared_context_service = SharedContextService(self.shared_context)",
        "self.script_registry_service = ScriptRegistryService()",
        "self.scene_observation_service = SceneObservationService(self)",
        "self.viewport_screenshot_service = ViewportScreenshotService(self)",
        "self.scene_intelligence_service = SceneIntelligenceService(self)",
        "self.verification_artifact_service = VerificationArtifactService(self)",
        "self.scene_edit_service = SceneEditService(self)",
        "self.material_authoring_service = MaterialAuthoringService(self)",
        "self.modifier_service = ModifierService(self)",
        "self.collection_organization_service = CollectionOrganizationService(self)",
        "self.verified_edit_batch_service = VerifiedEditBatchService(self)",
        "self.workspace_safety_diff_service = WorkspaceSafetyDiffService(self)",
        "self.provider_status_service = ProviderStatusService(self)",
        "self.polyhaven_service = PolyHavenService(self)",
        "self.sketchfab_service = SketchfabService(self)",
        "self.hyper3d_service = Hyper3DService(self)",
        "self.safety_policy_service = SafetyPolicyService(self)",
        "self.raw_code_execution_service = RawCodeExecutionService(self)",
        "self.geometry_nodes_service = GeometryNodesService(self)",
        "self.get_safety_status = self.safety_policy_service.get_safety_status",
        "self.execute_code = self.raw_code_execution_service.execute_code",
        "self.complete_geometry_node = self.geometry_nodes_service.complete_geometry_node",
        "self.get_geometry_nodes_status = self.geometry_nodes_service.get_geometry_nodes_status",
    ]:
        assert name in ADDON_TEXT


def test_addon_static_surface_includes_expected_commands() -> None:
    expected = [
        "get_scene_info",
        "get_object_info",
        "get_viewport_screenshot",
        "get_scene_index",
        "get_object_deep_info",
        "get_selection_info",
        "get_scene_health",
        "capture_viewport_pack",
        "create_verification_snapshot",
        "list_verification_snapshots",
        "get_supported_edit_operations",
        "create_primitive_object",
        "transform_object",
        "duplicate_object",
        "delete_objects",
        "set_object_visibility",
        "create_basic_material",
        "assign_material",
        "update_material_properties",
        "add_object_modifier",
        "update_object_modifier",
        "remove_object_modifier",
        "create_collection",
        "move_objects_to_collection",
        "delete_collection",
        "run_verified_edit_batch",
        "get_task_workspace",
        "create_workspace_task",
        "update_workspace_task",
        "list_workspace_tasks",
        "add_workspace_todo",
        "update_workspace_todo",
        "list_workspace_todos",
        "record_operation_journal_entry",
        "get_operation_journal",
        "create_scene_snapshot",
        "list_scene_snapshots",
        "diff_scene_snapshots",
        "detect_user_changes",
        "rollback_to_scene_snapshot",
        "undo_last_blender_operation",
        "get_safety_status",
        "execute_code",
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
        "get_polyhaven_categories",
        "search_polyhaven_assets",
        "download_polyhaven_asset",
        "set_texture",
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
        "search_sketchfab_models",
        "download_sketchfab_model",
        "poll_rodin_job_status",
        "import_generated_asset",
        "complete_geometry_node",
        "get_geometry_nodes_status",
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "clear_context_scripts",
    ]

    missing = [name for name in expected if f'"{name}":' not in ADDON_TEXT and f"'{name}':" not in ADDON_TEXT]
    assert missing == [], f"Missing addon command strings: {missing}"


def test_documented_mapping_differences_are_present_in_source() -> None:
    assert '"execute_code": self.execute_code' in ADDON_TEXT
    assert "create_rodin_job" in ADDON_TEXT
    assert not _has_def(SERVER_TEXT, "generate_hyper3d_model_via_text")
    assert not _has_def(SERVER_TEXT, "generate_hyper3d_model_via_images")
    assert "blendermcp_use_polyhaven" in ADDON_TEXT

