from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/context_tools.py").read_text(encoding="utf-8")
COLLECTION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/collection_tools.py").read_text(encoding="utf-8")
DEFORMATION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/deformation_tools.py").read_text(encoding="utf-8")
OBSERVATION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/observation_tools.py").read_text(encoding="utf-8")
LATTICE_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/lattice_tools.py").read_text(encoding="utf-8")
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
SELECTION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/selection_tools.py").read_text(encoding="utf-8")
SHAPE_KEY_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/shape_key_tools.py").read_text(encoding="utf-8")
VERIFICATION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/verification_tools.py").read_text(encoding="utf-8")
VERTEX_GROUP_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/vertex_group_tools.py").read_text(encoding="utf-8")
WORKFLOW_INTELLIGENCE_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/workflow_intelligence_tools.py").read_text(encoding="utf-8")
WORKSPACE_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/workspace_tools.py").read_text(encoding="utf-8")
SCRIPT_REGISTRY_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/script_registry_tools.py").read_text(encoding="utf-8")
CODE_EXECUTION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/code_execution_tools.py").read_text(encoding="utf-8")
REGISTRY_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/registry.py").read_text(encoding="utf-8")
SAFETY_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/safety_tools.py").read_text(encoding="utf-8")
PROVIDER_STATUS_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/provider_status_tools.py").read_text(encoding="utf-8")
POLYHAVEN_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/polyhaven_tools.py").read_text(encoding="utf-8")
SKETCHFAB_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/sketchfab_tools.py").read_text(encoding="utf-8")
HYPER3D_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/hyper3d_tools.py").read_text(encoding="utf-8")
GEOMETRY_NODES_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/geometry_nodes_tools.py").read_text(encoding="utf-8")
SERVER_TEXT = (ROOT / "src/overtli_blender/server.py").read_text(encoding="utf-8")
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")


def test_context_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/context_tools.py").exists()
    assert "def register_context_tools" in CONTEXT_TOOLS_TEXT


def test_context_tools_contains_expected_tool_names() -> None:
    for name in [
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
    ]:
        assert f"def {name}(" in CONTEXT_TOOLS_TEXT


def test_observation_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/observation_tools.py").exists()
    assert "def register_observation_tools" in OBSERVATION_TOOLS_TEXT


def test_observation_tools_contains_expected_tool_names() -> None:
    for name in [
        "get_scene_info",
        "get_object_info",
    ]:
        assert f"def {name}(" in OBSERVATION_TOOLS_TEXT


def test_screenshot_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/screenshot_tools.py").exists()
    assert "def register_screenshot_tools" in SCREENSHOT_TOOLS_TEXT


def test_screenshot_tools_contains_expected_tool_name() -> None:
    assert "def get_viewport_screenshot(" in SCREENSHOT_TOOLS_TEXT


def test_scene_intelligence_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/scene_intelligence_tools.py").exists()
    assert "def register_scene_intelligence_tools" in SCENE_INTELLIGENCE_TOOLS_TEXT


def test_scene_intelligence_tools_contains_expected_tool_names() -> None:
    for name in [
        "get_scene_index",
        "get_object_deep_info",
        "get_selection_info",
        "get_scene_health",
    ]:
        assert f"def {name}(" in SCENE_INTELLIGENCE_TOOLS_TEXT


def test_verification_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/verification_tools.py").exists()
    assert "def register_verification_tools" in VERIFICATION_TOOLS_TEXT


def test_verification_tools_contains_expected_tool_names() -> None:
    for name in [
        "capture_viewport_pack",
        "create_verification_snapshot",
        "list_verification_snapshots",
    ]:
        assert f"def {name}(" in VERIFICATION_TOOLS_TEXT


def test_script_registry_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/script_registry_tools.py").exists()
    assert "def register_script_registry_tools" in SCRIPT_REGISTRY_TOOLS_TEXT


