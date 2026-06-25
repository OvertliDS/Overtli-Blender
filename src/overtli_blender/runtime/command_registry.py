"""Single-source command registry for runtime governance and discovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from overtli_blender.common.permissions import RiskLevel
from overtli_blender.common.safety import build_command_safety_map


CATEGORIES = {
    "core",
    "scene",
    "project",
    "workspace",
    "verification",
    "editing",
    "materials",
    "textures",
    "baking",
    "geometry_nodes",
    "selection",
    "deformation",
    "sculpting",
    "animation",
    "rigging",
    "rendering",
    "assets",
    "files",
    "addon_management",
    "knowledge",
    "diagnostics",
    "release",
    "cache_management",
    "task_planning",
    "references",
    "spatial_measurement",
    "rename",
}

TOOL_PACKS = {
    "core",
    "scene_intelligence",
    "verified_editing",
    "materials",
    "geometry_nodes",
    "animation_presentation",
    "asset_workflows",
    "addon_knowledge",
    "release_diagnostics",
    "project_runtime",
    "file_access",
    "task_planning",
    "references",
    "spatial_measurement",
    "cache_management",
    "texture_baking",
}

GOVERNANCE_COMMANDS = {
    "get_system_status",
    "discover_tool_packs",
    "get_tool_pack",
    "search_tools",
    "get_tool_spec",
    "get_recommended_tools_for_task",
    "prepare_operation",
    "get_pending_approvals",
    "approve_operation",
    "deny_operation",
    "execute_approved_operation",
    "expire_approval",
    "get_operation_status",
    "list_recent_operations",
    "cancel_operation",
    "get_operation_log",
    "get_permission_profile",
    "set_permission_profile",
    "get_capability_policy",
    "validate_command_capabilities",
    "get_log_status",
    "export_operation_log",
    "get_command_registry_report",
}

MCP_ALIAS_COMMANDS = {
    "execute_blender_code": "execute_code",
    "generate_hyper3d_model_via_images": "create_rodin_job",
    "generate_hyper3d_model_via_text": "create_rodin_job",
}


@dataclass(frozen=True)
class CommandSpec:
    name: str
    title: str
    description: str
    category: str
    tool_pack: str
    service_name: str
    handler_method: str
    operation_type: str
    risk_level: str
    read_only: bool
    destructive: bool
    idempotent: bool
    requires_approval: bool
    requires_confirmation: bool
    supports_progress: bool
    supports_cancel: bool
    timeout_seconds: int
    rollback_strategy: str | None
    allowed_capabilities: tuple[str, ...] = field(default_factory=tuple)
    filesystem_access: str = "none"
    network_access: str = "none"
    blender_version_notes: str = ""
    input_schema_ref: str | None = None
    output_schema_ref: str | None = None
    smoke_flags: tuple[str, ...] = field(default_factory=tuple)
    mcp_tool_module: str | None = None
    public: bool = True
    deprecated: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("allowed_capabilities", "smoke_flags", "tags"):
            data[key] = list(data[key])
        return data


def _title(name: str) -> str:
    return name.replace("_", " ").title()


def _category(name: str, operation_type: str) -> str:
    lowered = name.lower()
    if any(marker in lowered for marker in ("reference", "landmark")):
        return "references"
    if any(marker in lowered for marker in ("distance", "angle", "area", "volume", "unit", "bounds", "raycast", "nearest", "intersection", "clearance", "alignment", "scale_ratio", "measurement")):
        return "spatial_measurement"
    if any(marker in lowered for marker in ("cache", "artifact", "orphan")):
        return "cache_management"
    if any(marker in lowered for marker in ("task", "revision", "session_time", "recent_operations", "changes_since", "operation_duration")):
        return "task_planning"
    if any(marker in lowered for marker in ("approved_root", "path_access", "project_text_file", "file_delete", "file_access_policy", "scan_project_files", "copy_file_into_project")):
        return "files"
    if any(marker in lowered for marker in ("project_workspace", "project_layout", "project_backup", "project_dependencies", "blend_file", "save_project_as", "register_blend_file")) or name == "get_project_status":
        return "project"
    if name in GOVERNANCE_COMMANDS:
        return "core"
    if "geometry_node" in lowered or operation_type == "GEOMETRY_NODES":
        return "geometry_nodes"
    if any(marker in lowered for marker in ("bake", "packed_texture", "pack_texture", "channel_pack")):
        return "baking"
    if any(marker in lowered for marker in ("material", "shader")):
        return "materials"
    if any(marker in lowered for marker in ("texture", "image", "uv")):
        return "textures"
    if "rename" in lowered:
        return "rename"
    if any(marker in lowered for marker in ("asset", "import", "export", "blend", "dependency", "scene_kit")):
        return "assets"
    if any(marker in lowered for marker in ("addon", "snippet", "skill", "api_docs", "review_package", "knowledge")):
        return "addon_management" if "addon" in lowered else "knowledge"
    if any(marker in lowered for marker in ("animation", "timeline", "keyframe", "camera", "light", "render", "compositor", "presentation")):
        return "animation" if "animation" in lowered or "timeline" in lowered or "keyframe" in lowered else "rendering"
    if any(marker in lowered for marker in ("rig", "armature", "driver", "physics", "pose")):
        return "rigging"
    if any(marker in lowered for marker in ("selection", "vertex_group", "shape_key", "lattice", "deformation", "sculpt", "measure")):
        return "deformation" if "deform" in lowered or "shape_key" in lowered or "lattice" in lowered else "selection"
    if any(marker in lowered for marker in ("workspace", "todo", "journal", "snapshot", "rollback", "undo")):
        return "workspace"
    if operation_type in {"OBSERVE", "VERIFY"}:
        return "verification" if operation_type == "VERIFY" else "scene"
    if operation_type in {"CREATE", "EDIT", "CLEANUP", "ROLLBACK"}:
        return "editing"
    return "core"


def _tool_pack(category: str) -> str:
    if category == "project":
        return "project_runtime"
    if category == "files":
        return "file_access"
    if category == "task_planning":
        return "task_planning"
    if category == "references":
        return "references"
    if category in {"spatial_measurement", "rename"}:
        return "spatial_measurement"
    if category == "cache_management":
        return "cache_management"
    if category in {"core", "project", "workspace", "diagnostics"}:
        return "core"
    if category in {"scene", "verification", "selection", "deformation", "sculpting"}:
        return "scene_intelligence" if category in {"scene", "verification"} else "verified_editing"
    if category == "baking":
        return "texture_baking"
    if category in {"materials", "textures"}:
        return "materials"
    if category == "geometry_nodes":
        return "geometry_nodes"
    if category in {"animation", "rigging", "rendering"}:
        return "animation_presentation"
    if category in {"assets", "files"}:
        return "asset_workflows"
    if category in {"addon_management", "knowledge"}:
        return "addon_knowledge"
    if category == "release":
        return "release_diagnostics"
    return "core"


def _capabilities(metadata: Any, name: str, category: str) -> tuple[str, ...]:
    caps: set[str] = set()
    if metadata.can_mutate_scene:
        caps.add("scene.write")
    else:
        caps.add("scene.read")
    if metadata.strict_blocked or metadata.risk_level == RiskLevel.HIGH:
        caps.add("scene.destructive")
    if metadata.can_write_files:
        caps.add("filesystem.project.write")
    elif category in {"assets", "files", "knowledge", "addon_management"}:
        caps.add("filesystem.project.read")
    if metadata.can_call_network:
        caps.add("network.providers")
    if metadata.can_execute_code or name == "execute_code":
        caps.add("raw_python")
    if category in {"textures", "baking"}:
        caps.add("texture.pack" if "pack" in name else "texture.bake")
    if category == "knowledge":
        caps.add("knowledge.read")
        if metadata.can_write_files:
            caps.add("knowledge.write")
    if category == "addon_management":
        caps.add("addon.inspect")
        if metadata.risk_level == RiskLevel.HIGH:
            caps.add("addon.manage")
    if metadata.operation_type.value == "EXPORT":
        caps.add("release.export")
    return tuple(sorted(caps))


def _from_safety(name: str, metadata: Any) -> CommandSpec:
    category = _category(name, metadata.operation_type.value)
    read_only = not (metadata.can_mutate_scene or metadata.can_write_files or metadata.can_execute_code or metadata.can_call_network)
    high_risk = metadata.risk_level == RiskLevel.HIGH
    destructive = metadata.strict_blocked or metadata.operation_type.value in {"CLEANUP", "ROLLBACK"} or "delete" in name or "remove" in name
    return CommandSpec(
        name=name,
        title=_title(name),
        description=f"{_title(name)} command ({metadata.operation_type.value.lower()}).",
        category=category,
        tool_pack=_tool_pack(category),
        service_name="BlenderCommandServer",
        handler_method=name,
        operation_type=metadata.operation_type.value,
        risk_level=metadata.risk_level.value,
        read_only=read_only,
        destructive=destructive,
        idempotent=read_only,
        requires_approval=high_risk or destructive,
        requires_confirmation=high_risk or metadata.strict_blocked,
        supports_progress=metadata.can_write_files or metadata.operation_type.value in {"RENDER", "EXPORT", "IMPORT"} or "bake" in name,
        supports_cancel=metadata.can_write_files or metadata.operation_type.value in {"RENDER", "EXPORT", "IMPORT"} or "bake" in name,
        timeout_seconds=300 if "bake" in name else (120 if metadata.operation_type.value in {"RENDER", "IMPORT", "EXPORT"} else 30),
        rollback_strategy="scene_snapshot" if metadata.can_mutate_scene else ("artifact_cleanup" if metadata.can_write_files else None),
        allowed_capabilities=_capabilities(metadata, name, category),
        filesystem_access="project_write" if metadata.can_write_files else "none",
        network_access="provider" if metadata.can_call_network else "none",
        blender_version_notes="Uses current addon compatibility guards.",
        input_schema_ref=f"socket:{name}:input",
        output_schema_ref=f"socket:{name}:output",
        smoke_flags=("--phase7b-full",) if name in GOVERNANCE_COMMANDS else (),
        mcp_tool_module=None,
        tags=tuple(sorted({category, _tool_pack(category), metadata.operation_type.value.lower(), name.replace("_", " "), *(("bake", "baking", "texture baking planned") if category in {"materials", "textures"} else ())})),
    )


def _governance_specs() -> dict[str, CommandSpec]:
    specs: dict[str, CommandSpec] = {}
    for name in GOVERNANCE_COMMANDS:
        destructive = name in {"execute_approved_operation", "set_permission_profile"}
        specs[name] = CommandSpec(
            name=name,
            title=_title(name),
            description=f"Runtime governance command for {_title(name).lower()}.",
            category="core" if name not in {"get_log_status", "export_operation_log"} else "diagnostics",
            tool_pack="core" if name not in {"get_log_status", "export_operation_log"} else "release_diagnostics",
            service_name="RuntimeGovernanceService",
            handler_method=name,
            operation_type="VERIFY" if not destructive else "EDIT",
            risk_level="LOW" if not destructive else "MEDIUM",
            read_only=not destructive,
            destructive=False,
            idempotent=not destructive,
            requires_approval=name == "set_permission_profile",
            requires_confirmation=name == "set_permission_profile",
            supports_progress=name in {"execute_approved_operation"},
            supports_cancel=name in {"execute_approved_operation", "cancel_operation"},
            timeout_seconds=30,
            rollback_strategy=None,
            allowed_capabilities=("scene.read",) if not destructive else ("scene.write",),
            filesystem_access="project_read" if "log" in name else "none",
            network_access="none",
            smoke_flags=("--phase7b-full",),
            mcp_tool_module="governance_tools",
            tags=("governance", "phase7b", name.replace("_", " ")),
        )
    return specs


def build_command_registry() -> dict[str, CommandSpec]:
    specs = {name: _from_safety(name, metadata) for name, metadata in build_command_safety_map().items()}
    specs.update(_governance_specs())
    for alias, target in MCP_ALIAS_COMMANDS.items():
        target_spec = specs[target]
        specs[alias] = CommandSpec(
            **{
                **target_spec.to_dict(),
                "name": alias,
                "title": _title(alias),
                "description": f"MCP compatibility wrapper for `{target}`.",
                "handler_method": target,
                "input_schema_ref": f"mcp:{alias}:input",
                "output_schema_ref": f"mcp:{alias}:output",
                "deprecated": False,
                "tags": tuple(sorted(set(target_spec.tags + ("mcp wrapper", alias.replace("_", " "))))),
                "allowed_capabilities": tuple(target_spec.allowed_capabilities),
                "smoke_flags": tuple(target_spec.smoke_flags),
            }
        )
    return dict(sorted(specs.items()))


def list_command_specs(public_only: bool = True) -> list[CommandSpec]:
    specs = build_command_registry().values()
    if public_only:
        specs = [spec for spec in specs if spec.public]
    return list(specs)


def get_command_spec(name: str) -> CommandSpec | None:
    return build_command_registry().get(name)


def command_registry_report() -> dict[str, Any]:
    specs = build_command_registry()
    envelope_pending = sorted(name for name in specs if name not in GOVERNANCE_COMMANDS)
    return {
        "status": "success",
        "command_count": len(specs),
        "categories": sorted({spec.category for spec in specs.values()}),
        "tool_packs": sorted({spec.tool_pack for spec in specs.values()}),
        "governance_commands": sorted(GOVERNANCE_COMMANDS),
        "response_envelope_migration": {
            "applied_to": sorted(GOVERNANCE_COMMANDS),
            "migration_pending": envelope_pending,
        },
    }
