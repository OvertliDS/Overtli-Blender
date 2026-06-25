from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
SMOKE_TEXT = (ROOT / "scripts/smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_phase3_verified_batch_is_allowlisted_not_arbitrary_code() -> None:
    for text in [
        "SUPPORTED_BATCH_OPERATIONS",
        "DESTRUCTIVE_OPERATIONS",
        '"delete_collection"',
        "batch_allow_destructive",
        "operation.confirm=True",
        "create_verification_snapshot",
    ]:
        assert text in ADDON_TEXT
    batch_section = ADDON_TEXT[ADDON_TEXT.index("class VerifiedEditBatchService"):ADDON_TEXT.index("class SafetyPolicyService")]
    assert "execute_code" not in batch_section
    assert "exec(" not in batch_section


def test_phase3_full_smoke_uses_safe_contained_names() -> None:
    for text in [
        "--phase3-full",
        "OVERTLI_PHASE3_SMOKE_",
        "OVERTLI_PHASE3_CUBE_",
        "OVERTLI_PHASE3_MAT_",
        "delete_objects",
        "delete_collection",
        '"confirm": True',
    ]:
        assert text in SMOKE_TEXT
    phase3_section = SMOKE_TEXT[SMOKE_TEXT.index("def run_phase3_full_smoke"):SMOKE_TEXT.index("def run_optional_material_ops_smoke")]
    for forbidden in ["execute_code", "download_polyhaven_asset", "download_sketchfab_model", "create_rodin_job"]:
        assert forbidden not in phase3_section
