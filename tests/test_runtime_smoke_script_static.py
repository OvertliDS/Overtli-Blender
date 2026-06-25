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
        "--phase2-full",
        "--phase3-full",
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
