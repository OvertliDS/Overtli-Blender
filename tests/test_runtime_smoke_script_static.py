from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE_TEXT = (ROOT / "scripts" / "smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_runtime_smoke_script_exists() -> None:
    assert (ROOT / "scripts" / "smoke_blender_addon_socket.py").is_file()


def test_runtime_smoke_script_uses_standard_library_only() -> None:
    assert "import argparse" in SMOKE_TEXT
    assert "import json" in SMOKE_TEXT
    assert "import socket" in SMOKE_TEXT
    assert "import sys" in SMOKE_TEXT
    assert "import time" in SMOKE_TEXT
    assert "import bpy" not in SMOKE_TEXT
    assert "subprocess" not in SMOKE_TEXT
    assert "os.system" not in SMOKE_TEXT
    assert "shutil.rmtree" not in SMOKE_TEXT


def test_runtime_smoke_script_has_expected_defaults_and_entrypoint() -> None:
    for text in [
        'DEFAULT_HOST = "localhost"',
        "DEFAULT_PORT = 9876",
        "def main(",
        "return 1",
        "return 0",
        "raise SystemExit(main())",
    ]:
        assert text in SMOKE_TEXT


def test_runtime_smoke_script_mentions_expected_commands_and_flags() -> None:
    for text in [
        "get_scene_info",
        "get_shared_context",
        "get_operation_history",
        "list_object_handles",
        "list_material_handles",
        "list_context_scripts",
        "execute_code",
        "get_geometry_nodes_status",
        "get_safety_status",
        "get_scene_index",
        "get_object_deep_info",
        "get_selection_info",
        "get_scene_health",
        "capture_viewport_pack",
        "create_verification_snapshot",
        "--include-screenshot",
        "--include-script-registry",
        "--include-provider-status",
        "--include-safety-status",
        "--include-scene-index",
        "--include-object-deep-info",
        "--include-selection-info",
        "--include-scene-health",
        "--include-screenshot-pack",
        "--include-verification-snapshot",
        "--include-edit-ops",
        "--include-material-ops",
        "--include-modifier-ops",
        "--include-collection-ops",
        "--include-verified-edit-batch",
        "--include-workspace-safety-diff",
        "--include-material-intelligence",
        "--include-material-channel-schema",
        "--include-material-templates",
        "--include-procedural-material",
        "--include-custom-material",
        "--include-texture-map-slots",
        "--include-shader-graph",
        "--include-material-preview",
        "--include-material-workflow-batch",
        "--include-selection-deep-info",
        "--include-vertex-group-ops",
        "--include-shape-key-ops",
        "--include-lattice-ops",
        "--include-deformation-modifier-ops",
        "--include-region-deformation",
        "--include-deformation-workflow-batch",
        "--phase2-full",
        "--phase3-full",
        "--phase4a-full",
        "--phase4b-full",
        "--phase5a-full",
        "--include-asset-formats",
        "--include-asset-scan",
        "--include-scene-assets",
        "--include-dependency-report",
        "--include-asset-manifest",
        "--include-import-export",
        "--include-scene-kit",
        "--include-asset-preview",
        "--include-asset-workflow-batch",
        "--phase5b-full",
        "--include-geometry-nodes-status",
        "--include-code-execution",
        "--expect-strict-blocks",
    ]:
        assert text in SMOKE_TEXT


def test_runtime_smoke_phase2_full_avoids_dangerous_optional_flows() -> None:
    phase2_start = SMOKE_TEXT.index("def run_phase2_full_smoke")
    phase2_end = SMOKE_TEXT.index("def run_optional_strict_block_smoke")
    phase2_block = SMOKE_TEXT[phase2_start:phase2_end]
    for text in [
        "run_optional_scene_index_smoke",
        "run_optional_selection_info_smoke",
        "run_optional_scene_health_smoke",
        "run_optional_object_deep_info_smoke",
        "run_optional_screenshot_pack_smoke",
        "run_optional_verification_snapshot_smoke",
    ]:
        assert text in phase2_block
    for text in [
        "run_optional_code_execution_smoke",
        "run_optional_script_registry_smoke",
        "run_optional_provider_status_smoke",
        "run_optional_geometry_nodes_status_smoke",
    ]:
        assert text not in phase2_block


def test_runtime_smoke_phase3_full_avoids_forbidden_commands() -> None:
    phase3_start = SMOKE_TEXT.index("def run_phase3_full_smoke")
    phase3_end = SMOKE_TEXT.index("def run_optional_material_ops_smoke")
    phase3_block = SMOKE_TEXT[phase3_start:phase3_end]
    for text in [
        "OVERTLI_PHASE3_SMOKE_",
        "OVERTLI_PHASE3_CUBE_",
        "OVERTLI_PHASE3_MAT_",
        "delete_objects",
        "delete_collection",
        "run_phase3_workspace_safety_diff_smoke",
        '"confirm": True',
    ]:
        assert text in phase3_block
    for text in [
        "execute_code",
        "download_polyhaven_asset",
        "download_sketchfab_model",
        "create_rodin_job",
    ]:
        assert text not in phase3_block


def test_runtime_smoke_phase4a_full_cleans_up_and_avoids_forbidden_commands() -> None:
    phase4a_start = SMOKE_TEXT.index("def run_phase4a_full_smoke")
    phase4a_end = SMOKE_TEXT.index("def run_phase4b_full_smoke")
    phase4a_block = SMOKE_TEXT[phase4a_start:phase4a_end]
    for text in [
        "OVERTLI_PHASE4A_SMOKE_",
        "OVERTLI_PHASE4A_CUBE_",
        "OVERTLI_PHASE4A_GOLD_",
        "run_optional_material_channel_schema_smoke",
        "run_optional_material_templates_smoke",
        "get_shader_graph",
        "bind_material_texture_map",
        "create_material_preview",
        "run_material_workflow_batch",
        "delete_materials",
        "delete_collection",
        "delete_objects",
        "bind_material_texture_map should reject missing strict file",
    ]:
        assert text in phase4a_block
    for text in [
        "execute_code",
        "download_polyhaven_asset",
        "download_sketchfab_model",
        "create_rodin_job",
    ]:
        assert text not in phase4a_block


def test_runtime_smoke_phase4b_full_cleans_up_and_avoids_forbidden_commands() -> None:
    phase4b_start = SMOKE_TEXT.index("def run_phase4b_full_smoke")
    phase4b_end = SMOKE_TEXT.index("def run_optional_modifier_ops_smoke")
    phase4b_block = SMOKE_TEXT[phase4b_start:phase4b_end]
    for text in [
        "OVERTLI_PHASE4B_SMOKE_",
        "OVERTLI_PHASE4B_MESH_",
        "OVERTLI_PHASE4B_MAT_",
        "OVERTLI_PHASE4B_TOP_",
        "OVERTLI_PHASE4B_SHAPE_",
        "OVERTLI_PHASE4B_LATTICE_",
        "get_selection_deep_info",
        "get_mesh_component_summary",
        "get_method_plan",
        "list_operation_playbooks",
        "get_tricks_knowledge_base",
        "get_anti_pattern_rules",
        "get_modifier_recipes",
        "score_selection_confidence",
        "scan_blender_asset_libraries",
        "preview_asset",
        "create_style_material",
        "create_paintable_texture",
        "delete_images",
        "list_uv_maps",
        "measure_object",
        "create_proportional_deformation",
        "get_sculpt_status",
        "create_sculpt_mask_from_vertex_group",
        "run_shape_key_sculpt_workflow",
        "create_vertex_group",
        "edit_shape_key_offsets",
        "create_lattice_deformer",
        "update_lattice_deformer",
        "add_deformation_modifier",
        "create_region_deformation",
        "run_deformation_workflow_batch",
        "delete_vertex_groups",
        "delete_shape_keys",
        "remove_lattice_deformer",
        "delete_objects",
        "delete_materials",
        "delete_collection",
        '"confirm": True',
    ]:
        assert text in phase4b_block
    for text in [
        "execute_code",
        "download_polyhaven_asset",
        "download_sketchfab_model",
        "create_rodin_job",
    ]:
        assert text not in phase4b_block


def test_runtime_smoke_phase5b_full_cleans_up_and_avoids_forbidden_commands() -> None:
    phase5b_start = SMOKE_TEXT.index("def run_phase5b_full_smoke")
    phase5b_end = SMOKE_TEXT.index("def build_parser")
    phase5b_block = SMOKE_TEXT[phase5b_start:phase5b_end]
    for text in [
        "OVERTLI_PHASE5B_",
        ".overtli_blender",
        "exports",
        "scene_kits",
        "get_supported_asset_formats",
        "scan_asset_folder",
        "list_scene_assets",
        "get_asset_dependency_report",
        "create_asset_manifest",
        "create_asset_preview",
        "export_selected_objects",
        "import_model_file",
        "create_scene_kit",
        "validate_scene_kit",
        "run_asset_workflow_batch",
        "cleanup_asset_artifacts",
        '"confirm": True',
    ]:
        assert text in phase5b_block
    for text in [
        "execute_code",
        "download_polyhaven_asset",
        "download_sketchfab_model",
        "create_rodin_job",
    ]:
        assert text not in phase5b_block
