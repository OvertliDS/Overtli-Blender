"""User-facing error catalog and remediation hints."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ErrorCatalogEntry:
    code: str
    title: str
    plain_language_summary: str
    technical_summary: str
    likely_causes: tuple[str, ...]
    safe_retry: bool
    user_actions: tuple[str, ...]
    related_tools: tuple[str, ...]
    docs_links: tuple[str, ...]
    severity: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, tuple):
                data[key] = list(value)
        return data


def _entry(code: str, title: str, summary: str, actions: tuple[str, ...], severity: str = "medium", retry: bool = True) -> ErrorCatalogEntry:
    return ErrorCatalogEntry(code, title, summary, summary, ("missing setup", "disabled tool pack", "permission gate", "invalid target"), retry, actions, ("get_runtime_dashboard", "get_setup_status", "explain_error"), ("docs/error_handling.md",), severity)


ERROR_CATALOG: dict[str, ErrorCatalogEntry] = {
    code: _entry(code, code.replace("_", " ").title(), summary, actions, severity)
    for code, summary, actions, severity in [
        ("BLENDER_NOT_CONNECTED", "The MCP client cannot reach the Blender addon socket.", ("Start Blender, enable the addon, and start the socket server.",), "high"),
        ("ADDON_NOT_LOADED", "Blender is running but the Overtli addon is not active.", ("Enable or reload the addon in Blender preferences.",), "high"),
        ("PROJECT_NOT_INITIALIZED", "The project workspace has not been initialized.", ("Run initialize_project_workspace or the onboarding checklist.",), "medium"),
        ("UNSAVED_BLEND", "The .blend file must be saved before this operation.", ("Save the blend file or choose a project workspace.",), "medium"),
        ("PATH_NOT_APPROVED", "The requested path is outside approved roots.", ("Add an approved root with confirmation or choose a project path.",), "high"),
        ("APPROVAL_REQUIRED", "This command needs explicit approval before it can run.", ("Review the approval summary and approve only exact intended operations.",), "medium"),
        ("APPROVAL_EXPIRED", "The approval record is no longer valid.", ("Prepare the operation again and approve the fresh request.",), "medium"),
        ("TOOL_PACK_DISABLED", "The active profile hides the requested tool pack.", ("Preview or activate a profile that includes the tool pack.",), "medium"),
        ("COMMAND_NOT_AVAILABLE", "The command is not registered in this runtime.", ("Run get_command_registry_report and verify addon/server versions.",), "high"),
        ("STRICT_MODE_BLOCKED", "Strict safety mode blocked a high-risk command.", ("Use a safer workflow or explicitly change mode with approval.",), "high"),
        ("OBJECT_NOT_FOUND", "The target object was not found.", ("Inspect the scene index and use exact object names.",), "low"),
        ("MATERIAL_NOT_FOUND", "The target material was not found.", ("List materials and use an exact material name.",), "low"),
        ("UV_MISSING", "The mesh does not have the UV data required for this workflow.", ("Create or select a UV map before continuing.",), "medium"),
        ("BAKE_UNSUPPORTED", "The requested bake pass is unsupported or unavailable.", ("Run validate_bake_setup and choose a supported pass.",), "medium"),
        ("SCULPT_UNSUPPORTED", "The sculpt workflow is unavailable for the target.", ("Check sculpt status and use a shape-key or lattice fallback.",), "medium"),
        ("SIMULATION_UNSUPPORTED", "The simulation operation is unsupported for this object or version.", ("Inspect simulation capabilities and choose a supported setup.",), "medium"),
        ("DRIVER_DSL_INVALID", "The driver DSL failed validation.", ("Run validate_driver_dsl and fix the reported field.",), "medium"),
        ("ADDON_SOURCE_UNTRUSTED", "The addon source root is not approved for inspection.", ("Approve only the exact read-only addon source root you intend to scan.",), "high"),
        ("CACHE_CLEANUP_REQUIRES_PLAN", "Cache cleanup requires a plan before execution.", ("Run plan_cache_cleanup and review the generated plan.",), "medium"),
    ]
}


def get_error_catalog() -> dict[str, Any]:
    return {"status": "success", "errors": [entry.to_dict() for entry in ERROR_CATALOG.values()]}


def explain_error(code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = ERROR_CATALOG.get(code)
    if not entry:
        return {"status": "error", "message": f"Unknown error code: {code}"}
    return {"status": "success", "error": entry.to_dict(), "context": context or {}}


def get_remediation_steps(code: str) -> dict[str, Any]:
    entry = ERROR_CATALOG.get(code)
    if not entry:
        return {"status": "error", "message": f"Unknown error code: {code}"}
    return {"status": "success", "code": code, "steps": list(entry.user_actions), "safe_retry": entry.safe_retry}
