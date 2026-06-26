"""Runtime dashboard and UX status summaries."""

from __future__ import annotations

from typing import Any


def runtime_dashboard(preferences: dict[str, Any], tool_profile: dict[str, Any], setup_status: dict[str, Any], approval_queue: dict[str, Any] | None = None, recent_operations: dict[str, Any] | None = None) -> dict[str, Any]:
    prefs_tools = preferences.get("tool_profiles", {})
    prefs_fs = preferences.get("filesystem", {})
    warnings = []
    if not prefs_fs.get("approved_roots"):
        warnings.append("No approved roots configured.")
    if setup_status.get("blockers"):
        warnings.extend(setup_status["blockers"])
    return {
        "status": "success",
        "dashboard": {
            "mode": preferences.get("filesystem", {}).get("permission_profile", "standard"),
            "active_tool_profile": prefs_tools.get("active_profile", "safe_scene"),
            "enabled_tool_packs": prefs_tools.get("enabled_tool_packs") or tool_profile.get("enabled_tool_packs", []),
            "active_skill_packs": prefs_tools.get("active_skill_packs", []),
            "approved_roots_count": len(prefs_fs.get("approved_roots", [])),
            "approval_queue": approval_queue or {"approvals": []},
            "recent_operations": recent_operations or {"operations": []},
            "setup": setup_status,
            "warnings": warnings,
            "next_recommended_actions": setup_status.get("next_actions", []),
        },
    }


def approval_queue_summary(queue: dict[str, Any]) -> dict[str, Any]:
    approvals = queue.get("approvals", [])
    return {"status": "success", "pending_count": len(approvals), "approvals": approvals}


def recent_operation_summary(operations: dict[str, Any]) -> dict[str, Any]:
    items = operations.get("operations") or operations.get("recent_operations") or []
    failures = [item for item in items if item.get("status") not in {None, "success"}]
    return {"status": "success", "operation_count": len(items), "failure_count": len(failures), "operations": items[:20], "failures": failures[:10]}
