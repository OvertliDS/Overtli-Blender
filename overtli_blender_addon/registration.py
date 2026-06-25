"""Registration scaffold for the experimental packaged addon."""

from __future__ import annotations

from .preferences import OvertliBlenderAddonPreferences


CLASSES = (OvertliBlenderAddonPreferences,)


def register():
    import bpy

    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