def test_script_registry_tools_contains_expected_tool_names() -> None:
    for name in [
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "clear_context_scripts",
    ]:
        assert f"def {name}(" in SCRIPT_REGISTRY_TOOLS_TEXT


def test_code_execution_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/code_execution_tools.py").exists()
    assert "def register_code_execution_tools" in CODE_EXECUTION_TOOLS_TEXT


def test_code_execution_tools_contains_expected_tool_name() -> None:
    assert "def execute_blender_code(" in CODE_EXECUTION_TOOLS_TEXT
    assert '"execute_code"' in CODE_EXECUTION_TOOLS_TEXT


def test_registry_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/registry.py").exists()
    assert "def register_all_tools" in REGISTRY_TOOLS_TEXT


def test_registry_module_references_all_tool_registration_helpers() -> None:
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
        "register_selection_tools",
        "register_vertex_group_tools",
        "register_shape_key_tools",
        "register_lattice_tools",
        "register_deformation_tools",
        "register_workflow_intelligence_tools",
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


def test_provider_status_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/provider_status_tools.py").exists()
    assert "def register_provider_status_tools" in PROVIDER_STATUS_TOOLS_TEXT


def test_provider_status_tools_contains_expected_tool_names() -> None:
    for name in [
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
    ]:
        assert f"def {name}(" in PROVIDER_STATUS_TOOLS_TEXT


def test_safety_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/safety_tools.py").exists()
    assert "def register_safety_tools" in SAFETY_TOOLS_TEXT


def test_safety_tools_contains_expected_tool_name() -> None:
    assert "def get_safety_status(" in SAFETY_TOOLS_TEXT


def test_polyhaven_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/polyhaven_tools.py").exists()
    assert "def register_polyhaven_tools" in POLYHAVEN_TOOLS_TEXT


def test_polyhaven_tools_contains_expected_tool_names() -> None:
    for name in [
        "get_polyhaven_categories",
        "search_polyhaven_assets",
        "download_polyhaven_asset",
        "set_texture",
    ]:
        assert f"def {name}(" in POLYHAVEN_TOOLS_TEXT


def test_sketchfab_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/sketchfab_tools.py").exists()
    assert "def register_sketchfab_tools" in SKETCHFAB_TOOLS_TEXT


def test_sketchfab_tools_contains_expected_tool_names() -> None:
    for name in [
        "search_sketchfab_models",
        "download_sketchfab_model",
    ]:
        assert f"def {name}(" in SKETCHFAB_TOOLS_TEXT


def test_hyper3d_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/hyper3d_tools.py").exists()
    assert "def register_hyper3d_tools" in HYPER3D_TOOLS_TEXT


def test_hyper3d_tools_contains_expected_tool_names() -> None:
    for name in [
        "generate_hyper3d_model_via_text",
        "generate_hyper3d_model_via_images",
        "poll_rodin_job_status",
        "import_generated_asset",
    ]:
        assert f"def {name}(" in HYPER3D_TOOLS_TEXT


def test_geometry_nodes_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/overtli_blender/tools/geometry_nodes_tools.py").exists()
    assert "def register_geometry_nodes_tools" in GEOMETRY_NODES_TOOLS_TEXT


def test_geometry_nodes_tools_contains_expected_tool_names() -> None:
    for name in [
        "complete_geometry_node",
        "get_geometry_nodes_status",
    ]:
        assert f"def {name}(" in GEOMETRY_NODES_TOOLS_TEXT


def test_phase3_tools_modules_exist_and_register_tools() -> None:
    for path, helper in [
        ("scene_edit_tools.py", "register_scene_edit_tools"),
        ("material_tools.py", "register_material_tools"),
        ("modifier_tools.py", "register_modifier_tools"),
        ("collection_tools.py", "register_collection_tools"),
        ("workspace_tools.py", "register_workspace_tools"),
    ]:
        text = (ROOT / f"src/overtli_blender/tools/{path}").read_text(encoding="utf-8")
        assert helper in text


