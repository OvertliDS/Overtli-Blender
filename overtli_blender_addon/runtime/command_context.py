"""Command context objects for packaged runtime routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandContext:
    command_name: str
    params: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None
    operation_id: str | None = None
