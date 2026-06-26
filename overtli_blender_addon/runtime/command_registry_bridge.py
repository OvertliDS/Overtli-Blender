"""Lazy bridge from packaged addon code to the shared command registry."""

from __future__ import annotations


def command_registry_report():
    from overtli_blender.runtime.command_registry import command_registry_report as _report

    return _report()


def get_command_spec(name: str):
    from overtli_blender.runtime.command_registry import get_command_spec as _get

    return _get(name)


def list_command_specs():
    from overtli_blender.runtime.command_registry import list_command_specs as _list

    return _list()


__all__ = ["command_registry_report", "get_command_spec", "list_command_specs"]
