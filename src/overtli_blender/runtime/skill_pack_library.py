"""Bundled Phase 9B skill pack library."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BundledSkillPack:
    skill_pack_id: str
    title: str
    intent_patterns: tuple[str, ...]
    method_rules: tuple[str, ...]
    anti_patterns: tuple[str, ...]
    required_inspection: tuple[str, ...]
    tool_packs: tuple[str, ...]
    preflight: tuple[str, ...]
    execution_stages: tuple[str, ...]
    verification_stages: tuple[str, ...]
    rollback_strategy: str
    blender_version_notes: str
    known_limitations: tuple[str, ...]
    examples: tuple[str, ...]
    risk_level: str = "LOW"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, tuple):
                data[key] = list(value)
        return data


def _pack(skill_pack_id: str, title: str, intents: tuple[str, ...], tool_packs: tuple[str, ...], risk: str = "LOW") -> BundledSkillPack:
    return BundledSkillPack(
        skill_pack_id=skill_pack_id,
        title=title,
        intent_patterns=intents,
        method_rules=("inspect first", "prefer non-destructive workflow", "verify before claiming success"),
        anti_patterns=("blind execution", "overwriting user assets", "claiming visual success without evidence"),
        required_inspection=("scene summary", "selection state", "workspace status"),
        tool_packs=tool_packs,
        preflight=("project initialized", "approved roots configured", "relevant tools enabled"),
        execution_stages=("plan", "prepare", "execute gated operations", "verify"),
        verification_stages=("structural check", "artifact or screenshot when applicable", "operation summary"),
        rollback_strategy="scene snapshot or generated artifact cleanup depending on operation",
        blender_version_notes="Designed against Blender 5.1 API mirror with conservative fallbacks for older versions.",
        known_limitations=("Does not execute workflows automatically.", "High-risk operations still require explicit approval."),
        examples=intents,
        risk_level=risk,
    )


def _detailed_pack(
    skill_pack_id: str,
    title: str,
    intents: tuple[str, ...],
    method_rules: tuple[str, ...],
    anti_patterns: tuple[str, ...],
    required_inspection: tuple[str, ...],
    tool_packs: tuple[str, ...],
    preflight: tuple[str, ...],
    execution_stages: tuple[str, ...],
    verification_stages: tuple[str, ...],
    rollback_strategy: str,
    examples: tuple[str, ...],
    risk: str = "LOW",
    limitations: tuple[str, ...] = (),
) -> BundledSkillPack:
    return BundledSkillPack(
        skill_pack_id=skill_pack_id,
        title=title,
        intent_patterns=intents,
        method_rules=method_rules,
        anti_patterns=anti_patterns,
        required_inspection=required_inspection,
        tool_packs=tool_packs,
        preflight=preflight,
        execution_stages=execution_stages,
        verification_stages=verification_stages,
        rollback_strategy=rollback_strategy,
        blender_version_notes="Designed against the current Overtli-Blender command registry and Blender API compatibility guards.",
        known_limitations=limitations or ("Guidance pack only; use matching MCP tools to execute.",),
        examples=examples,
        risk_level=risk,
    )


BUNDLED_SKILL_PACKS: dict[str, BundledSkillPack] = {
    "blender_scene_planning": _detailed_pack(
        "blender_scene_planning",
        "Blender Scene Planning",
        ("plan a Blender scene", "make a task checklist", "organize a multi-step edit", "scene supervisor workflow"),
        (
            "start from scene, selection, project, health, and revision inspection",
            "turn vague requests into ordered tasks and todos before mutation",
            "choose structured tools or skill packs per stage",
            "record evidence on completed tasks instead of claiming from intent",
        ),
        ("one-shot generation without inspection", "skipping task status updates", "marking work verified without evidence"),
        ("get_scene_info", "get_scene_index", "get_scene_health", "get_project_status", "get_scene_revision"),
        ("core", "task_planning", "scene_intelligence", "project_runtime", "product_ux", "bundled_skills"),
        ("create or inspect project workspace", "search relevant tools and skill packs", "identify destructive steps"),
        ("create_scene_plan", "create workspace tasks/todos", "execute stage by stage", "complete tasks with evidence"),
        ("scene health", "object/material counts", "snapshot or screenshot when available", "task evidence"),
        "Use verification snapshots and workspace task evidence; for failed stages, resume from the last verified task.",
        ("Plan and build a small furnished room.", "Audit a scene, list fixes, then execute them safely."),
    ),
    "spatial_snap_transform": _detailed_pack(
        "spatial_snap_transform",
        "Spatial Snap and Transform",
        ("place objects on the floor", "snap object to surface", "align to another object", "fix scale rotation location", "avoid clipping"),
        (
            "measure dimensions, bounds, anchors, and ground contact before moving",
            "preserve explicit anchors such as bottom_center, origin, center, or selected contact point",
            "use snapping, cursor placement, transforms, and surface alignment deliberately",
            "validate clearance, intersections, and scene composition after placement",
        ),
        ("placing by eye only", "ignoring scale application warnings", "leaving objects half below floor or floating"),
        ("measure_object", "measure_distance", "validate_ground_contact", "validate_scene_composition", "get_object_deep_info"),
        ("spatial_measurement", "verified_editing", "reference_construction", "scene_intelligence"),
        ("inspect target and support object bounds", "choose anchor and relationship", "snapshot if existing assets move"),
        ("transform_object_dimensions", "align_object_to_surface", "transform_object", "run_verified_edit_batch"),
        ("ground/contact validation", "clearance/intersection report", "composition validation"),
        "Create a snapshot before moving existing user objects; restore or transform back from recorded pre-move values.",
        ("Put a cube exactly on the floor.", "Resize a prop and keep its base planted.", "Align a chair to a table without clipping."),
        "MEDIUM",
    ),
    "scripted_blender_workflows": _detailed_pack(
        "scripted_blender_workflows",
        "Scripted Blender Workflows",
        ("write a Blender Python script", "use bpy for unsupported operation", "automate a custom edit", "register reusable script"),
        (
            "prefer structured MCP tools first and script only the missing Blender API operation",
            "keep code short, scoped, idempotent when possible, and named-object based",
            "print structural evidence and return enough state for verification",
            "use shared handles for multi-step script workflows",
        ),
        ("large unreviewed scripts", "filesystem/network calls in raw Blender scripts", "silent mutation without verification"),
        ("get_scene_info", "get_object_deep_info", "search_blender_api_docs", "get_blender_api_topic", "get_safety_status"),
        ("core", "addon_knowledge", "addon_interop", "release_diagnostics", "project_runtime"),
        ("inspect scene and API topic", "snapshot before risky mutation", "confirm high-risk intent"),
        ("execute_code", "execute_blender_code", "register_context_script", "execute_context_script"),
        ("printed script evidence", "scene/object readback", "snapshot diff or health check"),
        "Use pre-script snapshots and keep scripts small enough to reverse manually or through rollback tools.",
        ("Use bpy to set a property not covered by a structured tool.", "Register a reusable scene audit script."),
        "HIGH",
        ("The addon scanner blocks dangerous call patterns; scripts with those patterns must be redesigned.",),
    ),
    "workspace_project_safety": _detailed_pack(
        "workspace_project_safety",
        "Workspace and Project Safety",
        ("set up project workspace", "save unsaved blend safely", "manage approved roots", "read write project files"),
        (
            "resolve workspace before file operations",
            "use temp workspaces for unsaved blends and promote intentionally",
            "keep file writes inside approved project roots",
            "plan external writes, project moves, and deletes before execution",
        ),
        ("writing beside the addon source", "assuming unsaved blends have a project root", "deleting files without plan approval"),
        ("get_project_status", "resolve_project_workspace", "get_file_access_policy", "list_approved_roots"),
        ("project_runtime", "file_access", "task_planning", "verification"),
        ("detect loaded project folder", "initialize temp or project workspace", "check approved roots"),
        ("initialize_temp_workspace", "initialize_project_workspace", "promote_temp_workspace_to_project", "write_project_text_file"),
        ("validate_project_layout", "get_project_status", "operation summary", "file existence checks"),
        "Use backups and project move/copy plans before replacing or relocating project files.",
        ("Create a safe workspace for an unsaved blend.", "Collect references into the project folder."),
        "MEDIUM",
    ),
    "cleanup_snapshot_recovery": _detailed_pack(
        "cleanup_snapshot_recovery",
        "Cleanup, Snapshot, and Recovery",
        ("clean scene", "delete generated objects", "clear test artifacts", "rollback a bad edit", "remove empty collections"),
        (
            "plan cleanup scope before deletion",
            "prefer generated-prefix cleanup or exact names",
            "create snapshots before destructive scene operations",
            "use dry-run outputs and confirmation flags for destructive execution",
        ),
        ("broad delete all without scope", "cleanup without snapshot", "ignoring empty-collection and material ownership warnings"),
        ("scene_cleanup_plan", "create_verification_snapshot", "get_scene_health", "get_scene_index"),
        ("verified_editing", "cache_management", "project_runtime", "file_access", "scene_intelligence"),
        ("snapshot current state", "dry-run cleanup plan", "confirm exact scope"),
        ("clear_scene", "delete_objects", "delete_collection", "execute_cache_cleanup", "rollback_to_scene_snapshot"),
        ("post-cleanup scene health", "object/collection/material counts", "snapshot rollback readiness"),
        "Use scene snapshots for rollback and keep file-delete/cache cleanup behind approval ids and exact paths.",
        ("Remove generated OVERTLI test objects.", "Rollback after a failed scene generation attempt."),
        "HIGH",
    ),
    "reference_modeling": _pack("reference_modeling", "Reference Modeling", ("match a reference image", "model from reference"), ("reference_construction", "spatial_measurement", "advanced_modeling")),
    "hard_surface_modeling": _pack("hard_surface_modeling", "Hard Surface Modeling", ("hard surface armor", "panel lines", "beveled prop"), ("advanced_modeling", "geometry_nodes", "verified_editing")),
    "organic_proportion_editing": _pack("organic_proportion_editing", "Organic Proportion Editing", ("bigger body part", "stylized proportion"), ("verified_editing", "sculpt_workflows", "spatial_measurement")),
    "procedural_modeling": _pack("procedural_modeling", "Procedural Modeling", ("procedural building", "scatter", "radial array"), ("geometry_nodes", "advanced_modeling")),
    "geometry_nodes_patterns": _pack("geometry_nodes_patterns", "Geometry Nodes Patterns", ("geometry nodes recipe", "node group"), ("geometry_nodes",)),
    "pbr_material_authoring": _pack("pbr_material_authoring", "PBR Material Authoring", ("pbr material", "normal roughness metallic"), ("materials", "texture_baking")),
    "texture_baking": _pack("texture_baking", "Texture Baking", ("bake normal and ORM maps", "bake textures"), ("texture_baking", "materials"), "MEDIUM"),
    "texture_painting_preflight": _pack("texture_painting_preflight", "Texture Painting Preflight", ("paint decal", "texture paint"), ("materials", "texture_baking")),
    "sculpt_refinement": _pack("sculpt_refinement", "Sculpt Refinement", ("sculpt refinement", "smooth region"), ("sculpt_workflows", "verified_editing"), "MEDIUM"),
    "cloth_pattern_workflow": _pack("cloth_pattern_workflow", "Cloth Pattern Workflow", ("cloth cape", "cloth panel"), ("cloth_patterns", "simulation_workflows"), "MEDIUM"),
    "character_rigging": _pack("character_rigging", "Character Rigging", ("character rig", "ik chain"), ("rigging", "pose_library"), "MEDIUM"),
    "animation_blocking": _pack("animation_blocking", "Animation Blocking", ("animation shot", "blocking keys"), ("advanced_animation", "action_library", "shot_workflows")),
    "product_rendering": _pack("product_rendering", "Product Rendering", ("product render", "studio shot"), ("animation_presentation", "materials")),
    "cinematic_lighting": _pack("cinematic_lighting", "Cinematic Lighting", ("cinematic lighting", "shot lighting"), ("animation_presentation", "shot_workflows")),
    "game_asset_export": _pack("game_asset_export", "Game Asset Export", ("game-ready prop", "export glb"), ("asset_workflows", "texture_baking"), "MEDIUM"),
    "scene_cleanup": _pack("scene_cleanup", "Scene Cleanup", ("clean imported model", "scene cleanup"), ("verified_editing", "cache_management"), "MEDIUM"),
    "addon_development": _pack("addon_development", "Addon Development", ("create addon", "validate addon"), ("addon_knowledge", "addon_interop", "release_diagnostics"), "HIGH"),
    "project_repair": _pack("project_repair", "Project Repair", ("repair broken project textures", "missing assets"), ("project_runtime", "file_access", "asset_workflows")),
    "diagnostics_review": _pack("diagnostics_review", "Diagnostics Review", ("diagnose addon connection", "why failed"), ("release_diagnostics", "error_help", "onboarding")),
}


def list_bundled_skill_packs() -> dict[str, Any]:
    return {"status": "success", "skill_packs": [pack.to_dict() for pack in BUNDLED_SKILL_PACKS.values()]}


def get_bundled_skill_pack(skill_pack_id: str) -> dict[str, Any]:
    pack = BUNDLED_SKILL_PACKS.get(skill_pack_id)
    if not pack:
        return {"status": "error", "message": f"Unknown bundled skill pack: {skill_pack_id}"}
    return {"status": "success", "skill_pack": pack.to_dict()}


def search_bundled_skill_packs(query: str, top_k: int = 10) -> dict[str, Any]:
    terms = [term.lower() for term in query.split() if term.strip()]
    matches = []
    for pack in BUNDLED_SKILL_PACKS.values():
        haystack = " ".join([pack.skill_pack_id, pack.title, *pack.intent_patterns, *pack.tool_packs, *pack.examples]).lower()
        score = sum(3 if term in pack.skill_pack_id else 1 for term in terms if term in haystack)
        if not terms or score:
            matches.append((score, pack))
    matches.sort(key=lambda item: (-item[0], item[1].skill_pack_id))
    return {"status": "success", "query": query, "results": [pack.to_dict() for _, pack in matches[: max(1, min(top_k, 25))]]}


def recommend_skill_packs(task_description: str) -> dict[str, Any]:
    results = search_bundled_skill_packs(task_description, top_k=5)["results"]
    return {"status": "success", "recommendations": results, "reason": "Ranked by task term matches."}
