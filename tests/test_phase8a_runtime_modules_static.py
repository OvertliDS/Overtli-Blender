from overtli_blender.runtime.bake_manifest import BakeClassification, BakeWorkflowManifest
from overtli_blender.runtime.bake_planning import classify_bake_pass, estimate_bake_cost, normalize_bake_pass_name, plan_bake_outputs
from overtli_blender.runtime.channel_packing import get_channel_layout, validate_channel_pack_inputs
from overtli_blender.runtime.image_resources import color_space_intent_for_pass, safe_image_filename


def test_bake_classification_is_honest():
    assert normalize_bake_pass_name("ambient occlusion") == "AO"
    assert classify_bake_pass("normal") == BakeClassification.NATIVE
    assert classify_bake_pass("metallic") == BakeClassification.DERIVED
    assert classify_bake_pass("curvature") == BakeClassification.APPROXIMATED
    assert classify_bake_pass("unknown") == BakeClassification.UNSUPPORTED


def test_bake_cost_and_output_plan():
    cost = estimate_bake_cost(["NORMAL", "AO"], 64, object_count=2)
    assert cost["pixels"] == 64 * 64 * 2 * 2
    outputs = plan_bake_outputs(["Cube"], ["normal"], 64, "textures/baked")
    assert outputs[0]["classification"] == "native"
    assert outputs[0]["color_space_intent"] == "Non-Color"


def test_image_resource_helpers():
    assert safe_image_filename("Cube 01", "NORMAL", "PNG") == "Cube_01_normal.png"
    assert color_space_intent_for_pass("base_color") == "sRGB"
    assert color_space_intent_for_pass("roughness") == "Non-Color"


def test_channel_packing_layouts_and_validation():
    assert get_channel_layout("ORM") == {"R": "AO", "G": "ROUGHNESS", "B": "METALLIC"}
    validation = validate_channel_pack_inputs({"AO": "missing.png", "ROUGHNESS": "missing2.png", "METALLIC": "missing3.png"}, "ORM")
    assert validation["valid"] is False
    assert validation["missing_files"]


def test_manifest_model_serializes_classification():
    manifest = BakeWorkflowManifest(workflow_id="wf", workflow_name="test")
    assert manifest.to_dict()["workflow_id"] == "wf"
