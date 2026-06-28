"""Packaged Blender addon entrypoint for Overtli-Blender."""

from __future__ import annotations

import importlib
import os
import sys

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


def _reload_child_modules() -> None:
    """Force Blender to use freshly installed package files after addon reinstall."""
    importlib.invalidate_caches()
    package_root = os.path.dirname(os.path.abspath(__file__))
    for current_root, dirs, files in os.walk(package_root):
        if os.path.basename(current_root) == "__pycache__":
            for filename in files:
                if filename.endswith((".pyc", ".pyo")):
                    try:
                        os.remove(os.path.join(current_root, filename))
                    except OSError:
                        pass
            try:
                os.rmdir(current_root)
            except OSError:
                pass
            dirs[:] = []
    prefixes = (f"{__name__}.", "overtli_blender.")
    stale_modules = [
        name
        for name in sys.modules
        if any(name.startswith(prefix) for prefix in prefixes) or name == "overtli_blender"
    ]
    for module_name in sorted(stale_modules, reverse=True):
        sys.modules.pop(module_name, None)


def register():
    _reload_child_modules()
    from .registration import register as register_package

    register_package()


def unregister():
    from .registration import unregister as unregister_package

    unregister_package()
