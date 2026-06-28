from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_cleanup_dimension_and_validation_commands_are_public_and_socket_bound() -> None:
    scene_tools = _read("src/overtli_blender/tools/scene_edit_tools.py")
    socket_server = _read("overtli_blender_addon/runtime/socket_server.py")
    server = _read("src/overtli_blender/server.py")

    for command in [
        "create_box",
        "transform_object_dimensions",
        "scene_cleanup_plan",
        "clear_scene",
        "validate_ground_contact",
        "align_object_to_surface",
        "validate_scene_composition",
    ]:
        assert f"def {command}" in scene_tools
        assert f'"{command}":' in socket_server

    for browser_visible_command in [
        "create_box",
        "transform_object_dimensions",
        "scene_cleanup_plan",
        "validate_ground_contact",
        "align_object_to_surface",
        "validate_scene_composition",
    ]:
        assert f'"{browser_visible_command}"' in server


def test_clear_scene_defaults_to_dry_run_and_confirmation_for_destructive_cleanup() -> None:
    assert "def clear_scene(" in ADDON_TEXT
    clear_scene_section = ADDON_TEXT[ADDON_TEXT.index("def clear_scene("):ADDON_TEXT.index("def scene_cleanup_plan(")]
    for expected in [
        'scope="prefix"',
        'prefix="OVERTLI_"',
        "dry_run=True",
        "confirm=False",
        "approval_required",
        "create_scene_snapshot",
        "requires_approval",
    ]:
        assert expected in clear_scene_section


def test_unsaved_artifacts_use_user_local_temp_workspace_not_addon_root() -> None:
    runtime_workspace = _read("src/overtli_blender/runtime/project_workspace.py")
    workspace_service = _read("overtli_blender_addon/services/workspace.py")
    verification_service = _read("overtli_blender_addon/services/verification.py")
    project_tools = _read("src/overtli_blender/tools/project_workspace_tools.py")

    for expected in [
        "def temp_workspace_root",
        "def initialize_temp_workspace",
        "def resolve_artifact_workspace",
        "Overtli-Blender",
        "temp_workspaces",
    ]:
        assert expected in runtime_workspace

    assert "runtime_resolve_artifact_workspace" in workspace_service
    assert "runtime_resolve_artifact_workspace" in verification_service
    assert "def initialize_temp_workspace" in project_tools
    assert "def promote_temp_workspace_to_project" in project_tools


def test_batch_schema_accepts_command_name_and_prevalidates_before_mutation() -> None:
    batch_section = ADDON_TEXT[ADDON_TEXT.index("class VerifiedEditBatchService"):ADDON_TEXT.index("class SafetyPolicyService")]
    for expected in [
        "command_name",
        "prevalidate_only",
        "prevalidate_all",
        "expected_schema",
        "alternate_schema",
        "create_box",
        "transform_object_dimensions",
        "clear_scene",
        "validate_scene_composition",
    ]:
        assert expected in batch_section

    scene_tools = _read("src/overtli_blender/tools/scene_edit_tools.py")
    assert "prevalidate_only" in scene_tools
    assert "prevalidate_all" in scene_tools


def test_destructive_tool_search_does_not_return_unrelated_create_tools() -> None:
    from overtli_blender.runtime.tool_packs import get_tool_spec, search_tools

    result = search_tools("delete scene objects", limit=20)
    names = {item["name"] for item in result["results"]}
    assert "delete_objects" in names or "clear_scene" in names
    assert "create_collection" not in names
    assert "create_primitive_object" not in names

    spec = get_tool_spec("run_verified_edit_batch")
    assert spec is not None
    assert "accepted_operation_schema" in spec["tool"]
    assert "command_name" in spec["tool"]["accepted_operation_schema"]["preferred"]
    assert "type" in spec["tool"]["accepted_operation_schema"]["legacy"]


def test_workspace_scene_plan_and_color_management_compatibility_are_exposed() -> None:
    workspace_tools = _read("src/overtli_blender/tools/workspace_tools.py")
    render_tools = _read("src/overtli_blender/tools/render_tools.py")
    animation_service = _read("overtli_blender_addon/services/animation.py")
    socket_server = _read("overtli_blender_addon/runtime/socket_server.py")

    for command in ["complete_workspace_task", "create_scene_plan", "list_scene_plan"]:
        assert f"def {command}" in workspace_tools
        assert f'"{command}":' in socket_server

    assert "def get_supported_color_management" in render_tools
    assert "auto_compatible" in render_tools
    assert "def get_supported_color_management" in animation_service
    assert "_compatible_choice" in animation_service
