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
    "geometry_nodes": ToolPack("geometry_nodes", "Geometry Nodes", "Geometry Nodes inspection, templates, modifiers, and procedural workflows.", ("geometry_nodes",)),
    "animation_presentation": ToolPack("animation_presentation", "Animation and Presentation", "Animation, rigging, cameras, lighting, rendering, and compositor workflows.", ("animation", "rigging", "rendering")),
    "asset_workflows": ToolPack("asset_workflows", "Asset Workflows", "Local asset library, import/export, dependency, scene kit, and file workflows.", ("assets", "files")),
    "addon_knowledge": ToolPack("addon_knowledge", "Addon and Knowledge", "Addon management, API knowledge, snippets, skill packs, and review packages.", ("addon_management", "knowledge")),
    "release_diagnostics": ToolPack("release_diagnostics", "Release Diagnostics", "Release, diagnostic, log, and packaging support.", ("release", "diagnostics")),
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
