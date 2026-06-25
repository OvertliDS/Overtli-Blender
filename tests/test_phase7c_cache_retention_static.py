from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase7c_cache_retention_categories_and_commands_exist() -> None:
    runtime = (ROOT / "src/overtli_blender/runtime/cache_retention.py").read_text(encoding="utf-8")
    for category in ["temp", "derived_previews", "smoke_artifacts", "verification_snapshots", "logs", "diagnostics", "release_artifacts", "exports", "final_renders", "knowledge_indexes"]:
        assert category in runtime
    addon = (ROOT / "addon.py").read_text(encoding="utf-8")
    assert "class CacheRetentionService" in addon
    for name in ["get_cache_status", "plan_cache_cleanup", "execute_cache_cleanup", "pin_artifact", "unpin_artifact", "find_orphaned_artifacts", "compact_operation_history"]:
        assert f'"{name}":' in addon
