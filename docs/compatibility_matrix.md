# Compatibility Matrix

Phase 10A tracks Blender compatibility surfaces in `src/overtli_blender/runtime/compatibility_matrix.py`.

Covered surfaces:

- Addon registration: `bpy.utils.register_class`, `bpy.utils.unregister_class`, `AddonPreferences`, `Panel`, `Operator`.
- Addon installation: `bpy.ops.preferences.addon_install`, `bpy.ops.preferences.addon_enable`, `bpy.utils.script_paths`.
- Runtime paths: `bpy.app.version`, `bpy.app.background`, `bpy.path.abspath`, `bpy.path.relpath`.
- Animation APIs: `Action`, `ActionLayer`, `ActionSlot`, `FCurve`, `NlaTrack`, `Driver`, `PoseBone`.
- Geometry Nodes APIs: `GeometryNodeTree`, `NodeTree`, `NodeSocket`, `NodesModifier`.
