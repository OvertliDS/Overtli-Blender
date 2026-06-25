from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase7c_task_graph_schema_and_time_revision_exist() -> None:
    task_runtime = (ROOT / "src/overtli_blender/runtime/task_graph.py").read_text(encoding="utf-8")
    for marker in ["TASK_STATUSES", "completed_unverified", "verified", "stale", "TaskGraphStore"]:
        assert marker in task_runtime
    time_runtime = (ROOT / "src/overtli_blender/runtime/time_revision.py").read_text(encoding="utf-8")
    assert "class TimeRevisionTracker" in time_runtime
    addon = (ROOT / "addon.py").read_text(encoding="utf-8")
    for klass in ["TaskGraphService", "TimeRevisionService"]:
        assert f"class {klass}" in addon
