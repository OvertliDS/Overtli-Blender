"""Packaged addon dispatcher bridge scaffold."""

from __future__ import annotations

from typing import Any, Callable


class PackagedDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register_handler(self, name: str, handler: Callable[..., Any]) -> None:
        self._handlers[name] = handler

    def dispatch(self, name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        handler = self._handlers.get(name)
        if not handler:
            return {"status": "not_implemented", "message": f"Packaged handler not migrated yet: {name}"}
        return {"status": "success", "result": handler(**(params or {}))}
