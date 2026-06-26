"""Blender runtime compatibility helpers."""

from __future__ import annotations


def blender_version_tuple():
    try:
        import bpy
    except ModuleNotFoundError:
        return None
    return tuple(getattr(bpy.app, "version", (0, 0, 0)))


def is_background_mode() -> bool:
    try:
        import bpy
    except ModuleNotFoundError:
        return False
    return bool(getattr(bpy.app, "background", False))
