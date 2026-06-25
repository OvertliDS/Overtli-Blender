"""Standard operation response envelope helpers."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4


def build_operation_response(
    *,
    status: str,
    tool: str,
    result: dict[str, Any] | None = None,
    warnings: list[Any] | None = None,
    errors: list[Any] | None = None,
    request_id: str | None = None,
    operation_id: str | None = None,
    started_at: float | None = None,
    required_user_action: str | None = None,
) -> dict[str, Any]:
    started = started_at or time.time()
    return {
        "status": status,
        "request_id": request_id or f"req_{uuid4().hex[:16]}",
        "operation_id": operation_id or f"op_{uuid4().hex[:16]}",
        "tool": tool,
        "result": result or {},
        "warnings": warnings or [],
        "errors": errors or [],
        "changed_targets": [],
        "created_artifacts": [],
        "scene_revision_before": None,
        "scene_revision_after": None,
        "rollback": {"available": False, "method": None, "artifact": None},
        "required_user_action": required_user_action,
        "duration_ms": int((time.time() - started) * 1000),
    }
