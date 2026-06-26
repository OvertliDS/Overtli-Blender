"""Blender version adapter."""

from __future__ import annotations


def current_version():
    try:
        import bpy
    except ModuleNotFoundError:
        return None
    return tuple(getattr(bpy.app, "version", (0, 0, 0)))
