from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any

from .errors import ErrorCode
from .operation_types import OperationType
from .permissions import RiskLevel


def _serialize_value(value: Any) -> Any:
    if is_dataclass(value):
        return {f.name: _serialize_value(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if hasattr(value, "value") and isinstance(getattr(value, "value"), (str, int, float, bool, type(None))):
        return value.value
    return value


@dataclass
class WarningInfo:
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _serialize_value(asdict(self))


@dataclass
class ErrorInfo:
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _serialize_value(asdict(self))


@dataclass
class VerificationInfo:
    required: bool = False
    performed: bool = False
    status: str = "not_applicable"
    artifacts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _serialize_value(asdict(self))


@dataclass
class RollbackInfo:
    available: bool = False
    method: str | None = None
    operation_id: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _serialize_value(asdict(self))


@dataclass
class ToolResult:
    status: str
    tool: str
    operation_type: OperationType
    result: dict[str, Any] = field(default_factory=dict)
    operation_id: str | None = None
    request_id: str | None = None
    target_handles: list[str] = field(default_factory=list)
    warnings: list[WarningInfo] = field(default_factory=list)
    errors: list[ErrorInfo] = field(default_factory=list)
    confidence: float | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    verification: VerificationInfo = field(default_factory=VerificationInfo)
    rollback: RollbackInfo = field(default_factory=RollbackInfo)

    def to_dict(self) -> dict[str, Any]:
        return _serialize_value(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def success_result(
    tool: str,
    operation_type: OperationType,
    result: dict | None = None,
    **kwargs: Any,
) -> ToolResult:
    return ToolResult(
        status="success",
        tool=tool,
        operation_type=operation_type,
        result=dict(result or {}),
        **kwargs,
    )


def error_result(
    tool: str,
    operation_type: OperationType,
    code: str,
    message: str,
    **kwargs: Any,
) -> ToolResult:
    error = ErrorInfo(code=code, message=message, details=kwargs.pop("error_details", {}))
    errors = list(kwargs.pop("errors", []))
    errors.insert(0, error)
    return ToolResult(
        status="error",
        tool=tool,
        operation_type=operation_type,
        errors=errors,
        **kwargs,
    )

