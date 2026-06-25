"""Tool pack discovery and command search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .command_registry import CommandSpec, get_command_spec, list_command_specs


@dataclass(frozen=True)
class ToolPack:
    name: str
    title: str
    description: str
    categories: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "categories": list(self.categories),
        }


TOOL_PACK_DEFINITIONS = {
    "core": ToolPack("core", "Core Governance", "Status, permissions, approvals, operations, and tool discovery.", ("core", "workspace", "diagnostics")),
    "scene_intelligence": ToolPack("scene_intelligence", "Scene Intelligence", "Scene inspection, verification, screenshots, and health checks.", ("scene", "verification")),
    "verified_editing": ToolPack("verified_editing", "Verified Editing", "Structured scene edits, deformation, selection, cleanup, and rollback.", ("editing", "selection", "deformation", "sculpting")),
    "materials": ToolPack("materials", "Materials", "Material, shader, texture, preview, and future baking workflows.", ("materials", "textures", "baking")),
    "texture_baking": ToolPack("texture_baking", "Texture Baking", "Bake preflight, target images, native and derived maps, channel packing, validation, relink, and cleanup.", ("baking", "textures")),
    "geometry_nodes": ToolPack("geometry_nodes", "Geometry Nodes", "Geometry Nodes inspection, templates, modifiers, and procedural workflows.", ("geometry_nodes",)),
    "animation_presentation": ToolPack("animation_presentation", "Animation and Presentation", "Animation, rigging, cameras, lighting, rendering, and compositor workflows.", ("animation", "rigging", "rendering")),
    "asset_workflows": ToolPack("asset_workflows", "Asset Workflows", "Local asset library, import/export, dependency, scene kit, and file workflows.", ("assets", "files")),
    "addon_knowledge": ToolPack("addon_knowledge", "Addon and Knowledge", "Addon management, API knowledge, snippets, skill packs, and review packages.", ("addon_management", "knowledge")),
    "release_diagnostics": ToolPack("release_diagnostics", "Release Diagnostics", "Release, diagnostic, log, and packaging support.", ("release", "diagnostics")),
    "project_runtime": ToolPack("project_runtime", "Project Runtime", "Saved/unsaved .blend status, project workspace layout, backups, and dependency collection.", ("project",)),
    "file_access": ToolPack("file_access", "File Access", "Approved roots, canonical path validation, safe text reads/writes, project copies, and delete planning.", ("files",)),
    "task_planning": ToolPack("task_planning", "Task Planning", "Task graph, stale detection, session time, scene revision, and recent operation tracking.", ("task_planning",)),
    "references": ToolPack("references", "References", "Reference image import, placement, calibration, landmarks, and visibility controls.", ("references",)),
    "spatial_measurement": ToolPack("spatial_measurement", "Spatial Measurement", "Distances, angles, bounds, units, raycasts, intersections, and rename planning.", ("spatial_measurement", "rename")),
    "cache_management": ToolPack("cache_management", "Cache Management", "Cache status, cleanup planning, pinning, orphan scanning, and operation history compaction.", ("cache_management",)),
    "advanced_modeling": ToolPack("advanced_modeling", "Advanced Modeling", "Mesh schemas, profiles, curves, modifier stacks, hard-surface assets, validation, and cleanup planning.", ("advanced_modeling", "construction_validation", "geometry_nodes", "verified_editing", "project_runtime")),
    "reference_construction": ToolPack("reference_construction", "Reference Construction", "Reference-driven modeling plans, calibrated measurements, construction steps, and alignment checks.", ("reference_construction", "references", "spatial_measurement")),
    "sculpt_workflows": ToolPack("sculpt_workflows", "Sculpt Workflows", "Sculpt session setup, masks, face sets, shape-key variants, and gated stroke batches.", ("sculpt_workflows", "verified_editing")),
    "cloth_patterns": ToolPack("cloth_patterns", "Cloth Patterns", "Pattern panels, seams, pins, collision setup, and gated cloth preview/cache operations.", ("cloth_patterns", "cache_management")),
    "advanced_animation": ToolPack("advanced_animation", "Advanced Animation", "Animation system inspection, keyframe batches, F-curve editing, retime plans, and motion previews.", ("advanced_animation", "animation", "motion_validation")),
    "action_library": ToolPack("action_library", "Action Library", "Action inventory, deep info, create, duplicate, rename, assign, and approval-gated deletion.", ("action_library", "advanced_animation")),
    "nla_workflows": ToolPack("nla_workflows", "NLA Workflows", "Non-linear animation tracks, strips, muting, validation, and guarded deletion.", ("nla_workflows", "advanced_animation")),
    "drivers": ToolPack("drivers", "Drivers", "Allowlisted driver DSL validation, creation, inspection, and approval-gated removal.", ("drivers", "advanced_animation", "rigging")),
    "rigging": ToolPack("rigging", "Rigging", "Rig templates, control recipes, IK constraints, custom rig properties, and rig validation.", ("rigging",)),
    "pose_library": ToolPack("pose_library", "Pose Library", "Pose inspection, manifest-backed snapshots, pose assets, comparison, and guarded application/deletion.", ("pose_library", "rigging")),
    "shot_workflows": ToolPack("shot_workflows", "Shot Workflows", "Shot ranges, camera cuts, timeline markers, shot plans, and validation.", ("shot_workflows", "rendering")),
    "simulation_workflows": ToolPack("simulation_workflows", "Simulation Workflows", "Simulation capabilities, bounded setup, cache status, and approval-gated preview/bake/clear.", ("simulation_workflows", "cache_management", "cloth_patterns")),
    "motion_validation": ToolPack("motion_validation", "Motion Validation", "Motion, driver, NLA, rig, shot, and simulation validation reports.", ("motion_validation", "advanced_animation", "rigging")),
}


def discover_tool_packs() -> dict[str, Any]:
    specs = list_command_specs()
    counts = {name: 0 for name in TOOL_PACK_DEFINITIONS}
    for spec in specs:
        counts[spec.tool_pack] = counts.get(spec.tool_pack, 0) + 1
    return {
        "status": "success",
        "tool_packs": [{**pack.to_dict(), "command_count": counts.get(name, 0)} for name, pack in TOOL_PACK_DEFINITIONS.items()],
    }


def get_tool_pack(name: str) -> dict[str, Any]:
    pack = TOOL_PACK_DEFINITIONS.get(name)
    if not pack:
        return {"status": "error", "message": f"Unknown tool pack: {name}"}
    commands = [spec.to_dict() for spec in list_command_specs() if spec.tool_pack == name]
    return {"status": "success", "tool_pack": pack.to_dict(), "commands": commands}


def _risk_value(risk: str) -> int:
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3}.get(risk.upper(), 99)


def search_tools(query: str, category: str | None = None, tool_pack: str | None = None, risk_max: str | None = None, limit: int = 20) -> dict[str, Any]:
    terms = [term.lower() for term in query.split() if term.strip()]
    max_value = _risk_value(risk_max) if risk_max else 99
    matches: list[tuple[int, CommandSpec]] = []
    for spec in list_command_specs():
        if category and spec.category != category:
            continue
        if tool_pack and spec.tool_pack != tool_pack:
            continue
        if _risk_value(spec.risk_level) > max_value:
            continue
        haystack = " ".join([
            spec.name,
            spec.title,
            spec.description,
            spec.category,
            spec.tool_pack,
            " ".join(spec.tags),
            " ".join(spec.allowed_capabilities),
        ]).lower()
        score = sum(3 if term in spec.name.lower() else 1 for term in terms if term in haystack)
        if not terms or score:
            matches.append((score, spec))
    matches.sort(key=lambda item: (-item[0], item[1].name))
    return {
        "status": "success",
        "query": query,
        "results": [spec.to_dict() for _, spec in matches[: max(1, min(limit, 50))]],
    }


def get_tool_spec(name: str) -> dict[str, Any]:
    spec = get_command_spec(name)
    if not spec:
        return {"status": "error", "message": f"Unknown tool: {name}"}
    return {"status": "success", "tool": spec.to_dict()}


def get_recommended_tools_for_task(task: str, limit: int = 8) -> dict[str, Any]:
    return search_tools(task, limit=limit)
