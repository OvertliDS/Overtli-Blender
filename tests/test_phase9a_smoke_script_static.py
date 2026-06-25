from pathlib import Path


SMOKE = Path("scripts/smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_phase9a_smoke_flags_exist():
    for flag in [
        "--include-animation-system",
        "--include-action-library",
        "--include-fcurve-editing",
        "--include-nla-workflow",
        "--include-driver-dsl",
        "--include-rig-template",
        "--include-pose-library",
        "--include-shot-workflow",
        "--include-simulation-workflow",
        "--include-motion-validation",
        "--phase9a-full",
    ]:
        assert flag in SMOKE


def test_phase9a_smoke_uses_smoke_created_data_and_gates_risky_actions():
    assert "OVERTLI_PHASE9A_" in SMOKE
    assert "create_driver_from_dsl should require approval" in SMOKE
    assert "apply_pose_snapshot should require approval" in SMOKE
    assert "simulate_preview_range should require approval" in SMOKE
    assert "clear_simulation_cache should require approval" in SMOKE
    assert "delete_objects" in SMOKE
