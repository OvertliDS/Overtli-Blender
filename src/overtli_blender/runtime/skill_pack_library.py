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


BUNDLED_SKILL_PACKS: dict[str, BundledSkillPack] = {
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
