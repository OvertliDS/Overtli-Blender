from pathlib import Path


from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def test_phase9a_addon_service_classes_exist():
    for marker in [
        "class AnimationIntelligenceAdvancedService",
        "class ActionLibraryService",
        "class FCurveEditingService",
        "class NLAWorkflowService",
        "class DriverDSLService",
        "class RigTemplateService",
        "class RigValidationService",
        "class PoseLibraryWorkflowService",
        "class ShotWorkflowService",
        "class SimulationWorkflowService",
        "class MotionValidationService",
        "class AnimationRiggingWorkflowBatchService",
    ]:
        assert marker in ADDON_TEXT


def test_phase9a_socket_handlers_exist():
    for command in [
        "get_animation_system_capabilities",
        "inspect_animation_system",
        "create_action",
        "insert_keyframe_batch",
        "set_fcurve_interpolation",
        "create_nla_track",
        "add_action_to_nla",
        "validate_driver_dsl",
        "create_driver_from_dsl",
        "create_rig_template",
        "create_ik_chain",
        "validate_rig",
        "create_pose_snapshot",
        "create_shot_plan",
        "get_simulation_capabilities",
        "inspect_simulation_state",
        "simulate_preview_range",
        "validate_motion",
        "run_animation_rigging_workflow_batch",
    ]:
        assert f'"{command}"' in ADDON_TEXT


def test_phase9a_high_risk_paths_are_honest_and_gated():
    for marker in [
        "requires_approval",
        "high_risk",
        "unsupported",
        "Driver creation requires confirmation",
        "Cache baking is approval-gated",
    ]:
        assert marker in ADDON_TEXT
