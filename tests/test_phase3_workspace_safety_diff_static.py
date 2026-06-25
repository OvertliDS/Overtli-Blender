from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/workspace_tools.py").read_text(encoding="utf-8")
SMOKE_TEXT = (ROOT / "scripts/smoke_blender_addon_socket.py").read_text(encoding="utf-8")


PHASE3_MASTER_COMMANDS = [
    "get_task_workspace",
    "create_workspace_task",
    "update_workspace_task",
    "list_workspace_tasks",
    "add_workspace_todo",
    "update_workspace_todo",
    "list_workspace_todos",
    "record_operation_journal_entry",
    "get_operation_journal",
    "create_scene_snapshot",
    "list_scene_snapshots",
    "diff_scene_snapshots",
    "detect_user_changes",
    "rollback_to_scene_snapshot",
    "undo_last_blender_operation",
]


def test_phase3_workspace_service_exists_and_maps_commands() -> None:
    assert "class WorkspaceSafetyDiffService" in ADDON_TEXT
    assert "self.workspace_safety_diff_service = WorkspaceSafetyDiffService(self)" in ADDON_TEXT
    for command in PHASE3_MASTER_COMMANDS:
        assert f'"{command}": self.{command}' in ADDON_TEXT


def test_phase3_workspace_service_covers_master_feature_list_terms() -> None:
    for text in [
        "TODO_STATES",
        "TASK_STATES",
        "operation_journal",
        "create_scene_snapshot",
        "diff_scene_snapshots",
        "detect_user_changes",
        "rollback_to_scene_snapshot requires confirm=True",
        "undo_last_blender_operation requires confirm=True",
        "remove_new_objects",
    ]:
        assert text in ADDON_TEXT


def test_phase3_workspace_mcp_wrappers_exist() -> None:
    assert "def register_workspace_tools" in TOOLS_TEXT
    for command in PHASE3_MASTER_COMMANDS:
        assert f"def {command}(" in TOOLS_TEXT
        assert f'"{command}"' in TOOLS_TEXT


def test_phase3_workspace_smoke_exists_and_is_wired() -> None:
    for text in [
        "--include-workspace-safety-diff",
        "run_phase3_workspace_safety_diff_smoke",
        "create_workspace_task",
        "add_workspace_todo",
        "create_scene_snapshot",
        "diff_scene_snapshots",
        "detect_user_changes",
        "rollback_to_scene_snapshot",
    ]:
        assert text in SMOKE_TEXT
