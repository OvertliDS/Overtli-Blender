from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BLENDER_UNAVAILABLE = "BLENDER_UNAVAILABLE"
    BLENDER_COMMAND_FAILED = "BLENDER_COMMAND_FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNSAFE_OPERATION = "UNSAFE_OPERATION"
    NOT_FOUND = "NOT_FOUND"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"


class OvertliBlenderError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict:
        return {
            "code": self.code.value,
            "message": self.message,
            "details": dict(self.details),
        }

