# Code created by Siddharth Ahuja: www.github.com/ahujasid (c) 2025
"""Blender entrypoint for the packaged Overtli-Blender addon."""

from __future__ import annotations

import importlib
import os
import sys
import traceback


_MISSING_PACKAGE_MESSAGE = "Install the Overtli-Blender addon zip built by scripts/build_addon_zip.py."


def _ensure_development_package_path() -> None:
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)


def _load_package():
    _ensure_development_package_path()
    try:
        return importlib.import_module("overtli_blender_addon")
    except ModuleNotFoundError as exc:
        if exc.name == "overtli_blender_addon":
            raise RuntimeError(_MISSING_PACKAGE_MESSAGE) from exc
        raise


try:
    _PACKAGE = _load_package()
    bl_info = _PACKAGE.bl_info
except Exception:
    _PACKAGE = None
    bl_info = {
        "name": "Overtli-Blender",
        "author": "OvertliDS",
        "version": (0, 1, 0),
        "blender": (3, 0, 0),
        "location": "View3D > Sidebar > Overtli-Blender",
        "description": _MISSING_PACKAGE_MESSAGE,
        "category": "Interface",
    }


def register():
    package = _PACKAGE or _load_package()
    package.register()


def unregister():
    if _PACKAGE is not None:
        _PACKAGE.unregister()


if __name__ == "__main__":
    try:
        register()
    except Exception:
        print(_MISSING_PACKAGE_MESSAGE)
        traceback.print_exc()
        raise
