from overtli_blender.runtime.command_registry import build_command_registry
from overtli_blender.runtime.tool_packs import TOOL_PACK_DEFINITIONS
from overtli_blender.common.safety import build_command_safety_map


PHASE7C_COMMANDS = {
    "get_project_status",
    "resolve_project_workspace",
    "initialize_project_workspace",
    "validate_project_layout",
    "get_file_access_policy",
    "validate_path_access",
    "write_project_text_file",
    "plan_file_delete",
    "execute_approved_file_delete",
    "get_cache_status",
    "plan_cache_cleanup",
    "create_task",
    "get_task_graph",
    "get_session_time",
    "create_scene_revision_marker",
    "import_reference_image",
    "calibrate_reference_scale",
    "calculate_distance",
    "get_oriented_bounds",
    "plan_rename",
    "execute_rename",
}


def test_phase7c_commands_are_registered_and_safety_classified() -> None:
    registry = build_command_registry()
    safety = build_command_safety_map()
    assert not (PHASE7C_COMMANDS - set(registry))
    assert not (PHASE7C_COMMANDS - set(safety))
    assert registry["execute_rename"].requires_approval
    assert registry["execute_cache_cleanup"].requires_approval


def test_phase7c_tool_packs_exist() -> None:
    for pack in ["project_runtime", "file_access", "task_planning", "references", "spatial_measurement", "cache_management"]:
        assert pack in TOOL_PACK_DEFINITIONS
