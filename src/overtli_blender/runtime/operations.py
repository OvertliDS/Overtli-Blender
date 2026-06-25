"""Operation queue, status, progress, and cancellation skeleton."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class OperationState:
    operation_id: str
    command: str
    status: str = "queued"
    started_at: float | None = None
    finished_at: float | None = None
    duration: float | None = None
    progress: float = 0.0
    warnings: list[Any] = field(default_factory=list)
    errors: list[Any] = field(default_factory=list)
    cancel_requested: bool = False
    created_artifacts: list[Any] = field(default_factory=list)
    changed_targets: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OperationRuntime:
    def __init__(self) -> None:
        self._operations: dict[str, OperationState] = {}

    def create_operation(self, command: str) -> OperationState:
        operation = OperationState(operation_id=f"op_{uuid4().hex[:16]}", command=command, status="running", started_at=time.time())
        self._operations[operation.operation_id] = operation
        return operation

    def finish_operation(self, operation_id: str, status: str = "success", warnings: list[Any] | None = None, errors: list[Any] | None = None) -> None:
        operation = self._operations.get(operation_id)
        if not operation:
            return
        operation.status = status
        operation.finished_at = time.time()
        operation.duration = operation.finished_at - (operation.started_at or operation.finished_at)
        operation.progress = 1.0
        if warnings:
            operation.warnings.extend(warnings)
        if errors:
            operation.errors.extend(errors)

    def get_operation_status(self, operation_id: str | None = None) -> dict[str, Any]:
        if operation_id:
            operation = self._operations.get(operation_id)
            if not operation:
                return {"status": "not_implemented", "message": "Operation id is unknown or already expired.", "operation_id": operation_id}
            return {"status": "success", "operation": operation.to_dict()}
        return {"status": "success", "operations": [op.to_dict() for op in self._operations.values()]}

    def list_recent_operations(self, limit: int = 20) -> dict[str, Any]:
        operations = list(self._operations.values())[-max(1, min(limit, 100)) :]
        return {"status": "success", "operations": [op.to_dict() for op in operations]}

    def cancel_operation(self, operation_id: str) -> dict[str, Any]:
        operation = self._operations.get(operation_id)
        if not operation:
            return {"status": "not_implemented", "message": "No cancellable operation found.", "operation_id": operation_id}
        operation.cancel_requested = True
        if operation.status in {"queued", "running"}:
            operation.status = "cancel_requested"
        return {"status": "success", "operation": operation.to_dict()}

    def get_operation_log(self, operation_id: str | None = None) -> dict[str, Any]:
        return self.get_operation_status(operation_id)


DEFAULT_OPERATION_RUNTIME = OperationRuntime()
