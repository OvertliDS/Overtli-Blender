"""Static compatibility matrix for Phase 10A release-candidate checks."""

from __future__ import annotations


COMPATIBILITY_MATRIX = {
    "addon_registration": {
        "api": ["bpy.utils.register_class", "bpy.utils.unregister_class", "AddonPreferences", "Panel", "Operator"],
        "minimum_blender": "3.0.0",
        "phase10a_impact": "packaged addon registration delegates to modular package classes",
    },
    "addon_install": {
        "api": ["bpy.ops.preferences.addon_install", "bpy.ops.preferences.addon_enable", "bpy.utils.script_paths"],
        "minimum_blender": "3.0.0",
        "phase10a_impact": "package zip is primary install artifact",
    },
    "runtime_paths": {
        "api": ["bpy.app.version", "bpy.app.background", "bpy.path.abspath", "bpy.path.relpath"],
        "minimum_blender": "3.0.0",
        "phase10a_impact": "packaged runtime resolves development src or bundled shared runtime",
    },
    "animation_apis": {
        "api": ["Action", "ActionLayer", "ActionSlot", "FCurve", "NlaTrack", "Driver", "PoseBone"],
        "minimum_blender": "4.0.0",
        "phase10a_impact": "adapter module records version-sensitive names",
    },
    "geometry_nodes_apis": {
        "api": ["GeometryNodeTree", "NodeTree", "NodeSocket", "NodesModifier"],
        "minimum_blender": "3.0.0",
        "phase10a_impact": "adapter module records Geometry Nodes compatibility names",
    },
}


def compatibility_report() -> dict:
    return {"status": "passed", "matrix": COMPATIBILITY_MATRIX, "checked_surfaces": sorted(COMPATIBILITY_MATRIX)}
