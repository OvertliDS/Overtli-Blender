from overtli_blender.runtime.mesh_validation import validate_mesh_schema
from overtli_blender.runtime.modeling_plan import plan_modifier_stack, select_modeling_method


def test_phase8b_mesh_schema_validation_bounds_and_summary():
    schema = {"vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]], "edges": [], "faces": [[0, 1, 2]]}
    result = validate_mesh_schema(schema)
    assert result["valid"] is True
    assert result["summary"]["vertices"] == 3
    assert result["summary"]["estimated_memory_bytes"] > 0


def test_phase8b_mesh_schema_rejects_bad_face_index():
    result = validate_mesh_schema({"vertices": [[0, 0, 0]], "edges": [], "faces": [[0, 1, 2]]})
    assert result["valid"] is False
    assert "face-index-out-of-range-0" in result["errors"]


def test_phase8b_modeling_plan_selects_methods_and_modifiers():
    assert select_modeling_method("make a pipe along curve")["method"] == "curve_profile"
    assert plan_modifier_stack([{"type": "BEVEL"}, {"type": "WEIGHTED_NORMAL"}])["status"] == "success"
    assert plan_modifier_stack([{"type": "APPLY_DESTRUCTIVE"}])["status"] == "error"
