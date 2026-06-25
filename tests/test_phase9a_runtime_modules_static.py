import pytest

from overtli_blender.runtime.driver_dsl import compile_driver_expression, validate_driver_dsl
from overtli_blender.runtime.fcurve_tools import build_fcurve_modifier_plan, validate_keyframe_batch
from overtli_blender.runtime.motion_validation import (
    validate_driver_variables,
    validate_motion_bounds,
    validate_nla_overlaps,
    validate_missing_targets,
)
from overtli_blender.runtime.pose_library import PoseComparison, PoseSnapshot
from overtli_blender.runtime.rig_schema import BoneSpec, RigTemplate
from overtli_blender.runtime.shot_manifest import ShotPlan, ShotRange
from overtli_blender.runtime.simulation_manifest import SimulationSetup


def test_phase9a_driver_dsl_compiles_allowlisted_expression():
    dsl = {"operation": "clamp", "source": {"target_name": "Cube", "data_path": "location.x"}, "min": 0, "max": 1}
    assert validate_driver_dsl(dsl)["status"] == "success"
    assert compile_driver_expression(dsl)["expression"] == "min(max(var, 0.0), 1.0)"


def test_phase9a_driver_dsl_rejects_unknown_operations():
    with pytest.raises(ValueError, match="Unsupported driver DSL operation"):
        validate_driver_dsl({"operation": "__import__", "source": {"target_name": "Cube", "data_path": "location.x"}})


def test_phase9a_keyframe_validation_and_modifier_planning():
    valid = validate_keyframe_batch(
        [
            {"frame": 1, "data_path": "location", "value": [0, 0, 0]},
            {"frame": 24, "data_path": "location", "value": [1, 0, 0]},
        ]
    )
    assert valid["count"] == 2
    assert valid["frame_range"] == [1.0, 24.0]
    assert build_fcurve_modifier_plan("CYCLES")["modifier_type"] == "CYCLES"
    with pytest.raises(ValueError, match="Unsupported F-curve modifier"):
        build_fcurve_modifier_plan("EXECUTE_CODE")


def test_phase9a_manifest_and_schema_validation():
    rig = RigTemplate("simple", (BoneSpec("root", (0, 0, 0), (0, 0, 1)), BoneSpec("spine", (0, 0, 1), (0, 0, 2), parent="root")))
    shot = ShotPlan("plan", ranges=(ShotRange("shot_a", 1, 24),))
    sim = SimulationSetup("Cube", "cloth", 1, 24, {"quality": 5, "mass": 0.3})
    assert rig.to_dict()["bones"][1]["parent"] == "root"
    assert shot.to_dict()["ranges"][0]["frame_end"] == 24
    assert sim.to_dict()["simulation_type"] == "cloth"


def test_phase9a_motion_validation_helpers_report_issues():
    assert validate_driver_variables([{"name": "var"}])["issues"]
    assert validate_nla_overlaps([{"name": "a", "frame_start": 1, "frame_end": 10}, {"name": "b", "frame_start": 5, "frame_end": 12}])["issues"]
    assert validate_missing_targets([{"name": "IK", "exists": False}])["missing_count"] == 1
    assert validate_motion_bounds([{"frame": 1, "location": [20, 0, 0]}], {"max_x": 10})["issues"]


def test_phase9a_pose_snapshot_compare_detects_delta():
    a = PoseSnapshot("A", "Rig", bones={"Bone": {"location": [0, 0, 0], "rotation_euler": [0, 0, 0], "scale": [1, 1, 1]}})
    comparison = PoseComparison("A", "B", ("Bone",), 1.0)
    assert a.to_dict()["bones"]["Bone"]["location"] == [0, 0, 0]
    assert comparison.to_dict()["changed_bones"] == ("Bone",)


def test_phase9a_keyframes_reject_bad_payload():
    with pytest.raises(ValueError):
        validate_keyframe_batch([{"frame": "bad", "data_path": "", "value": 1}])