def test_phase3_tools_contain_expected_tool_names() -> None:
    expected = {
        SCENE_EDIT_TOOLS_TEXT: ["get_supported_edit_operations", "create_primitive_object", "transform_object", "duplicate_object", "delete_objects", "set_object_visibility", "run_verified_edit_batch"],
        MATERIAL_TOOLS_TEXT: ["create_basic_material", "assign_material", "update_material_properties"],
        MODIFIER_TOOLS_TEXT: ["add_object_modifier", "update_object_modifier", "remove_object_modifier"],
        COLLECTION_TOOLS_TEXT: ["create_collection", "move_objects_to_collection", "delete_collection"],
        WORKSPACE_TOOLS_TEXT: ["get_task_workspace", "create_workspace_task", "add_workspace_todo", "record_operation_journal_entry", "create_scene_snapshot", "diff_scene_snapshots", "rollback_to_scene_snapshot"],
    }
    for source, names in expected.items():
        for name in names:
            assert f"def {name}(" in source


def test_phase4a_material_tool_modules_exist_and_register_tools() -> None:
    expected = {
        MATERIAL_INTELLIGENCE_TOOLS_TEXT: ["register_material_intelligence_tools", "get_material_channel_schema", "get_supported_material_templates", "list_materials_deep", "get_material_deep_info"],
        ADVANCED_MATERIAL_TOOLS_TEXT: ["register_advanced_material_tools", "create_material_from_template", "create_custom_material", "create_procedural_material", "create_material_variant", "apply_material_to_objects", "run_material_workflow_batch", "delete_materials"],
        SHADER_GRAPH_TOOLS_TEXT: ["register_shader_graph_tools", "get_shader_graph", "set_material_node_input", "add_material_node", "connect_material_nodes", "remove_material_node"],
        MATERIAL_TEXTURE_TOOLS_TEXT: ["register_material_texture_tools", "bind_material_texture_map"],
        MATERIAL_PREVIEW_TOOLS_TEXT: ["register_material_preview_tools", "create_material_preview"],
    }
    for source, names in expected.items():
        for name in names:
            assert f"def {name}(" in source or f"def {name}_" in source


def test_phase4b_tool_modules_exist_and_register_tools() -> None:
    expected = {
        SELECTION_TOOLS_TEXT: ["register_selection_tools", "get_selection_deep_info", "get_mesh_component_summary"],
        VERTEX_GROUP_TOOLS_TEXT: ["register_vertex_group_tools", "create_vertex_group", "update_vertex_group_weights", "list_vertex_groups", "delete_vertex_groups"],
        SHAPE_KEY_TOOLS_TEXT: ["register_shape_key_tools", "create_shape_key", "update_shape_key_value", "edit_shape_key_offsets", "list_shape_keys", "delete_shape_keys"],
        LATTICE_TOOLS_TEXT: ["register_lattice_tools", "create_lattice_deformer", "update_lattice_deformer", "apply_lattice_to_object", "remove_lattice_deformer"],
        DEFORMATION_TOOLS_TEXT: ["register_deformation_tools", "add_deformation_modifier", "update_deformation_modifier", "create_region_deformation", "run_deformation_workflow_batch"],
        WORKFLOW_INTELLIGENCE_TOOLS_TEXT: ["register_workflow_intelligence_tools", "get_method_plan", "list_operation_playbooks", "get_tricks_knowledge_base", "get_anti_pattern_rules", "get_modifier_recipes", "score_selection_confidence", "scan_blender_asset_libraries", "preview_asset", "import_texture_folder", "create_style_material", "create_paintable_texture", "delete_images", "list_uv_maps", "create_vertex_group_from_uv_island", "measure_object", "measure_distance", "create_proportional_deformation", "get_sculpt_status", "configure_sculpt_brush", "create_sculpt_mask_from_vertex_group", "run_shape_key_sculpt_workflow"],
    }
    for source, names in expected.items():
        for name in names:
            assert f"def {name}(" in source


