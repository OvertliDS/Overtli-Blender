from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORDERED_ADDON_FILES = [
    "addon.py",
    "overtli_blender_addon/core.py",
    "overtli_blender_addon/services/context.py",
    "overtli_blender_addon/services/scene.py",
    "overtli_blender_addon/services/verification.py",
    "overtli_blender_addon/services/assets.py",
    "overtli_blender_addon/services/materials.py",
    "overtli_blender_addon/services/modeling.py",
    "overtli_blender_addon/services/spatial.py",
    "overtli_blender_addon/services/sculpt.py",
    "overtli_blender_addon/services/animation.py",
    "overtli_blender_addon/services/workspace.py",
    "overtli_blender_addon/services/diagnostics.py",
    "overtli_blender_addon/services/geometry_nodes.py",
    "overtli_blender_addon/services/addon_management.py",
    "overtli_blender_addon/services/knowledge.py",
    "overtli_blender_addon/services/baking.py",
    "overtli_blender_addon/services/product_ux.py",
    "overtli_blender_addon/runtime/dispatcher.py",
    "overtli_blender_addon/runtime/socket_server.py",
    "overtli_blender_addon/preferences.py",
    "overtli_blender_addon/ui/panels.py",
    "overtli_blender_addon/operators.py",
    "overtli_blender_addon/registration.py",
]


def read_addon_package_source() -> str:
    return "\n".join((ROOT / rel).read_text(encoding="utf-8") for rel in ORDERED_ADDON_FILES)


ADDON_PACKAGE_SOURCE = read_addon_package_source()
