"""Command handler facade for the legacy-compatible packaged runtime."""

from __future__ import annotations

from typing import Any, Callable


def build_command_handlers(server: Any) -> dict[str, Callable[..., Any]]:
    return server._build_command_handlers()
