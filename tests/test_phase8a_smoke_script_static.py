from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = (ROOT / "scripts/smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_phase8a_smoke_flags_exist():
    for flag in (
        "--include-bake-capabilities",
        "--include-bake-preflight",
        "--include-bake-target-images",
        "--include-native-bake",
        "--include-derived-bake",
        "--include-selected-to-active-bake",
        "--include-channel-packing",
        "--include-baked-material",
        "--include-bake-cleanup-plan",
        "--include-verified-bake-workflow",
        "--phase8a-full",
    ):
        assert flag in SMOKE


def test_phase8a_smoke_uses_project_local_workspace():
    assert "phase8a_smoke" in SMOKE
    assert "OVERTLI_PHASE8A_TARGET" in SMOKE
    assert "run_verified_bake_workflow" in SMOKE
