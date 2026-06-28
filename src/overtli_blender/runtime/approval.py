"""Two-phase approval records for high-risk runtime operations."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from .command_registry import get_command_spec


def canonical_params_hash(command_name: str, params: dict[str, Any] | None) -> str:
    payload = {"command_name": command_name, "params": params or {}}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass
class ApprovalRecord:
    approval_id: str
    command_name: str
    params_hash: str
    target_summary: list[Any] = field(default_factory=list)
    path_summary: list[Any] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    risk_level: str = "LOW"
    destructive: bool = False
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    scene_revision: int | None = None
    required_capabilities: list[str] = field(default_factory=list)
    rollback_strategy: str | None = None
    status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ApprovalRuntime:
    def __init__(self, ttl_seconds: int = 600) -> None:
        self.ttl_seconds = ttl_seconds
        self._records: dict[str, ApprovalRecord] = {}

    def prepare_operation(self, command_name: str, params: dict[str, Any] | None = None, scene_revision: int | None = None) -> dict[str, Any]:
        spec = get_command_spec(command_name)
        if not spec:
            return {"status": "error", "message": f"Unknown command: {command_name}"}
        if spec.read_only and not spec.requires_approval:
            return {"status": "success", "approval_required": False, "tool": command_name}
        now = time.time()
        record = ApprovalRecord(
            approval_id=f"appr_{uuid4().hex[:16]}",
            command_name=command_name,
            params_hash=canonical_params_hash(command_name, params),
            params=dict(params or {}),
            risk_level=spec.risk_level,
            destructive=spec.destructive,
            created_at=now,
            expires_at=now + self.ttl_seconds,
            scene_revision=scene_revision,
            required_capabilities=list(spec.allowed_capabilities),
            rollback_strategy=spec.rollback_strategy,
        )
        self._records[record.approval_id] = record
        return {"status": "requires_approval", "approval_required": True, "approval": record.to_dict()}

    def get_pending_approvals(self) -> dict[str, Any]:
        self.expire_approval()
        return {"status": "success", "approvals": [record.to_dict() for record in self._records.values() if record.status == "pending"]}

    def get_approval_record(self, approval_id: str) -> dict[str, Any]:
        record = self._records.get(approval_id)
        if not record:
            return {"status": "error", "message": f"Unknown approval: {approval_id}"}
        return {"status": "success", "approval": record.to_dict()}

    def approve_operation(self, approval_id: str) -> dict[str, Any]:
        record = self._records.get(approval_id)
        if not record:
            return {"status": "error", "message": f"Unknown approval: {approval_id}"}
        if time.time() > record.expires_at:
            record.status = "expired"
            return {"status": "error", "message": "Approval expired", "approval": record.to_dict()}
        record.status = "approved"
        return {"status": "success", "approval": record.to_dict()}

    def approve_and_validate_operation(
        self,
        approval_id: str,
        expected_command_name: str | None = None,
        expected_params_hash: str | None = None,
    ) -> dict[str, Any]:
        record = self._records.get(approval_id)
        if not record:
            return {"status": "error", "message": f"Unknown approval: {approval_id}"}
        if time.time() > record.expires_at and record.status in {"pending", "approved"}:
            record.status = "expired"
            return {"status": "error", "message": "Approval expired", "approval": record.to_dict()}
        if record.status in {"denied", "expired", "executed"}:
            return {"status": "error", "message": f"Approval is {record.status}", "approval": record.to_dict()}
        if expected_command_name and record.command_name != expected_command_name:
            return {"status": "error", "message": "Approval command changed", "approval": record.to_dict()}
        if expected_params_hash and record.params_hash != expected_params_hash:
            return {"status": "error", "message": "Approval parameters changed", "approval": record.to_dict()}
        record.status = "approved"
        return {"status": "success", "approval": record.to_dict()}

    def deny_operation(self, approval_id: str, reason: str | None = None) -> dict[str, Any]:
        record = self._records.get(approval_id)
        if not record:
            return {"status": "error", "message": f"Unknown approval: {approval_id}"}
        record.status = "denied"
        data = record.to_dict()
        if reason:
            data["reason"] = reason
        return {"status": "success", "approval": data}

    def expire_approval(self, approval_id: str | None = None) -> dict[str, Any]:
        now = time.time()
        expired: list[str] = []
        records = [self._records[approval_id]] if approval_id and approval_id in self._records else list(self._records.values())
        for record in records:
            if record.status == "pending" and now > record.expires_at:
                record.status = "expired"
                expired.append(record.approval_id)
        return {"status": "success", "expired": expired}

    def execute_approved_operation(self, approval_id: str, command_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        validation = self.validate_approved_operation(approval_id, command_name, params)
        if validation.get("status") != "success":
            return validation
        return {
            "status": "success",
            "approval": validation["approval"],
            "dispatch_required": True,
            "message": "Approval validated; caller must dispatch the exact approved structured command and then mark_executed.",
        }

    def validate_approved_operation(self, approval_id: str, command_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        record = self._records.get(approval_id)
        if not record:
            return {"status": "error", "message": f"Unknown approval: {approval_id}"}
        if time.time() > record.expires_at and record.status in {"pending", "approved"}:
            record.status = "expired"
            return {"status": "error", "message": "Approval expired", "approval": record.to_dict()}
        if record.status != "approved":
            return {"status": "error", "message": f"Approval is {record.status}", "approval": record.to_dict()}
        if record.command_name != command_name or record.params_hash != canonical_params_hash(command_name, params):
            return {"status": "error", "message": "Approval parameters changed", "approval": record.to_dict()}
        return {"status": "success", "approval": record.to_dict()}

    def mark_executed(self, approval_id: str) -> dict[str, Any]:
        record = self._records.get(approval_id)
        if not record:
            return {"status": "error", "message": f"Unknown approval: {approval_id}"}
        record.status = "executed"
        return {"status": "success", "approval": record.to_dict()}


DEFAULT_APPROVAL_RUNTIME = ApprovalRuntime()
