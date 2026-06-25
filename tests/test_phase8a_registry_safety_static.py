from overtli_blender.common.safety import build_command_safety_map
from overtli_blender.runtime.command_registry import get_command_spec
from overtli_blender.runtime.tool_packs import TOOL_PACK_DEFINITIONS


PHASE8A_COMMANDS = {
    "get_bake_capabilities",
    "validate_bake_setup",
    "estimate_bake_cost",
    "create_bake_target_images",
    "assign_bake_targets",
    "list_bake_targets",
    "bake_material_maps",
    "bake_selected_to_active",
    "bake_procedural_material",
    "bake_derived_map",
    "bake_curvature_map",
    "bake_thickness_map",
    "pack_texture_channels",
    "unpack_texture_channels",
    "validate_packed_texture",
    "save_baked_textures",
    "validate_baked_textures",
    "relink_baked_textures",
    "create_baked_material",
    "plan_bake_cleanup",
    "execute_bake_cleanup",
    "run_verified_bake_workflow",
    "list_project_images",
    "get_image_resource_info",
    "rename_image_resource",
}


def test_phase8a_commands_have_safety_and_command_specs():
    safety = build_command_safety_map()
    missing = PHASE8A_COMMANDS - set(safety)
    assert not missing
    for command in PHASE8A_COMMANDS:
        spec = get_command_spec(command)
        assert spec is not None
        assert spec.category in {"baking", "textures"}
        assert spec.tool_pack in {"texture_baking", "materials"}


def test_phase8a_high_risk_cleanup_is_approval_gated():
    spec = get_command_spec("execute_bake_cleanup")
    assert spec.risk_level == "HIGH"
    assert spec.requires_approval is True
    assert spec.requires_confirmation is True


def test_texture_baking_tool_pack_exists():
    assert "texture_baking" in TOOL_PACK_DEFINITIONS
