from pathlib import Path


SMOKE = Path("scripts/smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_phase8b_smoke_flags_exist():
    for flag in [
        "--include-modeling-capabilities",
        "--include-mesh-schema",
        "--include-profile-modeling",
        "--include-curve-construction",
        "--include-modifier-construction",
        "--include-reference-construction",
        "--include-sculpt-workflow",
        "--include-cloth-patterns",
        "--include-construction-validation",
        "--include-construction-cleanup-plan",
        "--phase8b-full",
    ]:
        assert flag in SMOKE


def test_phase8b_smoke_uses_smoke_created_data_and_gates_risky_actions():
    assert "OVERTLI_PHASE8B_" in SMOKE
    assert "apply_sculpt_stroke_batch should require approval" in SMOKE
    assert "simulate_cloth_preview should require approval" in SMOKE
    assert "delete_objects" in SMOKE
