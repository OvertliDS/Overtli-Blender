"""Compatibility alias for command registry bridge imports."""

from __future__ import annotations

from .command_registry_bridge import command_registry_report, get_command_spec, list_command_specs

__all__ = ["command_registry_report", "get_command_spec", "list_command_specs"]
