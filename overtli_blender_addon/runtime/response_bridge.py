"""Response envelope helpers for socket compatibility."""

from __future__ import annotations

from typing import Any


def success(result: Any) -> dict[str, Any]:
    return {"status": "success", "result": result}


def error(code: str, message: str, remediation: str | None = None) -> dict[str, Any]:
    payload = {"code": code, "message": message}
    if remediation:
        payload["remediation"] = remediation
    return {"status": "error", "errors": [payload]}
