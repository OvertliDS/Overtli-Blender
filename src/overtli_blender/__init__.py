"""Overtli-Blender integration through the Model Context Protocol."""

from __future__ import annotations

from importlib import import_module

__version__ = "0.1.0"

__all__ = ["__version__", "BlenderConnection", "get_blender_connection"]


def __getattr__(name: str):
    if name in {"BlenderConnection", "get_blender_connection"}:
        module = import_module(".server", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
