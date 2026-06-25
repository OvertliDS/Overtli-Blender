"""Experimental packaged addon layout for Overtli-Blender.

The production addon remains `addon.py` during Phase 7B. This package is the
migration scaffold that future phases will fill by moving services gradually.
"""

bl_info = {
    "name": "Overtli-Blender",
    "author": "OvertliDS",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Overtli-Blender",
    "description": "Experimental packaged Overtli-Blender addon layout.",
    "category": "Interface",
}


def register():
    from .registration import register as register_package

    register_package()


def unregister():
    from .registration import unregister as unregister_package

    unregister_package()
