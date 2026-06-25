from overtli_blender.common.safety import build_command_safety_map
from overtli_blender.runtime.command_registry import build_command_registry
from overtli_blender.runtime.tool_packs import TOOL_PACK_DEFINITIONS, search_tools


PHASE9A_COMMANDS = [
    "get_animation_system_capabilities",
    "inspect_animation_system",
    "list_actions",
    "get_action_deep_info",
    "create_action",
    "duplicate_action",
    "rename_action",
    "assign_action",
    "delete_actions",
    "insert_keyframe_batch",
    "edit_keyframes",
    "retime_action",
    "set_fcurve_interpolation",
    "add_fcurve_modifier",
    "remove_fcurve_modifier",
    "create_nla_track",
    "add_action_to_nla",
    "edit_nla_strip",
    "mute_nla_track",
    "delete_nla_tracks",
    "validate_nla_stack",
    "validate_driver_dsl",
    "create_driver_from_dsl",
    "remove_drivers",
    "create_rig_template",
    "create_control_bones",
    "create_ik_chain",
    "add_rig_constraint",
    "remove_rig_constraints",
    "add_custom_rig_properties",
    "validate_rig",
    "inspect_pose",
    "create_pose_snapshot",
    "apply_pose_snapshot",
    "create_pose_asset",
    "list_pose_assets",
    "compare_poses",
    "delete_pose_assets",
    "create_shot_range",
    "create_camera_cut",
    "create_timeline_marker",
    "create_shot_plan",
    "validate_shot_plan",
    "get_simulation_capabilities",
    "inspect_simulation_state",
    "configure_rigidbody_basic",
    "configure_cloth_simulation_advanced",
    "configure_softbody_basic",
    "configure_hair_curve_dynamics_basic",
    "get_simulation_cache_status",
    "simulate_preview_range",
    "bake_simulation_cache",
    "clear_simulation_cache",
    "create_motion_path_preview",
    "validate_motion",
    "run_animation_rigging_workflow_batch",
]


def test_phase9a_commands_have_command_specs_and_tool_packs():
    registry = build_command_registry()
    expected_packs = {
        "advanced_animation",
        "action_library",
        "nla_workflows",
        "drivers",
        "rigging",
        "pose_library",
        "shot_workflows",
        "simulation_workflows",
        "motion_validation",
    }
    for command in PHASE9A_COMMANDS:
        spec = registry[command]
        assert spec.tool_pack in expected_packs
        assert spec.risk_level in {"LOW", "MEDIUM", "HIGH"}


def test_phase9a_high_risk_commands_require_approval():
    registry = build_command_registry()
    safety = build_command_safety_map()
    for command in [
        "delete_actions",
        "edit_keyframes",
        "retime_action",
        "remove_fcurve_modifier",
        "delete_nla_tracks",
        "remove_drivers",
        "remove_rig_constraints",
        "apply_pose_snapshot",
        "delete_pose_assets",
        "simulate_preview_range",
        "bake_simulation_cache",
        "clear_simulation_cache",
    ]:
        spec = registry[command]
        metadata = safety[command]
        assert spec.risk_level == "HIGH"
        assert spec.requires_approval is True
        assert metadata.strict_blocked is True


def test_phase9a_tool_packs_and_search_terms_exist():
    for pack in [
        "advanced_animation",
        "action_library",
        "nla_workflows",
        "drivers",
        "rigging",
        "pose_library",
        "shot_workflows",
        "simulation_workflows",
        "motion_validation",
    ]:
        assert pack in TOOL_PACK_DEFINITIONS
    for query in ["driver dsl", "pose snapshot", "shot plan", "simulation cache", "validate motion"]:
        assert search_tools(query)["results"]
