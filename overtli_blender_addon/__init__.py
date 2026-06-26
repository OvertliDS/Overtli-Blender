"""Packaged Blender addon entrypoint for Overtli-Blender."""

from __future__ import annotations

# Blender's addon discovery reads this module directly and expects a literal
# top-level bl_info assignment. Do not replace this with an imported alias.
bl_info = {
    "name": "Overtli-Blender",
    "author": "OvertliDS",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Overtli-Blender",
    "description": "Local-first Blender MCP socket addon.",
    "category": "Interface",
}


def register():
    from .registration import register as register_package

    register_package()


def unregister():
    from .registration import unregister as unregister_package

    unregister_package()
