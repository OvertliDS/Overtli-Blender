"""Addon preferences scaffold for the packaged addon migration."""

from __future__ import annotations


try:
    import bpy
    from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
except ModuleNotFoundError:
    bpy = None
    BoolProperty = EnumProperty = IntProperty = StringProperty = None


if bpy:
    class OvertliBlenderAddonPreferences(bpy.types.AddonPreferences):
        bl_idname = __package__ or "overtli_blender_addon"

        host: StringProperty(name="Host", default="localhost")
        port: IntProperty(name="Port", default=9876)
        permission_profile: EnumProperty(
            name="Permission Profile",
            items=[
                ("read_only", "Read Only", "Scene and metadata inspection only"),
                ("standard", "Standard", "Structured local project work"),
                ("trusted_project", "Trusted Project", "Project writes and guarded destructive operations"),
                ("developer", "Developer", "Developer surfaces including raw Python gates"),
            ],
            default="standard",
        )
        experimental_package_layout: BoolProperty(name="Experimental packaged layout", default=True)

        def draw(self, context):
            layout = self.layout
            layout.prop(self, "host")
            layout.prop(self, "port")
            layout.prop(self, "permission_profile")
            layout.prop(self, "experimental_package_layout")
else:
    class OvertliBlenderAddonPreferences:
        bl_idname = "overtli_blender_addon"
