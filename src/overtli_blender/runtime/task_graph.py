"""JSON-backed task graph primitives."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .path_utils import atomic_write_text, canonical_path


TASK_STATUSES = ("planned", "ready", "in_progress", "waiting_for_approval", "waiting_for_user_selection", "blocked", "completed_unverified", "verified", "failed", "rolled_back", "stale", "archived")


class TaskGraphStore:
    def __init__(self, workspace_dir: str | Path):
        self.tasks_dir = canonical_path(workspace_dir) / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        return self.tasks_dir / f"{task_id}.json"

    def create_task(self, goal: str, **kwargs: Any) -> dict[str, Any]:
        task_id = kwargs.get("task_id") or f"task_{int(time.time() * 1000)}"
        task = {
            "task_id": task_id,
            "goal": goal,
            "status": kwargs.get("status", "planned"),
            "priority": kwargs.get("priority", "normal"),
            "dependencies": kwargs.get("dependencies", []),
            "blocked_by": kwargs.get("blocked_by", []),
            "target_handles": kwargs.get("target_handles", []),
            "acceptance_criteria": kwargs.get("acceptance_criteria", []),
            "required_approvals": kwargs.get("required_approvals", []),
            "created_revision": kwargs.get("created_revision", 0),
            "last_verified_revision": None,
            "artifacts": [],
            "user_notes": kwargs.get("user_notes", []),
            "model_summary": kwargs.get("model_summary"),
        }
        atomic_write_text(self._path(task_id), json.dumps(task, indent=2, sort_keys=True))
        return {"status": "success", "task": task}

    def get_task(self, task_id: str) -> dict[str, Any]:
        path = self._path(task_id)
        if not path.exists():
            return {"status": "error", "message": f"Unknown task: {task_id}"}
        return {"status": "success", "task": json.loads(path.read_text(encoding="utf-8"))}

    def list_tasks(self, status: str | None = None) -> dict[str, Any]:
        tasks = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.tasks_dir.glob("task_*.json"))]
        if status:
            tasks = [task for task in tasks if task.get("status") == status]
        return {"status": "success", "tasks": tasks}

    def update_task(self, task_id: str, **updates: Any) -> dict[str, Any]:
        result = self.get_task(task_id)
        if result["status"] != "success":
            return result
        task = result["task"]
        for key, value in updates.items():
            if value is not None:
                task[key] = value
        atomic_write_text(self._path(task_id), json.dumps(task, indent=2, sort_keys=True))
        return {"status": "success", "task": task}
