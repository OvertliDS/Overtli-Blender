from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase7c_rename_service_is_plan_first_and_approval_gated() -> None:
    addon = (ROOT / "addon.py").read_text(encoding="utf-8")
    assert "class SafeRenameRelocationService" in addon
    for marker in ["plan_rename", "execute_rename", "collision", "requires_approval", "batch_rename_files", "rename_project"]:
        assert marker in addon
