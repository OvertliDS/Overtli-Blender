from __future__ import annotations

from .core import *

class BLENDERMCP_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = "overtli_blender_addon"

    tool_profile: EnumProperty(
        name="Tool Profile",
        description="Default user-facing Overtli tool profile",
        items=[
            ("minimal", "Minimal", "Compact read-only setup"),
            ("read_only_review", "Read Only Review", "Inspection and diagnostics"),
            ("safe_scene", "Safe Scene", "Default non-destructive scene work"),
            ("materials", "Materials", "Material and texture workflows"),
            ("modeling", "Modeling", "Modeling and reference workflows"),
            ("animation", "Animation", "Animation, rigging, and shot workflows"),
            ("full_standard", "Full Standard", "Broad standard tool surface"),
            ("developer", "Developer", "Addon development and interop tools"),
        ],
        default="safe_scene",
    )
    show_diagnostics: BoolProperty(name="Show Diagnostics Hints", default=True)
    approved_roots_hint: StringProperty(name="Approved Roots Hint", default="Use MCP preferences commands to add roots with approval.")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Overtli-Blender Runtime UX")
        layout.prop(self, "tool_profile")
        layout.prop(self, "show_diagnostics")
        layout.prop(self, "approved_roots_hint")
        layout.label(text="Permission expansion, raw Python, and third-party operator execution are MCP approval-gated.")