def test_server_imports_and_registers_context_tools() -> None:
    assert "from overtli_blender.tools.registry import register_all_tools" in SERVER_TEXT
    assert "register_all_tools(mcp, get_blender_connection, image_type=Image)" in SERVER_TEXT


def test_server_no_longer_defines_execute_blender_code() -> None:
    assert "def execute_blender_code(" not in SERVER_TEXT


def test_server_still_contains_composition_root_bits() -> None:
    for name in [
        "FastMCP",
        "get_blender_connection",
        "main",
    ]:
        assert name in SERVER_TEXT


def test_phase6b_tool_modules_exist_and_register_tools() -> None:
    expected = {
        "addon_management_tools.py": ["register_addon_management_tools", "get_addon_management_status", "list_blender_addons", "install_local_addon", "remove_blender_addon"],
        "addon_development_tools.py": ["register_addon_development_tools", "create_addon_skeleton", "validate_addon_skeleton", "package_addon_zip"],
        "api_knowledge_tools.py": ["register_api_knowledge_tools", "inspect_blender_api_docs", "build_blender_api_index", "search_blender_api_docs", "get_blender_api_topic"],
        "snippet_library_tools.py": ["register_snippet_library_tools", "create_verified_snippet", "validate_verified_snippet", "run_verified_snippet_smoke", "delete_verified_snippets"],
        "skill_pack_tools.py": ["register_skill_pack_tools", "create_skill_pack", "validate_skill_pack", "run_skill_pack", "delete_skill_packs"],
        "review_package_tools.py": ["register_review_package_tools", "export_project_review_package", "validate_review_package"],
        "advanced_knowledge_workflow_tools.py": ["register_advanced_knowledge_workflow_tools", "run_advanced_knowledge_workflow_batch"],
    }
    for filename, names in expected.items():
        path = ROOT / f"src/overtli_blender/tools/{filename}"
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        for name in names:
            assert f"def {name}(" in text


def test_phase6b_registry_references_all_tool_helpers() -> None:
    for name in [
        "register_addon_management_tools",
        "register_addon_development_tools",
        "register_api_knowledge_tools",
        "register_snippet_library_tools",
        "register_skill_pack_tools",
        "register_review_package_tools",
        "register_advanced_knowledge_workflow_tools",
    ]:
        assert name in REGISTRY_TOOLS_TEXT


def test_addon_command_strings_are_still_present() -> None:
    for name in [
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
        "get_selection_deep_info",
        "get_mesh_component_summary",
        "create_vertex_group",
        "update_vertex_group_weights",
        "list_vertex_groups",
        "delete_vertex_groups",
        "create_shape_key",
        "update_shape_key_value",
        "edit_shape_key_offsets",
        "list_shape_keys",
        "delete_shape_keys",
        "create_lattice_deformer",
        "update_lattice_deformer",
        "apply_lattice_to_object",
        "remove_lattice_deformer",
        "add_deformation_modifier",
        "update_deformation_modifier",
        "create_region_deformation",
        "run_deformation_workflow_batch",
        "get_method_plan",
        "list_operation_playbooks",
        "get_tricks_knowledge_base",
        "get_anti_pattern_rules",
        "get_modifier_recipes",
        "score_selection_confidence",
        "scan_blender_asset_libraries",
        "preview_asset",
        "import_texture_folder",
        "create_style_material",
        "create_paintable_texture",
        "delete_images",
        "list_uv_maps",
        "create_vertex_group_from_uv_island",
        "measure_object",
        "measure_distance",
        "create_proportional_deformation",
        "get_sculpt_status",
        "configure_sculpt_brush",
        "create_sculpt_mask_from_vertex_group",
        "run_shape_key_sculpt_workflow",
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
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
        "execute_code",
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
    ]:
        assert f'"{name}":' in ADDON_TEXT or f"'{name}':" in ADDON_TEXT

