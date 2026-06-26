"""Packaged addon dispatcher bridge."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable


COMMAND_NOT_AVAILABLE = {
    "status": "error",
    "errors": [
        {
            "code": "COMMAND_NOT_AVAILABLE",
            "message": "Command is not available.",
            "remediation": "Use search_tools or discover_tool_packs.",
        }
    ],
}


@dataclass(frozen=True)
class DispatchResult:
    command: str
    elapsed_ms: float
    response: dict[str, Any]


class PackagedDispatcher:
    """Small command dispatcher used by the packaged runtime boundary."""

    def __init__(self, handlers: dict[str, Callable[..., Any]] | None = None) -> None:
        self._handlers: dict[str, Callable[..., Any]] = dict(handlers or {})

    def register_handler(self, name: str, handler: Callable[..., Any]) -> None:
        self._handlers[name] = handler

    def has_command(self, name: str) -> bool:
        return name in self._handlers

    def dispatch(self, name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.dispatch_with_timing(name, params).response

    def dispatch_with_timing(self, name: str, params: dict[str, Any] | None = None) -> DispatchResult:
        started = perf_counter()
        handler = self._handlers.get(name)
        if not handler:
            return DispatchResult(name, 0.0, dict(COMMAND_NOT_AVAILABLE))
        try:
            result = handler(**(params or {}))
            response = result if isinstance(result, dict) and "status" in result else {"status": "success", "result": result}
        except Exception as exc:
            response = {"status": "error", "errors": [{"code": "COMMAND_FAILED", "message": str(exc), "remediation": "Check Blender console logs and command parameters."}]}
        elapsed = round((perf_counter() - started) * 1000, 3)
        return DispatchResult(name, elapsed, response)


def build_dispatcher_from_server(server: Any) -> PackagedDispatcher:
    return PackagedDispatcher(server._build_command_handlers())
