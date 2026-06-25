"""Bridge from packaged addon code to the shared command registry."""

from __future__ import annotations

from overtli_blender.runtime.command_registry import command_registry_report, get_command_spec, list_command_specs

__all__ = ["command_registry_report", "get_command_spec", "list_command_specs"]
