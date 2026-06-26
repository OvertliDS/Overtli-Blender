"""Small Blender API access adapter."""

from __future__ import annotations


def require_bpy():
    import bpy

    return bpy
