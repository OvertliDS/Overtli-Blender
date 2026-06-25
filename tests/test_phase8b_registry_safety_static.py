from overtli_blender.runtime.command_registry import build_command_registry
from overtli_blender.runtime.tool_packs import TOOL_PACK_DEFINITIONS, search_tools


PHASE8B_COMMANDS = [
    "get_modeling_capabilities",
    "validate_mesh_schema",
    "create_mesh_from_schema",
    "create_profile_curve",
    "extrude_profile",
    "lathe_profile",
    "loft_profiles",
    "bridge_profile_loops",
    "create_curve_path_object",
    "create_beveled_curve_object",
    "create_modifier_stack",
    "create_hard_surface_panel",
    "create_pipe_or_rail",
    "create_modular_assembly",
    "plan_reference_construction",
    "run_reference_construction_step",
    "validate_reference_alignment",
    "configure_sculpt_session",
    "create_sculpt_mask",
    "create_face_set",
    "apply_sculpt_stroke_batch",
    "create_shape_key_sculpt_variant",
    "validate_sculpt_result",
    "create_cloth_pattern_panel",
    "define_cloth_seam_pair",
    "create_cloth_setup",
    "create_cloth_pin_group",
    "create_cloth_collision_setup",
    "simulate_cloth_preview",
    "bake_cloth_cache",
    "clear_cloth_cache",
    "convert_cloth_result",
    "validate_construction_geometry",
    "plan_construction_cleanup",
    "execute_construction_cleanup",
    "run_advanced_modeling_workflow_batch",
]


def test_phase8b_commands_have_command_specs_and_tool_packs():
    registry = build_command_registry()
    for command in PHASE8B_COMMANDS:
        spec = registry[command]
        assert spec.tool_pack in {"advanced_modeling", "reference_construction", "sculpt_workflows", "cloth_patterns"}
        assert spec.risk_level in {"LOW", "MEDIUM", "HIGH"}


def test_phase8b_high_risk_commands_require_approval():
    registry = build_command_registry()
    for command in ["apply_sculpt_stroke_batch", "simulate_cloth_preview", "bake_cloth_cache", "clear_cloth_cache", "convert_cloth_result", "execute_construction_cleanup"]:
        spec = registry[command]
        assert spec.risk_level == "HIGH"
        assert spec.requires_approval is True


def test_phase8b_tool_packs_and_search_terms_exist():
    for pack in ["advanced_modeling", "reference_construction", "sculpt_workflows", "cloth_patterns"]:
        assert pack in TOOL_PACK_DEFINITIONS
    for query in ["create custom mesh", "lathe profile", "make pipe along curve", "cloth pattern panel", "validate construction geometry"]:
        assert search_tools(query)["results"]
