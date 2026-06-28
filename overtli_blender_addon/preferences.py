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
            ("browser_full_standard", "Browser Full Standard", "Browser connector full structured tool surface"),
            ("full_standard", "Full Standard", "Broad standard tool surface"),
            ("developer", "Developer", "Addon development and interop tools"),
        ],
        default="full_standard",
    )
    local_permission_profile: EnumProperty(
        name="Local Permission Profile",
        description="Default local Overtli permission profile",
        items=[
            ("standard", "Standard", "Safe local structured work"),
            ("trusted_project", "Trusted Project", "Project-trusted elevated work"),
            ("developer", "Developer", "Developer capabilities"),
        ],
        default="standard",
    )
    local_approval_mode: EnumProperty(
        name="Local Approval Mode",
        description="Default approval behavior for local addon use",
        items=[
            ("always_ask", "Always Ask", "Ask before every mutation"),
            ("ask_for_medium_high", "Ask Medium/High", "Ask for medium and high risk mutations"),
            ("ask_for_high_destructive", "Ask High/Destructive", "Allow safe structured writes; ask for high risk and destructive work"),
            ("ask_for_destructive_only", "Ask Destructive Only", "Ask for destructive, raw, delete, and lifecycle work"),
            ("full_access_developer", "Full Access Developer", "Developer mode with unsafe overrides still gated separately"),
            ("read_only", "Read Only", "No mutations"),
        ],
        default="ask_for_high_destructive",
    )
    browser_tool_profile: EnumProperty(
        name="Browser Tool Profile",
        description="Default browser connector tool profile",
        items=[
            ("browser_full_standard", "Browser Full Standard", "Full browser structured tool profile"),
            ("chatgpt_browser_default", "ChatGPT Browser Default", "Backward-compatible alias"),
        ],
        default="browser_full_standard",
    )
    browser_permission_profile: EnumProperty(
        name="Browser Permission Profile",
        description="Default browser connector permission profile",
        items=[
            ("browser_standard", "Browser Standard", "Safe structured browser mutations"),
            ("remote_browser_safe", "Remote Browser Safe", "Backward-compatible alias"),
        ],
        default="browser_standard",
    )
    browser_approval_mode: EnumProperty(
        name="Browser Approval Mode",
        description="Default approval behavior for browser connector use",
        items=[
            ("always_ask", "Always Ask", "Ask before every mutation"),
            ("ask_for_medium_high", "Ask Medium/High", "Ask for medium and high risk mutations"),
            ("ask_for_high_destructive", "Ask High/Destructive", "Allow safe structured writes; ask for high risk and destructive work"),
            ("ask_for_destructive_only", "Ask Destructive Only", "Ask for destructive, raw, delete, and lifecycle work"),
            ("read_only", "Read Only", "No mutations"),
        ],
        default="ask_for_destructive_only",
    )
    approval_timeout_seconds: IntProperty(name="Approval Timeout Seconds", default=900, min=60, max=86400)
    browser_mutation_path_status: EnumProperty(
        name="Browser Mutation Path Status",
        items=[
            ("complete", "Complete", "Browser mutation path has executor, write tools, permission, and approval mode"),
            ("incomplete_missing_executor", "Missing Executor", "Approval execution tool missing"),
            ("incomplete_missing_write_tools", "Missing Write Tools", "Safe structured write tools missing"),
            ("incomplete_permission_blocked", "Permission Blocked", "Browser permission profile blocks safe writes"),
            ("unknown", "Unknown", "Not checked"),
        ],
        default="complete",
    )
    require_approval_for_raw_python: BoolProperty(name="Require Approval For Raw Python", default=True)
    require_approval_for_provider_downloads: BoolProperty(name="Require Approval For Provider Downloads", default=True)
    require_approval_for_file_delete: BoolProperty(name="Require Approval For File Delete", default=True)
    require_approval_for_external_writes: BoolProperty(name="Require Approval For External Writes", default=True)
    show_diagnostics: BoolProperty(name="Show Diagnostics Hints", default=True)
    approved_roots_hint: StringProperty(name="Approved Roots Hint", default="Use MCP preferences commands to add roots with approval.")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Overtli-Blender Runtime UX")
        layout.prop(self, "tool_profile")
        layout.prop(self, "local_permission_profile")
        layout.prop(self, "local_approval_mode")
        layout.prop(self, "browser_tool_profile")
        layout.prop(self, "browser_permission_profile")
        layout.prop(self, "browser_approval_mode")
        layout.prop(self, "browser_mutation_path_status")
        layout.prop(self, "approval_timeout_seconds")
        layout.prop(self, "require_approval_for_raw_python")
        layout.prop(self, "require_approval_for_provider_downloads")
        layout.prop(self, "require_approval_for_file_delete")
        layout.prop(self, "require_approval_for_external_writes")
        layout.prop(self, "show_diagnostics")
        layout.prop(self, "approved_roots_hint")
        layout.label(text="Permission expansion, raw Python, and third-party operator execution are MCP approval-gated.")


