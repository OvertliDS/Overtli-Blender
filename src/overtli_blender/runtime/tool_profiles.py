"""Built-in Phase 9B tool profile definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ToolProfile:
    name: str
    title: str
    enabled_tool_packs: tuple[str, ...]
    permission_profile: str
    hidden_risky_tools: tuple[str, ...]
    recommended_skill_packs: tuple[str, ...]
    max_visible_tools: int
    default_workflow_hints: tuple[str, ...]
    risk_rank: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("enabled_tool_packs", "hidden_risky_tools", "recommended_skill_packs", "default_workflow_hints"):
            data[key] = list(data[key])
        return data


BUILTIN_TOOL_PROFILES: dict[str, ToolProfile] = {
    "minimal": ToolProfile("minimal", "Minimal", ("core", "scene_intelligence", "error_help", "onboarding"), "read_only", ("execute_code", "delete_objects"), ("diagnostics_review",), 35, ("Inspect before editing.", "Keep tool list compact."), 0),
    "read_only_review": ToolProfile("read_only_review", "Read Only Review", ("core", "scene_intelligence", "project_runtime", "file_access", "addon_knowledge", "error_help", "onboarding"), "read_only", ("execute_code", "download_polyhaven_asset", "install_local_addon"), ("project_repair", "diagnostics_review", "scene_cleanup"), 70, ("Use review and diagnostics tools only.", "Do not mutate the scene."), 0),
    "safe_scene": ToolProfile("safe_scene", "Safe Scene", ("core", "scene_intelligence", "verified_editing", "project_runtime", "file_access", "task_planning", "references", "spatial_measurement", "product_ux", "error_help"), "standard", ("execute_code", "delete_objects", "remove_blender_addon"), ("reference_modeling", "scene_cleanup", "project_repair"), 90, ("Prefer non-destructive scene edits.", "Use approvals for destructive work."), 1),
    "materials": ToolProfile("materials", "Materials", ("core", "scene_intelligence", "materials", "texture_baking", "project_runtime", "file_access", "product_ux", "bundled_skills", "error_help"), "standard", ("delete_materials", "execute_bake_cleanup"), ("pbr_material_authoring", "texture_baking", "texture_painting_preflight"), 100, ("Validate UVs and texture paths first.", "Never overwrite original textures without approval."), 1),
    "modeling": ToolProfile("modeling", "Modeling", ("core", "scene_intelligence", "verified_editing", "advanced_modeling", "reference_construction", "spatial_measurement", "references", "product_ux", "bundled_skills"), "standard", ("execute_construction_cleanup", "apply_sculpt_stroke_batch"), ("reference_modeling", "hard_surface_modeling", "procedural_modeling"), 120, ("Pick modifier or Geometry Nodes methods before brute force edits.",), 1),
    "animation": ToolProfile("animation", "Animation", ("core", "scene_intelligence", "advanced_animation", "action_library", "nla_workflows", "drivers", "rigging", "pose_library", "shot_workflows", "simulation_workflows", "motion_validation", "product_ux"), "standard", ("delete_actions", "remove_drivers", "clear_simulation_cache"), ("animation_blocking", "character_rigging", "cinematic_lighting"), 130, ("Validate rigs, drivers, and NLA before mutation.",), 1),
    "full_standard": ToolProfile("full_standard", "Full Standard", ("core", "scene_intelligence", "verified_editing", "materials", "texture_baking", "geometry_nodes", "animation_presentation", "asset_workflows", "addon_knowledge", "project_runtime", "file_access", "task_planning", "references", "spatial_measurement", "cache_management", "advanced_modeling", "reference_construction", "sculpt_workflows", "cloth_patterns", "advanced_animation", "action_library", "nla_workflows", "drivers", "rigging", "pose_library", "shot_workflows", "simulation_workflows", "motion_validation", "product_ux", "preferences", "tool_profiles", "bundled_skills", "error_help", "onboarding"), "standard", ("execute_code", "remove_blender_addon", "execute_approved_addon_operator"), ("scene_cleanup", "diagnostics_review"), 180, ("Use compact recommendations to avoid overwhelming clients.",), 2),
    "developer": ToolProfile("developer", "Developer", ("core", "scene_intelligence", "addon_knowledge", "addon_interop", "release_diagnostics", "project_runtime", "file_access", "preferences", "tool_profiles", "error_help", "onboarding"), "developer", ("execute_code", "enable_blender_addon", "execute_approved_addon_operator"), ("addon_development", "diagnostics_review", "project_repair"), 140, ("Inspect addon source read-only before any execution.", "Exact approval is required for third-party operators."), 3),
}


def list_tool_profiles() -> dict[str, Any]:
    return {"status": "success", "profiles": [profile.to_dict() for profile in BUILTIN_TOOL_PROFILES.values()]}


def get_profile(name: str) -> ToolProfile | None:
    return BUILTIN_TOOL_PROFILES.get(name)


def preview_profile_change(current_name: str, requested_name: str) -> dict[str, Any]:
    current = get_profile(current_name) or BUILTIN_TOOL_PROFILES["safe_scene"]
    requested = get_profile(requested_name)
    if not requested:
        return {"status": "error", "message": f"Unknown tool profile: {requested_name}"}
    return {
        "status": "success",
        "current_profile": current.to_dict(),
        "requested_profile": requested.to_dict(),
        "enables_packs": sorted(set(requested.enabled_tool_packs) - set(current.enabled_tool_packs)),
        "disables_packs": sorted(set(current.enabled_tool_packs) - set(requested.enabled_tool_packs)),
        "expands_risk": requested.risk_rank > current.risk_rank,
        "requires_approval": requested.risk_rank > current.risk_rank,
    }


def recommend_profile(task_description: str, current_context: dict[str, Any] | None = None) -> dict[str, Any]:
    text = f"{task_description} {current_context or {}}".lower()
    if any(term in text for term in ("addon", "operator", "python", "developer", "source")):
        name = "developer"
    elif any(term in text for term in ("animation", "rig", "pose", "nla", "driver", "shot")):
        name = "animation"
    elif any(term in text for term in ("material", "texture", "bake", "uv", "pbr")):
        name = "materials"
    elif any(term in text for term in ("model", "mesh", "reference", "hard surface", "cloth", "sculpt")):
        name = "modeling"
    elif any(term in text for term in ("review", "diagnose", "inspect", "read only")):
        name = "read_only_review"
    else:
        name = "safe_scene"
    return {"status": "success", "recommended_profile": BUILTIN_TOOL_PROFILES[name].to_dict(), "reason": f"Matched task terms to {name} profile."}
