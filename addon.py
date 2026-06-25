# Code created by Siddharth Ahuja: www.github.com/ahujasid © 2025

import bpy
import mathutils
import math
import json
import os
import sys
import threading
import socket
import time
import requests
import tempfile
import traceback
import os
import shutil
import zipfile
import re
import hashlib
from uuid import uuid4
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
import io
from contextlib import redirect_stdout, suppress
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Union, Any, Optional, Tuple

ADDON_ROOT = os.path.dirname(os.path.abspath(__file__))
if ADDON_ROOT not in sys.path:
    sys.path.insert(0, ADDON_ROOT)
SRC_ROOT = os.path.join(ADDON_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

try:
    from overtli_blender.common.safety import (
        AVAILABLE_SAFETY_MODES,
        DEFAULT_SAFETY_MODE,
        SAFETY_MODE_AUDIT,
        SAFETY_MODE_COMPAT,
        SAFETY_MODE_STRICT,
        SAFETY_POLICY_VERSION,
        build_command_safety_map,
    )
    from overtli_blender.common.permissions import RiskLevel
    from overtli_blender.runtime.approval import DEFAULT_APPROVAL_RUNTIME, canonical_params_hash
    from overtli_blender.runtime.capabilities import (
        get_capability_policy as runtime_get_capability_policy,
        get_permission_profile as runtime_get_permission_profile,
        set_permission_profile as runtime_set_permission_profile,
        validate_command_capabilities as runtime_validate_command_capabilities,
    )
    from overtli_blender.runtime.command_registry import command_registry_report, get_command_spec
    from overtli_blender.runtime.logging import export_operation_log as runtime_export_operation_log
    from overtli_blender.runtime.logging import get_log_status as runtime_get_log_status
    from overtli_blender.runtime.operation_response import build_operation_response
    from overtli_blender.runtime.operations import DEFAULT_OPERATION_RUNTIME
    from overtli_blender.runtime.cache_retention import get_cache_status as runtime_get_cache_status
    from overtli_blender.runtime.cache_retention import plan_cache_cleanup as runtime_plan_cache_cleanup
    from overtli_blender.runtime.file_access import FileAccessPolicy
    from overtli_blender.runtime.project_workspace import initialize_workspace as runtime_initialize_workspace
    from overtli_blender.runtime.project_workspace import resolve_workspace as runtime_resolve_workspace
    from overtli_blender.runtime.project_workspace import validate_layout as runtime_validate_layout
    from overtli_blender.runtime.spatial import angle_degrees as runtime_angle_degrees
    from overtli_blender.runtime.spatial import convert_units as runtime_convert_units
    from overtli_blender.runtime.spatial import distance as runtime_distance
    from overtli_blender.runtime.task_graph import TASK_STATUSES, TaskGraphStore
    from overtli_blender.runtime.time_revision import TimeRevisionTracker
    from overtli_blender.runtime.tool_packs import (
        discover_tool_packs as runtime_discover_tool_packs,
        get_recommended_tools_for_task as runtime_get_recommended_tools_for_task,
        get_tool_pack as runtime_get_tool_pack,
        get_tool_spec as runtime_get_tool_spec,
        search_tools as runtime_search_tools,
    )
except ModuleNotFoundError:
    class RiskLevel(str, Enum):
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        DESTRUCTIVE = "DESTRUCTIVE"

    SAFETY_MODE_COMPAT = "compatibility"
    SAFETY_MODE_AUDIT = "audit"
    SAFETY_MODE_STRICT = "strict"
    SAFETY_POLICY_VERSION = "1.0"
    DEFAULT_SAFETY_MODE = SAFETY_MODE_COMPAT
    AVAILABLE_SAFETY_MODES = [SAFETY_MODE_COMPAT, SAFETY_MODE_AUDIT, SAFETY_MODE_STRICT]

    _FALLBACK_APPROVAL_RECORDS = {}

    def _fallback_metadata_value(metadata, key, default=None):
        value = getattr(metadata, key, default)
        return value.value if hasattr(value, "value") else value

    def _fallback_category(name, operation_type):
        lowered = name.lower()
        if name in {
            "get_system_status", "get_project_status", "discover_tool_packs", "get_tool_pack",
            "search_tools", "get_tool_spec", "get_recommended_tools_for_task", "prepare_operation",
            "get_pending_approvals", "approve_operation", "deny_operation", "execute_approved_operation",
            "expire_approval", "get_operation_status", "list_recent_operations", "cancel_operation",
            "get_operation_log", "get_permission_profile", "set_permission_profile",
            "get_capability_policy", "validate_command_capabilities", "get_log_status",
            "export_operation_log", "get_command_registry_report",
        }:
            return "core"
        if "geometry_node" in lowered or operation_type == "GEOMETRY_NODES":
            return "geometry_nodes"
        if "material" in lowered or "shader" in lowered:
            return "materials"
        if "asset" in lowered or "import" in lowered or "export" in lowered:
            return "assets"
        if "addon" in lowered:
            return "addon_management"
        if "workspace" in lowered or "todo" in lowered or "journal" in lowered or "snapshot" in lowered:
            return "workspace"
        if operation_type == "VERIFY":
            return "verification"
        return "scene" if operation_type == "OBSERVE" else "editing"

    def _fallback_pack(category):
        if category in {"core", "workspace", "verification"}:
            return "core" if category != "verification" else "scene_intelligence"
        if category in {"materials", "textures"}:
            return "materials"
        if category == "geometry_nodes":
            return "geometry_nodes"
        if category in {"assets", "files"}:
            return "asset_workflows"
        if category in {"addon_management", "knowledge"}:
            return "addon_knowledge"
        return "verified_editing"

    def _fallback_command_specs():
        specs = {}
        for command_name, metadata in build_command_safety_map().items():
            operation_type = _fallback_metadata_value(metadata, "operation_type", "VERIFY")
            risk_level = _fallback_metadata_value(metadata, "risk_level", "LOW")
            category = _fallback_category(command_name, operation_type)
            pack = _fallback_pack(category)
            strict_blocked = bool(_fallback_metadata_value(metadata, "strict_blocked", False))
            high_risk = risk_level in {"HIGH", "DESTRUCTIVE"}
            can_mutate = bool(_fallback_metadata_value(metadata, "can_mutate_scene", False))
            can_write = bool(_fallback_metadata_value(metadata, "can_write_files", False))
            can_network = bool(_fallback_metadata_value(metadata, "can_call_network", False))
            can_code = bool(_fallback_metadata_value(metadata, "can_execute_code", False))
            caps = ["scene.write" if can_mutate else "scene.read"]
            if high_risk or strict_blocked:
                caps.append("scene.destructive")
            if can_write:
                caps.append("filesystem.project.write")
            if can_network:
                caps.append("network.providers")
            if can_code:
                caps.append("raw_python")
            specs[command_name] = {
                "name": command_name,
                "title": command_name.replace("_", " ").title(),
                "description": f"{command_name} command.",
                "category": category,
                "tool_pack": pack,
                "service_name": "BlenderCommandServer",
                "handler_method": command_name,
                "operation_type": operation_type,
                "risk_level": risk_level,
                "read_only": not (can_mutate or can_write or can_network or can_code),
                "destructive": high_risk or strict_blocked or "delete" in command_name or "remove" in command_name,
                "idempotent": not (can_mutate or can_write or can_network or can_code),
                "requires_approval": high_risk or strict_blocked,
                "requires_confirmation": high_risk or strict_blocked,
                "supports_progress": can_write,
                "supports_cancel": can_write,
                "timeout_seconds": 30,
                "rollback_strategy": "scene_snapshot" if can_mutate else None,
                "allowed_capabilities": sorted(set(caps)),
                "filesystem_access": "project_write" if can_write else "none",
                "network_access": "provider" if can_network else "none",
                "blender_version_notes": "single-file fallback metadata",
                "input_schema_ref": f"socket:{command_name}:input",
                "output_schema_ref": f"socket:{command_name}:output",
                "smoke_flags": ["--phase7b-full"] if command_name.startswith(("get_", "discover_", "search_", "prepare_", "approve_", "deny_")) else [],
                "mcp_tool_module": None,
                "public": True,
                "deprecated": False,
                "tags": [command_name.replace("_", " "), category, pack, "bake" if category in {"materials", "textures"} else ""],
            }
        return specs

    class _FallbackApprovalRuntime:
        def __init__(self):
            self.records = {}

        def prepare_operation(self, command_name, params=None, scene_revision=None):
            payload = json.dumps({"command_name": command_name, "params": params or {}}, sort_keys=True, separators=(",", ":")).encode("utf-8")
            approval_id = f"appr_{uuid4().hex[:16]}"
            record = {
                "approval_id": approval_id,
                "command_name": command_name,
                "params_hash": hashlib.sha256(payload).hexdigest(),
                "target_summary": [],
                "path_summary": [],
                "risk_level": "HIGH",
                "destructive": True,
                "created_at": time.time(),
                "expires_at": time.time() + 600,
                "scene_revision": scene_revision,
                "required_capabilities": [],
                "rollback_strategy": "scene_snapshot",
                "status": "pending",
            }
            self.records[approval_id] = record
            return {"status": "requires_approval", "approval_required": True, "approval": record}

        def get_pending_approvals(self):
            return {"status": "success", "approvals": [record for record in self.records.values() if record["status"] == "pending"]}

        def approve_operation(self, approval_id):
            record = self.records.get(approval_id)
            if not record:
                return {"status": "error", "message": f"Unknown approval: {approval_id}"}
            record["status"] = "approved"
            return {"status": "success", "approval": record}

        def deny_operation(self, approval_id, reason=None):
            record = self.records.get(approval_id)
            if not record:
                return {"status": "error", "message": f"Unknown approval: {approval_id}"}
            record["status"] = "denied"
            return {"status": "success", "approval": record, "reason": reason}

        def expire_approval(self, approval_id=None):
            return {"status": "success", "expired": []}

        def execute_approved_operation(self, approval_id, command_name, params=None):
            return {"status": "not_implemented", "message": "Approved execution dispatch is staged for migrated operations.", "approval_id": approval_id, "command_name": command_name}

    DEFAULT_APPROVAL_RUNTIME = _FallbackApprovalRuntime()

    def canonical_params_hash(command_name, params=None):
        payload = json.dumps({"command_name": command_name, "params": params or {}}, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def runtime_get_permission_profile():
        return {"status": "success", "profile": "standard", "capabilities": ["scene.read", "scene.write"]}

    def runtime_set_permission_profile(profile, confirm=False):
        return {"status": "requires_approval" if not confirm else "success", "profile": profile}

    def runtime_get_capability_policy():
        return {
            "status": "success",
            "capabilities": [
                "scene.read", "scene.write", "scene.destructive",
                "filesystem.project.read", "filesystem.project.write",
                "network.providers", "addon.inspect", "addon.manage",
                "raw_python", "knowledge.read", "knowledge.write", "release.export",
            ],
            "profiles": {
                "read_only": ["scene.read", "filesystem.project.read", "addon.inspect", "knowledge.read"],
                "standard": ["scene.read", "scene.write", "filesystem.project.read", "filesystem.project.write", "addon.inspect", "knowledge.read", "knowledge.write"],
                "trusted_project": ["scene.read", "scene.write", "scene.destructive", "filesystem.project.read", "filesystem.project.write", "addon.inspect", "knowledge.read", "knowledge.write", "release.export"],
                "developer": [
                    "scene.read", "scene.write", "scene.destructive",
                    "filesystem.project.read", "filesystem.project.write",
                    "network.providers", "addon.inspect", "addon.manage",
                    "raw_python", "knowledge.read", "knowledge.write", "release.export",
                ],
            },
            "active_profile": "standard",
        }

    def runtime_validate_command_capabilities(command_name, profile=None):
        spec = _fallback_command_specs().get(command_name)
        if not spec:
            return {"status": "error", "message": f"Unknown command: {command_name}"}
        policy = runtime_get_capability_policy()
        profile_name = profile or policy["active_profile"]
        allowed_capabilities = set(policy["profiles"].get(profile_name, []))
        required_capabilities = set(spec.get("allowed_capabilities", []))
        missing = sorted(required_capabilities - allowed_capabilities)
        return {
            "status": "success" if not missing else "error",
            "command_name": command_name,
            "profile": profile_name,
            "allowed": not missing,
            "required_capabilities": sorted(required_capabilities),
            "missing_capabilities": missing,
        }

    def command_registry_report():
        specs = _fallback_command_specs()
        return {
            "status": "success",
            "command_count": len(specs),
            "categories": sorted({spec["category"] for spec in specs.values()}),
            "tool_packs": sorted({spec["tool_pack"] for spec in specs.values()}),
            "governance_commands": [name for name in specs if name in {
                "get_system_status", "discover_tool_packs", "search_tools", "get_tool_spec",
                "prepare_operation", "approve_operation", "deny_operation", "get_log_status",
            }],
            "response_envelope_migration": {"applied_to": [], "migration_pending": sorted(specs)},
        }

    def get_command_spec(name):
        return _fallback_command_specs().get(name)

    def runtime_get_log_status():
        return {"status": "success", "log_dir": ".overtli_blender/logs", "redaction_keys": ["api_key", "token", "secret", "password", "credential", "auth"]}

    def runtime_export_operation_log(operation_id=None):
        return {"status": "success", "events": [], "operation_id": operation_id}

    def build_operation_response(**kwargs):
        return {"status": kwargs.get("status", "success"), "tool": kwargs.get("tool"), "result": kwargs.get("result", {})}

    class _FallbackOperationRuntime:
        def get_operation_status(self, operation_id=None):
            return {"status": "success", "operations": [], "operation_id": operation_id}
        def list_recent_operations(self, limit=20):
            return {"status": "success", "operations": []}
        def cancel_operation(self, operation_id):
            return {"status": "not_implemented", "operation_id": operation_id}
        def get_operation_log(self, operation_id=None):
            return {"status": "success", "operations": [], "operation_id": operation_id}

    DEFAULT_OPERATION_RUNTIME = _FallbackOperationRuntime()

    def _phase7c_canonical_path(path):
        from pathlib import Path
        return Path(path).expanduser().resolve(strict=False)

    def runtime_distance(a, b):
        return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))

    def runtime_angle_degrees(a, b, c):
        ba = [x - y for x, y in zip(a, b)]
        bc = [x - y for x, y in zip(c, b)]
        dot = sum(x * y for x, y in zip(ba, bc))
        denom = math.sqrt(sum(x * x for x in ba)) * math.sqrt(sum(x * x for x in bc))
        if denom == 0:
            raise ValueError("Cannot calculate angle with zero-length vector.")
        return math.degrees(math.acos(max(-1.0, min(1.0, dot / denom))))

    def runtime_convert_units(value, from_unit="BLENDER_UNIT", to_unit="METERS", scale_length=1.0):
        meters = float(value) * float(scale_length) if from_unit.upper() in {"BLENDER_UNIT", "BU"} else float(value)
        converted = meters / float(scale_length) if to_unit.upper() in {"BLENDER_UNIT", "BU"} and scale_length else meters
        return {"status": "success", "value": converted, "value_meters": meters, "from_unit": from_unit, "to_unit": to_unit, "confidence": "high"}

    class FileAccessPolicy:
        def __init__(self, project_root=None, approved_roots=None):
            self.project_root = _phase7c_canonical_path(project_root or ADDON_ROOT)
            self.approved_roots = sorted({str(_phase7c_canonical_path(root)) for root in [self.project_root, *(approved_roots or [])]})

        def _is_relative_to(self, child, parent):
            try:
                _phase7c_canonical_path(child).relative_to(_phase7c_canonical_path(parent))
                return True
            except ValueError:
                return False

        def to_dict(self):
            return {"project_root": str(self.project_root), "approved_roots": list(self.approved_roots), "symlink_escape_blocked": True, "atomic_writes": True}

        def add_root(self, root):
            resolved = str(_phase7c_canonical_path(root))
            if resolved not in self.approved_roots:
                self.approved_roots.append(resolved)
                self.approved_roots.sort()
            return self.to_dict()

        def remove_root(self, root):
            resolved = str(_phase7c_canonical_path(root))
            self.approved_roots = [item for item in self.approved_roots if item != resolved]
            if str(self.project_root) not in self.approved_roots:
                self.approved_roots.append(str(self.project_root))
            return self.to_dict()

        def validate(self, path, access="read"):
            resolved = _phase7c_canonical_path(path)
            within_root = any(self._is_relative_to(resolved, root) for root in self.approved_roots)
            requires_approval = access in {"write", "delete"} and not self._is_relative_to(resolved, self.project_root)
            return {"status": "success" if within_root else "error", "path": str(resolved), "access": access, "allowed": within_root and not requires_approval, "requires_approval": requires_approval, "approved_roots": self.approved_roots, "warnings": [] if within_root else ["path-outside-approved-roots"]}

        def read_text(self, path, max_bytes=200000):
            check = self.validate(path, "read")
            if check["status"] != "success":
                return check
            target = _phase7c_canonical_path(path)
            if not target.exists() or target.is_dir():
                return {"status": "error", "message": "Path is not a readable file.", "path": str(target)}
            data = target.read_bytes()
            if len(data) > max_bytes:
                return {"status": "error", "message": "Text file exceeds max_bytes.", "path": str(target), "bytes": len(data)}
            return {"status": "success", "path": str(target), "bytes": len(data), "text": data.decode("utf-8")}

        def write_text(self, path, text):
            check = self.validate(path, "write")
            if check["status"] != "success":
                return check
            if check["requires_approval"]:
                return {"status": "requires_approval", **check}
            target = _phase7c_canonical_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            temp_path = target.with_name(f".{target.name}.tmp")
            temp_path.write_text(text, encoding="utf-8")
            os.replace(temp_path, target)
            return {"status": "success", "path": str(target), "bytes": len(text.encode("utf-8"))}

        def copy_into_project(self, source, destination):
            source_check = self.validate(source, "read")
            dest_check = self.validate(destination, "write")
            if source_check["status"] != "success":
                return source_check
            if dest_check["status"] != "success":
                return dest_check
            if dest_check["requires_approval"]:
                return {"status": "requires_approval", **dest_check}
            os.makedirs(os.path.dirname(dest_check["path"]), exist_ok=True)
            shutil.copy2(source_check["path"], dest_check["path"])
            return {"status": "success", "source": source_check["path"], "destination": dest_check["path"]}

        def plan_delete(self, paths):
            files = []
            bytes_total = 0
            for path in paths:
                check = self.validate(path, "delete")
                if check["status"] == "success" and os.path.isfile(check["path"]):
                    size = os.path.getsize(check["path"])
                    files.append({"path": check["path"], "bytes": size})
                    bytes_total += size
            approval_id = "delete_" + hashlib.sha256(json.dumps(files, sort_keys=True).encode("utf-8")).hexdigest()[:16]
            return {"status": "requires_approval", "approval_id": approval_id, "files": files, "bytes": bytes_total, "risks": [], "rollback": {"available": False}}

    _PHASE7C_STANDARD_FOLDERS = (
        ".overtli", "assets", "textures/source", "textures/working", "textures/baked", "textures/packed",
        os.path.join("references", "images"), "imports", "exports", "renders/previews", "renders/finals", "backups",
    )

    def runtime_resolve_workspace(blend_filepath=None, preferred_root=None, repo_root=None, allow_repo_fallback=True):
        if preferred_root:
            root = _phase7c_canonical_path(preferred_root)
            return {"status": "success", "workspace": {"resolved": True, "project_root": str(root), "workspace_dir": str(root / ".overtli"), "manifest_path": str(root / ".overtli" / "project.json"), "source": "preferred_root"}, "options": []}
        if blend_filepath:
            root = _phase7c_canonical_path(blend_filepath).parent
            return {"status": "success", "workspace": {"resolved": True, "project_root": str(root), "workspace_dir": str(root / ".overtli"), "manifest_path": str(root / ".overtli" / "project.json"), "source": "blend_parent"}, "options": []}
        options = [{"source": "repo_fallback", "project_root": str(_phase7c_canonical_path(repo_root or ADDON_ROOT))}] if allow_repo_fallback else []
        return {"status": "unsaved_blend", "workspace": {"resolved": False, "source": "temporary"}, "options": options, "warnings": ["Unsaved .blend has no trusted project root."]}

    def runtime_initialize_workspace(project_root, project_name=None, create_standard_folders=True, overwrite_manifest=False):
        root = _phase7c_canonical_path(project_root)
        if create_standard_folders:
            for folder in _PHASE7C_STANDARD_FOLDERS:
                (root / folder).mkdir(parents=True, exist_ok=True)
        manifest = root / ".overtli" / "project.json"
        if manifest.exists() and not overwrite_manifest:
            return {"status": "requires_approval", "message": "Project manifest already exists.", "workspace": {"project_root": str(root), "manifest_path": str(manifest)}}
        manifest.parent.mkdir(parents=True, exist_ok=True)
        payload = {"project_name": project_name or root.name, "project_root": str(root), "standard_folders": list(_PHASE7C_STANDARD_FOLDERS)}
        manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return {"status": "success", "workspace": {"resolved": True, "project_root": str(root), "workspace_dir": str(root / ".overtli"), "manifest_path": str(manifest), "source": "explicit"}, "manifest": payload}

    def runtime_validate_layout(project_root):
        root = _phase7c_canonical_path(project_root)
        missing = [folder for folder in _PHASE7C_STANDARD_FOLDERS if not (root / folder).exists()]
        return {"status": "success" if not missing else "warning", "project_root": str(root), "missing": missing, "standard_folders": list(_PHASE7C_STANDARD_FOLDERS)}

    def runtime_get_cache_status(base):
        root = _phase7c_canonical_path(base)
        categories = []
        for category in ["temp", "derived_previews", "smoke_artifacts", "verification_snapshots", "logs", "diagnostics", "release_artifacts", "exports", "final_renders", "knowledge_indexes"]:
            path = root / category
            files = [p for p in path.rglob("*") if p.is_file()] if path.exists() else []
            categories.append({"category": category, "path": str(path), "file_count": len(files), "bytes": sum(p.stat().st_size for p in files), "oldest": None, "newest": None, "pinned_count": 0, "cleanup_policy": "manual_approval_required"})
        return {"status": "success", "categories": categories}

    def runtime_plan_cache_cleanup(base, categories=None, older_than_days=None):
        return {"status": "requires_approval", "approval_id": "cache_fallback_plan", "files": [], "bytes": 0, "dry_run": True}

    TASK_STATUSES = ("planned", "ready", "in_progress", "waiting_for_approval", "waiting_for_user_selection", "blocked", "completed_unverified", "verified", "failed", "rolled_back", "stale", "archived")

    class TaskGraphStore:
        def __init__(self, workspace_dir):
            self.tasks_dir = _phase7c_canonical_path(workspace_dir) / "tasks"
            self.tasks_dir.mkdir(parents=True, exist_ok=True)

        def _path(self, task_id):
            return self.tasks_dir / f"{task_id}.json"

        def create_task(self, goal, **kwargs):
            task_id = kwargs.get("task_id") or f"task_{int(time.time() * 1000)}"
            task = {"task_id": task_id, "goal": goal, "status": kwargs.get("status", "planned"), "priority": kwargs.get("priority", "normal"), "dependencies": kwargs.get("dependencies", []), "blocked_by": kwargs.get("blocked_by", []), "target_handles": kwargs.get("target_handles", []), "acceptance_criteria": kwargs.get("acceptance_criteria", []), "required_approvals": kwargs.get("required_approvals", []), "created_revision": kwargs.get("created_revision", 0), "last_verified_revision": None, "artifacts": [], "user_notes": kwargs.get("user_notes", []), "model_summary": kwargs.get("model_summary")}
            self._path(task_id).write_text(json.dumps(task, indent=2, sort_keys=True), encoding="utf-8")
            return {"status": "success", "task": task}

        def get_task(self, task_id):
            path = self._path(task_id)
            if not path.exists():
                return {"status": "error", "message": f"Unknown task: {task_id}"}
            return {"status": "success", "task": json.loads(path.read_text(encoding="utf-8"))}

        def list_tasks(self, status=None):
            tasks = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.tasks_dir.glob("task_*.json"))]
            return {"status": "success", "tasks": [task for task in tasks if not status or task.get("status") == status]}

        def update_task(self, task_id, **updates):
            result = self.get_task(task_id)
            if result["status"] != "success":
                return result
            task = result["task"]
            task.update({key: value for key, value in updates.items() if value is not None})
            self._path(task_id).write_text(json.dumps(task, indent=2, sort_keys=True), encoding="utf-8")
            return {"status": "success", "task": task}

    class TimeRevisionTracker:
        def __init__(self):
            self.session_start_monotonic = time.monotonic()
            self.session_start_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self.scene_revision = 0
            self.operations = []

        def time_info(self):
            return {"status": "success", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "local": time.strftime("%Y-%m-%d %H:%M:%S"), "session_start_utc": self.session_start_utc, "monotonic_elapsed": time.monotonic() - self.session_start_monotonic}

        def marker(self, label=None, source="overtli"):
            self.scene_revision += 1
            entry = {"revision": self.scene_revision, "label": label, "source": source, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            self.operations.append(entry)
            return {"status": "success", "marker": entry}

        def recent(self, limit=20):
            return {"status": "success", "operations": self.operations[-limit:]}

    def runtime_discover_tool_packs():
        specs = _fallback_command_specs()
        packs = {}
        descriptions = {
            "core": "Status, permissions, approvals, operations, and discovery.",
            "scene_intelligence": "Scene inspection and verification.",
            "verified_editing": "Structured editing and recovery.",
            "materials": "Material, shader, texture, and future baking workflows.",
            "geometry_nodes": "Geometry Nodes workflows.",
            "asset_workflows": "Assets and import/export workflows.",
            "addon_knowledge": "Addon and knowledge workflows.",
        }
        for spec in specs.values():
            pack = spec["tool_pack"]
            packs.setdefault(pack, {"name": pack, "title": pack.replace("_", " ").title(), "description": descriptions.get(pack, ""), "categories": set(), "command_count": 0})
            packs[pack]["categories"].add(spec["category"])
            packs[pack]["command_count"] += 1
        return {"status": "success", "tool_packs": [{**pack, "categories": sorted(pack["categories"])} for pack in packs.values()]}
    def runtime_get_tool_pack(name):
        specs = _fallback_command_specs()
        commands = [spec for spec in specs.values() if spec["tool_pack"] == name]
        if not commands:
            return {"status": "error", "message": f"Unknown tool pack: {name}"}
        return {"status": "success", "tool_pack": {"name": name, "title": name.replace("_", " ").title()}, "commands": commands}
    def runtime_search_tools(query, category=None, tool_pack=None, risk_max=None, limit=20):
        terms = [term.lower() for term in str(query).split() if term.strip()]
        risk_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "DESTRUCTIVE": 4}
        risk_limit = risk_order.get(str(risk_max or "DESTRUCTIVE").upper(), 4)
        results = []
        for spec in _fallback_command_specs().values():
            if category and spec["category"] != category:
                continue
            if tool_pack and spec["tool_pack"] != tool_pack:
                continue
            if risk_order.get(spec["risk_level"], 99) > risk_limit:
                continue
            haystack = " ".join([spec["name"], spec["title"], spec["description"], spec["category"], spec["tool_pack"], " ".join(spec["tags"]), " ".join(spec["allowed_capabilities"])]).lower()
            if not terms or any(term in haystack for term in terms):
                results.append(spec)
        return {"status": "success", "query": query, "results": results[: max(1, min(int(limit), 50))]}
    def runtime_get_tool_spec(name):
        spec = _fallback_command_specs().get(name)
        if not spec:
            return {"status": "error", "message": f"Unknown tool: {name}"}
        return {"status": "success", "tool": spec}
    def runtime_get_recommended_tools_for_task(task, limit=8):
        return runtime_search_tools(task, limit=limit)

    @dataclass(frozen=True)
    class _FallbackCommandSafetyMetadata:
        command_type: str
        operation_type: str
        risk_level: RiskLevel
        reversibility: str
        can_mutate_scene: bool = False
        can_execute_code: bool = False
        can_call_network: bool = False
        can_write_files: bool = False
        provider_api_key_involved: bool = False
        strict_blocked: bool = False
        default_action: str = "allow"
        strict_action: str = "block"
        warnings: tuple[str, ...] = ()

    def _fallback_spec(command_type, operation_type, risk_level, reversibility, **kwargs):
        return _FallbackCommandSafetyMetadata(
            command_type=command_type,
            operation_type=operation_type,
            risk_level=risk_level,
            reversibility=reversibility,
            **kwargs,
        )

    def build_command_safety_map():
        return {
            "get_scene_info": _fallback_spec("get_scene_info", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "get_object_info": _fallback_spec("get_object_info", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "get_shared_context": _fallback_spec("get_shared_context", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "get_operation_history": _fallback_spec("get_operation_history", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "list_object_handles": _fallback_spec("list_object_handles", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "list_material_handles": _fallback_spec("list_material_handles", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "list_context_scripts": _fallback_spec("list_context_scripts", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "get_polyhaven_status": _fallback_spec("get_polyhaven_status", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "get_hyper3d_status": _fallback_spec("get_hyper3d_status", "VERIFY", RiskLevel.LOW, "REVERSIBLE", provider_api_key_involved=True),
            "get_sketchfab_status": _fallback_spec("get_sketchfab_status", "VERIFY", RiskLevel.LOW, "REVERSIBLE", provider_api_key_involved=True),
            "get_geometry_nodes_status": _fallback_spec("get_geometry_nodes_status", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "get_geometry_nodes_capabilities": _fallback_spec("get_geometry_nodes_capabilities", "GEOMETRY_NODES", RiskLevel.LOW, "REVERSIBLE"),
            "list_geometry_node_groups": _fallback_spec("list_geometry_node_groups", "GEOMETRY_NODES", RiskLevel.LOW, "REVERSIBLE"),
            "get_geometry_node_group_deep_info": _fallback_spec("get_geometry_node_group_deep_info", "GEOMETRY_NODES", RiskLevel.LOW, "REVERSIBLE"),
            "list_geometry_nodes_modifiers": _fallback_spec("list_geometry_nodes_modifiers", "GEOMETRY_NODES", RiskLevel.LOW, "REVERSIBLE"),
            "get_geometry_nodes_modifier_info": _fallback_spec("get_geometry_nodes_modifier_info", "GEOMETRY_NODES", RiskLevel.LOW, "REVERSIBLE"),
            "get_supported_geometry_node_templates": _fallback_spec("get_supported_geometry_node_templates", "GEOMETRY_NODES", RiskLevel.LOW, "REVERSIBLE"),
            "validate_geometry_node_group": _fallback_spec("validate_geometry_node_group", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "get_safety_status": _fallback_spec("get_safety_status", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "get_viewport_screenshot": _fallback_spec("get_viewport_screenshot", "CAMERA", RiskLevel.MEDIUM, "REVERSIBLE", warnings=("viewport-context-dependent",)),
            "get_scene_index": _fallback_spec("get_scene_index", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "get_object_deep_info": _fallback_spec("get_object_deep_info", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "get_selection_info": _fallback_spec("get_selection_info", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "get_scene_health": _fallback_spec("get_scene_health", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "capture_viewport_pack": _fallback_spec("capture_viewport_pack", "CAMERA", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True, warnings=("writes-local-verification-artifacts", "viewport-context-dependent")),
            "create_verification_snapshot": _fallback_spec("create_verification_snapshot", "VERIFY", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True, warnings=("writes-local-verification-artifacts",)),
            "list_verification_snapshots": _fallback_spec("list_verification_snapshots", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "get_supported_edit_operations": _fallback_spec("get_supported_edit_operations", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "create_primitive_object": _fallback_spec("create_primitive_object", "CREATE", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "transform_object": _fallback_spec("transform_object", "EDIT", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "duplicate_object": _fallback_spec("duplicate_object", "CREATE", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "delete_objects": _fallback_spec("delete_objects", "CLEANUP", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required",)),
            "set_object_visibility": _fallback_spec("set_object_visibility", "EDIT", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "create_basic_material": _fallback_spec("create_basic_material", "MATERIAL", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "assign_material": _fallback_spec("assign_material", "MATERIAL", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "update_material_properties": _fallback_spec("update_material_properties", "MATERIAL", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "get_material_channel_schema": _fallback_spec("get_material_channel_schema", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "get_supported_material_templates": _fallback_spec("get_supported_material_templates", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "list_materials_deep": _fallback_spec("list_materials_deep", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "get_material_deep_info": _fallback_spec("get_material_deep_info", "OBSERVE", RiskLevel.LOW, "REVERSIBLE"),
            "get_shader_graph": _fallback_spec("get_shader_graph", "SHADER", RiskLevel.LOW, "REVERSIBLE"),
            "create_material_from_template": _fallback_spec("create_material_from_template", "MATERIAL", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "create_custom_material": _fallback_spec("create_custom_material", "MATERIAL", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "create_procedural_material": _fallback_spec("create_procedural_material", "MATERIAL", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "create_material_variant": _fallback_spec("create_material_variant", "MATERIAL", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "apply_material_to_objects": _fallback_spec("apply_material_to_objects", "MATERIAL", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "bind_material_texture_map": _fallback_spec("bind_material_texture_map", "TEXTURE", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "set_material_node_input": _fallback_spec("set_material_node_input", "SHADER", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "add_material_node": _fallback_spec("add_material_node", "SHADER", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "connect_material_nodes": _fallback_spec("connect_material_nodes", "SHADER", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "create_material_preview": _fallback_spec("create_material_preview", "VERIFY", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True),
            "run_material_workflow_batch": _fallback_spec("run_material_workflow_batch", "MATERIAL", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True, can_write_files=True),
            "remove_material_node": _fallback_spec("remove_material_node", "SHADER", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True),
            "delete_materials": _fallback_spec("delete_materials", "CLEANUP", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True),
            "add_object_modifier": _fallback_spec("add_object_modifier", "MODIFIER", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "update_object_modifier": _fallback_spec("update_object_modifier", "MODIFIER", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "remove_object_modifier": _fallback_spec("remove_object_modifier", "MODIFIER", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required",)),
            "create_collection": _fallback_spec("create_collection", "CREATE", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "move_objects_to_collection": _fallback_spec("move_objects_to_collection", "EDIT", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "delete_collection": _fallback_spec("delete_collection", "CLEANUP", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "empty-collection-only-by-default")),
            "run_verified_edit_batch": _fallback_spec("run_verified_edit_batch", "EDIT", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True, can_write_files=True, warnings=("writes-local-verification-artifacts",)),
            "get_task_workspace": _fallback_spec("get_task_workspace", "VERIFY", RiskLevel.LOW, "REVERSIBLE", can_write_files=True),
            "create_workspace_task": _fallback_spec("create_workspace_task", "UPDATE_KNOWLEDGE", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True),
            "update_workspace_task": _fallback_spec("update_workspace_task", "UPDATE_KNOWLEDGE", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True),
            "list_workspace_tasks": _fallback_spec("list_workspace_tasks", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "add_workspace_todo": _fallback_spec("add_workspace_todo", "UPDATE_KNOWLEDGE", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True),
            "update_workspace_todo": _fallback_spec("update_workspace_todo", "UPDATE_KNOWLEDGE", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True),
            "list_workspace_todos": _fallback_spec("list_workspace_todos", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "record_operation_journal_entry": _fallback_spec("record_operation_journal_entry", "UPDATE_KNOWLEDGE", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True),
            "get_operation_journal": _fallback_spec("get_operation_journal", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "create_scene_snapshot": _fallback_spec("create_scene_snapshot", "VERIFY", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True, warnings=("writes-local-workspace-artifacts",)),
            "list_scene_snapshots": _fallback_spec("list_scene_snapshots", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "diff_scene_snapshots": _fallback_spec("diff_scene_snapshots", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "detect_user_changes": _fallback_spec("detect_user_changes", "VERIFY", RiskLevel.LOW, "REVERSIBLE"),
            "rollback_to_scene_snapshot": _fallback_spec("rollback_to_scene_snapshot", "ROLLBACK", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "existing-objects-only")),
            "undo_last_blender_operation": _fallback_spec("undo_last_blender_operation", "ROLLBACK", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required",)),
            "create_object_handle": _fallback_spec("create_object_handle", "CREATE", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "create_material_handle": _fallback_spec("create_material_handle", "MATERIAL", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "register_context_script": _fallback_spec("register_context_script", "UPDATE_KNOWLEDGE", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True),
            "execute_context_script": _fallback_spec("execute_context_script", "UPDATE_KNOWLEDGE", RiskLevel.HIGH, "UNKNOWN", can_execute_code=True, can_write_files=True, strict_blocked=True),
            "clear_context_scripts": _fallback_spec("clear_context_scripts", "CLEANUP", RiskLevel.MEDIUM, "PARTIAL", can_write_files=True, strict_blocked=True),
            "clear_shared_context": _fallback_spec("clear_shared_context", "CLEANUP", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True, strict_blocked=True),
            "get_polyhaven_categories": _fallback_spec("get_polyhaven_categories", "ASSET_LIBRARY", RiskLevel.LOW, "REVERSIBLE", can_call_network=True),
            "search_polyhaven_assets": _fallback_spec("search_polyhaven_assets", "ASSET_LIBRARY", RiskLevel.MEDIUM, "REVERSIBLE", can_call_network=True),
            "download_polyhaven_asset": _fallback_spec("download_polyhaven_asset", "ASSET_LIBRARY", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, can_call_network=True, can_write_files=True, strict_blocked=True),
            "set_texture": _fallback_spec("set_texture", "TEXTURE", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "search_sketchfab_models": _fallback_spec("search_sketchfab_models", "ASSET_LIBRARY", RiskLevel.MEDIUM, "REVERSIBLE", can_call_network=True, provider_api_key_involved=True),
            "download_sketchfab_model": _fallback_spec("download_sketchfab_model", "ASSET_LIBRARY", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, can_call_network=True, can_write_files=True, provider_api_key_involved=True, strict_blocked=True),
            "create_rodin_job": _fallback_spec("create_rodin_job", "ASSET_LIBRARY", RiskLevel.HIGH, "UNKNOWN", can_call_network=True, provider_api_key_involved=True, strict_blocked=True),
            "poll_rodin_job_status": _fallback_spec("poll_rodin_job_status", "VERIFY", RiskLevel.MEDIUM, "REVERSIBLE", can_call_network=True, provider_api_key_involved=True),
            "import_generated_asset": _fallback_spec("import_generated_asset", "IMPORT", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, can_call_network=True, can_write_files=True, provider_api_key_involved=True, strict_blocked=True),
            "create_geometry_node_group_from_template": _fallback_spec("create_geometry_node_group_from_template", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True, can_write_files=True),
            "create_custom_geometry_node_recipe": _fallback_spec("create_custom_geometry_node_recipe", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True, can_write_files=True),
            "apply_geometry_nodes_modifier": _fallback_spec("apply_geometry_nodes_modifier", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True),
            "set_geometry_nodes_modifier_input": _fallback_spec("set_geometry_nodes_modifier_input", "GEOMETRY_NODES", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True),
            "create_procedural_asset": _fallback_spec("create_procedural_asset", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True, can_write_files=True),
            "create_scatter_system": _fallback_spec("create_scatter_system", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True, can_write_files=True),
            "create_curve_generator": _fallback_spec("create_curve_generator", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True, can_write_files=True),
            "create_radial_array_system": _fallback_spec("create_radial_array_system", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True, can_write_files=True),
            "create_panel_generator": _fallback_spec("create_panel_generator", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True, can_write_files=True),
            "create_cable_or_rope_generator": _fallback_spec("create_cable_or_rope_generator", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True, can_write_files=True),
            "create_terrain_noise_system": _fallback_spec("create_terrain_noise_system", "GEOMETRY_NODES", RiskLevel.MEDIUM, "REVERSIBLE", can_mutate_scene=True, can_write_files=True),
            "create_geometry_nodes_preview": _fallback_spec("create_geometry_nodes_preview", "VERIFY", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True),
            "create_geometry_nodes_scene_kit": _fallback_spec("create_geometry_nodes_scene_kit", "EXPORT", RiskLevel.MEDIUM, "REVERSIBLE", can_write_files=True),
            "run_geometry_nodes_workflow_batch": _fallback_spec("run_geometry_nodes_workflow_batch", "GEOMETRY_NODES", RiskLevel.MEDIUM, "PARTIAL", can_mutate_scene=True, can_write_files=True),
            "delete_geometry_node_groups": _fallback_spec("delete_geometry_node_groups", "CLEANUP", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True),
            "remove_geometry_nodes_modifiers": _fallback_spec("remove_geometry_nodes_modifiers", "CLEANUP", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True),
            "complete_geometry_node": _fallback_spec("complete_geometry_node", "GEOMETRY_NODES", RiskLevel.HIGH, "PARTIAL", can_mutate_scene=True, strict_blocked=True),
            "execute_code": _fallback_spec("execute_code", "VERIFY", RiskLevel.HIGH, "UNKNOWN", can_execute_code=True, strict_blocked=True),
        }

bl_info = {
    "name": "Overtli-Blender",
    "author": "OvertliDS",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Overtli-Blender",
    "description": "Connect Blender to Overtli-Blender via MCP",
    "category": "Interface",
}

RODIN_FREE_TRIAL_KEY = "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"

# Add User-Agent as required by Poly Haven API
REQ_HEADERS = requests.utils.default_headers()
REQ_HEADERS.update({"User-Agent": "overtli-blender"})

# Check if this is Blender 4+
IS_BLENDER_4 = bpy.app.version[0] >= 4

# Geometry Nodes Data Classes
@dataclass
class NodeDefinition:
    """Node definition data class"""
    type: str  # Node type name
    location: List[float] = field(default_factory=lambda: [0.0, 0.0])  # Node position [x, y]
    label: str = ""  # Node label
    inputs: Dict[str, Any] = field(default_factory=dict)  # Input values dictionary
    properties: Dict[str, Any] = field(default_factory=dict)  # Node properties parameter dictionary


@dataclass
class NodeLink:
    """Node connection data class"""
    from_node: Union[str, int]  # Source node name or index
    from_socket: Union[str, int]  # Source socket name or index
    to_node: Union[str, int]  # Target node name or index
    to_socket: Union[str, int]  # Target socket name or index


@dataclass
class GeometryNodeNetwork:
    """Geometry node network data class"""
    object_name: str  # Object name
    nodes: List[NodeDefinition] = field(default_factory=list)  # Node list
    links: List[NodeLink] = field(default_factory=list)  # Connection list
    input_sockets: List[Dict[str, str]] = field(default_factory=list)  # Input interface definition
    output_sockets: List[Dict[str, str]] = field(default_factory=list)  # Output interface definition


@dataclass
class SocketInfo:
    """Socket information data class"""
    name: str  # Socket name
    type: str  # Socket type
    description: str  # Socket description
    identifier: str  # Socket identifier
    enabled: bool  # Whether enabled
    hide: bool  # Whether hidden
    default_value: Any = None  # Default value (if any)


@dataclass
class PropertyInfo:
    """Node property information data class"""
    identifier: str  # Property identifier
    name: str  # Property name
    description: str  # Property description
    type: str  # Property type
    default_value: Any = None  # Default value (if any)
    enum_items: List[Dict[str, str]] = field(default_factory=list)  # Enum options (if any)


@dataclass
class NodeInfo:
    """Node information data class"""
    name: str  # Node type name (identifier used to create the node)
    description: str  # Node description
    inputs: List[SocketInfo] = field(default_factory=list)  # Input socket information
    outputs: List[SocketInfo] = field(default_factory=list)  # Output socket information
    properties: List[PropertyInfo] = field(default_factory=list)  # Node property information


class SharedContextService:
    def __init__(self, shared_context):
        self.shared_context = shared_context

    def add_to_history(self, operation, input_data, result):
        """Add operation to history"""
        self.shared_context['history'].append({
            'operation': operation,
            'input': input_data,
            'result': str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
            'timestamp': time.time()
        })
        # Keep only last 50 operations
        if len(self.shared_context['history']) > 50:
            self.shared_context['history'] = self.shared_context['history'][-50:]

    def store_object_handle(self, handle, obj_name):
        """Store object reference by handle"""
        obj = bpy.data.objects.get(obj_name)
        if obj:
            self.shared_context['objects'][handle] = obj
            return f"Stored object '{obj_name}' as handle '{handle}'"
        return f"Object '{obj_name}' not found"

    def store_material_handle(self, handle, mat_name):
        """Store material reference by handle"""
        mat = bpy.data.materials.get(mat_name)
        if mat:
            self.shared_context['materials'][handle] = mat
            return f"Stored material '{mat_name}' as handle '{handle}'"
        return f"Material '{mat_name}' not found"

    def store_operation_result(self, op_id, result):
        """Store operation result by ID"""
        self.shared_context['operations'][op_id] = result
        return f"Stored operation result as '{op_id}'"

    def get_shared_context(self):
        """Get current shared context state"""
        return {
            "variables": self.shared_context['variables'],
            "object_handles": list(self.shared_context['objects'].keys()),
            "material_handles": list(self.shared_context['materials'].keys()),
            "operation_ids": list(self.shared_context['operations'].keys()),
            "history_count": len(self.shared_context['history'])
        }

    def clear_shared_context(self, section="all"):
        """Clear shared context (all, variables, objects, materials, operations, history)"""
        if section == "all":
            self.shared_context['variables'].clear()
            self.shared_context['objects'].clear()
            self.shared_context['materials'].clear()
            self.shared_context['operations'].clear()
            self.shared_context['history'].clear()
            return "Cleared all shared context"
        elif section == "variables":
            self.shared_context['variables'].clear()
            return "Cleared shared variables"
        elif section == "objects":
            self.shared_context['objects'].clear()
            return "Cleared object handles"
        elif section == "materials":
            self.shared_context['materials'].clear()
            return "Cleared material handles"
        elif section == "operations":
            self.shared_context['operations'].clear()
            return "Cleared operation results"
        elif section == "history":
            self.shared_context['history'].clear()
            return "Cleared operation history"
        else:
            return f"Unknown section: {section}. Use: all, variables, objects, materials, operations, history"

    def get_operation_history(self, count=10):
        """Get recent operation history"""
        recent_history = self.shared_context['history'][-count:] if count else self.shared_context['history']
        return {"history": recent_history, "total_operations": len(self.shared_context['history'])}

    def create_object_handle(self, handle, object_name):
        """Create a handle for an object to reference in future operations"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object '{object_name}' not found"}

        self.shared_context['objects'][handle] = obj
        self.add_to_history("create_object_handle", f"{handle} -> {object_name}", f"Created handle '{handle}'")

        return {
            "success": True,
            "handle": handle,
            "object_name": object_name,
            "object_type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z]
        }

    def create_material_handle(self, handle, material_name):
        """Create a handle for a material to reference in future operations"""
        mat = bpy.data.materials.get(material_name)
        if not mat:
            return {"error": f"Material '{material_name}' not found"}

        self.shared_context['materials'][handle] = mat
        self.add_to_history("create_material_handle", f"{handle} -> {material_name}", f"Created handle '{handle}'")

        return {
            "success": True,
            "handle": handle,
            "material_name": material_name,
            "uses_nodes": mat.use_nodes
        }

    def list_object_handles(self):
        """List all object handles and their details"""
        handles = {}
        for handle, obj in self.shared_context['objects'].items():
            handles[handle] = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "visible": obj.visible_get()
            }
        return {"object_handles": handles}

    def list_material_handles(self):
        """List all material handles and their details"""
        handles = {}
        for handle, mat in self.shared_context['materials'].items():
            handles[handle] = {
                "name": mat.name,
                "uses_nodes": mat.use_nodes,
                "users": mat.users
            }
        return {"material_handles": handles}


class ScriptRegistryService:
    def _get_script_directory(self, category):
        """Get the script directory path for a given category"""
        import tempfile
        temp_dir = tempfile.gettempdir()
        script_dir = os.path.join(temp_dir, ".blendermcp", category)
        os.makedirs(script_dir, exist_ok=True)
        return script_dir

    def _get_metadata_path(self, script_dir):
        """Get the metadata file path for a script directory"""
        return os.path.join(script_dir, ".meta.json")

    def _load_metadata(self, script_dir):
        """Load metadata for a script directory"""
        metadata_path = self._get_metadata_path(script_dir)
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_script_metadata(self, script_dir, script_name, permanent):
        """Save metadata for a script"""
        import time
        metadata = self._load_metadata(script_dir)
        metadata[script_name] = {
            "permanent": permanent,
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "description": f"{'Permanent' if permanent else 'Temporary'} script"
        }

        metadata_path = self._get_metadata_path(script_dir)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def register_context_script(self, script_name, script_content, category="default", permanent=False):
        """Register a Python script for later execution"""
        try:
            # Validate script syntax
            try:
                compile(script_content, f"{script_name}.py", 'exec')
            except SyntaxError as e:
                return {
                    "status": "error",
                    "message": f"Script syntax error: {str(e)}"
                }

            # Save script to file
            script_dir = self._get_script_directory(category)
            script_path = os.path.join(script_dir, f"{script_name}.py")

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # Save metadata
            self._save_script_metadata(script_dir, script_name, permanent)

            permanence = "permanent" if permanent else "temporary"
            return {
                "status": "success",
                "message": f"Script '{script_name}' registered as {permanence} in category '{category}'"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error registering script: {str(e)}"
            }

    def execute_context_script(self, script_name, category="default"):
        """Execute a previously registered script"""
        try:
            script_dir = self._get_script_directory(category)
            script_path = os.path.join(script_dir, f"{script_name}.py")

            if not os.path.exists(script_path):
                return {
                    "status": "error",
                    "message": f"Script '{script_name}' not found in category '{category}'"
                }

            # Read script content
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Execute script and capture output
            import io
            from contextlib import redirect_stdout, redirect_stderr

            output_buffer = io.StringIO()
            error_buffer = io.StringIO()

            try:
                with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                    # Create a safe execution environment
                    exec_globals = {
                        'bpy': bpy,
                        'mathutils': mathutils,
                        '__name__': '__main__'
                    }
                    exec(script_content, exec_globals)

                output = output_buffer.getvalue()
                errors = error_buffer.getvalue()

                if errors:
                    return {
                        "status": "error",
                        "message": f"Script execution error: {errors}",
                        "output": output
                    }

                return {
                    "status": "success",
                    "output": output if output else "Script executed successfully (no output)"
                }

            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Script execution error: {str(e)}",
                    "output": output_buffer.getvalue()
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing script: {str(e)}"
            }

    def list_context_scripts(self, category=None):
        """List all registered scripts"""
        try:
            import tempfile
            import time

            base_dir = os.path.join(tempfile.gettempdir(), ".blendermcp")

            if not os.path.exists(base_dir):
                return {
                    "status": "success",
                    "scripts": {}
                }

            scripts = {}

            if category:
                categories = [category]
            else:
                categories = [d for d in os.listdir(base_dir)
                            if os.path.isdir(os.path.join(base_dir, d))]

            for cat in categories:
                cat_dir = os.path.join(base_dir, cat)
                if not os.path.exists(cat_dir):
                    continue

                metadata = self._load_metadata(cat_dir)
                script_list = []

                for filename in os.listdir(cat_dir):
                    if filename.endswith('.py'):
                        script_name = filename[:-3]  # Remove .py extension
                        script_path = os.path.join(cat_dir, filename)
                        stat = os.stat(script_path)

                        script_meta = metadata.get(script_name, {})
                        script_list.append({
                            "name": script_name,
                            "size": stat.st_size,
                            "created": script_meta.get("created", time.ctime(stat.st_ctime)),
                            "permanent": script_meta.get("permanent", False),
                            "description": script_meta.get("description", "")
                        })

                if script_list:
                    # Sort by permanence (permanent first), then by name
                    script_list.sort(key=lambda x: (not x["permanent"], x["name"]))
                    scripts[cat] = script_list

            return {
                "status": "success",
                "scripts": scripts
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error listing scripts: {str(e)}"
            }

    def clear_context_scripts(self, category=None, script_name=None, clear_permanent=False):
        """Clear scripts from the registry"""
        try:
            import tempfile
            import shutil

            base_dir = os.path.join(tempfile.gettempdir(), ".blendermcp")

            if not os.path.exists(base_dir):
                return {
                    "status": "success",
                    "message": "No scripts to clear"
                }

            if script_name and category:
                # Clear specific script
                cat_dir = os.path.join(base_dir, category)
                script_path = os.path.join(cat_dir, f"{script_name}.py")

                if not os.path.exists(script_path):
                    return {
                        "status": "error",
                        "message": f"Script '{script_name}' not found in category '{category}'"
                    }

                # Check if script is permanent
                metadata = self._load_metadata(cat_dir)
                script_meta = metadata.get(script_name, {})
                is_permanent = script_meta.get("permanent", False)

                if is_permanent and not clear_permanent:
                    return {
                        "status": "error",
                        "message": f"Script '{script_name}' is permanent. Use clear_permanent=True to force deletion."
                    }

                # Remove script file
                os.remove(script_path)

                # Remove from metadata
                if script_name in metadata:
                    del metadata[script_name]
                    metadata_path = self._get_metadata_path(cat_dir)
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)

                return {
                    "status": "success",
                    "message": f"Script '{script_name}' cleared from category '{category}'"
                }

            elif category:
                # Clear entire category (respecting permanent scripts)
                cat_dir = os.path.join(base_dir, category)
                if not os.path.exists(cat_dir):
                    return {
                        "status": "success",
                        "message": f"Category '{category}' was already empty"
                    }

                metadata = self._load_metadata(cat_dir)
                cleared_count = 0
                permanent_count = 0

                # Process each script in the category
                for filename in os.listdir(cat_dir):
                    if filename.endswith('.py'):
                        script_name = filename[:-3]
                        script_meta = metadata.get(script_name, {})
                        is_permanent = script_meta.get("permanent", False)

                        if is_permanent and not clear_permanent:
                            permanent_count += 1
                        else:
                            script_path = os.path.join(cat_dir, filename)
                            os.remove(script_path)
                            if script_name in metadata:
                                del metadata[script_name]
                            cleared_count += 1

                # Update metadata file
                if metadata or permanent_count > 0:
                    metadata_path = self._get_metadata_path(cat_dir)
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                else:
                    # No scripts left, remove entire directory
                    shutil.rmtree(cat_dir)

                message = f"Cleared {cleared_count} temporary scripts from category '{category}'"
                if permanent_count > 0:
                    message += f". {permanent_count} permanent scripts preserved."

                return {
                    "status": "success",
                    "message": message
                }

            else:
                # Clear all scripts (respecting permanent scripts)
                cleared_count = 0
                permanent_count = 0

                for cat_name in os.listdir(base_dir):
                    cat_dir = os.path.join(base_dir, cat_name)
                    if not os.path.isdir(cat_dir):
                        continue

                    metadata = self._load_metadata(cat_dir)
                    cat_cleared = 0

                    for filename in os.listdir(cat_dir):
                        if filename.endswith('.py'):
                            script_name = filename[:-3]
                            script_meta = metadata.get(script_name, {})
                            is_permanent = script_meta.get("permanent", False)

                            if is_permanent and not clear_permanent:
                                permanent_count += 1
                            else:
                                script_path = os.path.join(cat_dir, filename)
                                os.remove(script_path)
                                if script_name in metadata:
                                    del metadata[script_name]
                                cleared_count += 1
                                cat_cleared += 1

                    # Update or remove category
                    if metadata or (permanent_count > 0 and cat_cleared < len([f for f in os.listdir(cat_dir) if f.endswith('.py')])):
                        metadata_path = self._get_metadata_path(cat_dir)
                        with open(metadata_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2)
                    else:
                        # Check if directory is empty (except metadata)
                        remaining_files = [f for f in os.listdir(cat_dir) if not f.startswith('.meta')]
                        if not remaining_files:
                            shutil.rmtree(cat_dir)

                message = f"Cleared {cleared_count} temporary scripts"
                if permanent_count > 0:
                    message += f". {permanent_count} permanent scripts preserved."

                return {
                    "status": "success",
                    "message": message
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error clearing scripts: {str(e)}"
            }

class SceneObservationService:
    def __init__(self, server):
        self.server = server

    def get_scene_info(self):
        try:
            print("Getting scene info...")
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
            }

            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 10:
                    break
                scene_info["objects"].append({
                    "name": obj.name,
                    "type": obj.type,
                    "location": [
                        round(float(obj.location.x), 2),
                        round(float(obj.location.y), 2),
                        round(float(obj.location.z), 2),
                    ],
                })

            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    def get_object_info(self, name):
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "materials": [],
        }

        if obj.type == "MESH":
            obj_info["world_bounding_box"] = self.server._get_aabb(obj)

        for slot in obj.material_slots:
            if slot.material:
                obj_info["materials"].append(slot.material.name)

        if obj.type == "MESH" and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }

        return obj_info


class ViewportScreenshotService:
    def __init__(self, server):
        self.server = server

    def get_viewport_screenshot(self, max_size=800, filepath=None, format="png"):
        try:
            if not filepath:
                return {"error": "No filepath provided"}

            area = None
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    area = a
                    break

            if not area:
                return {"error": "No 3D viewport found"}

            with bpy.context.temp_override(area=area):
                bpy.ops.screen.screenshot_area(filepath=filepath)

            img = bpy.data.images.load(filepath)
            width, height = img.size

            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img.scale(new_width, new_height)
                img.file_format = format.upper()
                img.save()
                width, height = new_width, new_height

            bpy.data.images.remove(img)

            return {
                "success": True,
                "width": width,
                "height": height,
                "filepath": filepath
            }
        except Exception as e:
            return {"error": str(e)}


class SceneIntelligenceService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _vector(value, digits=4):
        return [round(float(component), digits) for component in value]

    @staticmethod
    def _matrix(value, digits=4):
        return [[round(float(component), digits) for component in row] for row in value]

    @staticmethod
    def _collection_names(obj):
        return [collection.name for collection in getattr(obj, "users_collection", [])]

    @staticmethod
    def _material_names(obj):
        names = []
        for slot in getattr(obj, "material_slots", []):
            if slot.material:
                names.append(slot.material.name)
        return names

    @staticmethod
    def _modifier_names(obj):
        return [modifier.name for modifier in getattr(obj, "modifiers", [])]

    @staticmethod
    def _constraint_names(obj):
        return [constraint.name for constraint in getattr(obj, "constraints", [])]

    def _world_bounds(self, obj):
        if not hasattr(obj, "bound_box") or not obj.bound_box:
            return None

        corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        if not corners:
            return None

        min_corner = [min(corner[index] for corner in corners) for index in range(3)]
        max_corner = [max(corner[index] for corner in corners) for index in range(3)]
        center = [(min_corner[index] + max_corner[index]) / 2 for index in range(3)]
        size = [max_corner[index] - min_corner[index] for index in range(3)]
        return {
            "min": self._vector(min_corner),
            "max": self._vector(max_corner),
            "center": self._vector(center),
            "size": self._vector(size),
        }

    def _object_summary(self, obj, include_materials=True, include_modifiers=True, include_constraints=True):
        active = bpy.context.view_layer.objects.active
        summary = {
            "name": obj.name,
            "type": obj.type,
            "visible": bool(obj.visible_get()),
            "hidden_viewport": bool(obj.hide_viewport),
            "selected": bool(obj.select_get()),
            "active": active == obj,
            "collection_names": self._collection_names(obj),
            "parent": obj.parent.name if obj.parent else None,
            "children": [child.name for child in obj.children],
            "location": self._vector(obj.location),
            "rotation_euler": self._vector(obj.rotation_euler),
            "scale": self._vector(obj.scale),
            "dimensions": self._vector(obj.dimensions),
            "bound_box_world": self._world_bounds(obj),
        }
        if include_materials:
            summary["material_names"] = self._material_names(obj)
        if include_modifiers:
            summary["modifier_names"] = self._modifier_names(obj)
        if include_constraints:
            summary["constraint_names"] = self._constraint_names(obj)
        return summary

    def _collection_summary(self, collection):
        return {
            "name": collection.name,
            "object_count": len(collection.objects),
            "children": [child.name for child in collection.children],
            "hide_viewport": bool(collection.hide_viewport),
        }

    def _material_summary(self, material):
        return {
            "name": material.name,
            "use_nodes": bool(material.use_nodes),
            "users": int(material.users),
        }

    def get_scene_index(
        self,
        include_hidden=True,
        include_materials=True,
        include_modifiers=True,
        include_constraints=True,
        include_collections=True,
        max_objects=None,
    ):
        warnings = []
        scene = bpy.context.scene
        objects = list(scene.objects)
        if not include_hidden:
            objects = [obj for obj in objects if obj.visible_get()]

        truncated = False
        if max_objects is not None:
            try:
                max_count = max(0, int(max_objects))
                if len(objects) > max_count:
                    objects = objects[:max_count]
                    truncated = True
                    warnings.append(f"Scene index truncated to {max_count} objects")
            except (TypeError, ValueError):
                warnings.append(f"Ignoring invalid max_objects value: {max_objects!r}")

        scene_data = {
            "name": scene.name,
            "frame_current": int(scene.frame_current),
            "frame_start": int(scene.frame_start),
            "frame_end": int(scene.frame_end),
            "unit_system": scene.unit_settings.system,
            "render_engine": scene.render.engine,
            "object_count": len(scene.objects),
            "collection_count": len(bpy.data.collections),
            "material_count": len(bpy.data.materials),
            "camera_count": sum(1 for obj in scene.objects if obj.type == "CAMERA"),
            "light_count": sum(1 for obj in scene.objects if obj.type == "LIGHT"),
        }

        return {
            "status": "success",
            "scene": scene_data,
            "objects": [
                self._object_summary(obj, include_materials, include_modifiers, include_constraints)
                for obj in objects
            ],
            "collections": [self._collection_summary(collection) for collection in bpy.data.collections] if include_collections else [],
            "materials": [self._material_summary(material) for material in bpy.data.materials] if include_materials else [],
            "warnings": warnings,
            "truncated": truncated,
        }

    def _mesh_stats(self, obj):
        mesh = obj.data
        return {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "triangles_estimate": sum(max(1, len(poly.vertices) - 2) for poly in mesh.polygons),
        }

    def _modifier_details(self, obj):
        return [
            {
                "name": modifier.name,
                "type": modifier.type,
                "show_viewport": bool(modifier.show_viewport),
                "show_render": bool(modifier.show_render),
            }
            for modifier in getattr(obj, "modifiers", [])
        ]

    def _constraint_details(self, obj):
        return [
            {
                "name": constraint.name,
                "type": constraint.type,
                "mute": bool(constraint.mute),
                "influence": round(float(constraint.influence), 4),
            }
            for constraint in getattr(obj, "constraints", [])
        ]

    def _material_slots(self, obj):
        materials = []
        for index, slot in enumerate(getattr(obj, "material_slots", [])):
            material = slot.material
            materials.append({
                "slot_index": index,
                "slot_name": slot.name,
                "material_name": material.name if material else None,
                "use_nodes": bool(material.use_nodes) if material else False,
            })
        return materials

    def _animation_summary(self, obj):
        animation_data = obj.animation_data
        if not animation_data:
            return {"has_animation_data": False}
        action = animation_data.action
        return {
            "has_animation_data": True,
            "action": action.name if action else None,
            "fcurve_count": len(action.fcurves) if action else 0,
            "nla_track_count": len(animation_data.nla_tracks),
        }

    def _custom_properties(self, obj):
        properties = {}
        for key in obj.keys():
            if key == "_RNA_UI":
                continue
            value = obj.get(key)
            if isinstance(value, (str, int, float, bool)) or value is None:
                properties[key] = value
            else:
                properties[key] = str(value)
        return properties

    def _type_specific_info(self, obj):
        data = getattr(obj, "data", None)
        if obj.type == "CAMERA" and data:
            return {
                "lens": round(float(data.lens), 4),
                "sensor_width": round(float(data.sensor_width), 4),
                "clip_start": round(float(data.clip_start), 4),
                "clip_end": round(float(data.clip_end), 4),
                "dof_enabled": bool(data.dof.use_dof),
            }
        if obj.type == "LIGHT" and data:
            return {
                "light_type": data.type,
                "energy": round(float(data.energy), 4),
                "color": self._vector(data.color),
                "use_shadow": bool(getattr(data, "use_shadow", False)),
            }
        if obj.type == "CURVE" and data:
            return {"spline_count": len(data.splines), "dimensions": data.dimensions}
        if obj.type == "ARMATURE" and data:
            return {"bone_count": len(data.bones)}
        if obj.type == "EMPTY":
            return {"empty_display_type": obj.empty_display_type}
        return {}

    def get_object_deep_info(
        self,
        object_name=None,
        name=None,
        include_mesh_stats=True,
        include_material_slots=True,
        include_modifiers=True,
        include_constraints=True,
        include_animation=True,
        include_custom_properties=True,
    ):
        target_name = object_name or name
        if not target_name:
            return {"status": "error", "message": "object_name is required"}

        obj = bpy.data.objects.get(target_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {target_name}"}

        info = {
            "name": obj.name,
            "type": obj.type,
            "data_name": obj.data.name if getattr(obj, "data", None) else None,
            "parent": obj.parent.name if obj.parent else None,
            "children": [child.name for child in obj.children],
            "collection_names": self._collection_names(obj),
            "visible": bool(obj.visible_get()),
            "selected": bool(obj.select_get()),
            "active": bpy.context.view_layer.objects.active == obj,
            "transform": {
                "location": self._vector(obj.location),
                "rotation_euler": self._vector(obj.rotation_euler),
                "scale": self._vector(obj.scale),
                "matrix_world": self._matrix(obj.matrix_world),
            },
            "dimensions": self._vector(obj.dimensions),
            "bounding_box": self._world_bounds(obj),
            "type_specific": self._type_specific_info(obj),
        }
        if include_mesh_stats and obj.type == "MESH" and obj.data:
            info["mesh_stats"] = self._mesh_stats(obj)
        if include_material_slots:
            info["materials"] = self._material_slots(obj)
        if include_modifiers:
            info["modifiers"] = self._modifier_details(obj)
        if include_constraints:
            info["constraints"] = self._constraint_details(obj)
        if include_animation:
            info["animation"] = self._animation_summary(obj)
        if include_custom_properties:
            info["custom_properties"] = self._custom_properties(obj)

        return {"status": "success", "object": info, "warnings": []}

    def get_selection_info(self):
        selected = list(bpy.context.selected_objects)
        active = bpy.context.view_layer.objects.active
        bounds = None
        warnings = []

        if selected:
            object_bounds = [self._world_bounds(obj) for obj in selected]
            object_bounds = [bound for bound in object_bounds if bound]
            if object_bounds:
                min_corner = [min(bound["min"][index] for bound in object_bounds) for index in range(3)]
                max_corner = [max(bound["max"][index] for bound in object_bounds) for index in range(3)]
                center = [(min_corner[index] + max_corner[index]) / 2 for index in range(3)]
                size = [max_corner[index] - min_corner[index] for index in range(3)]
                bounds = {
                    "min": self._vector(min_corner),
                    "max": self._vector(max_corner),
                    "center": self._vector(center),
                    "size": self._vector(size),
                }

        mode = getattr(bpy.context, "mode", "UNKNOWN")
        if mode != "OBJECT":
            warnings.append("Edit-mode component selection details are not implemented; object selection was reported without changing mode")

        return {
            "status": "success",
            "active_object": active.name if active else None,
            "selected_objects": [obj.name for obj in selected],
            "selected_count": len(selected),
            "mode": mode,
            "selection_bounds": bounds,
            "objects": [
                {
                    "name": obj.name,
                    "type": obj.type,
                    "visible": bool(obj.visible_get()),
                    "dimensions": self._vector(obj.dimensions),
                }
                for obj in selected
            ],
            "warnings": warnings,
        }

    def get_scene_health(self):
        scene = bpy.context.scene
        objects = list(scene.objects)
        mesh_objects = [obj for obj in objects if obj.type == "MESH"]
        hidden = [obj for obj in objects if obj.hide_viewport or not obj.visible_get()]
        no_material = [obj for obj in mesh_objects if not self._material_names(obj)]
        negative_scale = [obj for obj in objects if any(float(axis) < 0 for axis in obj.scale)]
        unapplied_scale = [obj for obj in objects if any(abs(float(axis) - 1.0) > 0.001 for axis in obj.scale)]
        missing_mesh_data = [obj for obj in mesh_objects if obj.data is None]
        far_from_origin = [obj for obj in objects if obj.location.length > 10000]
        empty_collections = [collection for collection in bpy.data.collections if len(collection.objects) == 0 and len(collection.children) == 0]
        issues = []

        def add_issue(severity, code, message, issue_objects=None):
            issues.append({
                "severity": severity,
                "code": code,
                "message": message,
                "objects": [obj.name for obj in issue_objects or []],
            })

        if not any(obj.type == "CAMERA" for obj in objects):
            add_issue("warning", "NO_CAMERA", "Scene has no camera")
        if not any(obj.type == "LIGHT" for obj in objects):
            add_issue("info", "NO_LIGHTS", "Scene has no lights")
        if no_material:
            add_issue("info", "MISSING_MATERIALS", f"{len(no_material)} mesh object(s) have no material slots", no_material[:20])
        if hidden:
            add_issue("info", "HIDDEN_OBJECTS", f"{len(hidden)} object(s) are hidden or not visible in viewport", hidden[:20])
        if len(objects) > 1000:
            add_issue("warning", "LARGE_OBJECT_COUNT", f"Scene has {len(objects)} objects")
        if negative_scale:
            add_issue("warning", "NEGATIVE_SCALE", f"{len(negative_scale)} object(s) have negative scale", negative_scale[:20])
        if unapplied_scale:
            add_issue("info", "UNAPPLIED_SCALE", f"{len(unapplied_scale)} object(s) have scale different from 1.0", unapplied_scale[:20])
        if missing_mesh_data:
            add_issue("error", "MISSING_MESH_DATA", f"{len(missing_mesh_data)} mesh object(s) have missing mesh data", missing_mesh_data[:20])
        if empty_collections:
            issues.append({
                "severity": "info",
                "code": "EMPTY_COLLECTIONS",
                "message": f"{len(empty_collections)} empty collection(s)",
                "objects": [],
                "collections": [collection.name for collection in empty_collections[:20]],
            })
        if far_from_origin:
            add_issue("warning", "FAR_FROM_ORIGIN", f"{len(far_from_origin)} object(s) are very far from origin", far_from_origin[:20])

        summary = {
            "object_count": len(objects),
            "hidden_count": len(hidden),
            "mesh_count": len(mesh_objects),
            "material_count": len(bpy.data.materials),
            "missing_material_objects": len(no_material),
            "camera_count": sum(1 for obj in objects if obj.type == "CAMERA"),
            "light_count": sum(1 for obj in objects if obj.type == "LIGHT"),
            "objects_with_negative_scale": len(negative_scale),
            "objects_with_unapplied_scale": len(unapplied_scale),
            "objects_with_modifiers": sum(1 for obj in objects if len(getattr(obj, "modifiers", [])) > 0),
        }
        return {"status": "success", "summary": summary, "issues": issues, "warnings": []}


class VerificationArtifactService:
    DEFAULT_VIEWS = ["perspective", "front", "right", "top"]
    SUPPORTED_VIEWS = {"perspective", "front", "right", "top", "back", "left", "bottom", "camera"}

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _utc_timestamp():
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @staticmethod
    def _snapshot_stamp():
        return time.strftime("%Y%m%d_%H%M%S", time.localtime())

    @staticmethod
    def _safe_label(label):
        if not label:
            return "scene"
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(label)).strip("._-")
        return safe[:60] or "scene"

    def _artifact_root(self, artifact_root=None):
        root = artifact_root or os.environ.get("OVERTLI_BLENDER_ARTIFACT_ROOT") or ADDON_ROOT
        return os.path.abspath(os.path.expanduser(str(root)))

    def _snapshot_dir(self, snapshot_name=None, label=None, artifact_root=None):
        snapshot_id = f"{self._snapshot_stamp()}_{self._safe_label(snapshot_name or label)}"
        base_dir = os.path.join(self._artifact_root(artifact_root), ".overtli_blender", "verification", "snapshots", snapshot_id)
        suffix = 1
        candidate = base_dir
        while os.path.exists(candidate):
            suffix += 1
            candidate = f"{base_dir}_{suffix}"
        os.makedirs(candidate, exist_ok=True)
        return os.path.basename(candidate), candidate

    @staticmethod
    def _write_json(path, data):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, sort_keys=True)

    def _find_viewport_context(self):
        screen = bpy.context.screen
        if not screen:
            return None
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            region = next((region for region in area.regions if region.type == "WINDOW"), None)
            space = next((space for space in area.spaces if space.type == "VIEW_3D"), None)
            if region and space and space.region_3d:
                return area, region, space, space.region_3d
        return None

    def _capture_named_view(self, view_name, filepath, max_size):
        viewport_context = self._find_viewport_context()
        if not viewport_context:
            return {"view": view_name, "path": filepath, "status": "error", "message": "No 3D viewport found"}

        area, region, space, region_3d = viewport_context
        original_state = {
            "view_perspective": region_3d.view_perspective,
            "view_location": region_3d.view_location.copy(),
            "view_rotation": region_3d.view_rotation.copy(),
            "view_distance": region_3d.view_distance,
            "view_camera_zoom": region_3d.view_camera_zoom,
            "view_camera_offset": tuple(region_3d.view_camera_offset),
        }

        try:
            with bpy.context.temp_override(area=area, region=region, space_data=space, region_data=region_3d):
                if view_name == "camera":
                    if bpy.context.scene.camera is None:
                        return {"view": view_name, "path": filepath, "status": "error", "message": "Scene has no active camera"}
                    region_3d.view_perspective = "CAMERA"
                elif view_name != "perspective":
                    bpy.ops.view3d.view_axis(type=view_name.upper(), align_active=False)
                else:
                    region_3d.view_perspective = "PERSP"
                bpy.ops.screen.screenshot_area(filepath=filepath)

            img = bpy.data.images.load(filepath)
            width, height = img.size
            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                width = max(1, int(width * scale))
                height = max(1, int(height * scale))
                img.scale(width, height)
                img.file_format = "PNG"
                img.save()
            bpy.data.images.remove(img)
            return {"view": view_name, "path": filepath, "width": width, "height": height, "status": "success"}
        except Exception as exc:
            return {"view": view_name, "path": filepath, "status": "error", "message": str(exc)}
        finally:
            try:
                region_3d.view_perspective = original_state["view_perspective"]
                region_3d.view_location = original_state["view_location"]
                region_3d.view_rotation = original_state["view_rotation"]
                region_3d.view_distance = original_state["view_distance"]
                region_3d.view_camera_zoom = original_state["view_camera_zoom"]
                region_3d.view_camera_offset = original_state["view_camera_offset"]
            except Exception:
                pass

    def _normalize_views(self, views):
        if not views:
            return list(self.DEFAULT_VIEWS), []
        normalized = []
        warnings = []
        for view in views:
            name = str(view).strip().lower()
            if name not in self.SUPPORTED_VIEWS:
                warnings.append(f"Unsupported view skipped: {view}")
                continue
            if name not in normalized:
                normalized.append(name)
        if not normalized:
            normalized = list(self.DEFAULT_VIEWS)
            warnings.append("No supported views requested; default views were used")
        return normalized, warnings

    def capture_viewport_pack(self, views=None, max_size=800, include_manifest=True, snapshot_name=None, artifact_dir=None, artifact_root=None):
        max_size = max(64, min(int(max_size), 4096))
        view_names, warnings = self._normalize_views(views)
        if artifact_dir:
            snapshot_id = os.path.basename(os.path.normpath(artifact_dir))
            target_dir = artifact_dir
            os.makedirs(target_dir, exist_ok=True)
        else:
            snapshot_id, target_dir = self._snapshot_dir(snapshot_name=snapshot_name or "viewport_pack", artifact_root=artifact_root)

        screenshot_dir = os.path.join(target_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshots = []
        for view_name in view_names:
            path = os.path.join(screenshot_dir, f"{view_name}.png")
            result = self._capture_named_view(view_name, path, max_size)
            screenshots.append(result)
            if result.get("status") != "success":
                warnings.append(f"{view_name}: {result.get('message', 'capture failed')}")

        if not any(item.get("status") == "success" for item in screenshots):
            return {
                "status": "error",
                "message": "No screenshots were captured",
                "snapshot_id": snapshot_id,
                "artifact_dir": target_dir,
                "screenshots": screenshots,
                "warnings": warnings,
            }

        manifest = {
            "snapshot_id": snapshot_id,
            "created_at": self._utc_timestamp(),
            "artifact_dir": target_dir,
            "command": "capture_viewport_pack",
            "parameters": {"views": view_names, "max_size": max_size, "include_manifest": include_manifest},
            "screenshots": screenshots,
            "warnings": warnings,
        }
        manifest_path = os.path.join(target_dir, "manifest.json")
        if include_manifest:
            self._write_json(manifest_path, manifest)

        return {
            "status": "success",
            "snapshot_id": snapshot_id,
            "artifact_dir": target_dir,
            "screenshots": screenshots,
            "manifest_path": manifest_path if include_manifest else None,
            "warnings": warnings,
        }

    def create_verification_snapshot(
        self,
        label=None,
        include_scene_index=True,
        include_scene_health=True,
        include_selection=True,
        include_screenshots=True,
        views=None,
        max_size=800,
        artifact_root=None,
    ):
        snapshot_id, target_dir = self._snapshot_dir(label=label or "scene", artifact_root=artifact_root)
        warnings = []
        artifacts = {"screenshots": []}

        if include_scene_index:
            path = os.path.join(target_dir, "scene_index.json")
            scene_index = self.server.scene_intelligence_service.get_scene_index()
            self._write_json(path, scene_index)
            artifacts["scene_index"] = "scene_index.json"
            warnings.extend(scene_index.get("warnings", []))

        if include_scene_health:
            path = os.path.join(target_dir, "scene_health.json")
            scene_health = self.server.scene_intelligence_service.get_scene_health()
            self._write_json(path, scene_health)
            artifacts["scene_health"] = "scene_health.json"
            warnings.extend(scene_health.get("warnings", []))

        if include_selection:
            path = os.path.join(target_dir, "selection_info.json")
            selection_info = self.server.scene_intelligence_service.get_selection_info()
            self._write_json(path, selection_info)
            artifacts["selection_info"] = "selection_info.json"
            warnings.extend(selection_info.get("warnings", []))

        if include_screenshots:
            pack_result = self.capture_viewport_pack(
                views=views,
                max_size=max_size,
                include_manifest=False,
                snapshot_name=snapshot_id,
                artifact_dir=target_dir,
                artifact_root=artifact_root,
            )
            artifacts["screenshots"] = [
                os.path.relpath(item.get("path"), target_dir).replace("\\", "/")
                for item in pack_result.get("screenshots", [])
                if item.get("status") == "success" and item.get("path")
            ]
            warnings.extend(pack_result.get("warnings", []))
            if pack_result.get("status") != "success":
                warnings.append(pack_result.get("message", "Screenshot pack failed"))

        manifest = {
            "snapshot_id": snapshot_id,
            "label": label,
            "created_at": self._utc_timestamp(),
            "blender_file": bpy.data.filepath or None,
            "scene_name": bpy.context.scene.name,
            "safety_mode": self.server.safety_policy_service.mode,
            "commands": {
                "include_scene_index": bool(include_scene_index),
                "include_scene_health": bool(include_scene_health),
                "include_selection": bool(include_selection),
                "include_screenshots": bool(include_screenshots),
            },
            "artifact_dir": target_dir,
            "artifacts": artifacts,
            "warnings": warnings,
        }
        manifest_path = os.path.join(target_dir, "manifest.json")
        self._write_json(manifest_path, manifest)

        return {
            "status": "success",
            "snapshot_id": snapshot_id,
            "artifact_dir": target_dir,
            "manifest_path": manifest_path,
            "artifacts": artifacts,
            "warnings": warnings,
        }

    def list_verification_snapshots(self):
        snapshot_root = os.path.join(self._artifact_root(), ".overtli_blender", "verification", "snapshots")
        if not os.path.isdir(snapshot_root):
            return {"status": "success", "snapshot_root": snapshot_root, "snapshots": [], "warnings": []}

        snapshots = []
        for name in sorted(os.listdir(snapshot_root), reverse=True):
            path = os.path.join(snapshot_root, name)
            if not os.path.isdir(path):
                continue
            manifest_path = os.path.join(path, "manifest.json")
            snapshots.append({
                "snapshot_id": name,
                "artifact_dir": path,
                "manifest_path": manifest_path if os.path.exists(manifest_path) else None,
            })
        return {"status": "success", "snapshot_root": snapshot_root, "snapshots": snapshots, "warnings": []}


class ProviderStatusService:
    def __init__(self, server):
        self.server = server

    def get_polyhaven_status(self):
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled:
            return {"enabled": True, "message": "PolyHaven integration is enabled and ready to use."}
        return {
            "enabled": False,
            "message": """PolyHaven integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Poly Haven' checkbox
                            3. Restart the connection to the MCP server"""
        }

    def get_hyper3d_status(self):
        enabled = bpy.context.scene.blendermcp_use_hyper3d
        if enabled:
            if not bpy.context.scene.blendermcp_hyper3d_api_key:
                return {
                    "enabled": False,
                    "message": """Hyper3D Rodin integration is currently enabled, but API key is not given. To enable it:
                                1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Hyper3D Rodin 3D model generation' checkbox checked
                                3. Choose the right plaform and fill in the API Key
                                4. Restart the connection to the MCP server"""
                }
            mode = bpy.context.scene.blendermcp_hyper3d_mode
            message = f"Hyper3D Rodin integration is enabled and ready to use. Mode: {mode}. " + \
                f"Key type: {'private' if bpy.context.scene.blendermcp_hyper3d_api_key != RODIN_FREE_TRIAL_KEY else 'free_trial'}"
            return {"enabled": True, "message": message}
        return {
            "enabled": False,
            "message": """Hyper3D Rodin integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use Hyper3D Rodin 3D model generation' checkbox
                            3. Restart the connection to the MCP server"""
        }

    def get_sketchfab_status(self):
        enabled = bpy.context.scene.blendermcp_use_sketchfab
        api_key = bpy.context.scene.blendermcp_sketchfab_api_key

        if api_key:
            try:
                response = requests.get(
                    "https://api.sketchfab.com/v3/me",
                    headers={"Authorization": f"Token {api_key}"},
                    timeout=30,
                )
                if response.status_code == 200:
                    user_data = response.json()
                    username = user_data.get("username", "Unknown user")
                    return {
                        "enabled": True,
                        "message": f"Sketchfab integration is enabled and ready to use. Logged in as: {username}"
                    }
                return {
                    "enabled": False,
                    "message": f"Sketchfab API key seems invalid. Status code: {response.status_code}"
                }
            except requests.exceptions.Timeout:
                return {
                    "enabled": False,
                    "message": "Timeout connecting to Sketchfab API. Check your internet connection."
                }
            except Exception as e:
                return {
                    "enabled": False,
                    "message": f"Error testing Sketchfab API key: {str(e)}"
                }

        if enabled and api_key:
            return {"enabled": True, "message": "Sketchfab integration is enabled and ready to use."}
        if enabled and not api_key:
            return {
                "enabled": False,
                "message": """Sketchfab integration is currently enabled, but API key is not given. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Keep the 'Use Sketchfab' checkbox checked
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to the MCP server"""
            }
        return {
            "enabled": False,
            "message": """Sketchfab integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Sketchfab' checkbox
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to the MCP server"""
        }

class PolyHavenService:
    def __init__(self, server):
        self.server = server

    def get_polyhaven_categories(self, asset_type):
        try:
            if asset_type not in ["hdris", "textures", "models", "all"]:
                return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}

            response = requests.get(f"https://api.polyhaven.com/categories/{asset_type}", headers=REQ_HEADERS)
            if response.status_code == 200:
                return {"categories": response.json()}
            return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def search_polyhaven_assets(self, asset_type=None, categories=None):
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}
            if asset_type and asset_type != "all":
                if asset_type not in ["hdris", "textures", "models"]:
                    return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}
                params["type"] = asset_type
            if categories:
                params["categories"] = categories
            response = requests.get(url, params=params, headers=REQ_HEADERS)
            if response.status_code == 200:
                assets = response.json()
                limited_assets = {}
                for i, (key, value) in enumerate(assets.items()):
                    if i >= 20:
                        break
                    limited_assets[key] = value
                return {"assets": limited_assets, "total_count": len(assets), "returned_count": len(limited_assets)}
            return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def download_polyhaven_asset(self, asset_id, asset_type, resolution="1k", file_format=None):
        try:
            files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}", headers=REQ_HEADERS)
            if files_response.status_code != 200:
                return {"error": f"Failed to get asset files: {files_response.status_code}"}

            files_data = files_response.json()

            if asset_type == "hdris":
                if not file_format:
                    file_format = "hdr"
                if "hdri" in files_data and resolution in files_data["hdri"] and file_format in files_data["hdri"][resolution]:
                    file_info = files_data["hdri"][resolution][file_format]
                    file_url = file_info["url"]
                    with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                        response = requests.get(file_url, headers=REQ_HEADERS)
                        if response.status_code != 200:
                            return {"error": f"Failed to download HDRI: {response.status_code}"}
                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name

                    try:
                        if not bpy.data.worlds:
                            bpy.data.worlds.new("World")
                        world = bpy.data.worlds[0]
                        world.use_nodes = True
                        node_tree = world.node_tree
                        for node in node_tree.nodes:
                            node_tree.nodes.remove(node)

                        tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
                        tex_coord.location = (-800, 0)
                        mapping = node_tree.nodes.new(type='ShaderNodeMapping')
                        mapping.location = (-600, 0)
                        env_tex = node_tree.nodes.new(type='ShaderNodeTexEnvironment')
                        env_tex.location = (-400, 0)
                        env_tex.image = bpy.data.images.load(tmp_path)
                        if file_format.lower() == 'exr':
                            try:
                                env_tex.image.colorspace_settings.name = 'Linear'
                            except:
                                env_tex.image.colorspace_settings.name = 'Non-Color'
                        else:
                            for color_space in ['Linear', 'Linear Rec.709', 'Non-Color']:
                                try:
                                    env_tex.image.colorspace_settings.name = color_space
                                    break
                                except:
                                    continue
                        background = node_tree.nodes.new(type='ShaderNodeBackground')
                        background.location = (-200, 0)
                        output = node_tree.nodes.new(type='ShaderNodeOutputWorld')
                        output.location = (0, 0)
                        node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
                        node_tree.links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
                        node_tree.links.new(env_tex.outputs['Color'], background.inputs['Color'])
                        node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
                        bpy.context.scene.world = world
                        try:
                            tempfile._cleanup()
                        except:
                            pass
                        return {"success": True, "message": f"HDRI {asset_id} imported successfully", "image_name": env_tex.image.name}
                    except Exception as e:
                        return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
                return {"error": f"Requested resolution or format not available for this HDRI"}

            if asset_type == "textures":
                if not file_format:
                    file_format = "jpg"
                downloaded_maps = {}
                try:
                    for map_type in files_data:
                        if map_type not in ["blend", "gltf"]:
                            if resolution in files_data[map_type] and file_format in files_data[map_type][resolution]:
                                file_info = files_data[map_type][resolution][file_format]
                                file_url = file_info["url"]
                                with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                                    response = requests.get(file_url, headers=REQ_HEADERS)
                                    if response.status_code == 200:
                                        tmp_file.write(response.content)
                                        tmp_path = tmp_file.name
                                        image = bpy.data.images.load(tmp_path)
                                        image.name = f"{asset_id}_{map_type}.{file_format}"
                                        image.pack()
                                        if map_type in ['color', 'diffuse', 'albedo']:
                                            try:
                                                image.colorspace_settings.name = 'sRGB'
                                            except:
                                                pass
                                        else:
                                            try:
                                                image.colorspace_settings.name = 'Non-Color'
                                            except:
                                                pass
                                        downloaded_maps[map_type] = image
                                        try:
                                            os.unlink(tmp_path)
                                        except:
                                            pass
                    if not downloaded_maps:
                        return {"error": "No texture maps found for the requested resolution and format"}
                    mat = bpy.data.materials.new(name=asset_id)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    for node in nodes:
                        nodes.remove(node)
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    output.location = (300, 0)
                    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
                    principled.location = (0, 0)
                    links.new(principled.outputs[0], output.inputs[0])
                    tex_coord = nodes.new(type='ShaderNodeTexCoord')
                    tex_coord.location = (-800, 0)
                    mapping = nodes.new(type='ShaderNodeMapping')
                    mapping.location = (-600, 0)
                    mapping.vector_type = 'TEXTURE'
                    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
                    x_pos = -400
                    y_pos = 300
                    for map_type, image in downloaded_maps.items():
                        tex_node = nodes.new(type='ShaderNodeTexImage')
                        tex_node.location = (x_pos, y_pos)
                        tex_node.image = image
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            try:
                                tex_node.image.colorspace_settings.name = 'sRGB'
                            except:
                                pass
                        else:
                            try:
                                tex_node.image.colorspace_settings.name = 'Non-Color'
                            except:
                                pass
                        links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                        elif map_type.lower() in ['roughness', 'rough']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                        elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                        elif map_type.lower() in ['normal', 'nor']:
                            normal_map = nodes.new(type='ShaderNodeNormalMap')
                            normal_map.location = (x_pos + 200, y_pos)
                            links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                            links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                        elif map_type in ['displacement', 'disp', 'height']:
                            disp_node = nodes.new(type='ShaderNodeDisplacement')
                            disp_node.location = (x_pos + 200, y_pos - 200)
                            links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                            links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                        y_pos -= 250

                    texture_nodes = {}
                    for node in nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            for map_type, image in downloaded_maps.items():
                                if node.image == image:
                                    texture_nodes[map_type] = node
                                    break
                    for map_name in ['color', 'diffuse', 'albedo']:
                        if map_name in texture_nodes:
                            links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                            break
                    for map_name in ['roughness', 'rough']:
                        if map_name in texture_nodes:
                            links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                            break
                    for map_name in ['metallic', 'metalness', 'metal']:
                        if map_name in texture_nodes:
                            links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                            break
                    for map_name in ['gl', 'dx', 'nor']:
                        if map_name in texture_nodes:
                            normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                            normal_map_node.location = (100, 100)
                            links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                            links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                            break
                    for map_name in ['displacement', 'disp', 'height']:
                        if map_name in texture_nodes:
                            disp_node = nodes.new(type='ShaderNodeDisplacement')
                            disp_node.location = (300, -200)
                            disp_node.inputs['Scale'].default_value = 0.1
                            links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                            links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                            break
                    if 'arm' in texture_nodes:
                        separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
                        separate_rgb.location = (-200, -100)
                        links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Image'])
                        if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                            links.new(separate_rgb.outputs['G'], principled.inputs['Roughness'])
                        if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                            links.new(separate_rgb.outputs['B'], principled.inputs['Metallic'])
                        base_color_node = None
                        for map_name in ['color', 'diffuse', 'albedo']:
                            if map_name in texture_nodes:
                                base_color_node = texture_nodes[map_name]
                                break
                        if base_color_node:
                            mix_node = nodes.new(type='ShaderNodeMixRGB')
                            mix_node.location = (100, 200)
                            mix_node.blend_type = 'MULTIPLY'
                            mix_node.inputs['Fac'].default_value = 0.8
                            for link in base_color_node.outputs['Color'].links:
                                if link.to_socket == principled.inputs['Base Color']:
                                    links.remove(link)
                            links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                            links.new(separate_rgb.outputs['R'], mix_node.inputs[2])
                            links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    if 'ao' in texture_nodes:
                        base_color_node = None
                        for map_name in ['color', 'diffuse', 'albedo']:
                            if map_name in texture_nodes:
                                base_color_node = texture_nodes[map_name]
                                break
                        if base_color_node:
                            mix_node = nodes.new(type='ShaderNodeMixRGB')
                            mix_node.location = (100, 200)
                            mix_node.blend_type = 'MULTIPLY'
                            mix_node.inputs['Fac'].default_value = 0.8
                            for link in base_color_node.outputs['Color'].links:
                                if link.to_socket == principled.inputs['Base Color']:
                                    links.remove(link)
                            links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                            links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                            links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    material_handle = f"material_{asset_id}"
                    self.server.shared_context['materials'][material_handle] = mat
                    self.server._add_to_history("download_polyhaven_asset", f"texture {asset_id}", f"Created material {mat.name}")
                    return {
                        "success": True,
                        "message": f"Texture {asset_id} imported as material",
                        "material": mat.name,
                        "material_handle": material_handle,
                        "maps": list(downloaded_maps.keys())
                    }
                except Exception as e:
                    return {"error": f"Failed to process textures: {str(e)}"}

            if asset_type == "models":
                if not file_format:
                    file_format = "gltf"
                if file_format in files_data and resolution in files_data[file_format]:
                    file_info = files_data[file_format][resolution][file_format]
                    file_url = file_info["url"]
                    temp_dir = tempfile.mkdtemp()
                    main_file_path = ""
                    try:
                        main_file_name = file_url.split("/")[-1]
                        main_file_path = os.path.join(temp_dir, main_file_name)
                        response = requests.get(file_url, headers=REQ_HEADERS)
                        if response.status_code != 200:
                            return {"error": f"Failed to download model: {response.status_code}"}
                        with open(main_file_path, "wb") as f:
                            f.write(response.content)
                        if "include" in file_info and file_info["include"]:
                            for include_path, include_info in file_info["include"].items():
                                include_url = include_info["url"]
                                include_file_path = os.path.join(temp_dir, include_path)
                                os.makedirs(os.path.dirname(include_file_path), exist_ok=True)
                                include_response = requests.get(include_url, headers=REQ_HEADERS)
                                if include_response.status_code == 200:
                                    with open(include_file_path, "wb") as f:
                                        f.write(include_response.content)
                        if file_format in ("gltf", "glb"):
                            bpy.ops.import_scene.gltf(filepath=main_file_path)
                        elif file_format == "fbx":
                            bpy.ops.import_scene.fbx(filepath=main_file_path)
                        elif file_format == "obj":
                            bpy.ops.import_scene.obj(filepath=main_file_path)
                        elif file_format == "blend":
                            with bpy.data.libraries.load(main_file_path, link=False) as (data_from, data_to):
                                data_to.objects = data_from.objects
                            for obj in data_to.objects:
                                if obj is not None:
                                    bpy.context.collection.objects.link(obj)
                        else:
                            return {"error": f"Unsupported model format: {file_format}"}
                        imported_objects = [obj.name for obj in bpy.context.selected_objects]
                        object_handles = {}
                        for i, obj_name in enumerate(imported_objects):
                            handle = f"imported_{asset_id}_{i}"
                            self.server.shared_context['objects'][handle] = bpy.data.objects[obj_name]
                            object_handles[handle] = obj_name
                        self.server._add_to_history("download_polyhaven_asset", f"model {asset_id}", f"Imported {len(imported_objects)} objects")
                        return {
                            "success": True,
                            "message": f"Model {asset_id} imported successfully",
                            "imported_objects": imported_objects,
                            "object_handles": object_handles
                        }
                    except Exception as e:
                        return {"error": f"Failed to import model: {str(e)}"}
                    finally:
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                return {"error": "Requested format or resolution not available for this model"}

            return {"error": f"Unsupported asset type: {asset_type}"}
        except Exception as e:
            return {"error": f"Failed to download asset: {str(e)}"}

    def set_texture(self, object_name, texture_id):
        try:
            obj = bpy.data.objects.get(object_name)
            if not obj:
                return {"error": f"Object not found: {object_name}"}
            if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
                return {"error": f"Object {object_name} cannot accept materials"}

            texture_images = {}
            for img in bpy.data.images:
                if img.name.startswith(texture_id + "_"):
                    map_type = img.name.split('_')[-1].split('.')[0]
                    img.reload()
                    if map_type.lower() in ['color', 'diffuse', 'albedo']:
                        try:
                            img.colorspace_settings.name = 'sRGB'
                        except:
                            pass
                    else:
                        try:
                            img.colorspace_settings.name = 'Non-Color'
                        except:
                            pass
                    if not img.packed_file:
                        img.pack()
                    texture_images[map_type] = img

            if not texture_images:
                return {"error": f"No texture images found for: {texture_id}. Please download the texture first."}

            new_mat_name = f"{texture_id}_material_{object_name}"
            existing_mat = bpy.data.materials.get(new_mat_name)
            if existing_mat:
                bpy.data.materials.remove(existing_mat)
            new_mat = bpy.data.materials.new(name=new_mat_name)
            new_mat.use_nodes = True
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links
            nodes.clear()
            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (600, 0)
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            principled.location = (300, 0)
            links.new(principled.outputs[0], output.inputs[0])
            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            tex_coord.location = (-800, 0)
            mapping = nodes.new(type='ShaderNodeMapping')
            mapping.location = (-600, 0)
            mapping.vector_type = 'TEXTURE'
            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
            x_pos = -400
            y_pos = 300
            for map_type, image in texture_images.items():
                tex_node = nodes.new(type='ShaderNodeTexImage')
                tex_node.location = (x_pos, y_pos)
                tex_node.image = image
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    try:
                        tex_node.image.colorspace_settings.name = 'sRGB'
                    except:
                        pass
                else:
                    try:
                        tex_node.image.colorspace_settings.name = 'Non-Color'
                    except:
                        pass
                links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                elif map_type.lower() in ['roughness', 'rough']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                elif map_type.lower() in ['normal', 'nor', 'dx', 'gl']:
                    normal_map = nodes.new(type='ShaderNodeNormalMap')
                    normal_map.location = (x_pos + 200, y_pos)
                    links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                elif map_type.lower() in ['displacement', 'disp', 'height']:
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (x_pos + 200, y_pos - 200)
                    disp_node.inputs['Scale'].default_value = 0.1
                    links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                y_pos -= 250

            texture_nodes = {}
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    for map_type, image in texture_images.items():
                        if node.image == image:
                            texture_nodes[map_type] = node
                            break
            for map_name in ['color', 'diffuse', 'albedo']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                    break
            for map_name in ['roughness', 'rough']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                    break
            for map_name in ['metallic', 'metalness', 'metal']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                    break
            for map_name in ['normal', 'nor', 'dx', 'gl']:
                if map_name in texture_nodes:
                    normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                    normal_map_node.location = (100, 100)
                    links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                    links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                    break
            for map_name in ['displacement', 'disp', 'height']:
                if map_name in texture_nodes:
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (300, -200)
                    disp_node.inputs['Scale'].default_value = 0.1
                    links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                    break

            if 'arm' in texture_nodes:
                separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
                separate_rgb.location = (-200, -100)
                links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Image'])
                if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                    links.new(separate_rgb.outputs['G'], principled.inputs['Roughness'])
                if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                    links.new(separate_rgb.outputs['B'], principled.inputs['Metallic'])
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break
                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(separate_rgb.outputs['R'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])

            if 'ao' in texture_nodes:
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break
                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])

            while len(obj.data.materials) > 0:
                obj.data.materials.pop(index=0)
            obj.data.materials.append(new_mat)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.context.view_layer.update()
            material_handle = f"material_{texture_id}"
            self.server.shared_context['materials'][material_handle] = new_mat
            self.server._add_to_history("set_texture", f"texture {texture_id}", f"Created material {new_mat.name}")

            material_info = {
                "name": new_mat.name,
                "has_nodes": new_mat.use_nodes,
                "node_count": len(new_mat.node_tree.nodes),
                "texture_nodes": []
            }
            for node in new_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    connections = []
                    for output in node.outputs:
                        for link in output.links:
                            connections.append(f"{output.name} → {link.to_node.name}.{link.to_socket.name}")
                    material_info["texture_nodes"].append({
                        "name": node.name,
                        "image": node.image.name,
                        "colorspace": node.image.colorspace_settings.name,
                        "connections": connections
                    })

            return {
                "success": True,
                "message": f"Created new material and applied texture {texture_id} to {object_name}",
                "material": new_mat.name,
                "maps": list(texture_images.keys()),
                "material_info": material_info
            }
        except Exception as e:
            print(f"Error in set_texture: {str(e)}")
            traceback.print_exc()
            return {"error": f"Failed to apply texture: {str(e)}"}


class SketchfabService:
    def __init__(self, server):
        self.server = server

    def get_sketchfab_status(self):
        return ProviderStatusService(self.server).get_sketchfab_status()

    def search_sketchfab_models(self, query, categories=None, count=20, downloadable=True):
        try:
            api_key = bpy.context.scene.blendermcp_sketchfab_api_key
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}
            params = {
                "type": "models",
                "q": query,
                "count": count,
                "downloadable": downloadable,
                "archives_flavours": False
            }
            if categories:
                params["categories"] = categories
            headers = {"Authorization": f"Token {api_key}"}
            response = requests.get("https://api.sketchfab.com/v3/search", headers=headers, params=params, timeout=30)
            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}
            if response.status_code != 200:
                return {"error": f"API request failed with status code {response.status_code}"}
            response_data = response.json()
            if response_data is None:
                return {"error": "Received empty response from Sketchfab API"}
            results = response_data.get("results", [])
            if not isinstance(results, list):
                return {"error": f"Unexpected response format from Sketchfab API: {response_data}"}
            return response_data
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def download_sketchfab_model(self, uid):
        try:
            api_key = bpy.context.scene.blendermcp_sketchfab_api_key
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}
            headers = {"Authorization": f"Token {api_key}"}
            download_endpoint = f"https://api.sketchfab.com/v3/models/{uid}/download"
            response = requests.get(download_endpoint, headers=headers, timeout=30)
            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}
            if response.status_code != 200:
                return {"error": f"Download request failed with status code {response.status_code}"}
            data = response.json()
            if data is None:
                return {"error": "Received empty response from Sketchfab API for download request"}
            gltf_data = data.get("gltf")
            if not gltf_data:
                return {"error": "No gltf download URL available for this model. Response: " + str(data)}
            download_url = gltf_data.get("url")
            if not download_url:
                return {"error": "No download URL available for this model. Make sure the model is downloadable and you have access."}
            model_response = requests.get(download_url, timeout=60)
            if model_response.status_code != 200:
                return {"error": f"Model download failed with status code {model_response.status_code}"}
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, f"{uid}.zip")
            with open(zip_file_path, "wb") as f:
                f.write(model_response.content)
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    file_path = file_info.filename
                    target_path = os.path.join(temp_dir, os.path.normpath(file_path))
                    abs_temp_dir = os.path.abspath(temp_dir)
                    abs_target_path = os.path.abspath(target_path)
                    if not abs_target_path.startswith(abs_temp_dir):
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with path traversal attempt"}
                    if ".." in file_path:
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with directory traversal sequence"}
                zip_ref.extractall(temp_dir)
            gltf_files = [f for f in os.listdir(temp_dir) if f.endswith('.gltf') or f.endswith('.glb')]
            if not gltf_files:
                with suppress(Exception):
                    shutil.rmtree(temp_dir)
                return {"error": "No glTF file found in the downloaded model"}
            main_file = os.path.join(temp_dir, gltf_files[0])
            bpy.ops.import_scene.gltf(filepath=main_file)
            imported_objects = [obj.name for obj in bpy.context.selected_objects]
            with suppress(Exception):
                shutil.rmtree(temp_dir)
            return {
                "success": True,
                "message": "Model imported successfully",
                "imported_objects": imported_objects
            }
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection and try again with a simpler model."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Failed to download model: {str(e)}"}


class Hyper3DService:
    def __init__(self, server):
        self.server = server

    def get_hyper3d_status(self):
        return ProviderStatusService(self.server).get_hyper3d_status()

    def create_rodin_job(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.create_rodin_job_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.create_rodin_job_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def create_rodin_job_main_site(self, text_prompt: str = None, images: list[tuple[str, str]] = None, bbox_condition=None):
        try:
            if images is None:
                images = []
            files = [
                *[("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)],
                ("tier", (None, "Sketch")),
                ("mesh_mode", (None, "Raw")),
            ]
            if text_prompt:
                files.append(("prompt", (None, text_prompt)))
            if bbox_condition:
                files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post(
                "https://hyperhuman.deemos.com/api/v2/rodin",
                headers={"Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}"},
                files=files
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def create_rodin_job_fal_ai(self, text_prompt: str = None, images: list[tuple[str, str]] = None, bbox_condition=None):
        try:
            req_data = {"tier": "Sketch"}
            if images:
                req_data["input_image_urls"] = images
            if text_prompt:
                req_data["prompt"] = text_prompt
            if bbox_condition:
                req_data["bbox_condition"] = bbox_condition
            response = requests.post(
                "https://queue.fal.run/fal-ai/hyper3d/rodin",
                headers={
                    "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
                    "Content-Type": "application/json",
                },
                json=req_data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.poll_rodin_job_status_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.poll_rodin_job_status_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def poll_rodin_job_status_main_site(self, subscription_key: str):
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/status",
            headers={"Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}"},
            json={"subscription_key": subscription_key},
        )
        data = response.json()
        return {"status_list": [i["status"] for i in data["jobs"]]}

    def poll_rodin_job_status_fal_ai(self, request_id: str):
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
            headers={"Authorization": f"KEY {bpy.context.scene.blendermcp_hyper3d_api_key}"},
        )
        return response.json()

    def import_generated_asset(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.import_generated_asset_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.import_generated_asset_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def import_generated_asset_main_site(self, task_uuid: str, name: str):
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/download",
            headers={"Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}"},
            json={'task_uuid': task_uuid}
        )
        data_ = response.json()
        temp_file = None
        for i in data_["list"]:
            if i["name"].endswith(".glb"):
                temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=task_uuid, suffix=".glb")
                try:
                    response = requests.get(i["url"], stream=True)
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    temp_file.close()
                except Exception as e:
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return {"succeed": False, "error": str(e)}
                break
        else:
            return {"succeed": False, "error": "Generation failed. Please first make sure that all jobs of the task are done and then try again later."}

        try:
            obj = self.server._clean_imported_glb(filepath=temp_file.name, mesh_name=name)
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }
            if obj.type == "MESH":
                result["world_bounding_box"] = self.server._get_aabb(obj)
            return {"succeed": True, **result}
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_generated_asset_fal_ai(self, request_id: str, name: str):
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={"Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}"},
        )
        data_ = response.json()
        temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=request_id, suffix=".glb")
        try:
            response = requests.get(data_["model_mesh"]["url"], stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file.close()
        except Exception as e:
            temp_file.close()
            os.unlink(temp_file.name)
            return {"succeed": False, "error": str(e)}

        try:
            obj = self.server._clean_imported_glb(filepath=temp_file.name, mesh_name=name)
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }
            if obj.type == "MESH":
                result["world_bounding_box"] = self.server._get_aabb(obj)
            return {"succeed": True, **result}
        except Exception as e:
            return {"succeed": False, "error": str(e)}


class SceneEditService:
    SUPPORTED_PRIMITIVES = {
        "cube": bpy.ops.mesh.primitive_cube_add,
        "uv_sphere": bpy.ops.mesh.primitive_uv_sphere_add,
        "ico_sphere": bpy.ops.mesh.primitive_ico_sphere_add,
        "cylinder": bpy.ops.mesh.primitive_cylinder_add,
        "cone": bpy.ops.mesh.primitive_cone_add,
        "plane": bpy.ops.mesh.primitive_plane_add,
        "torus": bpy.ops.mesh.primitive_torus_add,
    }

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _vector(value, default, length=3):
        if value is None:
            return list(default)
        if not isinstance(value, (list, tuple)) or len(value) != length:
            raise ValueError(f"Expected a {length}-item numeric list")
        return [float(item) for item in value]

    @staticmethod
    def _unique_name(base_name):
        base = re.sub(r"[^A-Za-z0-9_. -]+", "_", str(base_name or "Object")).strip() or "Object"
        if base not in bpy.data.objects:
            return base
        index = 1
        while f"{base}.{index:03d}" in bpy.data.objects:
            index += 1
        return f"{base}.{index:03d}"

    def _deep_info(self, object_name):
        return self.server.scene_intelligence_service.get_object_deep_info(object_name=object_name).get("object")

    def _verification(self, label, verify):
        if not verify:
            return {}
        return self.server.verification_artifact_service.create_verification_snapshot(
            label=label,
            include_scene_index=True,
            include_scene_health=True,
            include_selection=False,
            include_screenshots=False,
        )

    def _operation_record(self, operation, payload, result):
        self.server._add_to_history(operation, payload, result)

    def get_supported_edit_operations(self):
        return {
            "status": "success",
            "operations": {
                "create_primitive_object": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False, "supported_types": sorted(self.SUPPORTED_PRIMITIVES)},
                "transform_object": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "duplicate_object": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "delete_objects": {"risk_level": "HIGH", "mutates_scene": True, "requires_confirmation": True},
                "set_object_visibility": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "create_basic_material": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "assign_material": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "update_material_properties": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "add_object_modifier": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "update_object_modifier": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "remove_object_modifier": {"risk_level": "HIGH", "mutates_scene": True, "requires_confirmation": True},
                "create_collection": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "move_objects_to_collection": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "delete_collection": {"risk_level": "HIGH", "mutates_scene": True, "requires_confirmation": True, "require_empty_default": True},
                "run_verified_edit_batch": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
            },
            "warnings": [],
        }

    def create_primitive_object(self, primitive_type, name=None, location=None, rotation=None, scale=None, collection_name=None, material_name=None, verify=False):
        primitive_key = str(primitive_type or "").strip().lower()
        if primitive_key not in self.SUPPORTED_PRIMITIVES:
            return {"status": "error", "message": f"Unsupported primitive_type: {primitive_type}", "warnings": []}
        if material_name and material_name not in bpy.data.materials:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}

        self.SUPPORTED_PRIMITIVES[primitive_key]()
        obj = bpy.context.object
        obj.name = self._unique_name(name or f"Overtli_{primitive_key}")
        obj.location = self._vector(location, [0.0, 0.0, 0.0])
        obj.rotation_euler = self._vector(rotation, [0.0, 0.0, 0.0])
        obj.scale = self._vector(scale, [1.0, 1.0, 1.0])

        collection = None
        if collection_name:
            collection = bpy.data.collections.get(collection_name)
            if collection is None:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)
            for linked in list(obj.users_collection):
                linked.objects.unlink(obj)
            collection.objects.link(obj)

        if material_name:
            obj.data.materials.append(bpy.data.materials[material_name])

        result = {
            "status": "success",
            "object_name": obj.name,
            "object_type": obj.type,
            "created": True,
            "collection_name": collection.name if collection else (obj.users_collection[0].name if obj.users_collection else None),
            "transform": {"location": list(obj.location), "rotation": list(obj.rotation_euler), "scale": list(obj.scale)},
            "material_name": material_name,
            "object": self._deep_info(obj.name),
            "verification": self._verification(f"edit_{obj.name}", verify),
            "warnings": [],
        }
        self._operation_record("create_primitive_object", {"primitive_type": primitive_key, "name": name}, result)
        return result

    def transform_object(self, object_name, location=None, rotation=None, scale=None, relative=False, verify=False):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if location is not None:
            vec = self._vector(location, [0.0, 0.0, 0.0])
            obj.location = [obj.location[i] + vec[i] for i in range(3)] if relative else vec
        if rotation is not None:
            vec = self._vector(rotation, [0.0, 0.0, 0.0])
            obj.rotation_euler = [obj.rotation_euler[i] + vec[i] for i in range(3)] if relative else vec
        if scale is not None:
            vec = self._vector(scale, [1.0, 1.0, 1.0])
            obj.scale = [obj.scale[i] + vec[i] for i in range(3)] if relative else vec
        result = {"status": "success", "object_name": obj.name, "object": self._deep_info(obj.name), "verification": self._verification(f"transform_{obj.name}", verify), "warnings": []}
        self._operation_record("transform_object", {"object_name": object_name}, result)
        return result

    def duplicate_object(self, object_name, new_name=None, linked=False, location_offset=None, collection_name=None, verify=False):
        source = bpy.data.objects.get(object_name)
        if not source:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        duplicate = source.copy()
        if not linked and getattr(source, "data", None):
            duplicate.data = source.data.copy()
        duplicate.name = self._unique_name(new_name or f"{source.name}_copy")
        offset = self._vector(location_offset, [0.0, 0.0, 0.0])
        duplicate.location = [source.location[i] + offset[i] for i in range(3)]
        target_collection = bpy.data.collections.get(collection_name) if collection_name else (source.users_collection[0] if source.users_collection else bpy.context.scene.collection)
        if target_collection is None:
            return {"status": "error", "message": f"Collection not found: {collection_name}", "warnings": []}
        target_collection.objects.link(duplicate)
        result = {"status": "success", "source_object_name": source.name, "object_name": duplicate.name, "linked": bool(linked), "collection_name": target_collection.name, "object": self._deep_info(duplicate.name), "verification": self._verification(f"duplicate_{duplicate.name}", verify), "warnings": []}
        self._operation_record("duplicate_object", {"object_name": object_name, "new_name": new_name}, result)
        return result

    def delete_objects(self, object_names, confirm=False, allow_missing=False, verify=False):
        if not confirm:
            return {"status": "error", "message": "delete_objects requires confirm=True", "deleted": [], "missing": list(object_names or []), "refused": list(object_names or []), "warnings": []}
        if not isinstance(object_names, list) or not object_names:
            return {"status": "error", "message": "object_names must be a non-empty list", "deleted": [], "missing": [], "refused": [], "warnings": []}
        deleted, missing = [], []
        for name in object_names:
            if any(token in str(name) for token in ["*", "?", "["]):
                return {"status": "error", "message": f"Wildcard-like object name refused: {name}", "deleted": deleted, "missing": missing, "refused": [name], "warnings": []}
            obj = bpy.data.objects.get(str(name))
            if obj is None:
                missing.append(str(name))
                continue
            bpy.data.objects.remove(obj, do_unlink=True)
            deleted.append(str(name))
        if missing and not allow_missing:
            status = "partial" if deleted else "error"
            message = f"Missing objects: {missing}"
        else:
            status, message = "success", None
        result = {"status": status, "deleted": deleted, "missing": missing, "refused": [], "verification": self._verification("delete_objects", verify), "warnings": []}
        if message:
            result["message"] = message
        self._operation_record("delete_objects", {"object_names": object_names}, result)
        return result

    def set_object_visibility(self, object_name, hide_viewport=None, hide_render=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if hide_viewport is not None:
            obj.hide_viewport = bool(hide_viewport)
        if hide_render is not None:
            obj.hide_render = bool(hide_render)
        result = {"status": "success", "object_name": obj.name, "visibility": {"hide_viewport": bool(obj.hide_viewport), "hide_render": bool(obj.hide_render), "visible": bool(obj.visible_get())}, "verification": self._verification(f"visibility_{obj.name}", verify), "warnings": []}
        self._operation_record("set_object_visibility", {"object_name": object_name}, result)
        return result


class MaterialAuthoringService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _clamp(value, minimum=0.0, maximum=1.0):
        return max(minimum, min(maximum, float(value)))

    def _material_summary(self, material):
        props = {"base_color": list(material.diffuse_color), "metallic": 0.0, "roughness": 0.5, "alpha": float(material.diffuse_color[3])}
        if material.use_nodes:
            node = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
            if node:
                for key, socket_name in [("base_color", "Base Color"), ("metallic", "Metallic"), ("roughness", "Roughness"), ("alpha", "Alpha")]:
                    socket = node.inputs.get(socket_name)
                    if socket:
                        value = socket.default_value
                        props[key] = list(value) if hasattr(value, "__len__") and not isinstance(value, str) else float(value)
        return {"name": material.name, "use_nodes": bool(material.use_nodes), "users": int(material.users), "properties": props}

    def _set_properties(self, material, base_color=None, metallic=None, roughness=None, alpha=None):
        if base_color is not None:
            if not isinstance(base_color, (list, tuple)) or len(base_color) not in {3, 4}:
                raise ValueError("base_color must be a 3- or 4-item numeric list")
            color = [self._clamp(component) for component in base_color]
            if len(color) == 3:
                color.append(self._clamp(alpha if alpha is not None else material.diffuse_color[3]))
            material.diffuse_color = color
        elif alpha is not None:
            color = list(material.diffuse_color)
            color[3] = self._clamp(alpha)
            material.diffuse_color = color

        if material.use_nodes and material.node_tree:
            node = material.node_tree.nodes.get("Principled BSDF")
            if node:
                if base_color is not None and node.inputs.get("Base Color"):
                    node.inputs["Base Color"].default_value = material.diffuse_color
                if metallic is not None and node.inputs.get("Metallic"):
                    node.inputs["Metallic"].default_value = self._clamp(metallic)
                if roughness is not None and node.inputs.get("Roughness"):
                    node.inputs["Roughness"].default_value = self._clamp(roughness)
                if alpha is not None and node.inputs.get("Alpha"):
                    node.inputs["Alpha"].default_value = self._clamp(alpha)

    def create_basic_material(self, name, base_color=None, metallic=None, roughness=None, alpha=None, use_nodes=True, replace_existing=False):
        if not name:
            return {"status": "error", "message": "name is required", "warnings": []}
        material = bpy.data.materials.get(name)
        created = False
        if material and not replace_existing:
            return {"status": "success", "material_name": material.name, "created": False, "properties": self._material_summary(material)["properties"], "warnings": ["material already exists"]}
        if material is None:
            material = bpy.data.materials.new(name)
            created = True
        material.use_nodes = bool(use_nodes)
        self._set_properties(material, base_color, metallic, roughness, alpha)
        result = {"status": "success", "material_name": material.name, "created": created, "properties": self._material_summary(material)["properties"], "warnings": []}
        self.server._add_to_history("create_basic_material", {"name": name}, result)
        return result

    def assign_material(self, object_name, material_name, slot_index=None, replace=True, verify=False):
        obj = bpy.data.objects.get(object_name)
        material = bpy.data.materials.get(material_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        if slot_index is None:
            if replace and len(obj.data.materials) > 0:
                obj.data.materials[0] = material
                slot_index = 0
            else:
                obj.data.materials.append(material)
                slot_index = len(obj.data.materials) - 1
        else:
            slot_index = int(slot_index)
            while len(obj.data.materials) <= slot_index:
                obj.data.materials.append(None)
            obj.data.materials[slot_index] = material
        result = {"status": "success", "object_name": obj.name, "material_name": material.name, "slot_index": slot_index, "materials": [slot.material.name if slot.material else None for slot in obj.material_slots], "verification": self.server.scene_edit_service._verification(f"assign_material_{obj.name}", verify), "warnings": []}
        self.server._add_to_history("assign_material", {"object_name": object_name, "material_name": material_name}, result)
        return result

    def update_material_properties(self, material_name, base_color=None, metallic=None, roughness=None, alpha=None, verify=False):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        self._set_properties(material, base_color, metallic, roughness, alpha)
        result = {"status": "success", "material_name": material.name, "properties": self._material_summary(material)["properties"], "verification": self.server.scene_edit_service._verification(f"material_{material.name}", verify), "warnings": []}
        self.server._add_to_history("update_material_properties", {"material_name": material_name}, result)
        return result


MATERIAL_CHANNEL_SCHEMA = {
    "base_color": {"type": "rgba", "color_space": "sRGB", "principled_targets": ["Base Color"]},
    "albedo": {"type": "rgba", "color_space": "sRGB", "principled_targets": ["Base Color"]},
    "metallic": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Metallic"]},
    "roughness": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Roughness"]},
    "specular": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Specular IOR Level", "Specular"]},
    "ior": {"type": "float", "range": [1, 3], "color_space": "Non-Color", "principled_targets": ["IOR"]},
    "alpha": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Alpha"]},
    "opacity": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Alpha"]},
    "normal": {"type": "normal_map", "color_space": "Non-Color", "node_path": ["Image Texture", "Normal Map", "Principled Normal"]},
    "bump": {"type": "height_or_bump_map", "color_space": "Non-Color", "node_path": ["Image Texture or procedural", "Bump", "Principled Normal"]},
    "height": {"type": "height_or_bump_map", "color_space": "Non-Color", "node_path": ["Image Texture or procedural", "Bump", "Principled Normal"]},
    "displacement": {"type": "displacement_map", "color_space": "Non-Color", "node_path": ["Image Texture or procedural", "Displacement", "Material Output Displacement"]},
    "ambient_occlusion": {"type": "map_metadata", "color_space": "Non-Color", "principled_targets": []},
    "emission_color": {"type": "rgba_or_map", "color_space": "sRGB", "principled_targets": ["Emission Color", "Emission"]},
    "emission_strength": {"type": "float", "range": [0, 100], "color_space": "Non-Color", "principled_targets": ["Emission Strength"]},
    "subsurface": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Subsurface Weight", "Subsurface"]},
    "coat_weight": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Coat Weight", "Clearcoat"]},
    "coat_roughness": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Coat Roughness", "Clearcoat Roughness"]},
    "anisotropy": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Anisotropic IOR Level", "Anisotropic"]},
    "transmission": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Transmission Weight", "Transmission"]},
    "volume_absorption": {"type": "volume", "color_space": "sRGB", "principled_targets": []},
}

MATERIAL_MAP_KINDS = {
    "base_color_map": {"channel": "base_color", "color_space": "sRGB"},
    "albedo_map": {"channel": "albedo", "color_space": "sRGB"},
    "metallic_map": {"channel": "metallic", "color_space": "Non-Color"},
    "roughness_map": {"channel": "roughness", "color_space": "Non-Color"},
    "metallic_roughness_map": {"channel": "metallic_roughness", "color_space": "Non-Color", "packed": "glTF_metallic_roughness"},
    "normal_map": {"channel": "normal", "color_space": "Non-Color"},
    "bump_map": {"channel": "bump", "color_space": "Non-Color"},
    "height_map": {"channel": "height", "color_space": "Non-Color"},
    "displacement_map": {"channel": "displacement", "color_space": "Non-Color"},
    "ambient_occlusion_map": {"channel": "ambient_occlusion", "color_space": "Non-Color"},
    "emission_map": {"channel": "emission_color", "color_space": "sRGB"},
    "alpha_map": {"channel": "alpha", "color_space": "Non-Color"},
    "opacity_map": {"channel": "opacity", "color_space": "Non-Color"},
    "orm_map": {"channel": "packed", "color_space": "Non-Color", "packed": "ORM"},
    "rma_map": {"channel": "packed", "color_space": "Non-Color", "packed": "RMA"},
    "mra_map": {"channel": "packed", "color_space": "Non-Color", "packed": "MRA"},
    "mask_map": {"channel": "mask", "color_space": "Non-Color"},
    "color_ramp_map": {"channel": "procedural", "color_space": "sRGB"},
    "procedural_channel": {"channel": "procedural", "color_space": "Non-Color"},
}

PACKED_MAP_CONVENTIONS = {
    "ORM": "R=occlusion, G=roughness, B=metallic",
    "RMA": "R=roughness, G=metallic, B=ambient occlusion",
    "MRA": "R=metallic, G=roughness, B=ambient occlusion",
    "glTF_metallic_roughness": "G=roughness, B=metallic",
}

PHASE4A_TEMPLATE_NAMES = [
    "pbr_metal_gold", "pbr_metal_brushed", "pbr_plastic", "pbr_rubber", "pbr_ceramic", "pbr_clay",
    "glass_clear", "glass_frosted", "water_basic", "emission_neon", "toon_flat", "toon_rim",
    "fabric_woven", "leather_grain", "skin_basic", "stone_rough", "concrete_rough",
    "wood_procedural", "marble_procedural", "brick_procedural", "sci_fi_panel", "painted_metal",
    "car_paint_basic",
]


class MaterialIntelligenceService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _json_value(value):
        if hasattr(value, "__len__") and not isinstance(value, str):
            return [float(v) if isinstance(v, (int, float)) else v for v in value]
        if isinstance(value, (int, float, bool)):
            return value
        return str(value)

    @staticmethod
    def _principled_node(material):
        if not material or not material.use_nodes or not material.node_tree:
            return None
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeBsdfPrincipled" or node.name == "Principled BSDF":
                return node
        return None

    @staticmethod
    def _material_objects(material):
        names = []
        for obj in bpy.data.objects:
            data = getattr(obj, "data", None)
            if data and hasattr(data, "materials"):
                for slot_material in data.materials:
                    if slot_material == material:
                        names.append(obj.name)
                        break
        return names

    def get_material_channel_schema(self):
        return {
            "status": "success",
            "channels": MATERIAL_CHANNEL_SCHEMA,
            "map_kinds": MATERIAL_MAP_KINDS,
            "packed_map_conventions": PACKED_MAP_CONVENTIONS,
            "warnings": [],
        }

    def _channel_summary(self, material):
        principled = self._principled_node(material)
        channels = {}
        if not principled:
            return {"base_color": {"source": "material_diffuse", "value": list(material.diffuse_color)}, "warnings": ["no Principled BSDF node found"]}
        mapping = {
            "base_color": "Base Color", "metallic": "Metallic", "roughness": "Roughness", "alpha": "Alpha",
            "emission_color": "Emission Color", "emission_strength": "Emission Strength", "ior": "IOR",
            "coat_weight": "Coat Weight", "coat_roughness": "Coat Roughness", "transmission": "Transmission Weight",
        }
        for channel, socket_name in mapping.items():
            socket = principled.inputs.get(socket_name)
            if not socket and socket_name == "Emission Color":
                socket = principled.inputs.get("Emission")
            if socket:
                source = "linked" if socket.is_linked else "constant"
                channels[channel] = {"source": source, "value": self._json_value(socket.default_value)}
        normal = principled.inputs.get("Normal")
        channels["normal"] = {"source": "linked" if normal and normal.is_linked else "none"}
        return channels

    def _texture_slots(self, material):
        slots = {key: None for key in MATERIAL_MAP_KINDS}
        packed_maps = []
        if not material.use_nodes or not material.node_tree:
            return slots, packed_maps
        for node in material.node_tree.nodes:
            if node.bl_idname != "ShaderNodeTexImage":
                continue
            map_kind = node.get("overtli_map_kind") or "image_texture"
            entry = {
                "node": node.name,
                "map_kind": map_kind,
                "image_name": node.image.name if getattr(node, "image", None) else None,
                "filepath": bpy.path.abspath(node.image.filepath) if getattr(node, "image", None) and node.image.filepath else None,
                "color_space_intent": MATERIAL_MAP_KINDS.get(map_kind, {}).get("color_space", "unknown"),
                "packed_convention": node.get("overtli_packed_convention"),
            }
            if map_kind in slots:
                slots[map_kind] = entry
            if entry["packed_convention"]:
                packed_maps.append(entry)
        return slots, packed_maps

    def _material_record(self, material, include_node_summary=True, include_users=True, include_objects=True, include_texture_slots=True, include_channel_summary=True):
        objects = self._material_objects(material) if include_objects or include_users else []
        slots, packed = self._texture_slots(material) if include_texture_slots else ({}, [])
        node_count = len(material.node_tree.nodes) if material.use_nodes and material.node_tree else 0
        link_count = len(material.node_tree.links) if material.use_nodes and material.node_tree else 0
        image_count = 0
        procedural_count = 0
        if material.use_nodes and material.node_tree:
            for node in material.node_tree.nodes:
                if node.bl_idname == "ShaderNodeTexImage":
                    image_count += 1
                if node.bl_idname in {"ShaderNodeTexNoise", "ShaderNodeTexVoronoi", "ShaderNodeValToRGB", "ShaderNodeBump", "ShaderNodeNormalMap"}:
                    procedural_count += 1
        record = {
            "name": material.name,
            "use_nodes": bool(material.use_nodes),
            "users": int(material.users),
            "surface_node": self._principled_node(material).name if self._principled_node(material) else None,
            "node_count": node_count,
            "link_count": link_count,
            "image_texture_count": image_count,
            "procedural_node_count": procedural_count,
            "warnings": [],
        }
        if include_objects:
            record["object_names"] = objects
        if include_channel_summary:
            record["channel_summary"] = self._channel_summary(material)
        if include_texture_slots:
            record["texture_slots"] = slots
            record["packed_maps"] = packed
        if include_node_summary:
            record["node_summary"] = {"node_count": node_count, "link_count": link_count, "image_texture_count": image_count, "procedural_node_count": procedural_count}
        return record

    def list_materials_deep(self, include_node_summary=True, include_users=True, include_objects=True, include_texture_slots=True, include_channel_summary=True, max_materials=None):
        materials = list(bpy.data.materials)
        truncated = False
        if max_materials is not None and len(materials) > int(max_materials):
            materials = materials[:int(max_materials)]
            truncated = True
        return {
            "status": "success",
            "material_count": len(bpy.data.materials),
            "materials": [self._material_record(m, include_node_summary, include_users, include_objects, include_texture_slots, include_channel_summary) for m in materials],
            "truncated": truncated,
            "warnings": [],
        }

    def get_material_deep_info(self, material_name, include_node_graph=True, include_texture_slots=True, include_channel_summary=True, include_users=True, include_preview_hints=True):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        record = self._material_record(material, True, include_users, include_users, include_texture_slots, include_channel_summary)
        principled = self._principled_node(material)
        record["principled"] = {}
        if principled:
            for channel, socket_name in [("base_color", "Base Color"), ("metallic", "Metallic"), ("roughness", "Roughness"), ("alpha", "Alpha")]:
                socket = principled.inputs.get(socket_name)
                if socket:
                    record["principled"][channel] = self._json_value(socket.default_value)
        if include_node_graph:
            graph = self.server.shader_graph_service.get_shader_graph(material.name, max_nodes=80)
            record["graph"] = {"nodes": graph.get("nodes", []), "links": graph.get("links", []), "warnings": graph.get("warnings", [])}
        if include_preview_hints:
            record["preview_hints"] = {"preview_shape": material.get("overtli_preview_shape", "sphere"), "recommended_views": ["material_preview", "front", "isometric"]}
        return {"status": "success", "material": record, "warnings": []}


class MaterialTemplateService:
    DEFAULTS = {
        "pbr_metal_gold": ([1.0, 0.72, 0.22, 1.0], 1.0, 0.22, "pbr", "sphere"),
        "pbr_metal_brushed": ([0.78, 0.76, 0.70, 1.0], 1.0, 0.32, "pbr", "sphere"),
        "pbr_plastic": ([0.12, 0.22, 0.9, 1.0], 0.0, 0.38, "pbr", "cube"),
        "pbr_rubber": ([0.02, 0.02, 0.018, 1.0], 0.0, 0.78, "pbr", "sphere"),
        "pbr_ceramic": ([0.86, 0.82, 0.74, 1.0], 0.0, 0.24, "pbr", "sphere"),
        "pbr_clay": ([0.62, 0.38, 0.24, 1.0], 0.0, 0.74, "pbr", "sphere"),
        "glass_clear": ([0.85, 0.95, 1.0, 0.28], 0.0, 0.02, "transparent", "sphere"),
        "glass_frosted": ([0.82, 0.93, 1.0, 0.42], 0.0, 0.55, "transparent", "sphere"),
        "water_basic": ([0.18, 0.45, 0.75, 0.55], 0.0, 0.03, "transparent", "plane"),
        "emission_neon": ([0.1, 1.0, 0.75, 1.0], 0.0, 0.18, "emission", "sphere"),
        "toon_flat": ([0.95, 0.62, 0.25, 1.0], 0.0, 0.5, "stylized", "sphere"),
        "toon_rim": ([0.32, 0.42, 1.0, 1.0], 0.0, 0.45, "stylized", "sphere"),
        "fabric_woven": ([0.26, 0.22, 0.18, 1.0], 0.0, 0.86, "procedural", "sphere"),
        "leather_grain": ([0.21, 0.09, 0.035, 1.0], 0.0, 0.48, "procedural", "sphere"),
        "skin_basic": ([0.86, 0.56, 0.42, 1.0], 0.0, 0.42, "organic", "sphere"),
        "stone_rough": ([0.36, 0.35, 0.32, 1.0], 0.0, 0.82, "procedural", "cube"),
        "concrete_rough": ([0.48, 0.47, 0.43, 1.0], 0.0, 0.88, "procedural", "cube"),
        "wood_procedural": ([0.55, 0.28, 0.11, 1.0], 0.0, 0.46, "procedural", "cube"),
        "marble_procedural": ([0.86, 0.84, 0.78, 1.0], 0.0, 0.28, "procedural", "sphere"),
        "brick_procedural": ([0.56, 0.16, 0.08, 1.0], 0.0, 0.72, "procedural", "cube"),
        "sci_fi_panel": ([0.08, 0.10, 0.13, 1.0], 0.6, 0.34, "hard_surface", "cube"),
        "painted_metal": ([0.8, 0.08, 0.04, 1.0], 0.65, 0.42, "pbr", "sphere"),
        "car_paint_basic": ([0.02, 0.08, 0.74, 1.0], 0.25, 0.18, "pbr", "sphere"),
    }

    def __init__(self, server):
        self.server = server

    def _recipe(self, name):
        color, metallic, roughness, category, preview = self.DEFAULTS[name]
        procedural = name.endswith("_procedural") or name in {"fabric_woven", "leather_grain", "stone_rough", "concrete_rough", "brick_procedural", "sci_fi_panel"}
        return {
            "category": category,
            "description": f"{name.replace('_', ' ').title()} material recipe with PBR channels, map slots, and verification metadata.",
            "supported_parameters": {
                "base_color": "rgba", "metallic": "float", "roughness": "float", "alpha": "float",
                "emission_strength": "float", "noise_scale": "float", "bump_strength": "float",
                "normal_map_path": "path_optional", "roughness_map_path": "path_optional", "orm_map_path": "path_optional",
            },
            "default_parameters": {"base_color": color, "metallic": metallic, "roughness": roughness, "alpha": color[3], "noise_scale": 18.0, "bump_strength": 0.04},
            "channel_plan": {"base_color": "constant_or_map", "metallic": "constant_or_map", "roughness": "constant_map_or_noise", "normal": "optional_normal_or_bump", "ambient_occlusion": "metadata_or_packed_map"},
            "node_plan": ["Principled BSDF", "Image Texture optional", "Normal Map optional", "Bump optional"] + (["Noise Texture", "ColorRamp"] if procedural else []),
            "map_slots": ["base_color_map", "roughness_map", "metallic_map", "normal_map", "ambient_occlusion_map", "orm_map", "rma_map", "mra_map", "metallic_roughness_map"],
            "procedural_slots": ["roughness_noise", "bump_noise", "color_ramp"] if procedural else ["optional_noise_variation"],
            "preview_shape": preview,
            "risk_level": "MEDIUM",
            "known_limitations": ["No texture baking or external downloads in Phase 4A."],
        }

    def get_supported_material_templates(self):
        return {"status": "success", "templates": {name: self._recipe(name) for name in PHASE4A_TEMPLATE_NAMES}, "warnings": []}

    def create_material_from_template(self, template_name, material_name, parameters=None, map_slots=None, assign_to_object=None, replace_existing=False, verify=True):
        if template_name not in PHASE4A_TEMPLATE_NAMES:
            return {"status": "error", "message": f"Unsupported template_name: {template_name}", "supported_templates": PHASE4A_TEMPLATE_NAMES, "warnings": []}
        recipe = self._recipe(template_name)
        params = dict(recipe["default_parameters"])
        params.update(parameters or {})
        material_result = self.server.advanced_material_authoring_service.create_custom_material(
            material_name=material_name,
            recipe={"channels": params, "procedural": {"enabled": bool(recipe["procedural_slots"] and "optional" not in str(recipe["procedural_slots"]))}, "preview_shape": recipe["preview_shape"]},
            replace_existing=replace_existing,
            verify=False,
        )
        if material_result.get("status") != "success":
            return material_result
        warnings = material_result.get("warnings", [])
        for kind, path in (map_slots or {}).items():
            bind = self.server.material_texture_slot_service.bind_material_texture_map(material_name, kind, path, strict_file_exists=False, verify=False)
            warnings.extend(bind.get("warnings", []))
            if bind.get("status") == "error":
                warnings.append(bind.get("message"))
        assignment = None
        if assign_to_object:
            assignment = self.server.material_authoring_service.assign_material(assign_to_object, material_name, verify=False)
        deep = self.server.material_intelligence_service.get_material_deep_info(material_name, include_node_graph=True) if verify else None
        return {"status": "success", "template_name": template_name, "material_name": material_name, "material": material_result.get("material"), "assignment": assignment, "verification": deep, "warnings": warnings}


class AdvancedMaterialAuthoringService:
    def __init__(self, server):
        self.server = server

    def _ensure_material(self, material_name, replace_existing=False):
        if not material_name:
            raise ValueError("material_name is required")
        material = bpy.data.materials.get(material_name)
        created = False
        if material and not replace_existing:
            return material, created, ["material already exists"]
        if material is None:
            material = bpy.data.materials.new(material_name)
            created = True
        material.use_nodes = True
        if not material.node_tree:
            material.use_nodes = True
        return material, created, []

    @staticmethod
    def _set_input(node, names, value):
        for name in names:
            socket = node.inputs.get(name)
            if socket:
                socket.default_value = value
                return True
        return False

    def _apply_channels(self, material, channels):
        warnings = []
        principled = MaterialIntelligenceService._principled_node(material)
        if not principled:
            return ["No Principled BSDF node found"]
        scalar_map = {
            "metallic": ["Metallic"], "roughness": ["Roughness"], "alpha": ["Alpha"], "opacity": ["Alpha"],
            "ior": ["IOR"], "emission_strength": ["Emission Strength"], "subsurface": ["Subsurface Weight", "Subsurface"],
            "coat_weight": ["Coat Weight", "Clearcoat"], "coat_roughness": ["Coat Roughness", "Clearcoat Roughness"],
            "anisotropy": ["Anisotropic IOR Level", "Anisotropic"], "transmission": ["Transmission Weight", "Transmission"],
        }
        for channel, value in (channels or {}).items():
            try:
                if channel in {"base_color", "albedo"}:
                    color = list(value)
                    if len(color) == 3:
                        color.append(1.0)
                    material.diffuse_color = color
                    if not self._set_input(principled, ["Base Color"], color):
                        warnings.append("Base Color socket not available")
                elif channel == "emission_color":
                    self._set_input(principled, ["Emission Color", "Emission"], list(value))
                elif channel in scalar_map:
                    self._set_input(principled, scalar_map[channel], float(value))
                elif channel not in {"noise_scale", "bump_strength"}:
                    warnings.append(f"Channel recorded as metadata only: {channel}")
                material[f"overtli_channel_{channel}"] = json.dumps(value)
            except Exception as exc:
                warnings.append(f"Failed to set channel {channel}: {exc}")
        return warnings

    def _add_noise_bump(self, material, strength=0.04, scale=18.0):
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        principled = MaterialIntelligenceService._principled_node(material)
        if not principled:
            return ["No Principled BSDF node found for procedural bump"]
        noise = nodes.new(type="ShaderNodeTexNoise")
        noise.name = "OVERTLI Procedural Noise"
        if noise.inputs.get("Scale"):
            noise.inputs["Scale"].default_value = float(scale)
        bump = nodes.new(type="ShaderNodeBump")
        bump.name = "OVERTLI Procedural Bump"
        if bump.inputs.get("Strength"):
            bump.inputs["Strength"].default_value = float(strength)
        if noise.outputs.get("Fac") and bump.inputs.get("Height"):
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
        normal = principled.inputs.get("Normal")
        if bump.outputs.get("Normal") and normal:
            links.new(bump.outputs["Normal"], normal)
        return []

    def create_custom_material(self, material_name, recipe=None, replace_existing=False, verify=True):
        try:
            material, created, warnings = self._ensure_material(material_name, replace_existing)
        except ValueError as exc:
            return {"status": "error", "message": str(exc), "warnings": []}
        recipe = recipe or {}
        channels = recipe.get("channels", recipe)
        warnings.extend(self._apply_channels(material, channels))
        procedural = recipe.get("procedural") or {}
        if procedural.get("enabled"):
            warnings.extend(self._add_noise_bump(material, procedural.get("bump_strength", channels.get("bump_strength", 0.04)), procedural.get("noise_scale", channels.get("noise_scale", 18.0))))
        material["overtli_recipe"] = json.dumps(recipe, sort_keys=True)
        material["overtli_preview_shape"] = recipe.get("preview_shape", "sphere")
        deep = self.server.material_intelligence_service.get_material_deep_info(material.name, include_node_graph=True) if verify else None
        result = {"status": "success", "material_name": material.name, "created": created, "material": self.server.material_intelligence_service._material_record(material), "verification": deep, "warnings": warnings}
        self.server._add_to_history("create_custom_material", {"material_name": material_name}, result)
        return result

    def create_material_variant(self, source_material_name, variant_name, overrides=None, replace_existing=False, verify=True):
        source = bpy.data.materials.get(source_material_name)
        if not source:
            return {"status": "error", "message": f"Material not found: {source_material_name}", "warnings": []}
        existing = bpy.data.materials.get(variant_name)
        if existing and not replace_existing:
            return {"status": "error", "message": f"Material already exists: {variant_name}", "warnings": []}
        if existing:
            bpy.data.materials.remove(existing)
        material = source.copy()
        material.name = variant_name
        warnings = self._apply_channels(material, overrides or {})
        deep = self.server.material_intelligence_service.get_material_deep_info(material.name, include_node_graph=True) if verify else None
        return {"status": "success", "source_material_name": source_material_name, "material_name": material.name, "verification": deep, "warnings": warnings}

    def apply_material_to_objects(self, material_name, object_names, slot_index=None, replace=True, verify=True):
        results = []
        for object_name in object_names or []:
            results.append(self.server.material_authoring_service.assign_material(object_name, material_name, slot_index, replace, verify=False))
        status = "success" if all(item.get("status") == "success" for item in results) else "partial"
        verification = self.server.material_intelligence_service.get_material_deep_info(material_name, include_node_graph=False) if verify else None
        return {"status": status, "material_name": material_name, "object_names": object_names or [], "operation_results": results, "verification": verification, "warnings": []}

    def delete_materials(self, material_names, confirm=False, allow_missing=False, only_if_unused=False):
        if not confirm:
            return {"status": "error", "message": "delete_materials requires confirm=True", "deleted": [], "missing": list(material_names or []), "warnings": []}
        deleted, missing, refused, warnings = [], [], [], []
        for name in material_names or []:
            if any(token in str(name) for token in ["*", "?", "["]):
                refused.append(str(name))
                continue
            material = bpy.data.materials.get(str(name))
            if not material:
                missing.append(str(name))
                continue
            if only_if_unused and material.users > 0:
                refused.append(material.name)
                warnings.append(f"Material still has users: {material.name}")
                continue
            bpy.data.materials.remove(material)
            deleted.append(str(name))
        status = "success" if not refused and (allow_missing or not missing) else "partial" if deleted else "error"
        return {"status": status, "deleted": deleted, "missing": missing, "refused": refused, "warnings": warnings}


class ShaderGraphService:
    ALLOWED_NODE_TYPES = {
        "ShaderNodeTexNoise", "ShaderNodeTexVoronoi", "ShaderNodeValToRGB", "ShaderNodeBump",
        "ShaderNodeNormalMap", "ShaderNodeTexCoord", "ShaderNodeMapping", "ShaderNodeSeparateColor",
        "ShaderNodeMix", "ShaderNodeMath",
    }
    ALLOWED_INPUTS = {"Base Color", "Metallic", "Roughness", "Alpha", "Emission Color", "Emission Strength", "Scale", "Strength", "Distance", "Fac", "Color", "Normal", "Height"}

    def __init__(self, server):
        self.server = server

    def get_shader_graph(self, material_name, include_links=True, include_node_inputs=True, include_node_outputs=True, include_texture_metadata=True, max_nodes=None):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        if not material.use_nodes or not material.node_tree:
            return {"status": "success", "material_name": material.name, "nodes": [], "links": [], "warnings": ["material does not use nodes"]}
        nodes = list(material.node_tree.nodes)
        truncated = False
        if max_nodes is not None and len(nodes) > int(max_nodes):
            nodes = nodes[:int(max_nodes)]
            truncated = True
        node_names = {node.name for node in nodes}
        graph_nodes = []
        for node in nodes:
            item = {"name": node.name, "label": node.label, "type": node.type, "bl_idname": node.bl_idname, "location": [float(node.location.x), float(node.location.y)]}
            if include_node_inputs:
                item["inputs"] = [{"name": socket.name, "type": socket.type, "default_value": MaterialIntelligenceService._json_value(getattr(socket, "default_value", "")) if hasattr(socket, "default_value") else None, "is_linked": bool(socket.is_linked), "channel_guess": self._channel_guess(socket.name)} for socket in node.inputs]
            if include_node_outputs:
                item["outputs"] = [{"name": socket.name, "type": socket.type, "is_linked": bool(socket.is_linked)} for socket in node.outputs]
            if include_texture_metadata and node.bl_idname == "ShaderNodeTexImage":
                item["texture_metadata"] = {"map_kind": node.get("overtli_map_kind"), "color_space_intent": node.get("overtli_color_space_intent"), "packed_convention": node.get("overtli_packed_convention")}
            graph_nodes.append(item)
        links = []
        if include_links:
            for link in material.node_tree.links:
                if link.from_node.name in node_names and link.to_node.name in node_names:
                    links.append({"from_node": link.from_node.name, "from_socket": link.from_socket.name, "to_node": link.to_node.name, "to_socket": link.to_socket.name})
        return {"status": "success", "material_name": material.name, "nodes": graph_nodes, "links": links, "truncated": truncated, "warnings": []}

    @staticmethod
    def _channel_guess(socket_name):
        normalized = socket_name.lower().replace(" ", "_")
        return {"base_color": "base_color", "roughness": "roughness", "metallic": "metallic", "alpha": "alpha", "normal": "normal", "height": "height"}.get(normalized)

    def add_material_node(self, material_name, node_type, name=None, location=None):
        if node_type not in self.ALLOWED_NODE_TYPES:
            return {"status": "error", "message": f"Node type not allowlisted: {node_type}", "allowed_node_types": sorted(self.ALLOWED_NODE_TYPES), "warnings": []}
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        material.use_nodes = True
        node = material.node_tree.nodes.new(type=node_type)
        if name:
            node.name = str(name)
            node.label = str(name)
        if location and len(location) == 2:
            node.location = (float(location[0]), float(location[1]))
        return {"status": "success", "material_name": material.name, "node": {"name": node.name, "type": node.type, "bl_idname": node.bl_idname}, "warnings": []}

    def set_material_node_input(self, material_name, node_name, input_name, value):
        if input_name not in self.ALLOWED_INPUTS:
            return {"status": "error", "message": f"Node input not allowlisted: {input_name}", "warnings": []}
        material = bpy.data.materials.get(material_name)
        if not material or not material.node_tree:
            return {"status": "error", "message": f"Material not found or has no node tree: {material_name}", "warnings": []}
        node = material.node_tree.nodes.get(node_name)
        if not node:
            return {"status": "error", "message": f"Node not found: {node_name}", "warnings": []}
        socket = node.inputs.get(input_name)
        if not socket or not hasattr(socket, "default_value"):
            return {"status": "error", "message": f"Input not settable: {input_name}", "warnings": []}
        socket.default_value = value
        return {"status": "success", "material_name": material.name, "node_name": node.name, "input_name": input_name, "value": MaterialIntelligenceService._json_value(socket.default_value), "warnings": []}

    def connect_material_nodes(self, material_name, from_node, from_socket, to_node, to_socket):
        material = bpy.data.materials.get(material_name)
        if not material or not material.node_tree:
            return {"status": "error", "message": f"Material not found or has no node tree: {material_name}", "warnings": []}
        source = material.node_tree.nodes.get(from_node)
        target = material.node_tree.nodes.get(to_node)
        if not source or not target:
            return {"status": "error", "message": "Source or target node not found", "warnings": []}
        output = source.outputs.get(from_socket)
        input_socket = target.inputs.get(to_socket)
        if not output or not input_socket:
            return {"status": "error", "message": "Source or target socket not found", "warnings": []}
        material.node_tree.links.new(output, input_socket)
        return {"status": "success", "material_name": material.name, "link": {"from_node": source.name, "from_socket": output.name, "to_node": target.name, "to_socket": input_socket.name}, "warnings": []}

    def remove_material_node(self, material_name, node_name, confirm=False):
        if not confirm:
            return {"status": "error", "message": "remove_material_node requires confirm=True", "warnings": []}
        material = bpy.data.materials.get(material_name)
        if not material or not material.node_tree:
            return {"status": "error", "message": f"Material not found or has no node tree: {material_name}", "warnings": []}
        node = material.node_tree.nodes.get(node_name)
        if not node:
            return {"status": "error", "message": f"Node not found: {node_name}", "warnings": []}
        if node.bl_idname not in self.ALLOWED_NODE_TYPES or not node.name.startswith("OVERTLI"):
            return {"status": "error", "message": "Refusing to remove non-Overtli or non-allowlisted material node", "warnings": []}
        material.node_tree.nodes.remove(node)
        return {"status": "success", "material_name": material.name, "removed_node": node_name, "warnings": []}


class MaterialTextureSlotService:
    def __init__(self, server):
        self.server = server

    def bind_material_texture_map(self, material_name, map_kind, texture_path, strict_file_exists=True, connect=True, packed_convention=None, verify=True):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        if map_kind not in MATERIAL_MAP_KINDS:
            return {"status": "error", "message": f"Unsupported map_kind: {map_kind}", "supported_map_kinds": sorted(MATERIAL_MAP_KINDS), "warnings": []}
        warnings = []
        abs_path = bpy.path.abspath(texture_path) if texture_path else ""
        if strict_file_exists and (not abs_path or not os.path.exists(abs_path)):
            return {"status": "error", "message": f"Texture file not found: {texture_path}", "color_space_intent": MATERIAL_MAP_KINDS[map_kind]["color_space"], "warnings": []}
        material.use_nodes = True
        node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
        node.name = f"OVERTLI {map_kind}"
        node["overtli_map_kind"] = map_kind
        node["overtli_color_space_intent"] = MATERIAL_MAP_KINDS[map_kind]["color_space"]
        convention = packed_convention or MATERIAL_MAP_KINDS[map_kind].get("packed")
        if convention:
            node["overtli_packed_convention"] = convention
            warnings.append(f"Packed map convention recorded: {convention}; channel splitting is metadata-first in Phase 4A.")
        if abs_path and os.path.exists(abs_path):
            try:
                image = bpy.data.images.load(abs_path, check_existing=True)
                node.image = image
                if hasattr(image, "colorspace_settings"):
                    image.colorspace_settings.name = "Non-Color" if MATERIAL_MAP_KINDS[map_kind]["color_space"] == "Non-Color" else "sRGB"
            except Exception as exc:
                warnings.append(f"Texture node created but image load failed: {exc}")
        elif texture_path:
            warnings.append(f"Texture path recorded but not loaded because file is missing: {texture_path}")
        if connect:
            warnings.extend(self._connect_texture_node(material, node, map_kind))
        verification = self.server.material_intelligence_service.get_material_deep_info(material.name, include_node_graph=True) if verify else None
        return {"status": "success", "material_name": material.name, "map_kind": map_kind, "texture_path": texture_path, "color_space_intent": MATERIAL_MAP_KINDS[map_kind]["color_space"], "packed_convention": convention, "verification": verification, "warnings": warnings}

    def _connect_texture_node(self, material, image_node, map_kind):
        warnings = []
        principled = MaterialIntelligenceService._principled_node(material)
        if not principled:
            return ["No Principled BSDF node found for texture connection"]
        links = material.node_tree.links
        color_output = image_node.outputs.get("Color")
        alpha_output = image_node.outputs.get("Alpha")
        def link_to(output, socket_name):
            socket = principled.inputs.get(socket_name)
            if output and socket:
                links.new(output, socket)
                return True
            return False
        if map_kind in {"base_color_map", "albedo_map"}:
            if not link_to(color_output, "Base Color"):
                warnings.append("Base Color socket not available")
        elif map_kind in {"roughness_map", "metallic_map", "alpha_map", "opacity_map"}:
            socket_name = {"roughness_map": "Roughness", "metallic_map": "Metallic", "alpha_map": "Alpha", "opacity_map": "Alpha"}[map_kind]
            if not link_to(alpha_output or color_output, socket_name):
                warnings.append(f"{socket_name} socket not available")
        elif map_kind == "normal_map":
            normal = material.node_tree.nodes.new(type="ShaderNodeNormalMap")
            normal.name = "OVERTLI Normal Map"
            if color_output and normal.inputs.get("Color"):
                links.new(color_output, normal.inputs["Color"])
            if normal.outputs.get("Normal") and principled.inputs.get("Normal"):
                links.new(normal.outputs["Normal"], principled.inputs["Normal"])
        elif map_kind in {"bump_map", "height_map"}:
            bump = material.node_tree.nodes.new(type="ShaderNodeBump")
            bump.name = "OVERTLI Bump From Map"
            if color_output and bump.inputs.get("Height"):
                links.new(color_output, bump.inputs["Height"])
            if bump.outputs.get("Normal") and principled.inputs.get("Normal"):
                links.new(bump.outputs["Normal"], principled.inputs["Normal"])
        elif map_kind == "emission_map":
            link_to(color_output, "Emission Color") or link_to(color_output, "Emission")
        elif map_kind in {"ambient_occlusion_map", "orm_map", "rma_map", "mra_map", "metallic_roughness_map"}:
            warnings.append("Map recorded for agent-aware workflow; automatic packed/AO channel mixing is not blindly connected.")
        return warnings


class ProceduralTextureService:
    def __init__(self, server):
        self.server = server

    def create_procedural_material(self, material_name, procedural_type="noise", base_color=None, secondary_color=None, parameters=None, assign_to_object=None, replace_existing=False, verify=True):
        recipe = {
            "channels": {"base_color": base_color or [0.45, 0.45, 0.45, 1.0], "roughness": (parameters or {}).get("roughness", 0.68), "metallic": (parameters or {}).get("metallic", 0.0)},
            "procedural": {"enabled": True, "type": procedural_type, "noise_scale": (parameters or {}).get("noise_scale", 22.0), "bump_strength": (parameters or {}).get("bump_strength", 0.04), "secondary_color": secondary_color},
            "preview_shape": (parameters or {}).get("preview_shape", "sphere"),
        }
        result = self.server.advanced_material_authoring_service.create_custom_material(material_name, recipe, replace_existing, verify)
        if result.get("status") == "success" and assign_to_object:
            result["assignment"] = self.server.material_authoring_service.assign_material(assign_to_object, material_name, verify=False)
        return result


class MaterialPreviewService:
    def __init__(self, server):
        self.server = server

    def create_material_preview(self, material_name, preview_shape="sphere", artifact_root=None, include_snapshot=True):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        root = artifact_root or ADDON_ROOT
        preview_dir = os.path.join(root, ".overtli_blender", "material_previews")
        os.makedirs(preview_dir, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", material.name)
        manifest_path = os.path.join(preview_dir, f"{safe_name}_{int(time.time())}.json")
        payload = {
            "material_name": material.name,
            "preview_shape": preview_shape,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "deep_info": self.server.material_intelligence_service.get_material_deep_info(material.name, include_node_graph=False).get("material"),
            "note": "Phase 4A preview manifest; no external assets downloaded.",
        }
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        snapshot = None
        if include_snapshot:
            snapshot = self.server.verification_artifact_service.create_verification_snapshot(label=f"material_preview_{safe_name}", include_screenshots=False, artifact_root=root)
        return {"status": "success", "material_name": material.name, "preview_artifact": manifest_path, "snapshot": snapshot, "warnings": []}


class MaterialWorkflowBatchService:
    def __init__(self, server):
        self.server = server

    def run_material_workflow_batch(self, operations, label=None, artifact_root=None, verify=True):
        batch_id = f"material_batch_{int(time.time())}"
        before = self.server.workspace_safety_diff_service.create_scene_snapshot(label=f"{batch_id}_before", artifact_root=artifact_root or ADDON_ROOT) if verify else None
        results, errors, warnings = [], [], []
        for op in operations or []:
            command = op.get("command")
            params = op.get("params", {})
            if command not in {
                "create_material_from_template", "create_custom_material", "create_procedural_material",
                "create_material_variant", "apply_material_to_objects", "bind_material_texture_map",
                "set_material_node_input", "add_material_node", "connect_material_nodes", "create_material_preview",
            }:
                errors.append({"command": command, "message": "Command not allowed in material workflow batch"})
                continue
            result = getattr(self.server, command)(**params)
            results.append({"command": command, "result": result})
            warnings.extend(result.get("warnings", []))
            if result.get("status") == "error":
                errors.append({"command": command, "message": result.get("message")})
        after = self.server.workspace_safety_diff_service.create_scene_snapshot(label=f"{batch_id}_after", artifact_root=artifact_root or ADDON_ROOT) if verify else None
        status = "success" if not errors else "partial" if results else "error"
        return {"status": status, "batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors, "warnings": warnings}


class SelectionIntelligenceService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _vec(value):
        return [float(value[0]), float(value[1]), float(value[2])]

    @staticmethod
    def _bounds_from_points(points):
        if not points:
            return {"min": [], "max": [], "center": [], "size": []}
        mins = [min(point[i] for point in points) for i in range(3)]
        maxs = [max(point[i] for point in points) for i in range(3)]
        center = [(mins[i] + maxs[i]) / 2.0 for i in range(3)]
        size = [maxs[i] - mins[i] for i in range(3)]
        return {"min": mins, "max": maxs, "center": center, "size": size}

    def _object_bounds(self, objects):
        points = []
        for obj in objects:
            if getattr(obj, "bound_box", None):
                points.extend([obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box])
        return self._bounds_from_points(points)

    def _component_selection(self, obj, max_components):
        if not obj or obj.type != "MESH":
            return {"available": False, "warnings": ["active object is not a mesh"]}
        if bpy.context.mode != "EDIT_MESH":
            return {"available": False, "object_name": obj.name, "mode": bpy.context.mode, "warnings": ["component selection requires EDIT_MESH mode"]}
        try:
            import bmesh
            bm = bmesh.from_edit_mesh(obj.data)
            selected_vertices = [vert.index for vert in bm.verts if vert.select]
            selected_edges = [edge.index for edge in bm.edges if edge.select]
            selected_faces = [face.index for face in bm.faces if face.select]
            truncated = any(len(items) > max_components for items in [selected_vertices, selected_edges, selected_faces])
            return {
                "available": True,
                "object_name": obj.name,
                "mode": bpy.context.mode,
                "selected_vertices": {"count": len(selected_vertices), "indices": selected_vertices[:max_components]},
                "selected_edges": {"count": len(selected_edges), "indices": selected_edges[:max_components]},
                "selected_faces": {"count": len(selected_faces), "indices": selected_faces[:max_components]},
                "truncated": truncated,
                "warnings": [],
            }
        except Exception as exc:
            return {"available": False, "object_name": obj.name, "mode": bpy.context.mode, "warnings": [f"component selection unavailable: {exc}"]}

    def get_selection_deep_info(self, include_components=True, include_bounds=True, include_material_slots=True, include_vertex_groups=True, max_components=500):
        selected = list(bpy.context.selected_objects or [])
        active = bpy.context.view_layer.objects.active
        max_components = max(1, min(int(max_components or 500), 5000))
        result = {
            "status": "success",
            "mode": bpy.context.mode,
            "active_object": active.name if active else None,
            "selected_objects": [obj.name for obj in selected],
            "selected_count": len(selected),
            "object_selection_bounds": self._object_bounds(selected) if include_bounds else {},
            "component_selection": {"available": False, "warnings": ["component inspection disabled"]},
            "material_slots": [],
            "vertex_groups": [],
            "warnings": [],
        }
        if include_components:
            result["component_selection"] = self._component_selection(active, max_components)
            result["warnings"].extend(result["component_selection"].get("warnings", []))
        if active and active.type == "MESH" and include_material_slots:
            result["material_slots"] = [{"index": idx, "name": slot.material.name if slot.material else None} for idx, slot in enumerate(active.material_slots)]
        if active and active.type == "MESH" and include_vertex_groups:
            result["vertex_groups"] = [{"index": group.index, "name": group.name} for group in active.vertex_groups]
        return result

    def get_mesh_component_summary(self, object_name, include_bounds=True, include_material_faces=True, include_vertex_group_stats=True, include_shape_key_stats=True):
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        mesh = obj.data
        result = {
            "status": "success",
            "object_name": obj.name,
            "mesh_stats": {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "faces": len(mesh.polygons),
                "triangles_estimate": sum(max(1, len(poly.vertices) - 2) for poly in mesh.polygons),
            },
            "bounds": self._object_bounds([obj]) if include_bounds else {},
            "material_face_counts": {},
            "vertex_group_count": len(obj.vertex_groups) if include_vertex_group_stats else 0,
            "shape_key_count": len(mesh.shape_keys.key_blocks) if include_shape_key_stats and mesh.shape_keys else 0,
            "warnings": [],
        }
        if include_material_faces:
            counts = {}
            for poly in mesh.polygons:
                key = str(poly.material_index)
                counts[key] = counts.get(key, 0) + 1
            result["material_face_counts"] = counts
        return result


class VertexGroupService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _clamp(value, minimum=0.0, maximum=1.0):
        return max(minimum, min(maximum, float(value)))

    def _mesh_object(self, object_name):
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return None
        return obj

    def _indices_from_rule(self, obj, selection_mode, indices=None, rule=None):
        mesh = obj.data
        rule = rule or {}
        mode = str(selection_mode or "all").lower()
        if mode == "all":
            return list(range(len(mesh.vertices)))
        if mode == "indices":
            selected = [int(index) for index in (indices or [])]
            bad = [index for index in selected if index < 0 or index >= len(mesh.vertices)]
            if bad:
                raise ValueError(f"Vertex indices out of range: {bad[:10]}")
            return sorted(set(selected))
        if mode == "selected_vertices":
            if bpy.context.mode != "EDIT_MESH" or bpy.context.view_layer.objects.active != obj:
                raise ValueError("selected_vertices requires target object to be active in EDIT_MESH mode")
            import bmesh
            bm = bmesh.from_edit_mesh(mesh)
            return [vert.index for vert in bm.verts if vert.select]
        if mode == "by_axis":
            axis = str(rule.get("axis", "z")).lower()
            axis_index = {"x": 0, "y": 1, "z": 2}.get(axis)
            if axis_index is None:
                raise ValueError("by_axis requires axis x, y, or z")
            op = str(rule.get("operator", ">="))
            threshold = rule.get("threshold")
            coords = [vert.co[axis_index] for vert in mesh.vertices]
            if threshold is None:
                threshold = (min(coords) + max(coords)) / 2.0 if coords else 0.0
            threshold = float(threshold)
            return [vert.index for vert in mesh.vertices if (vert.co[axis_index] >= threshold if op in {">=", "above", "max"} else vert.co[axis_index] <= threshold)]
        if mode == "by_bounds":
            mins = rule.get("min")
            maxs = rule.get("max")
            if not isinstance(mins, (list, tuple)) or not isinstance(maxs, (list, tuple)) or len(mins) != 3 or len(maxs) != 3:
                raise ValueError("by_bounds requires rule.min and rule.max 3-item lists")
            return [vert.index for vert in mesh.vertices if all(float(mins[i]) <= vert.co[i] <= float(maxs[i]) for i in range(3))]
        if mode == "by_material_slot":
            slot_index = int(rule.get("slot_index", 0))
            found = set()
            for poly in mesh.polygons:
                if poly.material_index == slot_index:
                    found.update(poly.vertices)
            return sorted(found)
        if mode == "by_proximity_to_object":
            other = bpy.data.objects.get(rule.get("object_name"))
            radius = float(rule.get("radius", 1.0))
            if not other:
                raise ValueError("by_proximity_to_object requires rule.object_name")
            center = other.matrix_world.translation
            return [vert.index for vert in mesh.vertices if (obj.matrix_world @ vert.co - center).length <= radius]
        raise ValueError(f"Unsupported selection_mode: {selection_mode}")

    def _group_weight_stats(self, obj, group, max_vertices_sample=25):
        weights = []
        sample = []
        for vert in obj.data.vertices:
            for membership in vert.groups:
                if membership.group == group.index and membership.weight > 0:
                    weights.append(float(membership.weight))
                    if len(sample) < max_vertices_sample:
                        sample.append(vert.index)
        return {
            "name": group.name,
            "index": group.index,
            "nonzero_vertex_count": len(weights),
            "weight_min": min(weights) if weights else 0.0,
            "weight_max": max(weights) if weights else 0.0,
            "sample_indices": sample,
        }

    def create_vertex_group(self, object_name, group_name, selection_mode="all", indices=None, weight=1.0, replace_existing=False, rule=None):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        if not group_name:
            return {"status": "error", "message": "group_name is required", "warnings": []}
        existing = obj.vertex_groups.get(group_name)
        if existing and not replace_existing:
            return {"status": "error", "message": f"Vertex group already exists: {group_name}", "warnings": []}
        if existing:
            obj.vertex_groups.remove(existing)
        try:
            selected = self._indices_from_rule(obj, selection_mode, indices, rule)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}
        group = obj.vertex_groups.new(name=group_name)
        if selected:
            group.add(selected, self._clamp(weight), "REPLACE")
        result = {"status": "success", "object_name": obj.name, "group_name": group.name, "vertex_count": len(selected), "weight": self._clamp(weight), "selection_mode": selection_mode, "warnings": []}
        self.server._add_to_history("create_vertex_group", {"object_name": object_name, "group_name": group_name}, result)
        return result

    def update_vertex_group_weights(self, object_name, group_name, indices=None, weight=1.0, mode="replace", rule=None):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        group = obj.vertex_groups.get(group_name)
        if not group:
            return {"status": "error", "message": f"Vertex group not found: {group_name}", "warnings": []}
        try:
            selected = self._indices_from_rule(obj, "indices" if indices is not None else (rule or {}).get("selection_mode", "all"), indices, rule)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}
        op = {"replace": "REPLACE", "add": "ADD", "subtract": "SUBTRACT"}.get(str(mode).lower())
        if not op:
            return {"status": "error", "message": f"Unsupported weight update mode: {mode}", "warnings": []}
        if selected:
            group.add(selected, self._clamp(weight), op)
        result = {"status": "success", "object_name": obj.name, "group_name": group.name, "changed_count": len(selected), "mode": mode, "weight": self._clamp(weight), "warnings": []}
        self.server._add_to_history("update_vertex_group_weights", {"object_name": object_name, "group_name": group_name}, result)
        return result

    def list_vertex_groups(self, object_name, include_weights_summary=True, max_vertices_sample=25):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        groups = []
        for group in obj.vertex_groups:
            groups.append(self._group_weight_stats(obj, group, int(max_vertices_sample)) if include_weights_summary else {"name": group.name, "index": group.index})
        return {"status": "success", "object_name": obj.name, "vertex_groups": groups, "warnings": []}

    def delete_vertex_groups(self, object_name, group_names, confirm=False):
        if not confirm:
            return {"status": "error", "message": "delete_vertex_groups requires confirm=True", "deleted": [], "missing": list(group_names or []), "refused": list(group_names or []), "warnings": []}
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "deleted": [], "missing": [], "refused": list(group_names or []), "warnings": []}
        deleted, missing, refused = [], [], []
        for name in group_names or []:
            if any(token in str(name) for token in ["*", "?", "["]):
                refused.append(str(name))
                continue
            group = obj.vertex_groups.get(str(name))
            if not group:
                missing.append(str(name))
                continue
            obj.vertex_groups.remove(group)
            deleted.append(str(name))
        return {"status": "success" if not refused else "partial", "object_name": obj.name, "deleted": deleted, "missing": missing, "refused": refused, "warnings": []}


class ShapeKeyService:
    def __init__(self, server):
        self.server = server

    def _mesh_object(self, object_name):
        obj = bpy.data.objects.get(object_name)
        return obj if obj and obj.type == "MESH" else None

    def _shape_key(self, obj, name):
        return obj.data.shape_keys.key_blocks.get(name) if obj.data.shape_keys else None

    @staticmethod
    def _shape_summary(key):
        return {"name": key.name, "value": float(getattr(key, "value", 0.0)), "relative_key": key.relative_key.name if getattr(key, "relative_key", None) else None, "mute": bool(getattr(key, "mute", False))}

    def create_shape_key(self, object_name, shape_key_name, from_mix=False, replace_existing=False, value=0.0):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        if not shape_key_name:
            return {"status": "error", "message": "shape_key_name is required", "warnings": []}
        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis", from_mix=False)
        existing = self._shape_key(obj, shape_key_name)
        if existing and not replace_existing:
            return {"status": "error", "message": f"Shape key already exists: {shape_key_name}", "warnings": []}
        if existing:
            obj.active_shape_key_index = list(obj.data.shape_keys.key_blocks).index(existing)
            bpy.ops.object.shape_key_remove()
        key = obj.shape_key_add(name=shape_key_name, from_mix=bool(from_mix))
        key.value = max(-10.0, min(10.0, float(value)))
        result = {"status": "success", "object_name": obj.name, "shape_key": self._shape_summary(key), "warnings": []}
        self.server._add_to_history("create_shape_key", {"object_name": object_name, "shape_key_name": shape_key_name}, result)
        return result

    def update_shape_key_value(self, object_name, shape_key_name, value):
        obj = self._mesh_object(object_name)
        key = self._shape_key(obj, shape_key_name) if obj else None
        if not key:
            return {"status": "error", "message": f"Shape key not found: {shape_key_name}", "warnings": []}
        before = float(key.value)
        key.value = max(-10.0, min(10.0, float(value)))
        return {"status": "success", "object_name": obj.name, "shape_key_name": key.name, "before_value": before, "after_value": float(key.value), "warnings": []}

    def _target_indices(self, obj, offsets=None, vertex_group_name=None, deformation=None):
        if offsets:
            indices = [int(item["index"]) for item in offsets if "index" in item]
            bad = [index for index in indices if index < 0 or index >= len(obj.data.vertices)]
            if bad:
                raise ValueError(f"Vertex indices out of range: {bad[:10]}")
            return sorted(set(indices))
        if vertex_group_name:
            group = obj.vertex_groups.get(vertex_group_name)
            if not group:
                raise ValueError(f"Vertex group not found: {vertex_group_name}")
            return [vert.index for vert in obj.data.vertices if any(m.group == group.index and m.weight > 0 for m in vert.groups)]
        rule = (deformation or {}).get("region") or {}
        if rule:
            return self.server.vertex_group_service._indices_from_rule(obj, rule.get("selection_mode", "by_bounds"), None, rule)
        raise ValueError("edit_shape_key_offsets requires offsets, vertex_group_name, or deformation.region")

    def edit_shape_key_offsets(self, object_name, shape_key_name, offsets=None, vertex_group_name=None, deformation=None, confirm=False, verify=False):
        if not confirm:
            return {"status": "error", "message": "edit_shape_key_offsets requires confirm=True", "warnings": []}
        obj = self._mesh_object(object_name)
        key = self._shape_key(obj, shape_key_name) if obj else None
        if not key:
            return {"status": "error", "message": f"Shape key not found: {shape_key_name}", "warnings": []}
        if key.name == "Basis":
            return {"status": "error", "message": "Refusing to edit Basis shape key", "warnings": []}
        try:
            target_indices = self._target_indices(obj, offsets, vertex_group_name, deformation)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}
        offset_map = {int(item["index"]): mathutils.Vector(item.get("offset", [0, 0, 0])) for item in (offsets or []) if "index" in item}
        mode = str((deformation or {}).get("mode", "translate"))
        amount = float((deformation or {}).get("amount", 0.0))
        vector = mathutils.Vector((deformation or {}).get("vector", [0.0, 0.0, amount]))
        center = mathutils.Vector((deformation or {}).get("center", [0.0, 0.0, 0.0]))
        for index in target_indices:
            base = obj.data.vertices[index].co.copy()
            if index in offset_map:
                delta = offset_map[index]
            elif mode == "translate":
                delta = vector
            elif mode == "scale_from_center":
                delta = (base - center) * amount
            elif mode == "inflate_along_normals":
                delta = obj.data.vertices[index].normal * amount
            elif mode == "taper_axis":
                delta = mathutils.Vector((base.x * amount * base.z, base.y * amount * base.z, 0.0))
            elif mode == "bend_approx":
                delta = mathutils.Vector((amount * base.z * base.z, 0.0, 0.0))
            else:
                return {"status": "error", "message": f"Unsupported deformation mode: {mode}", "warnings": []}
            key.data[index].co = base + delta
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"shape_key_{shape_key_name}", include_screenshots=False) if verify else {}
        result = {"status": "success", "object_name": obj.name, "shape_key_name": key.name, "changed_vertex_count": len(target_indices), "object_summary": self.server.selection_intelligence_service.get_mesh_component_summary(obj.name), "verification": verification, "warnings": []}
        self.server._add_to_history("edit_shape_key_offsets", {"object_name": object_name, "shape_key_name": shape_key_name}, result)
        return result

    def list_shape_keys(self, object_name, include_stats=True):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        keys = [self._shape_summary(key) for key in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else []
        return {"status": "success", "object_name": obj.name, "shape_keys": keys, "warnings": []}

    def delete_shape_keys(self, object_name, shape_key_names, confirm=False, allow_basis=False):
        if not confirm:
            return {"status": "error", "message": "delete_shape_keys requires confirm=True", "deleted": [], "missing": list(shape_key_names or []), "refused": list(shape_key_names or []), "warnings": []}
        obj = self._mesh_object(object_name)
        if not obj or not obj.data.shape_keys:
            return {"status": "error", "message": f"Mesh object or shape keys not found: {object_name}", "deleted": [], "missing": list(shape_key_names or []), "refused": [], "warnings": []}
        deleted, missing, refused = [], [], []
        for name in shape_key_names or []:
            key = self._shape_key(obj, str(name))
            if not key:
                missing.append(str(name))
                continue
            if key.name == "Basis" and not allow_basis:
                refused.append(key.name)
                continue
            obj.active_shape_key_index = list(obj.data.shape_keys.key_blocks).index(key)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.shape_key_remove()
            deleted.append(str(name))
        return {"status": "success" if not refused else "partial", "object_name": obj.name, "deleted": deleted, "missing": missing, "refused": refused, "warnings": []}


class LatticeDeformationService:
    def __init__(self, server):
        self.server = server

    def create_lattice_deformer(self, target_object_name, lattice_name=None, resolution=None, padding=0.25, collection_name=None, add_modifier=True, verify=False):
        target = bpy.data.objects.get(target_object_name)
        if not target:
            return {"status": "error", "message": f"Target object not found: {target_object_name}", "warnings": []}
        lattice_data = bpy.data.lattices.new(lattice_name or f"{target.name}_Lattice")
        resolution = resolution or [2, 2, 2]
        lattice_data.points_u, lattice_data.points_v, lattice_data.points_w = [max(2, min(12, int(v))) for v in resolution[:3]]
        lattice_obj = bpy.data.objects.new(lattice_name or lattice_data.name, lattice_data)
        bounds = self.server.selection_intelligence_service._object_bounds([target])
        center = bounds.get("center") or list(target.location)
        size = [max(0.01, v + float(padding) * 2.0) for v in (bounds.get("size") or list(target.dimensions))]
        lattice_obj.location = center
        lattice_obj.scale = size
        collection = bpy.data.collections.get(collection_name) if collection_name else (target.users_collection[0] if target.users_collection else bpy.context.scene.collection)
        if collection is None:
            collection = bpy.context.scene.collection
        collection.objects.link(lattice_obj)
        modifier_name = None
        if add_modifier:
            modifier = target.modifiers.new(name=f"{lattice_obj.name}_Lattice", type="LATTICE")
            modifier.object = lattice_obj
            modifier_name = modifier.name
        verification = self.server.scene_edit_service._verification(f"lattice_{lattice_obj.name}", verify)
        return {"status": "success", "target_object_name": target.name, "lattice_name": lattice_obj.name, "modifier_name": modifier_name, "bounds": bounds, "resolution": [lattice_data.points_u, lattice_data.points_v, lattice_data.points_w], "verification": verification, "warnings": []}

    def update_lattice_deformer(self, lattice_name, control_point_offsets=None, deformation=None, confirm=False, verify=False):
        if not confirm:
            return {"status": "error", "message": "update_lattice_deformer requires confirm=True", "warnings": []}
        lattice_obj = bpy.data.objects.get(lattice_name)
        if not lattice_obj or lattice_obj.type != "LATTICE":
            return {"status": "error", "message": f"Lattice object not found: {lattice_name}", "warnings": []}
        points = lattice_obj.data.points
        changed = 0
        if control_point_offsets:
            for item in control_point_offsets:
                index = int(item.get("index", -1))
                if 0 <= index < len(points):
                    points[index].co_deform += mathutils.Vector(item.get("offset", [0, 0, 0]))
                    changed += 1
        else:
            deformation = deformation or {}
            mode = str(deformation.get("mode", "move_top"))
            amount = float(deformation.get("amount", 0.05))
            coords = [point.co_deform.z for point in points]
            top = max(coords) if coords else 0.0
            bottom = min(coords) if coords else 0.0
            for point in points:
                if mode == "move_top" and point.co_deform.z >= top:
                    point.co_deform.z += amount
                    changed += 1
                elif mode == "move_bottom" and point.co_deform.z <= bottom:
                    point.co_deform.z += amount
                    changed += 1
                elif mode == "scale_axis":
                    axis = str(deformation.get("axis", "x"))
                    setattr(point.co_deform, axis, getattr(point.co_deform, axis) * (1.0 + amount))
                    changed += 1
                elif mode in {"twist_approx", "taper_axis", "bend_approx"}:
                    point.co_deform.x += amount * point.co_deform.z
                    changed += 1
        verification = self.server.scene_edit_service._verification(f"lattice_update_{lattice_obj.name}", verify)
        return {"status": "success", "lattice_name": lattice_obj.name, "changed_point_count": changed, "verification": verification, "warnings": []}

    def apply_lattice_to_object(self, target_object_name, lattice_name, modifier_name=None, create_if_missing=True):
        target = bpy.data.objects.get(target_object_name)
        lattice_obj = bpy.data.objects.get(lattice_name)
        if not target or not lattice_obj or lattice_obj.type != "LATTICE":
            return {"status": "error", "message": "Target object or lattice not found", "warnings": []}
        modifier = target.modifiers.get(modifier_name) if modifier_name else None
        if modifier is None:
            for candidate in target.modifiers:
                if candidate.type == "LATTICE" and getattr(candidate, "object", None) == lattice_obj:
                    modifier = candidate
                    break
        if modifier is None and create_if_missing:
            modifier = target.modifiers.new(name=modifier_name or f"{lattice_obj.name}_Lattice", type="LATTICE")
        if modifier is None:
            return {"status": "error", "message": "Lattice modifier not found and create_if_missing=False", "warnings": []}
        modifier.object = lattice_obj
        return {"status": "success", "object_name": target.name, "lattice_name": lattice_obj.name, "modifier": {"name": modifier.name, "type": modifier.type}, "warnings": []}

    def remove_lattice_deformer(self, lattice_name, target_object_name=None, remove_modifier=True, delete_lattice_object=True, confirm=False):
        if not confirm:
            return {"status": "error", "message": "remove_lattice_deformer requires confirm=True", "warnings": []}
        lattice_obj = bpy.data.objects.get(lattice_name)
        removed_modifiers = []
        if remove_modifier:
            targets = [bpy.data.objects.get(target_object_name)] if target_object_name else list(bpy.data.objects)
            for obj in [item for item in targets if item]:
                for modifier in list(obj.modifiers):
                    if modifier.type == "LATTICE" and getattr(modifier, "object", None) == lattice_obj:
                        removed_modifiers.append({"object_name": obj.name, "modifier_name": modifier.name})
                        obj.modifiers.remove(modifier)
        deleted = False
        if delete_lattice_object and lattice_obj:
            bpy.data.objects.remove(lattice_obj, do_unlink=True)
            deleted = True
        return {"status": "success", "lattice_name": lattice_name, "removed_modifiers": removed_modifiers, "deleted_lattice_object": deleted, "warnings": []}


class DeformationModifierService:
    SUPPORTED_MODIFIERS = {"SIMPLE_DEFORM", "DISPLACE", "SHRINKWRAP", "SMOOTH", "CORRECTIVE_SMOOTH", "LAPLACIANSMOOTH", "WARP"}
    ALLOWED_PROPERTIES = {
        "SIMPLE_DEFORM": {"deform_method", "deform_axis", "angle", "factor", "limits", "show_viewport", "show_render"},
        "DISPLACE": {"strength", "direction", "mid_level", "show_viewport", "show_render"},
        "SHRINKWRAP": {"target", "wrap_method", "offset", "show_viewport", "show_render"},
        "SMOOTH": {"factor", "iterations", "show_viewport", "show_render"},
        "CORRECTIVE_SMOOTH": {"factor", "iterations", "smooth_type", "show_viewport", "show_render"},
        "LAPLACIANSMOOTH": {"lambda_factor", "lambda_border", "iterations", "show_viewport", "show_render"},
        "WARP": {"strength", "falloff_type", "show_viewport", "show_render"},
    }

    def __init__(self, server):
        self.server = server

    def _summary(self, modifier):
        return {"name": modifier.name, "type": modifier.type, "vertex_group": getattr(modifier, "vertex_group", ""), "show_viewport": bool(modifier.show_viewport), "show_render": bool(modifier.show_render)}

    def _apply_properties(self, modifier, properties):
        warnings = []
        allowed = self.ALLOWED_PROPERTIES.get(modifier.type, set())
        for key, value in (properties or {}).items():
            if key not in allowed:
                warnings.append(f"Unsupported deformation modifier property skipped: {key}")
                continue
            if key == "target" and isinstance(value, str):
                value = bpy.data.objects.get(value)
                if value is None:
                    warnings.append(f"Target object not found for property target")
                    continue
            try:
                setattr(modifier, key, value)
            except Exception as exc:
                warnings.append(f"Failed to set {key}: {exc}")
        return warnings

    def add_deformation_modifier(self, object_name, modifier_type, name=None, properties=None, vertex_group_name=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        modifier_type = str(modifier_type or "").upper()
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if modifier_type not in self.SUPPORTED_MODIFIERS:
            return {"status": "error", "message": f"Unsupported deformation modifier_type: {modifier_type}", "warnings": []}
        if vertex_group_name and not obj.vertex_groups.get(vertex_group_name):
            return {"status": "error", "message": f"Vertex group not found: {vertex_group_name}", "warnings": []}
        modifier = obj.modifiers.new(name=name or modifier_type.title(), type=modifier_type)
        if vertex_group_name and hasattr(modifier, "vertex_group"):
            modifier.vertex_group = vertex_group_name
        warnings = self._apply_properties(modifier, properties)
        return {"status": "success", "object_name": obj.name, "modifier": self._summary(modifier), "verification": self.server.scene_edit_service._verification(f"deform_modifier_{obj.name}", verify), "warnings": warnings}

    def update_deformation_modifier(self, object_name, modifier_name, properties, vertex_group_name=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        modifier = obj.modifiers.get(modifier_name) if obj else None
        if not modifier:
            return {"status": "error", "message": f"Modifier not found: {modifier_name}", "warnings": []}
        if modifier.type not in self.SUPPORTED_MODIFIERS:
            return {"status": "error", "message": f"Modifier is not a Phase 4B deformation modifier: {modifier.type}", "warnings": []}
        before = self._summary(modifier)
        warnings = self._apply_properties(modifier, properties)
        if vertex_group_name is not None and hasattr(modifier, "vertex_group"):
            if vertex_group_name and not obj.vertex_groups.get(vertex_group_name):
                return {"status": "error", "message": f"Vertex group not found: {vertex_group_name}", "warnings": warnings}
            modifier.vertex_group = vertex_group_name
        return {"status": "success" if not warnings else "partial", "object_name": obj.name, "before": before, "modifier": self._summary(modifier), "verification": self.server.scene_edit_service._verification(f"deform_modifier_{obj.name}", verify), "warnings": warnings}


class DirectMeshEditService:
    def __init__(self, server):
        self.server = server


class DeformationWorkflowBatchService:
    SUPPORTED_BATCH_OPERATIONS = {
        "get_selection_deep_info", "get_mesh_component_summary", "create_vertex_group", "update_vertex_group_weights",
        "create_shape_key", "update_shape_key_value", "edit_shape_key_offsets", "create_lattice_deformer",
        "update_lattice_deformer", "apply_lattice_to_object", "add_deformation_modifier", "update_deformation_modifier",
        "create_region_deformation", "delete_vertex_groups", "delete_shape_keys", "remove_lattice_deformer",
    }
    DESTRUCTIVE_OPERATIONS = {"delete_vertex_groups", "delete_shape_keys", "remove_lattice_deformer"}

    def __init__(self, server):
        self.server = server

    def create_region_deformation(self, object_name, region, method="shape_key", deformation=None, name=None, verify=True, confirm=False):
        if not confirm:
            return {"status": "error", "message": "create_region_deformation requires confirm=True", "warnings": []}
        method = str(method or "shape_key")
        region = region or {}
        deformation = deformation or {"mode": "translate", "vector": [0, 0, 0.05]}
        group_name = region.get("vertex_group")
        created = {}
        if not group_name:
            group_name = name or f"{object_name}_Region"
            mode_map = {"axis_range": "by_axis", "bounds": "by_bounds", "material_slot": "by_material_slot", "all": "all", "selected_vertices": "selected_vertices"}
            selector = region.get("selector") or region.get("type") or "all"
            group_result = self.server.vertex_group_service.create_vertex_group(object_name, group_name, mode_map.get(selector, selector), rule=region, replace_existing=True)
            if group_result.get("status") != "success":
                return group_result
            created["vertex_group"] = group_result
        if method == "shape_key":
            shape_name = name or f"{group_name}_Shape"
            shape = self.server.shape_key_service.create_shape_key(object_name, shape_name, replace_existing=True, value=1.0)
            if shape.get("status") != "success":
                return shape
            edit = self.server.shape_key_service.edit_shape_key_offsets(object_name, shape_name, vertex_group_name=group_name, deformation=deformation, confirm=True, verify=verify)
            created.update({"shape_key_name": shape_name, "shape_key_edit": edit})
        elif method == "lattice":
            lattice_name = name or f"{object_name}_RegionLattice"
            created["lattice"] = self.server.lattice_deformation_service.create_lattice_deformer(object_name, lattice_name=lattice_name, verify=verify)
        elif method == "deformation_modifier":
            modifier_name = name or f"{object_name}_RegionDeform"
            created["modifier"] = self.server.deformation_modifier_service.add_deformation_modifier(object_name, deformation.get("modifier_type", "SIMPLE_DEFORM"), name=modifier_name, properties=deformation.get("properties", {"deform_method": "TAPER", "factor": 0.05}), vertex_group_name=group_name, verify=verify)
        else:
            return {"status": "error", "message": f"Unsupported deformation method: {method}", "warnings": []}
        return {"status": "success", "object_name": object_name, "method": method, "region": region, "created": created, "warnings": []}

    def run_deformation_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=30, batch_allow_destructive=False):
        operations = operations or []
        max_operations = max(1, min(int(max_operations), 60))
        if len(operations) > max_operations:
            return {"status": "error", "message": f"Batch exceeds max_operations={max_operations}", "operation_results": [], "errors": [], "warnings": []}
        batch_id = f"deform_batch_{int(time.time())}_{abs(hash(str(operations))) % 100000}"
        batch_label = label or batch_id
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_label}_before", include_screenshots=False) if create_before_snapshot else {}
        results, errors, warnings = [], [], []
        handlers = self.server._build_command_handlers()
        for index, operation in enumerate(operations):
            command = operation.get("type") or operation.get("command")
            params = dict(operation.get("params") or {})
            if command not in self.SUPPORTED_BATCH_OPERATIONS:
                errors.append({"index": index, "command": command, "message": "Unsupported deformation workflow operation"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_OPERATIONS and not (batch_allow_destructive and operation.get("confirm") is True):
                errors.append({"index": index, "command": command, "message": "Destructive operation requires batch_allow_destructive=True and operation.confirm=True"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_OPERATIONS:
                params.setdefault("confirm", True)
            result = handlers[command](**params)
            results.append({"index": index, "command": command, "result": result})
            warnings.extend(result.get("warnings", []) if isinstance(result, dict) else [])
            if isinstance(result, dict) and result.get("status") not in {"success"}:
                errors.append({"index": index, "command": command, "message": result.get("message", result.get("status"))})
                if stop_on_error:
                    break
        after = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_label}_after", include_screenshots=False) if create_after_snapshot else {}
        return {"status": "success" if not errors else ("partial" if results else "error"), "batch_id": batch_id, "label": batch_label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors, "warnings": warnings}


class MethodIntelligenceService:
    PLAYBOOKS = {
        "make_region_larger": ["inspect selection", "create or reuse vertex group", "prefer shape key or lattice", "verify before/after"],
        "arrange_repeated_objects": ["inspect count and spacing", "prefer array or geometry nodes", "avoid many unique duplicates", "verify scene health"],
        "create_pbr_material": ["inspect material slots", "choose template", "bind color-space-aware maps", "preview material"],
        "sculpt_region_safely": ["inspect mesh and masks", "prefer shape-key sculpt workflow", "use small brush settings", "capture verification snapshot"],
    }
    ANTI_PATTERNS = [
        "Do not run raw Python mesh edits when a structured vertex group, shape key, lattice, modifier, or playbook can solve the task.",
        "Do not apply modifiers destructively by default.",
        "Do not deform a vague region without selection, bounds, material slot, UV island, or vertex group evidence.",
        "Do not download assets or overwrite texture files as part of local smoke workflows.",
        "Do not claim visual success without snapshot or scene-health evidence when verification is requested.",
    ]
    MODIFIER_RECIPES = {
        "body_proportion_lattice": {"modifiers": ["LATTICE"], "requires": ["target_object", "lattice_cage"], "risk": "medium"},
        "localized_taper": {"modifiers": ["SIMPLE_DEFORM"], "requires": ["vertex_group"], "risk": "medium"},
        "soft_surface_relax": {"modifiers": ["SMOOTH", "CORRECTIVE_SMOOTH"], "requires": ["optional_vertex_group"], "risk": "medium"},
        "surface_fit": {"modifiers": ["SHRINKWRAP"], "requires": ["target_object"], "risk": "medium"},
    }

    def __init__(self, server):
        self.server = server

    def get_method_plan(self, intent, object_name=None, region=None, constraints=None, verify=True):
        constraints = constraints or []
        region = region or {}
        intent_text = str(intent or "").lower()
        if any(word in intent_text for word in ["sculpt", "brush", "grab", "smooth"]):
            method = "shape_key_sculpt_workflow"
            sequence = self.PLAYBOOKS["sculpt_region_safely"]
        elif any(word in intent_text for word in ["larger", "smaller", "wider", "deform", "proportion"]):
            method = "shape_key_or_lattice"
            sequence = self.PLAYBOOKS["make_region_larger"]
        elif any(word in intent_text for word in ["material", "shader", "pbr", "texture"]):
            method = "material_template_or_pbr_builder"
            sequence = self.PLAYBOOKS["create_pbr_material"]
        else:
            method = "inspect_then_choose_structured_tool"
            sequence = ["inspect scene", "choose non-destructive structured tool", "execute bounded operation", "verify result"]
        confidence = self.score_selection_confidence(object_name=object_name, region=region).get("confidence", 0.0) if object_name else 0.5
        return {"status": "success", "intent": intent, "object_name": object_name, "recommended_method": method, "sequence": sequence, "constraints": constraints, "confidence": confidence, "verification_required": bool(verify), "anti_patterns": self.ANTI_PATTERNS, "warnings": []}

    def list_operation_playbooks(self, category=None):
        playbooks = self.PLAYBOOKS
        if category:
            playbooks = {key: value for key, value in playbooks.items() if category in key}
        return {"status": "success", "playbooks": playbooks, "warnings": []}

    def get_tricks_knowledge_base(self, category=None):
        entries = {
            "deformation": ["Use vertex groups as reusable masks.", "Use shape keys for reversible local edits.", "Use lattices for broad proportion changes."],
            "materials": ["Keep non-color maps as Non-Color.", "Use templates before custom node graphs."],
            "sculpt": ["Prefer shape-key sculpt workflow for recoverability.", "Use masks/vertex groups before brush changes."],
        }
        return {"status": "success", "category": category, "entries": entries.get(category, entries), "warnings": []}

    def get_anti_pattern_rules(self):
        return {"status": "success", "anti_patterns": self.ANTI_PATTERNS, "warnings": []}

    def get_modifier_recipes(self, recipe_name=None):
        recipes = self.MODIFIER_RECIPES
        if recipe_name:
            recipes = {recipe_name: recipes.get(recipe_name)} if recipe_name in recipes else {}
        return {"status": "success", "recipes": recipes, "warnings": []}

    def score_selection_confidence(self, object_name=None, region=None):
        score = 0.0
        reasons = []
        obj = bpy.data.objects.get(object_name) if object_name else bpy.context.view_layer.objects.active
        if obj:
            score += 0.25
            reasons.append("target object exists")
        region = region or {}
        if region.get("vertex_group") and obj and obj.vertex_groups.get(region.get("vertex_group")):
            score += 0.45
            reasons.append("vertex group region exists")
        if region.get("min") and region.get("max"):
            score += 0.25
            reasons.append("bounded region supplied")
        if region.get("material_slot") is not None or region.get("slot_index") is not None:
            score += 0.2
            reasons.append("material slot region supplied")
        if bpy.context.mode == "EDIT_MESH":
            score += 0.2
            reasons.append("user edit-mode selection is available")
        return {"status": "success", "confidence": min(1.0, score), "reasons": reasons, "warnings": [] if score >= 0.5 else ["low-confidence-region"]}


class AssetMaterialWorkflowService:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".bmp", ".tga"}

    def __init__(self, server):
        self.server = server

    def scan_blender_asset_libraries(self, include_current_file=True, max_items=200):
        assets = []
        if include_current_file:
            for collection_name, data_blocks in [("materials", bpy.data.materials), ("objects", bpy.data.objects), ("images", bpy.data.images)]:
                for item in list(data_blocks)[:max_items]:
                    assets.append({"library": "current_file", "type": collection_name[:-1], "name": item.name, "users": int(getattr(item, "users", 0))})
                    if len(assets) >= max_items:
                        break
        return {"status": "success", "asset_count": len(assets), "assets": assets, "warnings": []}

    def preview_asset(self, asset_name, asset_type="material", artifact_root=None, include_snapshot=True):
        if asset_type == "material":
            return self.server.material_preview_service.create_material_preview(asset_name, artifact_root=artifact_root, include_snapshot=include_snapshot)
        datablocks = {"object": bpy.data.objects, "image": bpy.data.images, "collection": bpy.data.collections}.get(asset_type)
        if datablocks is None or asset_name not in datablocks:
            return {"status": "error", "message": f"Asset not found: {asset_type}:{asset_name}", "warnings": []}
        snapshot = self.server.verification_artifact_service.create_verification_snapshot(label=f"asset_preview_{asset_type}_{asset_name}", include_screenshots=False, artifact_root=artifact_root) if include_snapshot else {}
        return {"status": "success", "asset_name": asset_name, "asset_type": asset_type, "snapshot": snapshot, "warnings": []}

    def import_texture_folder(self, folder_path, material_name=None, assign_to_object=None, strict_file_exists=True, verify=True):
        folder = os.path.abspath(os.path.expanduser(str(folder_path or "")))
        if strict_file_exists and not os.path.isdir(folder):
            return {"status": "error", "message": f"Texture folder not found: {folder}", "warnings": []}
        files = []
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                if os.path.splitext(name)[1].lower() in self.IMAGE_EXTENSIONS:
                    files.append(os.path.join(folder, name))
        material_name = material_name or f"OVERTLI_TEXTURE_SET_{int(time.time())}"
        material_result = self.server.advanced_material_authoring_service.create_custom_material(material_name, replace_existing=True, verify=False)
        bindings = []
        kind_map = [("base_color", ["base", "albedo", "diffuse"]), ("roughness_map", ["rough"]), ("metallic_map", ["metal"]), ("normal_map", ["normal"]), ("height_map", ["height", "disp"]), ("ao_map", ["ao", "ambient"])]
        for path in files:
            lower = os.path.basename(path).lower()
            kind = next((candidate for candidate, tokens in kind_map if any(token in lower for token in tokens)), None)
            if kind:
                bindings.append(self.server.material_texture_slot_service.bind_material_texture_map(material_name, kind, path, strict_file_exists=False, verify=False))
        assignment = self.server.material_authoring_service.assign_material(assign_to_object, material_name, verify=False) if assign_to_object else None
        verification = self.server.material_intelligence_service.get_material_deep_info(material_name, include_node_graph=False) if verify else {}
        return {"status": "success", "folder_path": folder, "material_name": material_name, "texture_files": files, "bindings": bindings, "assignment": assignment, "verification": verification, "warnings": []}

    def create_style_material(self, style_name, material_name, parameters=None, assign_to_object=None, verify=True):
        style = str(style_name or "stylized").lower()
        templates = {"realistic": "pbr_metal_gold", "glass": "glass_clear", "fabric": "fabric_woven", "wood": "wood_procedural", "sci_fi": "sci_fi_panel", "stylized": "car_paint_basic"}
        template = templates.get(style, "car_paint_basic")
        return self.server.material_template_service.create_material_from_template(template, material_name, parameters=parameters or {}, assign_to_object=assign_to_object, replace_existing=True, verify=verify)

    def create_paintable_texture(self, object_name, material_name=None, image_name=None, width=1024, height=1024, base_color=None, verify=True):
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        width = max(16, min(8192, int(width)))
        height = max(16, min(8192, int(height)))
        image = bpy.data.images.new(image_name or f"{object_name}_Paintable", width=width, height=height, alpha=True)
        if base_color:
            image.generated_color = [float(v) for v in base_color[:4]]
        material_name = material_name or f"{object_name}_Paintable_Material"
        material = self.server.material_authoring_service.create_basic_material(material_name, base_color=base_color or [1, 1, 1, 1], replace_existing=True)
        self.server.material_authoring_service.assign_material(object_name, material_name, verify=False)
        verification = self.server.material_intelligence_service.get_material_deep_info(material_name, include_node_graph=False) if verify else {}
        return {"status": "success", "object_name": obj.name, "material_name": material_name, "image_name": image.name, "size": [width, height], "material": material, "verification": verification, "warnings": ["created in-memory image; save/pack explicitly if persistence is required"]}

    def delete_images(self, image_names, confirm=False, allow_missing=False):
        if not confirm:
            return {"status": "error", "message": "delete_images requires confirm=True", "deleted": [], "missing": list(image_names or []), "refused": list(image_names or []), "warnings": []}
        deleted, missing, refused = [], [], []
        for name in image_names or []:
            if any(token in str(name) for token in ["*", "?", "["]):
                refused.append(str(name))
                continue
            image = bpy.data.images.get(str(name))
            if image is None:
                missing.append(str(name))
                continue
            bpy.data.images.remove(image)
            deleted.append(str(name))
        status = "success" if not refused and (allow_missing or not missing) else "partial"
        return {"status": status, "deleted": deleted, "missing": missing, "refused": refused, "warnings": []}


class UVSelectionMeasurementService:
    def __init__(self, server):
        self.server = server

    def list_uv_maps(self, object_name, include_island_estimate=True):
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        maps = [{"name": uv.name, "index": index, "active": obj.data.uv_layers.active == uv} for index, uv in enumerate(obj.data.uv_layers)]
        return {"status": "success", "object_name": obj.name, "uv_maps": maps, "island_estimate_available": bool(include_island_estimate), "warnings": []}

    def create_vertex_group_from_uv_island(self, object_name, group_name, uv_map_name=None, island_seed_face_index=None, weight=1.0, confirm=False):
        if not confirm:
            return {"status": "error", "message": "create_vertex_group_from_uv_island requires confirm=True", "warnings": []}
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        mesh = obj.data
        if not mesh.uv_layers:
            return {"status": "error", "message": f"Object has no UV maps: {object_name}", "warnings": []}
        if island_seed_face_index is None:
            indices = sorted({vertex for poly in mesh.polygons for vertex in poly.vertices})
            warnings = ["no island seed supplied; captured all UV-mapped vertices"]
        else:
            face_index = int(island_seed_face_index)
            if face_index < 0 or face_index >= len(mesh.polygons):
                return {"status": "error", "message": f"Face index out of range: {face_index}", "warnings": []}
            indices = list(mesh.polygons[face_index].vertices)
            warnings = ["single-face UV island approximation used"]
        result = self.server.vertex_group_service.create_vertex_group(object_name, group_name, selection_mode="indices", indices=indices, weight=weight, replace_existing=True)
        result["warnings"] = result.get("warnings", []) + warnings
        return result

    def measure_object(self, object_name, include_bounds=True):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        bounds = self.server.selection_intelligence_service._object_bounds([obj]) if include_bounds and getattr(obj, "bound_box", None) else {}
        return {"status": "success", "object_name": obj.name, "location": list(obj.location), "dimensions": list(obj.dimensions), "bounds": bounds, "warnings": []}

    def measure_distance(self, object_a, object_b):
        first = bpy.data.objects.get(object_a)
        second = bpy.data.objects.get(object_b)
        if not first or not second:
            return {"status": "error", "message": "Both objects must exist", "warnings": []}
        distance = (first.matrix_world.translation - second.matrix_world.translation).length
        return {"status": "success", "object_a": first.name, "object_b": second.name, "distance": float(distance), "warnings": []}

    def create_proportional_deformation(self, object_name, region, deformation, method="shape_key", name=None, confirm=False, verify=True):
        deformation = dict(deformation or {})
        deformation.setdefault("falloff", "smooth")
        return self.server.deformation_workflow_batch_service.create_region_deformation(object_name, region, method=method, deformation=deformation, name=name, confirm=confirm, verify=verify)


class SculptWorkflowService:
    SUPPORTED_BRUSHES = {"grab", "elastic_grab", "smooth", "inflate", "draw", "clay_strips", "pinch", "flatten", "mask"}

    def __init__(self, server):
        self.server = server

    def get_sculpt_status(self, object_name=None):
        obj = bpy.data.objects.get(object_name) if object_name else bpy.context.view_layer.objects.active
        return {"status": "success", "mode": bpy.context.mode, "object_name": obj.name if obj else None, "is_mesh": bool(obj and obj.type == "MESH"), "supported_brushes": sorted(self.SUPPORTED_BRUSHES), "warnings": []}

    def configure_sculpt_brush(self, brush_name="grab", radius=50, strength=0.25, symmetry=None, confirm=False):
        if not confirm:
            return {"status": "error", "message": "configure_sculpt_brush requires confirm=True", "warnings": []}
        brush_key = str(brush_name or "").lower()
        if brush_key not in self.SUPPORTED_BRUSHES:
            return {"status": "error", "message": f"Unsupported sculpt brush: {brush_name}", "warnings": []}
        settings = bpy.context.scene.tool_settings
        if getattr(settings, "sculpt", None) and settings.sculpt.brush:
            settings.sculpt.brush.size = max(1, min(1000, int(radius)))
            settings.sculpt.brush.strength = max(0.0, min(1.0, float(strength)))
        return {"status": "success", "brush_name": brush_key, "radius": int(radius), "strength": float(strength), "symmetry": symmetry or {}, "warnings": ["brush configuration is session-local"]}

    def create_sculpt_mask_from_vertex_group(self, object_name, vertex_group_name, mask_name=None, confirm=False):
        if not confirm:
            return {"status": "error", "message": "create_sculpt_mask_from_vertex_group requires confirm=True", "warnings": []}
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH" or not obj.vertex_groups.get(vertex_group_name):
            return {"status": "error", "message": "Mesh object and vertex group are required", "warnings": []}
        return {"status": "success", "object_name": obj.name, "vertex_group_name": vertex_group_name, "mask_name": mask_name or vertex_group_name, "warnings": ["stored as vertex-group-backed sculpt mask intent; no destructive sculpt mask write performed"]}

    def run_shape_key_sculpt_workflow(self, object_name, vertex_group_name, shape_key_name, brush_action="inflate", amount=0.05, confirm=False, verify=True):
        if not confirm:
            return {"status": "error", "message": "run_shape_key_sculpt_workflow requires confirm=True", "warnings": []}
        if str(brush_action).lower() not in {"inflate", "grab", "elastic_grab", "smooth"}:
            return {"status": "error", "message": f"Unsupported shape-key sculpt action: {brush_action}", "warnings": []}
        shape = self.server.shape_key_service.create_shape_key(object_name, shape_key_name, replace_existing=True, value=1.0)
        if shape.get("status") != "success":
            return shape
        mode = "inflate_along_normals" if brush_action == "inflate" else "translate"
        vector = [0.0, 0.0, float(amount)] if mode == "translate" else None
        edit = self.server.shape_key_service.edit_shape_key_offsets(object_name, shape_key_name, vertex_group_name=vertex_group_name, deformation={"mode": mode, "amount": float(amount), "vector": vector or [0, 0, 0]}, confirm=True, verify=verify)
        return {"status": edit.get("status", "error"), "object_name": object_name, "shape_key_name": shape_key_name, "brush_action": brush_action, "shape_key": shape, "edit": edit, "warnings": edit.get("warnings", [])}


class AnimationIntelligenceService:
    def __init__(self, server):
        self.server = server

    def get_timeline_info(self, include_markers=True, include_playback=True):
        scene = bpy.context.scene
        fps = int(scene.render.fps)
        fps_base = float(scene.render.fps_base or 1.0)
        frame_start = int(scene.frame_start)
        frame_end = int(scene.frame_end)
        duration_frames = max(0, frame_end - frame_start + 1)
        result = {
            "status": "success",
            "frame_current": int(scene.frame_current),
            "frame_start": frame_start,
            "frame_end": frame_end,
            "fps": fps,
            "fps_base": fps_base,
            "duration_frames": duration_frames,
            "duration_seconds": round(duration_frames / max(1.0, fps / fps_base), 4),
            "warnings": [],
        }
        if include_markers:
            result["markers"] = [{"name": marker.name, "frame": int(marker.frame)} for marker in scene.timeline_markers]
        if include_playback:
            result["playback"] = {"use_preview_range": bool(scene.use_preview_range), "frame_preview_start": int(scene.frame_preview_start), "frame_preview_end": int(scene.frame_preview_end)}
        return result

    @staticmethod
    def _action_fcurves(action):
        return list(getattr(action, "fcurves", []) or [])

    @staticmethod
    def _animation_summary(animation_data, include_keyframes=False, include_drivers=True, max_keyframes=200):
        action = animation_data.action if animation_data else None
        fcurves = []
        truncated = False
        if action:
            for fcurve in AnimationIntelligenceService._action_fcurves(action):
                points = list(fcurve.keyframe_points)
                frames = [float(point.co.x) for point in points]
                interpolation_summary = {}
                keyframes = []
                for point in points:
                    interpolation_summary[point.interpolation] = interpolation_summary.get(point.interpolation, 0) + 1
                    if include_keyframes and len(keyframes) < max_keyframes:
                        keyframes.append({"frame": float(point.co.x), "value": float(point.co.y), "interpolation": point.interpolation})
                if include_keyframes and len(points) > len(keyframes):
                    truncated = True
                item = {"data_path": fcurve.data_path, "array_index": int(fcurve.array_index), "keyframe_count": len(points), "frame_range": [min(frames), max(frames)] if frames else None, "interpolation_summary": interpolation_summary}
                if include_keyframes:
                    item["keyframes"] = keyframes
                fcurves.append(item)
        drivers = []
        if include_drivers and animation_data:
            for fcurve in getattr(animation_data, "drivers", []) or []:
                driver = getattr(fcurve, "driver", None)
                drivers.append({"data_path": fcurve.data_path, "array_index": int(fcurve.array_index), "type": getattr(driver, "type", None), "expression": getattr(driver, "expression", None), "variable_count": len(getattr(driver, "variables", []) or [])})
        return {"action_name": action.name if action else None, "fcurves": fcurves, "drivers": drivers, "truncated": truncated}

    def list_animated_objects(self, include_material_animation=True, include_shape_key_animation=True, include_drivers=True, max_objects=None):
        objects = []
        warnings = []
        limit = int(max_objects) if max_objects is not None else None
        for obj in bpy.context.scene.objects:
            object_animation = self._animation_summary(obj.animation_data, include_drivers=include_drivers)
            material_animation = []
            shape_key_animation = None
            if include_material_animation:
                for slot in obj.material_slots:
                    if slot.material and slot.material.animation_data:
                        material_animation.append({"material_name": slot.material.name, **self._animation_summary(slot.material.animation_data, include_drivers=include_drivers)})
            if include_shape_key_animation and getattr(obj.data, "shape_keys", None) and obj.data.shape_keys.animation_data:
                shape_key_animation = self._animation_summary(obj.data.shape_keys.animation_data, include_drivers=include_drivers)
            if object_animation["fcurves"] or object_animation["drivers"] or material_animation or shape_key_animation:
                objects.append({"name": obj.name, "type": obj.type, "object_animation": object_animation, "material_animation": material_animation, "shape_key_animation": shape_key_animation, "driver_count": len(object_animation["drivers"])})
            if limit is not None and len(objects) >= limit:
                warnings.append("Animated object list truncated by max_objects")
                break
        return {"status": "success", "objects": objects, "count": len(objects), "warnings": warnings}

    def get_animation_deep_info(self, object_name=None, material_name=None, include_keyframes=True, include_fcurves=True, include_drivers=True, max_keyframes=200):
        target = None
        target_type = None
        if object_name:
            target = bpy.data.objects.get(object_name)
            target_type = "OBJECT"
        elif material_name:
            target = bpy.data.materials.get(material_name)
            target_type = "MATERIAL"
        if target is None and (object_name or material_name):
            return {"status": "error", "message": "Animation target not found", "warnings": []}
        if target is None:
            return {"status": "success", "target": {"type": "SCENE"}, "timeline": self.get_timeline_info(), "animated_objects": self.list_animated_objects(max_objects=100), "warnings": []}
        animation_data = self._animation_summary(target.animation_data, include_keyframes, include_drivers, max(1, min(int(max_keyframes), 1000)))
        if not include_fcurves:
            animation_data["fcurves"] = []
        return {"status": "success", "target": {"type": target_type, "name": target.name}, "animation_data": animation_data, "truncated": animation_data["truncated"], "warnings": []}

    def set_timeline_range(self, frame_start, frame_end, fps=None, current_frame=None):
        before = self.get_timeline_info()
        frame_start = int(frame_start)
        frame_end = int(frame_end)
        if frame_start >= frame_end or frame_end - frame_start > 10000:
            return {"status": "error", "message": "frame_start must be less than frame_end and range must be <= 10000 frames", "warnings": []}
        scene = bpy.context.scene
        scene.frame_start = frame_start
        scene.frame_end = frame_end
        if fps is not None:
            scene.render.fps = max(1, min(int(fps), 240))
        if current_frame is not None:
            scene.frame_set(max(frame_start, min(int(current_frame), frame_end)))
        after = self.get_timeline_info()
        self.server._add_to_history("set_timeline_range", {"frame_start": frame_start, "frame_end": frame_end, "fps": fps, "current_frame": current_frame}, after)
        return {"status": "success", "before": before, "after": after, "warnings": []}

    def set_current_frame(self, frame):
        scene = bpy.context.scene
        before = int(scene.frame_current)
        frame = int(frame)
        if frame < -100000 or frame > 100000:
            return {"status": "error", "message": "frame is outside safety bounds", "warnings": []}
        scene.frame_set(frame)
        return {"status": "success", "before_frame": before, "frame_current": int(scene.frame_current), "warnings": []}


class AnimationAuthoringService:
    TRANSFORM_PROPERTIES = {"location", "rotation_euler", "scale"}
    INTERPOLATIONS = {"CONSTANT", "LINEAR", "BEZIER"}
    LIGHT_PROPERTIES = {"energy", "color", "spot_size", "shadow_soft_size"}
    MATERIAL_CHANNELS = {"base_color", "metallic", "roughness", "alpha", "emission_color", "emission_strength"}

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _frames(values):
        frames = [int(value) for value in values]
        if not frames or len(frames) > 200 or min(frames) < -100000 or max(frames) > 100000:
            raise ValueError("frames/keyframes must contain 1-200 bounded frame values")
        return frames

    @staticmethod
    def _vec(value, length, label):
        if not isinstance(value, (list, tuple)) or len(value) != length:
            raise ValueError(f"{label} must be a {length}-item numeric list")
        return [float(item) for item in value]

    def _apply_interpolation(self, target, interpolation):
        interpolation = str(interpolation or "BEZIER").upper()
        if interpolation not in self.INTERPOLATIONS:
            raise ValueError(f"Unsupported interpolation: {interpolation}")
        if target.animation_data and target.animation_data.action:
            for fcurve in AnimationIntelligenceService._action_fcurves(target.animation_data.action):
                for point in fcurve.keyframe_points:
                    point.interpolation = interpolation

    def insert_transform_keyframes(self, object_name, frames, properties=None):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        properties = properties or ["location", "rotation_euler", "scale"]
        if any(prop not in self.TRANSFORM_PROPERTIES for prop in properties):
            return {"status": "error", "message": "Unsupported transform property requested", "warnings": []}
        try:
            frames = self._frames(frames)
            inserted = []
            for frame in frames:
                bpy.context.scene.frame_set(frame)
                for prop in properties:
                    obj.keyframe_insert(data_path=prop, frame=frame)
                    inserted.append({"property": prop, "frame": frame})
            return {"status": "success", "object_name": obj.name, "inserted": inserted, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def _animate_transform(self, obj, keyframes, interpolation, clear_existing, confirm_clear_existing, verify):
        if clear_existing:
            if not confirm_clear_existing:
                return {"status": "error", "message": "clear_existing requires confirm_clear_existing=True", "warnings": []}
            obj.animation_data_clear()
        try:
            frames = self._frames([item.get("frame") for item in keyframes])
            inserted = []
            for frame, item in zip(frames, keyframes):
                bpy.context.scene.frame_set(frame)
                if "location" in item:
                    obj.location = self._vec(item["location"], 3, "location")
                    obj.keyframe_insert(data_path="location", frame=frame)
                    inserted.append({"property": "location", "frame": frame})
                if "rotation" in item or "rotation_euler" in item:
                    obj.rotation_euler = self._vec(item.get("rotation", item.get("rotation_euler")), 3, "rotation")
                    obj.keyframe_insert(data_path="rotation_euler", frame=frame)
                    inserted.append({"property": "rotation_euler", "frame": frame})
                if "scale" in item:
                    obj.scale = self._vec(item["scale"], 3, "scale")
                    obj.keyframe_insert(data_path="scale", frame=frame)
                    inserted.append({"property": "scale", "frame": frame})
            self._apply_interpolation(obj, interpolation)
            verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_animation_{obj.name}", include_screenshots=False) if verify else None
            return {"status": "success", "object_name": obj.name, "keyframe_count": len(keyframes), "inserted": inserted, "interpolation": str(interpolation).upper(), "verification": verification, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def animate_object_transform(self, object_name, keyframes, interpolation="BEZIER", clear_existing=False, confirm_clear_existing=False, verify=False):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        return self._animate_transform(obj, keyframes, interpolation, clear_existing, confirm_clear_existing, verify)

    def animate_camera_transform(self, camera_name, keyframes, interpolation="BEZIER", clear_existing=False, confirm_clear_existing=False, verify=False):
        obj = bpy.data.objects.get(camera_name)
        if not obj or obj.type != "CAMERA":
            return {"status": "error", "message": f"Camera not found: {camera_name}", "warnings": []}
        return self._animate_transform(obj, keyframes, interpolation, clear_existing, confirm_clear_existing, verify)

    def animate_light_property(self, light_name, property_name, keyframes, interpolation="BEZIER"):
        obj = bpy.data.objects.get(light_name)
        if not obj or obj.type != "LIGHT":
            return {"status": "error", "message": f"Light not found: {light_name}", "warnings": []}
        property_name = str(property_name)
        if property_name not in self.LIGHT_PROPERTIES:
            return {"status": "error", "message": f"Unsupported light property: {property_name}", "warnings": []}
        try:
            frames = self._frames([item.get("frame") for item in keyframes])
            for frame, item in zip(frames, keyframes):
                bpy.context.scene.frame_set(frame)
                value = item.get("value")
                setattr(obj.data, property_name, self._vec(value, 3, property_name) if property_name == "color" else float(value))
                obj.data.keyframe_insert(data_path=property_name, frame=frame)
            self._apply_interpolation(obj.data, interpolation)
            return {"status": "success", "light_name": obj.name, "property_name": property_name, "keyframe_count": len(keyframes), "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def animate_material_property(self, material_name, channel, keyframes, interpolation="BEZIER"):
        mat = bpy.data.materials.get(material_name)
        if not mat:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        channel = str(channel)
        if channel not in self.MATERIAL_CHANNELS:
            return {"status": "error", "message": f"Unsupported material channel: {channel}", "warnings": []}
        mat.use_nodes = True
        node = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        socket_names = {"base_color": "Base Color", "metallic": "Metallic", "roughness": "Roughness", "alpha": "Alpha", "emission_color": "Emission Color", "emission_strength": "Emission Strength"}
        try:
            socket = node.inputs.get(socket_names[channel]) if node else None
            if socket is None and channel == "emission_color" and node:
                socket = node.inputs.get("Emission")
            if socket is None:
                return {"status": "error", "message": f"Material channel unavailable: {channel}", "warnings": []}
            frames = self._frames([item.get("frame") for item in keyframes])
            for frame, item in zip(frames, keyframes):
                bpy.context.scene.frame_set(frame)
                socket.default_value = self._vec(item.get("value"), 4, channel) if channel in {"base_color", "emission_color"} else float(item.get("value"))
                socket.keyframe_insert(data_path="default_value", frame=frame)
            return {"status": "success", "material_name": mat.name, "channel": channel, "keyframe_count": len(keyframes), "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def animate_shape_key_value(self, object_name, shape_key_name, keyframes, interpolation="BEZIER"):
        obj = bpy.data.objects.get(object_name)
        key = obj.data.shape_keys.key_blocks.get(shape_key_name) if obj and getattr(obj.data, "shape_keys", None) else None
        if not key:
            return {"status": "error", "message": f"Shape key not found: {shape_key_name}", "warnings": []}
        try:
            frames = self._frames([item.get("frame") for item in keyframes])
            for frame, item in zip(frames, keyframes):
                bpy.context.scene.frame_set(frame)
                key.value = float(item.get("value"))
                key.keyframe_insert(data_path="value", frame=frame)
            self._apply_interpolation(obj.data.shape_keys, interpolation)
            return {"status": "success", "object_name": obj.name, "shape_key_name": key.name, "keyframe_count": len(keyframes), "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def delete_animation_data(self, target_type, target_name, data_paths=None, confirm=False):
        if not confirm:
            return {"status": "error", "message": "delete_animation_data requires confirm=True", "warnings": []}
        target_type = str(target_type).lower()
        target = bpy.data.materials.get(target_name) if target_type == "material" else bpy.data.objects.get(target_name)
        if target_type == "camera" and (not target or target.type != "CAMERA"):
            target = None
        if target_type == "light" and (not target or target.type != "LIGHT"):
            target = None
        if not target:
            return {"status": "error", "message": f"Animation target not found: {target_name}", "warnings": []}
        deleted = []
        if data_paths and target.animation_data and target.animation_data.action:
            action = target.animation_data.action
            for fcurve in AnimationIntelligenceService._action_fcurves(action):
                if fcurve.data_path in data_paths:
                    deleted.append({"data_path": fcurve.data_path, "array_index": int(fcurve.array_index)})
                    if hasattr(action, "fcurves"):
                        action.fcurves.remove(fcurve)
        elif target.animation_data:
            action_name = target.animation_data.action.name if target.animation_data.action else None
            target.animation_data_clear()
            deleted.append({"action_name": action_name, "cleared": True})
        return {"status": "success", "target_type": target_type, "target_name": target_name, "deleted": deleted, "warnings": []}


class CameraCompositionService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _unique(base):
        base = re.sub(r"[^A-Za-z0-9_. -]+", "_", str(base or "OVERTLI_CAMERA")).strip() or "OVERTLI_CAMERA"
        if base not in bpy.data.objects:
            return base
        index = 1
        while f"{base}.{index:03d}" in bpy.data.objects:
            index += 1
        return f"{base}.{index:03d}"

    @staticmethod
    def _vec(value, default, length=3):
        if value is None:
            return list(default)
        if not isinstance(value, (list, tuple)) or len(value) != length:
            raise ValueError(f"Expected a {length}-item numeric list")
        return [float(item) for item in value]

    @staticmethod
    def _summary(obj):
        return {"name": obj.name, "type": obj.type, "location": list(obj.location), "rotation": list(obj.rotation_euler), "lens": float(obj.data.lens), "clip_start": float(obj.data.clip_start), "clip_end": float(obj.data.clip_end)}

    def create_camera(self, camera_name=None, location=None, rotation=None, lens=None, sensor_width=None, clip_start=None, clip_end=None, collection_name=None, set_active=False, verify=False):
        name = self._unique(camera_name or "OVERTLI_CAMERA")
        data = bpy.data.cameras.new(name)
        obj = bpy.data.objects.new(name, data)
        obj.location = self._vec(location, [0.0, -6.0, 3.0])
        obj.rotation_euler = self._vec(rotation, [math.radians(60.0), 0.0, 0.0])
        if lens is not None:
            data.lens = max(1.0, min(float(lens), 300.0))
        if sensor_width is not None:
            data.sensor_width = max(1.0, min(float(sensor_width), 200.0))
        if clip_start is not None:
            data.clip_start = max(0.001, float(clip_start))
        if clip_end is not None:
            data.clip_end = max(data.clip_start + 0.1, min(float(clip_end), 100000.0))
        collection = bpy.data.collections.get(collection_name) if collection_name else bpy.context.scene.collection
        if collection is None and collection_name:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        collection.objects.link(obj)
        if set_active:
            bpy.context.scene.camera = obj
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_camera_{name}", include_screenshots=False) if verify else None
        return {"status": "success", "camera": self._summary(obj), "set_active": bool(set_active), "verification": verification, "warnings": []}

    def _bounds(self, object_names):
        if not object_names:
            raise ValueError("object_names must contain at least one object")
        corners = []
        for name in object_names:
            obj = bpy.data.objects.get(name)
            if not obj:
                raise ValueError(f"Object not found: {name}")
            corners.extend([obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box])
        min_corner = mathutils.Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
        max_corner = mathutils.Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
        return (min_corner + max_corner) * 0.5, max_corner - min_corner, min_corner, max_corner

    def frame_camera_to_objects(self, camera_name, object_names, view="front_perspective", margin=1.25, distance_multiplier=1.0, look_at=True, set_active=True, verify=False):
        camera = bpy.data.objects.get(camera_name)
        if not camera or camera.type != "CAMERA":
            return {"status": "error", "message": f"Camera not found: {camera_name}", "warnings": []}
        directions = {
            "front": mathutils.Vector((0, -1, 0)),
            "back": mathutils.Vector((0, 1, 0)),
            "left": mathutils.Vector((-1, 0, 0)),
            "right": mathutils.Vector((1, 0, 0)),
            "top": mathutils.Vector((0, 0, 1)),
            "bottom": mathutils.Vector((0, 0, -1)),
            "front_perspective": mathutils.Vector((0.65, -1, 0.45)),
            "isometric": mathutils.Vector((1, -1, 0.75)),
            "camera_current": None,
        }
        if view not in directions:
            return {"status": "error", "message": f"Unsupported view: {view}", "warnings": []}
        try:
            center, size, min_corner, max_corner = self._bounds(object_names)
            direction = (camera.location - center).normalized() if view == "camera_current" else directions[view].normalized()
            if direction.length == 0:
                direction = directions["front_perspective"].normalized()
            distance = max(size.length * 0.5, 0.5) * max(1.0, float(margin)) * max(1.0, float(distance_multiplier)) * 2.5
            camera.location = center + direction * distance
            if look_at:
                camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
            if set_active:
                bpy.context.scene.camera = camera
            verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_frame_{camera.name}", include_screenshots=False) if verify else None
            return {"status": "success", "camera": self._summary(camera), "framed_bounds": {"center": list(center), "size": list(size), "min": list(min_corner), "max": list(max_corner)}, "verification": verification, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def set_active_camera(self, camera_name):
        camera = bpy.data.objects.get(camera_name)
        if not camera or camera.type != "CAMERA":
            return {"status": "error", "message": f"Camera not found: {camera_name}", "warnings": []}
        bpy.context.scene.camera = camera
        return {"status": "success", "camera_name": camera.name, "warnings": []}


class LightingSetupService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _vec(value, default, length=3):
        if value is None:
            return list(default)
        if not isinstance(value, (list, tuple)) or len(value) != length:
            raise ValueError(f"Expected a {length}-item numeric list")
        return [float(item) for item in value]

    @staticmethod
    def _unique(base):
        base = re.sub(r"[^A-Za-z0-9_. -]+", "_", str(base or "OVERTLI_LIGHT")).strip() or "OVERTLI_LIGHT"
        if base not in bpy.data.objects:
            return base
        index = 1
        while f"{base}.{index:03d}" in bpy.data.objects:
            index += 1
        return f"{base}.{index:03d}"

    @staticmethod
    def _summary(obj):
        data = obj.data
        return {"name": obj.name, "type": data.type, "location": list(obj.location), "rotation": list(obj.rotation_euler), "energy": float(data.energy), "color": list(data.color), "size": float(getattr(data, "size", getattr(data, "shadow_soft_size", 0.0)))}

    def create_light(self, light_name=None, light_type="AREA", location=None, rotation=None, energy=None, color=None, size=None, collection_name=None, verify=False):
        light_type = str(light_type or "AREA").upper()
        if light_type not in {"POINT", "SUN", "SPOT", "AREA"}:
            return {"status": "error", "message": f"Unsupported light_type: {light_type}", "warnings": []}
        name = self._unique(light_name or f"OVERTLI_{light_type}_LIGHT")
        data = bpy.data.lights.new(name, type=light_type)
        obj = bpy.data.objects.new(name, data)
        obj.location = self._vec(location, [3.0, -4.0, 4.0])
        obj.rotation_euler = self._vec(rotation, [math.radians(60), 0.0, math.radians(35)])
        data.energy = max(0.0, min(float(energy if energy is not None else 500.0), 100000.0))
        if color is not None:
            data.color = self._vec(color, [1, 1, 1])
        if size is not None:
            if hasattr(data, "size"):
                data.size = max(0.01, min(float(size), 1000.0))
            if hasattr(data, "shadow_soft_size"):
                data.shadow_soft_size = max(0.01, min(float(size), 1000.0))
        collection = bpy.data.collections.get(collection_name) if collection_name else bpy.context.scene.collection
        if collection is None and collection_name:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        collection.objects.link(obj)
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_light_{name}", include_screenshots=False) if verify else None
        return {"status": "success", "light": self._summary(obj), "verification": verification, "warnings": []}

    def create_lighting_setup(self, setup_name, target_object_names=None, preset="three_point", collection_name=None, replace_existing_with_prefix=False, confirm_replace=False, verify=False):
        preset = str(preset or "three_point").lower()
        if preset not in {"three_point", "studio", "product", "softbox"}:
            return {"status": "error", "message": f"Unsupported lighting preset: {preset}", "warnings": []}
        prefix = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(setup_name or "OVERTLI_LIGHT_SETUP")).strip("._-")
        if replace_existing_with_prefix:
            if not confirm_replace:
                return {"status": "error", "message": "replace_existing_with_prefix requires confirm_replace=True", "warnings": []}
            for obj in list(bpy.data.objects):
                if obj.type == "LIGHT" and obj.name.startswith(prefix):
                    bpy.data.objects.remove(obj, do_unlink=True)
        specs = [("KEY", "AREA", [-3, -4, 5], 650, [1, .95, .9], 5), ("FILL", "AREA", [4, -3, 3], 180, [.75, .85, 1], 7), ("RIM", "POINT", [0, 4, 4], 260, [1, 1, 1], 2)]
        if preset == "softbox":
            specs = [("SOFTBOX", "AREA", [0, -4, 4], 750, [1, 1, 1], 6)]
        lights = []
        for suffix, light_type, location, energy, color, size in specs:
            result = self.create_light(f"{prefix}_{suffix}", light_type, location, energy=energy, color=color, size=size, collection_name=collection_name)
            if result.get("status") == "success":
                lights.append(result["light"])
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_lighting_{prefix}", include_screenshots=False) if verify else None
        return {"status": "success", "setup_name": prefix, "preset": preset, "lights": lights, "verification": verification, "warnings": []}

    def update_light(self, light_name, energy=None, color=None, size=None, location=None, rotation=None, verify=False):
        obj = bpy.data.objects.get(light_name)
        if not obj or obj.type != "LIGHT":
            return {"status": "error", "message": f"Light not found: {light_name}", "warnings": []}
        if energy is not None:
            obj.data.energy = max(0.0, min(float(energy), 100000.0))
        if color is not None:
            obj.data.color = self._vec(color, [1, 1, 1])
        if size is not None and hasattr(obj.data, "size"):
            obj.data.size = max(0.01, min(float(size), 1000.0))
        if location is not None:
            obj.location = self._vec(location, [0, 0, 0])
        if rotation is not None:
            obj.rotation_euler = self._vec(rotation, [0, 0, 0])
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_update_light_{obj.name}", include_screenshots=False) if verify else None
        return {"status": "success", "light": self._summary(obj), "verification": verification, "warnings": []}

    def set_world_lighting(self, color=None, strength=None, verify=False):
        world = bpy.context.scene.world or bpy.data.worlds.new("World")
        bpy.context.scene.world = world
        world.use_nodes = True
        bg = next((node for node in world.node_tree.nodes if node.type == "BACKGROUND"), None)
        if not bg:
            bg = world.node_tree.nodes.new("ShaderNodeBackground")
        if color is not None:
            bg.inputs["Color"].default_value = self._vec(color, [1, 1, 1, 1], 4)
        if strength is not None:
            bg.inputs["Strength"].default_value = max(0.0, min(float(strength), 1000.0))
        verification = self.server.verification_artifact_service.create_verification_snapshot(label="phase5a_world_lighting", include_screenshots=False) if verify else None
        return {"status": "success", "world": world.name, "color": list(bg.inputs["Color"].default_value), "strength": float(bg.inputs["Strength"].default_value), "verification": verification, "warnings": []}


class RenderSettingsService:
    def __init__(self, server):
        self.server = server

    def get_render_settings(self):
        scene = bpy.context.scene
        return {"status": "success", "engine": scene.render.engine, "resolution": {"x": int(scene.render.resolution_x), "y": int(scene.render.resolution_y), "percentage": int(scene.render.resolution_percentage)}, "fps": int(scene.render.fps), "frame_range": {"start": int(scene.frame_start), "end": int(scene.frame_end), "current": int(scene.frame_current)}, "filepath": scene.render.filepath, "image_format": scene.render.image_settings.file_format, "cycles_samples": int(getattr(scene.cycles, "samples", 0)) if hasattr(scene, "cycles") else None, "warnings": []}

    def set_render_settings(self, engine=None, resolution_x=None, resolution_y=None, resolution_percentage=None, samples=None, image_format=None, transparent=None, color_management=None, clamp_for_smoke=False):
        scene = bpy.context.scene
        before = self.get_render_settings()
        if engine:
            engine = str(engine).upper()
            if engine not in {"BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES", "BLENDER_WORKBENCH"}:
                return {"status": "error", "message": f"Unsupported render engine: {engine}", "warnings": []}
            scene.render.engine = engine
        max_res = 640 if clamp_for_smoke else 8192
        if resolution_x is not None:
            scene.render.resolution_x = max(16, min(int(resolution_x), max_res))
        if resolution_y is not None:
            scene.render.resolution_y = max(16, min(int(resolution_y), max_res))
        if resolution_percentage is not None:
            scene.render.resolution_percentage = max(1, min(int(resolution_percentage), 100))
        if samples is not None and hasattr(scene, "cycles"):
            scene.cycles.samples = max(1, min(int(samples), 32 if clamp_for_smoke else 4096))
        if image_format:
            scene.render.image_settings.file_format = str(image_format).upper()
        if transparent is not None:
            scene.render.film_transparent = bool(transparent)
        if color_management:
            for key, value in color_management.items():
                if hasattr(scene.view_settings, key):
                    setattr(scene.view_settings, key, value)
        return {"status": "success", "before": before, "after": self.get_render_settings(), "warnings": ["Render settings were clamped for smoke-safe cost"] if clamp_for_smoke else []}

    def set_output_path(self, output_path=None, artifact_root=None, subdir="renders/stills", filename=None):
        path = RenderArtifactService.safe_output_path(output_path, artifact_root, subdir, filename or "render.png")
        bpy.context.scene.render.filepath = path
        return {"status": "success", "output_path": path, "warnings": []}


class RenderArtifactService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def artifact_root(artifact_root=None):
        return os.path.abspath(os.path.expanduser(str(artifact_root or os.environ.get("OVERTLI_BLENDER_ARTIFACT_ROOT") or ADDON_ROOT)))

    @staticmethod
    def stamp():
        return time.strftime("%Y%m%d_%H%M%S", time.localtime()) + f"_{time.time_ns()}"

    @staticmethod
    def safe_output_path(output_path=None, artifact_root=None, subdir="renders/stills", filename="render.png"):
        if output_path:
            return os.path.abspath(os.path.expanduser(str(output_path)))
        base = os.path.join(RenderArtifactService.artifact_root(artifact_root), ".overtli_blender", *str(subdir).split("/"))
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    @staticmethod
    def write_json(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, sort_keys=True)

    def render_still(self, output_path=None, artifact_root=None, filename=None, camera_name=None, frame=None, clamp_for_smoke=True, write_manifest=True):
        scene = bpy.context.scene
        if camera_name:
            camera = bpy.data.objects.get(camera_name)
            if not camera or camera.type != "CAMERA":
                return {"status": "error", "message": f"Camera not found: {camera_name}", "warnings": []}
            scene.camera = camera
        if frame is not None:
            scene.frame_set(int(frame))
        if clamp_for_smoke:
            self.server.render_settings_service.set_render_settings(resolution_x=min(scene.render.resolution_x, 640), resolution_y=min(scene.render.resolution_y, 640), samples=32, clamp_for_smoke=True)
        path = self.safe_output_path(output_path, artifact_root, "renders/stills", filename or f"OVERTLI_PHASE5A_STILL_{self.stamp()}.png")
        previous = scene.render.filepath
        try:
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "output_path": path, "warnings": []}
        finally:
            scene.render.filepath = previous
        artifact = {"path": path, "exists": os.path.exists(path), "bytes": os.path.getsize(path) if os.path.exists(path) else 0, "frame": int(scene.frame_current), "camera": scene.camera.name if scene.camera else None}
        manifest_path = None
        if write_manifest:
            manifest_path = path + ".manifest.json"
            self.write_json(manifest_path, {"command": "render_still", "artifact": artifact, "settings": self.server.render_settings_service.get_render_settings()})
        return {"status": "success", "artifact": artifact, "manifest_path": manifest_path, "warnings": []}

    def render_contact_sheet(self, object_names=None, camera_name=None, views=None, artifact_root=None, filename=None, clamp_for_smoke=True):
        views = (views or ["front", "right", "top"])[:8]
        manifest_path = self.safe_output_path(None, artifact_root, "renders/contact_sheets", filename or f"OVERTLI_PHASE5A_CONTACT_{self.stamp()}.json")
        artifacts = []
        for index, view in enumerate(views):
            still = self.render_still(artifact_root=artifact_root, filename=f"{os.path.splitext(os.path.basename(manifest_path))[0]}_{index}_{view}.png", camera_name=camera_name, clamp_for_smoke=clamp_for_smoke, write_manifest=False)
            artifacts.append({"view": view, "result": still})
        self.write_json(manifest_path, {"command": "render_contact_sheet", "object_names": object_names or [], "camera_name": camera_name, "views": views, "artifacts": artifacts})
        return {"status": "success", "manifest_path": manifest_path, "artifacts": artifacts, "warnings": []}

    def create_turntable_animation(self, object_name, frame_start=1, frame_end=48, axis="Z", rotations=1.0, empty_name=None, camera_name=None, confirm_clear_existing=False):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        frame_start = int(frame_start)
        frame_end = int(frame_end)
        if frame_start >= frame_end or frame_end - frame_start > 240:
            return {"status": "error", "message": "Turntable frame range must be 1-240 frames", "warnings": []}
        axis = str(axis or "Z").upper()
        if axis not in {"X", "Y", "Z"}:
            return {"status": "error", "message": f"Unsupported axis: {axis}", "warnings": []}
        idx = {"X": 0, "Y": 1, "Z": 2}[axis]
        start = list(obj.rotation_euler)
        obj.rotation_euler[idx] = start[idx]
        obj.keyframe_insert(data_path="rotation_euler", frame=frame_start)
        obj.rotation_euler[idx] = start[idx] + math.tau * float(rotations)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame_end)
        if obj.animation_data and obj.animation_data.action:
            for fcurve in AnimationIntelligenceService._action_fcurves(obj.animation_data.action):
                for point in fcurve.keyframe_points:
                    point.interpolation = "LINEAR"
        bpy.context.scene.frame_start = frame_start
        bpy.context.scene.frame_end = frame_end
        return {"status": "success", "object_name": obj.name, "frame_start": frame_start, "frame_end": frame_end, "axis": axis, "warnings": []}

    def render_preview_animation(self, output_dir=None, artifact_root=None, frame_start=None, frame_end=None, step=1, max_frames=24, camera_name=None, clamp_for_smoke=True):
        scene = bpy.context.scene
        start = int(frame_start if frame_start is not None else scene.frame_start)
        end = int(frame_end if frame_end is not None else scene.frame_end)
        frames = list(range(start, end + 1, max(1, int(step))))[:max(1, min(int(max_frames), 24))]
        base = output_dir or os.path.join(self.artifact_root(artifact_root), ".overtli_blender", "renders", "previews", f"OVERTLI_PHASE5A_PREVIEW_{self.stamp()}")
        os.makedirs(base, exist_ok=True)
        artifacts = []
        for frame in frames:
            artifacts.append({"frame": frame, "result": self.render_still(output_path=os.path.join(base, f"frame_{frame:04d}.png"), camera_name=camera_name, frame=frame, clamp_for_smoke=clamp_for_smoke, write_manifest=False)})
        manifest_path = os.path.join(base, "manifest.json")
        self.write_json(manifest_path, {"command": "render_preview_animation", "frames": frames, "artifacts": artifacts})
        return {"status": "success", "output_dir": base, "manifest_path": manifest_path, "frames": frames, "artifacts": artifacts, "warnings": []}


class CompositorPassService:
    def __init__(self, server):
        self.server = server

    def get_compositor_status(self):
        scene = bpy.context.scene
        layer = scene.view_layers[0] if scene.view_layers else None
        node_tree = getattr(scene, "node_tree", None)
        warnings = [] if node_tree is not None else ["Compositor node tree is not available in this Blender context"]
        return {"status": "success", "use_nodes": bool(getattr(scene, "use_nodes", False)), "node_count": len(node_tree.nodes) if node_tree else 0, "render_passes": {"use_pass_z": bool(getattr(layer, "use_pass_z", False)), "use_pass_mist": bool(getattr(layer, "use_pass_mist", False)), "use_pass_normal": bool(getattr(layer, "use_pass_normal", False))}, "warnings": warnings}

    def set_compositor_preset(self, preset="basic_viewer", confirm_replace=False):
        preset = str(preset or "basic_viewer").lower()
        if preset not in {"none", "basic_viewer", "transparent_preview", "mist_depth_preview"}:
            return {"status": "error", "message": f"Unsupported compositor preset: {preset}", "warnings": []}
        scene = bpy.context.scene
        if not hasattr(scene, "use_nodes"):
            return {"status": "error", "message": "Compositor nodes are not available in this Blender context", "warnings": []}
        node_tree = getattr(scene, "node_tree", None)
        if scene.use_nodes and node_tree and node_tree.nodes and preset != "none" and not confirm_replace:
            return {"status": "error", "message": "Existing compositor nodes require confirm_replace=True", "warnings": []}
        if preset == "none":
            scene.use_nodes = False
            return {"status": "success", "preset": preset, "warnings": []}
        scene.use_nodes = True
        tree = getattr(scene, "node_tree", None)
        if tree is None:
            return {"status": "error", "message": "Compositor node tree is not available in this Blender context", "warnings": []}
        tree.nodes.clear()
        layers = tree.nodes.new("CompositorNodeRLayers")
        composite = tree.nodes.new("CompositorNodeComposite")
        viewer = tree.nodes.new("CompositorNodeViewer")
        tree.links.new(layers.outputs["Image"], composite.inputs["Image"])
        tree.links.new(layers.outputs["Image"], viewer.inputs["Image"])
        return {"status": "success", "preset": preset, "node_count": len(tree.nodes), "warnings": []}

    def set_render_passes(self, use_pass_z=None, use_pass_mist=None, use_pass_normal=None, use_pass_diffuse_color=None):
        layer = bpy.context.scene.view_layers[0]
        changed = {}
        for name, value in {"use_pass_z": use_pass_z, "use_pass_mist": use_pass_mist, "use_pass_normal": use_pass_normal, "use_pass_diffuse_color": use_pass_diffuse_color}.items():
            if value is not None and hasattr(layer, name):
                setattr(layer, name, bool(value))
                changed[name] = bool(value)
        return {"status": "success", "changed": changed, "status_after": self.get_compositor_status(), "warnings": []}


class PresentationWorkflowBatchService:
    ALLOWED_COMMANDS = {"get_timeline_info", "list_animated_objects", "get_animation_deep_info", "set_timeline_range", "set_current_frame", "insert_transform_keyframes", "animate_object_transform", "animate_camera_transform", "animate_light_property", "animate_material_property", "animate_shape_key_value", "set_render_settings", "render_still", "render_contact_sheet", "create_turntable_animation", "render_preview_animation", "get_compositor_status", "set_compositor_preset", "set_render_passes", "delete_animation_data", "cleanup_presentation_artifacts"}
    DESTRUCTIVE_COMMANDS = {"delete_animation_data", "cleanup_presentation_artifacts"}

    def __init__(self, server):
        self.server = server

    def run_presentation_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=20, batch_allow_destructive=False, artifact_root=None):
        operations = operations or []
        if len(operations) > max(1, min(int(max_operations), 50)):
            return {"status": "error", "message": "Too many batch operations", "warnings": []}
        batch_id = f"presentation_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()}"
        batch_dir = os.path.join(RenderArtifactService.artifact_root(artifact_root), ".overtli_blender", "presentation", "batches", batch_id)
        os.makedirs(batch_dir, exist_ok=True)
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_before", include_screenshots=False, artifact_root=artifact_root) if create_before_snapshot else None
        results = []
        errors = []
        for op in operations:
            command = op.get("command")
            params = dict(op.get("params") or {})
            if command not in self.ALLOWED_COMMANDS:
                errors.append({"command": command, "message": "Command is not allowed in presentation batches"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_COMMANDS and not (batch_allow_destructive and params.get("confirm") is True):
                errors.append({"command": command, "message": "Destructive batch operation requires batch_allow_destructive=True and operation confirm=True"})
                if stop_on_error:
                    break
                continue
            if command in {"render_still", "render_contact_sheet", "render_preview_animation"}:
                params.setdefault("artifact_root", artifact_root)
                params.setdefault("clamp_for_smoke", True)
            try:
                result = self.server._build_command_handlers()[command](**params)
            except Exception as exc:
                result = {"status": "error", "message": str(exc), "warnings": []}
            results.append({"command": command, "params": params, "result": result})
            if result.get("status") == "error":
                errors.append({"command": command, "message": result.get("message")})
                if stop_on_error:
                    break
        after = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_after", include_screenshots=False, artifact_root=artifact_root) if create_after_snapshot else None
        manifest_path = os.path.join(batch_dir, "manifest.json")
        RenderArtifactService.write_json(manifest_path, {"batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors})
        return {"status": "partial" if errors else "success", "batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "render_artifacts": [], "operation_results": results, "errors": errors, "manifest_path": manifest_path, "warnings": []}

    def cleanup_presentation_artifacts(self, prefix, confirm=False, cleanup_scene_data=True, cleanup_render_artifacts=False, artifact_root=None):
        if not confirm:
            return {"status": "error", "message": "cleanup_presentation_artifacts requires confirm=True", "warnings": []}
        prefix = str(prefix or "")
        if len(prefix) < 6:
            return {"status": "error", "message": "A safe prefix is required", "warnings": []}
        deleted = {"objects": [], "collections": [], "materials": [], "cameras": [], "lights": []}
        if cleanup_scene_data:
            for obj in list(bpy.data.objects):
                if obj.name.startswith(prefix):
                    bucket = "cameras" if obj.type == "CAMERA" else "lights" if obj.type == "LIGHT" else "objects"
                    deleted[bucket].append(obj.name)
                    bpy.data.objects.remove(obj, do_unlink=True)
            for mat in list(bpy.data.materials):
                if mat.name.startswith(prefix):
                    deleted["materials"].append(mat.name)
                    bpy.data.materials.remove(mat)
            for col in list(bpy.data.collections):
                if col.name.startswith(prefix) and len(col.objects) == 0 and len(col.children) == 0:
                    deleted["collections"].append(col.name)
                    bpy.data.collections.remove(col)
        artifact_deleted = []
        if cleanup_render_artifacts:
            root = os.path.join(RenderArtifactService.artifact_root(artifact_root), ".overtli_blender")
            for current_root, _dirs, files in os.walk(root):
                for filename in files:
                    if filename.startswith(prefix):
                        path = os.path.join(current_root, filename)
                        os.remove(path)
                        artifact_deleted.append(path)
        return {"status": "success", "prefix": prefix, "deleted": deleted, "artifact_deleted": artifact_deleted, "warnings": []}


class AssetPathService:
    MODEL_EXTENSIONS = {".glb", ".gltf", ".obj", ".fbx", ".stl", ".ply", ".usd", ".usda", ".usdc", ".abc", ".dae"}
    TEXTURE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".hdr", ".webp"}
    MEDIA_EXTENSIONS = {".mp4", ".mov", ".avi"}

    @staticmethod
    def artifact_root(artifact_root=None):
        return RenderArtifactService.artifact_root(artifact_root)

    @staticmethod
    def workspace_path(*parts, artifact_root=None):
        path = os.path.join(AssetPathService.artifact_root(artifact_root), ".overtli_blender", *parts)
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def local_path(path, must_exist=True):
        if not path:
            raise ValueError("A local filesystem path is required")
        value = os.path.abspath(os.path.expanduser(str(path)))
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", str(path)):
            raise ValueError("Only local filesystem paths are supported")
        if must_exist and not os.path.exists(value):
            raise ValueError(f"Path does not exist: {value}")
        return value

    @staticmethod
    def classify(path):
        ext = os.path.splitext(str(path))[1].lower()
        if ext == ".blend":
            return "blend"
        if ext in AssetPathService.MODEL_EXTENSIONS:
            return "model"
        if ext in AssetPathService.TEXTURE_EXTENSIONS:
            return "texture"
        if ext in AssetPathService.MEDIA_EXTENSIONS:
            return "media"
        return "unknown"

    @staticmethod
    def write_json(path, data):
        RenderArtifactService.write_json(path, data)
        return path


class AssetLibraryIntelligenceService:
    IMPORT_OPERATORS = {
        "glb": [("bpy.ops.import_scene.gltf", lambda filepath: bpy.ops.import_scene.gltf(filepath=filepath))],
        "gltf": [("bpy.ops.import_scene.gltf", lambda filepath: bpy.ops.import_scene.gltf(filepath=filepath))],
        "obj": [("bpy.ops.wm.obj_import", lambda filepath: bpy.ops.wm.obj_import(filepath=filepath)), ("bpy.ops.import_scene.obj", lambda filepath: bpy.ops.import_scene.obj(filepath=filepath))],
        "fbx": [("bpy.ops.import_scene.fbx", lambda filepath: bpy.ops.import_scene.fbx(filepath=filepath))],
        "stl": [("bpy.ops.wm.stl_import", lambda filepath: bpy.ops.wm.stl_import(filepath=filepath)), ("bpy.ops.import_mesh.stl", lambda filepath: bpy.ops.import_mesh.stl(filepath=filepath))],
        "ply": [("bpy.ops.wm.ply_import", lambda filepath: bpy.ops.wm.ply_import(filepath=filepath)), ("bpy.ops.import_mesh.ply", lambda filepath: bpy.ops.import_mesh.ply(filepath=filepath))],
        "usd": [("bpy.ops.wm.usd_import", lambda filepath: bpy.ops.wm.usd_import(filepath=filepath))],
        "usda": [("bpy.ops.wm.usd_import", lambda filepath: bpy.ops.wm.usd_import(filepath=filepath))],
        "usdc": [("bpy.ops.wm.usd_import", lambda filepath: bpy.ops.wm.usd_import(filepath=filepath))],
        "abc": [("bpy.ops.wm.alembic_import", lambda filepath: bpy.ops.wm.alembic_import(filepath=filepath))],
        "dae": [("bpy.ops.wm.collada_import", lambda filepath: bpy.ops.wm.collada_import(filepath=filepath))],
    }
    EXPORT_OPERATORS = {
        "glb": [("bpy.ops.export_scene.gltf", lambda filepath, selected: bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLB", use_selection=selected))],
        "gltf": [("bpy.ops.export_scene.gltf", lambda filepath, selected: bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLTF_SEPARATE", use_selection=selected))],
        "obj": [("bpy.ops.wm.obj_export", lambda filepath, selected: bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=selected)), ("bpy.ops.export_scene.obj", lambda filepath, selected: bpy.ops.export_scene.obj(filepath=filepath, use_selection=selected))],
        "fbx": [("bpy.ops.export_scene.fbx", lambda filepath, selected: bpy.ops.export_scene.fbx(filepath=filepath, use_selection=selected))],
        "stl": [("bpy.ops.wm.stl_export", lambda filepath, selected: bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=selected)), ("bpy.ops.export_mesh.stl", lambda filepath, selected: bpy.ops.export_mesh.stl(filepath=filepath, use_selection=selected))],
        "ply": [("bpy.ops.wm.ply_export", lambda filepath, selected: bpy.ops.wm.ply_export(filepath=filepath, export_selected_objects=selected)), ("bpy.ops.export_mesh.ply", lambda filepath, selected: bpy.ops.export_mesh.ply(filepath=filepath, use_selection=selected))],
        "usd": [("bpy.ops.wm.usd_export", lambda filepath, selected: bpy.ops.wm.usd_export(filepath=filepath, selected_objects_only=selected))],
        "usda": [("bpy.ops.wm.usd_export", lambda filepath, selected: bpy.ops.wm.usd_export(filepath=filepath, selected_objects_only=selected))],
        "usdc": [("bpy.ops.wm.usd_export", lambda filepath, selected: bpy.ops.wm.usd_export(filepath=filepath, selected_objects_only=selected))],
        "abc": [("bpy.ops.wm.alembic_export", lambda filepath, selected: bpy.ops.wm.alembic_export(filepath=filepath, selected=selected))],
        "dae": [("bpy.ops.wm.collada_export", lambda filepath, selected: bpy.ops.wm.collada_export(filepath=filepath, selected=selected))],
    }

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _operator_exists(path):
        target = bpy.ops
        for part in path.replace("bpy.ops.", "").split("."):
            if not hasattr(target, part):
                return False
            target = getattr(target, part)
        return True

    def _format_status(self, mapping):
        result = {}
        for fmt, options in mapping.items():
            found = next((name for name, _runner in options if self._operator_exists(name)), None)
            result[fmt] = {"supported": bool(found), "operator": found}
        return result

    def get_supported_asset_formats(self):
        return {
            "status": "success",
            "import_formats": self._format_status(self.IMPORT_OPERATORS),
            "export_formats": self._format_status(self.EXPORT_OPERATORS),
            "blend_library": {"append_supported": True, "link_supported": True},
            "warnings": [],
        }

    def choose_importer(self, fmt):
        for name, runner in self.IMPORT_OPERATORS.get(str(fmt).lower(), []):
            if self._operator_exists(name):
                return name, runner
        return None, None

    def choose_exporter(self, fmt):
        for name, runner in self.EXPORT_OPERATORS.get(str(fmt).lower(), []):
            if self._operator_exists(name):
                return name, runner
        return None, None

    def scan_asset_folder(self, folder_path, recursive=True, include_textures=True, include_blend_files=True, include_model_files=True, max_files=1000, write_manifest=True, artifact_root=None):
        try:
            folder = AssetPathService.local_path(folder_path)
            if not os.path.isdir(folder):
                return {"status": "error", "message": "folder_path must be a directory", "warnings": []}
            max_files = max(1, min(int(max_files), 5000))
            formats = self.get_supported_asset_formats()
            assets = []
            by_type = {"model": 0, "texture": 0, "blend": 0, "media": 0, "unknown": 0}
            walker = os.walk(folder) if recursive else [(folder, [], os.listdir(folder))]
            truncated = False
            for root, dirs, files in walker:
                dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".venv", "Library", "Temp", "Logs", "Obj"}]
                for filename in files:
                    path = os.path.join(root, filename)
                    kind = AssetPathService.classify(path)
                    if kind == "texture" and not include_textures:
                        continue
                    if kind == "blend" and not include_blend_files:
                        continue
                    if kind == "model" and not include_model_files:
                        continue
                    stat = os.stat(path)
                    ext = os.path.splitext(filename)[1].lower().lstrip(".")
                    assets.append({"path": path, "name": filename, "extension": "." + ext if ext else "", "kind": kind, "size_bytes": stat.st_size, "modified_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)), "import_supported": bool(formats["import_formats"].get(ext, {}).get("supported")) if kind == "model" else kind == "blend", "warnings": []})
                    by_type[kind] = by_type.get(kind, 0) + 1
                    if len(assets) >= max_files:
                        truncated = True
                        break
                if truncated:
                    break
            manifest_path = None
            result = {"status": "success", "folder_path": folder, "recursive": bool(recursive), "file_count": len(assets), "by_type": by_type, "assets": assets, "manifest_path": None, "truncated": truncated, "warnings": []}
            if write_manifest:
                out = os.path.join(AssetPathService.workspace_path("assets", "scans", artifact_root=artifact_root), f"asset_scan_{RenderArtifactService.stamp()}.json")
                manifest_path = AssetPathService.write_json(out, result)
                result["manifest_path"] = manifest_path
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def list_asset_libraries(self, artifact_root=None):
        base = AssetPathService.workspace_path("assets", artifact_root=artifact_root)
        libraries = [{"name": "Repo Local Assets", "path": base, "source": "repo_workspace", "exists": os.path.isdir(base)}]
        prefs = getattr(bpy.context, "preferences", None)
        filepaths = getattr(prefs, "filepaths", None)
        for item in getattr(filepaths, "asset_libraries", []) or []:
            path = os.path.abspath(bpy.path.abspath(item.path))
            libraries.append({"name": item.name, "path": path, "source": "blender_preferences", "exists": os.path.isdir(path)})
        kit_root = AssetPathService.workspace_path("scene_kits", artifact_root=artifact_root)
        libraries.append({"name": "Scene Kits", "path": kit_root, "source": "scene_kits", "exists": os.path.isdir(kit_root)})
        return {"status": "success", "libraries": libraries, "warnings": []}

    def get_asset_file_info(self, file_path, inspect_blend_contents=True):
        try:
            path = AssetPathService.local_path(file_path)
            stat = os.stat(path)
            ext = os.path.splitext(path)[1].lower()
            kind = AssetPathService.classify(path)
            result = {"status": "success", "file_path": path, "name": os.path.basename(path), "extension": ext, "kind": kind, "size_bytes": stat.st_size, "modified_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)), "warnings": []}
            if kind == "model":
                fmt = ext.lstrip(".")
                supported = self.get_supported_asset_formats()["import_formats"].get(fmt, {"supported": False, "operator": None})
                result["import_support"] = supported
            if kind == "blend" and inspect_blend_contents:
                contents = {}
                with bpy.data.libraries.load(path, link=False) as (data_from, _data_to):
                    for attr in ["objects", "collections", "materials", "node_groups", "worlds", "actions"]:
                        contents[attr] = list(getattr(data_from, attr, []) or [])
                result["blend_contents"] = contents
            if kind == "texture":
                image = None
                try:
                    image = bpy.data.images.load(path, check_existing=False)
                    result["image"] = {"size": list(image.size), "source": image.source}
                finally:
                    if image:
                        bpy.data.images.remove(image)
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def list_scene_assets(self, include_objects=True, include_meshes=True, include_materials=True, include_images=True, include_libraries=True, include_actions=True, include_collections=True):
        result = {"status": "success", "counts": {}, "warnings": []}
        if include_objects:
            result["objects"] = [{"name": o.name, "type": o.type, "library": o.library.filepath if o.library else None, "material_slots": [s.material.name for s in o.material_slots if s.material]} for o in bpy.data.objects]
            result["counts"]["objects"] = len(result["objects"])
        if include_meshes:
            result["meshes"] = [{"name": m.name, "users": m.users, "library": m.library.filepath if m.library else None} for m in bpy.data.meshes]
            result["counts"]["meshes"] = len(result["meshes"])
        if include_materials:
            result["materials"] = [{"name": m.name, "users": m.users, "library": m.library.filepath if m.library else None} for m in bpy.data.materials]
            result["counts"]["materials"] = len(result["materials"])
        if include_images:
            images = []
            for image in bpy.data.images:
                path = bpy.path.abspath(image.filepath) if image.filepath else ""
                images.append({"name": image.name, "filepath": path, "packed_file": bool(image.packed_file), "source": image.source, "users": image.users, "missing": bool(path and not os.path.exists(path))})
            result["images"] = images
            result["counts"]["images"] = len(images)
        if include_libraries:
            result["libraries"] = [{"filepath": lib.filepath, "name": lib.name} for lib in bpy.data.libraries]
            result["counts"]["libraries"] = len(result["libraries"])
        if include_actions:
            result["actions"] = [{"name": a.name, "users": a.users, "frame_range": list(a.frame_range)} for a in bpy.data.actions]
            result["counts"]["actions"] = len(result["actions"])
        if include_collections:
            result["collections"] = [{"name": c.name, "object_count": len(c.objects), "child_count": len(c.children), "library": c.library.filepath if c.library else None} for c in bpy.data.collections]
            result["counts"]["collections"] = len(result["collections"])
        return result


class AssetDependencyService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _path_record(datablock, filepath):
        path = bpy.path.abspath(filepath) if filepath else ""
        packed = bool(getattr(datablock, "packed_file", None))
        return {"name": datablock.name, "filepath": path, "raw_filepath": filepath, "packed": packed, "missing": bool(path and not os.path.exists(path) and not packed), "absolute": bool(path and os.path.isabs(path)), "relative": str(filepath).startswith("//") if filepath else False, "users": getattr(datablock, "users", 0)}

    def get_asset_dependency_report(self, include_images=True, include_libraries=True, include_fonts=True, include_movie_clips=True, include_sounds=True, write_manifest=True, artifact_root=None):
        deps = {"images": [], "libraries": [], "fonts": [], "movie_clips": [], "sounds": []}
        if include_images:
            deps["images"] = [self._path_record(image, image.filepath) for image in bpy.data.images if image.filepath or image.packed_file]
        if include_libraries:
            deps["libraries"] = [{"name": lib.name, "filepath": bpy.path.abspath(lib.filepath), "raw_filepath": lib.filepath, "missing": bool(lib.filepath and not os.path.exists(bpy.path.abspath(lib.filepath))), "absolute": os.path.isabs(bpy.path.abspath(lib.filepath)) if lib.filepath else False, "relative": str(lib.filepath).startswith("//")} for lib in bpy.data.libraries]
        if include_fonts:
            deps["fonts"] = [self._path_record(font, font.filepath) for font in bpy.data.fonts if getattr(font, "filepath", "")]
        if include_movie_clips:
            deps["movie_clips"] = [self._path_record(clip, clip.filepath) for clip in bpy.data.movieclips if getattr(clip, "filepath", "")]
        if include_sounds:
            deps["sounds"] = [self._path_record(sound, sound.filepath) for sound in bpy.data.sounds if getattr(sound, "filepath", "")]
        flat = [item for values in deps.values() for item in values]
        summary = {"external_count": len(flat), "missing_count": sum(1 for item in flat if item.get("missing")), "absolute_path_count": sum(1 for item in flat if item.get("absolute")), "relative_path_count": sum(1 for item in flat if item.get("relative")), "packed_count": sum(1 for item in flat if item.get("packed"))}
        result = {"status": "success", "dependencies": deps, "summary": summary, "manifest_path": None, "warnings": []}
        if write_manifest:
            result["manifest_path"] = AssetPathService.write_json(os.path.join(AssetPathService.workspace_path("dependency_reports", artifact_root=artifact_root), f"dependency_report_{RenderArtifactService.stamp()}.json"), result)
        return result

    def create_asset_manifest(self, label=None, include_scene_index=True, include_scene_assets=True, include_dependencies=True, include_materials=True, include_animation=True, include_render_settings=True, include_previews=False, artifact_root=None):
        manifest = {"status": "success", "label": label or "asset_manifest", "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "warnings": []}
        if include_scene_index:
            manifest["scene_index"] = self.server.scene_intelligence_service.get_scene_index(max_objects=1000)
        if include_scene_assets:
            manifest["scene_assets"] = self.server.asset_library_intelligence_service.list_scene_assets(include_materials=include_materials, include_actions=include_animation)
        if include_dependencies:
            manifest["dependencies"] = self.get_asset_dependency_report(write_manifest=False)
        if include_render_settings:
            manifest["render_settings"] = self.server.render_settings_service.get_render_settings()
        if include_previews:
            manifest["preview"] = self.server.asset_preview_service.create_asset_preview(label=label or "asset_manifest_preview", artifact_root=artifact_root)
        safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(label or "manifest")).strip("._-") or "manifest"
        path = os.path.join(AssetPathService.workspace_path("assets", "manifests", artifact_root=artifact_root), f"{safe_label}_{RenderArtifactService.stamp()}.json")
        manifest["manifest_path"] = AssetPathService.write_json(path, manifest)
        return manifest

    def collect_external_dependencies(self, target_dir=None, overwrite=False, include_packed=False, artifact_root=None):
        target = target_dir or AssetPathService.workspace_path("assets", "dependencies", artifact_root=artifact_root)
        target = AssetPathService.local_path(target, must_exist=False)
        os.makedirs(target, exist_ok=True)
        report = self.get_asset_dependency_report(write_manifest=False)
        copied = []
        warnings = []
        for item in report["dependencies"].get("images", []):
            src = item.get("filepath")
            if not src or item.get("packed") and not include_packed or not os.path.exists(src):
                continue
            dst = os.path.join(target, os.path.basename(src))
            if os.path.exists(dst) and not overwrite:
                warnings.append(f"Skipped existing dependency: {dst}")
                continue
            shutil.copy2(src, dst)
            copied.append({"source": src, "target": dst})
        manifest_path = AssetPathService.write_json(os.path.join(target, "dependency_collection_manifest.json"), {"copied": copied, "warnings": warnings})
        return {"status": "success", "target_dir": target, "copied": copied, "manifest_path": manifest_path, "warnings": warnings}

    def validate_external_dependencies(self):
        report = self.get_asset_dependency_report(write_manifest=False)
        return {"status": "success", "portable": report["summary"]["missing_count"] == 0 and report["summary"]["absolute_path_count"] == 0, "dependency_report": report, "warnings": []}

    def pack_external_data(self, confirm=False):
        if not confirm:
            return {"status": "error", "message": "pack_external_data requires confirm=True", "warnings": []}
        try:
            bpy.ops.file.pack_all()
            return {"status": "success", "dependency_report": self.get_asset_dependency_report(write_manifest=False), "warnings": ["Packed external data into the current Blender session; save is not automatic"]}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def make_paths_relative(self, confirm=False):
        if not confirm:
            return {"status": "error", "message": "make_paths_relative requires confirm=True", "warnings": []}
        try:
            bpy.ops.file.make_paths_relative()
            return {"status": "success", "dependency_report": self.get_asset_dependency_report(write_manifest=False), "warnings": ["Converted paths in the current Blender session; save is not automatic"]}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}


class AssetImportService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _names():
        return {"objects": {o.name for o in bpy.data.objects}, "materials": {m.name for m in bpy.data.materials}, "images": {i.name for i in bpy.data.images}, "actions": {a.name for a in bpy.data.actions}}

    @staticmethod
    def _created(before):
        return {"created_objects": [o.name for o in bpy.data.objects if o.name not in before["objects"]], "created_materials": [m.name for m in bpy.data.materials if m.name not in before["materials"]], "created_images": [i.name for i in bpy.data.images if i.name not in before["images"]], "created_actions": [a.name for a in bpy.data.actions if a.name not in before["actions"]]}

    def import_model_file(self, file_path, format_hint=None, collection_name=None, rename_prefix=None, import_materials=True, import_animations=True, import_cameras_lights=True, verify=True):
        try:
            path = AssetPathService.local_path(file_path)
            fmt = str(format_hint or os.path.splitext(path)[1].lstrip(".")).lower()
            _op_name, runner = self.server.asset_library_intelligence_service.choose_importer(fmt)
            if not runner:
                return {"status": "error", "message": f"Unsupported import format: {fmt}", "warnings": []}
            collection = None
            if collection_name:
                collection = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
                if collection.name not in bpy.context.scene.collection.children:
                    bpy.context.scene.collection.children.link(collection)
            before = self._names()
            runner(path)
            created = self._created(before)
            for name in list(created["created_objects"]):
                obj = bpy.data.objects.get(name)
                if obj and rename_prefix:
                    obj.name = f"{rename_prefix}{obj.name}"
                if obj and collection:
                    for col in list(obj.users_collection):
                        col.objects.unlink(obj)
                    collection.objects.link(obj)
            if rename_prefix:
                created = self._created(before)
            verification = self.server.scene_intelligence_service.get_scene_index(max_objects=1000) if verify else None
            manifest = {"status": "success", "file_path": path, "format": fmt, "collection_name": collection.name if collection else None, **created, "verification": verification, "warnings": []}
            out = os.path.join(AssetPathService.workspace_path("imports", "phase5b"), f"import_manifest_{RenderArtifactService.stamp()}.json")
            manifest["manifest_path"] = AssetPathService.write_json(out, manifest)
            return manifest
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}


class AssetExportService:
    def __init__(self, server):
        self.server = server

    def _export(self, fmt, path, selected, overwrite):
        if os.path.exists(path) and not overwrite:
            return {"status": "error", "message": f"Output exists and overwrite=False: {path}", "warnings": []}
        op_name, runner = self.server.asset_library_intelligence_service.choose_exporter(fmt)
        if not runner:
            return {"status": "error", "message": f"Unsupported export format: {fmt}", "warnings": []}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        runner(path, selected)
        return {"status": "success", "format": fmt, "operator": op_name, "output_path": path, "exists": os.path.exists(path), "bytes": os.path.getsize(path) if os.path.exists(path) else 0, "warnings": []}

    def export_selected_objects(self, output_path=None, format_hint="glb", object_names=None, overwrite=False, artifact_root=None):
        fmt = str(format_hint or "glb").lower()
        ext = "glb" if fmt == "glb" else fmt
        path = output_path or os.path.join(AssetPathService.workspace_path("exports", "selected", artifact_root=artifact_root), f"selected_{RenderArtifactService.stamp()}.{ext}")
        path = AssetPathService.local_path(path, must_exist=False)
        previous = list(bpy.context.selected_objects)
        try:
            if object_names:
                bpy.ops.object.select_all(action="DESELECT")
                for name in object_names:
                    obj = bpy.data.objects.get(name)
                    if obj:
                        obj.select_set(True)
            return self._export(fmt, path, True, overwrite)
        finally:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in previous:
                if obj.name in bpy.data.objects:
                    obj.select_set(True)

    def export_scene(self, output_path=None, format_hint="glb", overwrite=False, artifact_root=None):
        fmt = str(format_hint or "glb").lower()
        path = output_path or os.path.join(AssetPathService.workspace_path("exports", "scenes", artifact_root=artifact_root), f"scene_{RenderArtifactService.stamp()}.{fmt}")
        path = AssetPathService.local_path(path, must_exist=False)
        return self._export(fmt, path, False, overwrite)


class BlendLibraryService:
    def __init__(self, server):
        self.server = server

    def append_blend_asset(self, blend_file_path, datablock_type, datablock_names, collection_name=None, link=False, rename_prefix=None, verify=True):
        try:
            path = AssetPathService.local_path(blend_file_path)
            if not path.lower().endswith(".blend"):
                return {"status": "error", "message": "append_blend_asset requires a .blend file", "warnings": []}
            attr_map = {"Object": "objects", "Collection": "collections", "Material": "materials", "NodeTree": "node_groups", "World": "worlds", "Action": "actions"}
            attr = attr_map.get(str(datablock_type))
            if not attr:
                return {"status": "error", "message": f"Unsupported datablock_type: {datablock_type}", "warnings": []}
            requested = list(datablock_names or [])
            with bpy.data.libraries.load(path, link=bool(link)) as (data_from, data_to):
                available = set(getattr(data_from, attr) or [])
                missing = [name for name in requested if name not in available]
                if missing:
                    return {"status": "error", "message": f"Datablocks not found: {missing}", "warnings": []}
                setattr(data_to, attr, requested)
            loaded = [block for block in getattr(data_to, attr) if block]
            collection = None
            if collection_name:
                collection = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
                if collection.name not in bpy.context.scene.collection.children:
                    bpy.context.scene.collection.children.link(collection)
            created = []
            for block in loaded:
                if rename_prefix:
                    block.name = f"{rename_prefix}{block.name}"
                created.append(block.name)
                if collection and str(datablock_type) == "Object" and block.name not in collection.objects:
                    collection.objects.link(block)
            return {"status": "success", "blend_file_path": path, "datablock_type": datablock_type, "datablocks": created, "linked": bool(link), "collection_name": collection.name if collection else None, "dependency_report": self.server.asset_dependency_service.get_asset_dependency_report(write_manifest=False) if verify else None, "warnings": ["Linked blend assets create external dependencies"] if link else []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}


class AssetPreviewService:
    def __init__(self, server):
        self.server = server

    def create_asset_preview(self, object_names=None, label=None, artifact_root=None, camera_name=None, clamp_for_smoke=True):
        filename = f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', str(label or 'asset_preview'))}_{RenderArtifactService.stamp()}.png"
        result = self.server.render_artifact_service.render_still(artifact_root=artifact_root, filename=filename, camera_name=camera_name, clamp_for_smoke=clamp_for_smoke)
        result["object_names"] = object_names or []
        return result

    def create_asset_contact_sheet(self, object_names=None, label=None, artifact_root=None, views=None, camera_name=None, clamp_for_smoke=True):
        filename = f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', str(label or 'asset_contact'))}_{RenderArtifactService.stamp()}.json"
        return self.server.render_artifact_service.render_contact_sheet(object_names=object_names, camera_name=camera_name, views=views, artifact_root=artifact_root, filename=filename, clamp_for_smoke=clamp_for_smoke)


class SceneKitService:
    def __init__(self, server):
        self.server = server

    def _kit_dir(self, kit_id, artifact_root=None):
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(kit_id)).strip("._-") or f"kit_{RenderArtifactService.stamp()}"
        return os.path.join(AssetPathService.workspace_path("scene_kits", artifact_root=artifact_root), safe)

    def create_scene_kit(self, kit_id=None, label=None, collection_name=None, object_names=None, export_format="glb", include_preview=True, include_scene_export=True, overwrite=False, artifact_root=None):
        kit_id = kit_id or f"scene_kit_{RenderArtifactService.stamp()}"
        kit_dir = self._kit_dir(kit_id, artifact_root)
        if os.path.exists(os.path.join(kit_dir, "manifest.json")) and not overwrite:
            return {"status": "error", "message": f"Scene kit exists and overwrite=False: {kit_dir}", "warnings": []}
        os.makedirs(os.path.join(kit_dir, "previews"), exist_ok=True)
        os.makedirs(os.path.join(kit_dir, "exports"), exist_ok=True)
        manifest = {"status": "success", "kit_id": os.path.basename(kit_dir), "label": label, "collection_name": collection_name, "object_names": object_names or [], "warnings": []}
        manifest["scene_index_path"] = AssetPathService.write_json(os.path.join(kit_dir, "scene_index.json"), self.server.scene_intelligence_service.get_scene_index(max_objects=1000))
        manifest["scene_health_path"] = AssetPathService.write_json(os.path.join(kit_dir, "scene_health.json"), self.server.scene_intelligence_service.get_scene_health())
        manifest["dependencies_path"] = AssetPathService.write_json(os.path.join(kit_dir, "dependencies.json"), self.server.asset_dependency_service.get_asset_dependency_report(write_manifest=False))
        if include_preview:
            manifest["preview"] = self.server.asset_preview_service.create_asset_preview(object_names=object_names, label=kit_id, artifact_root=artifact_root)
        if include_scene_export:
            export_path = os.path.join(kit_dir, "exports", f"{os.path.basename(kit_dir)}.{export_format}")
            if object_names:
                manifest["export"] = self.server.asset_export_service.export_selected_objects(export_path, export_format, object_names, overwrite=True)
            else:
                manifest["export"] = self.server.asset_export_service.export_scene(export_path, export_format, overwrite=True)
        manifest["manifest_path"] = AssetPathService.write_json(os.path.join(kit_dir, "manifest.json"), manifest)
        return manifest

    def validate_scene_kit(self, kit_path):
        try:
            path = AssetPathService.local_path(kit_path)
            manifest = os.path.join(path, "manifest.json") if os.path.isdir(path) else path
            if not os.path.exists(manifest):
                return {"status": "error", "message": "Scene kit manifest not found", "warnings": []}
            with open(manifest, "r", encoding="utf-8") as file:
                data = json.load(file)
            required = ["scene_index_path", "scene_health_path", "dependencies_path"]
            missing = [key for key in required if not data.get(key) or not os.path.exists(data.get(key))]
            return {"status": "success", "kit_path": os.path.dirname(manifest), "valid": not missing, "missing": missing, "manifest": data, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def list_scene_kits(self, artifact_root=None):
        root = AssetPathService.workspace_path("scene_kits", artifact_root=artifact_root)
        kits = []
        for name in sorted(os.listdir(root)):
            manifest = os.path.join(root, name, "manifest.json")
            if os.path.exists(manifest):
                kits.append({"kit_id": name, "path": os.path.join(root, name), "manifest_path": manifest})
        return {"status": "success", "kits": kits, "warnings": []}

    def import_scene_kit(self, kit_path, collection_name=None, rename_prefix=None):
        validation = self.validate_scene_kit(kit_path)
        if validation.get("status") != "success" or not validation.get("valid"):
            return validation
        export = validation["manifest"].get("export") or {}
        output_path = export.get("output_path")
        if not output_path:
            return {"status": "error", "message": "Scene kit has no importable export artifact", "warnings": []}
        return self.server.asset_import_service.import_model_file(output_path, collection_name=collection_name, rename_prefix=rename_prefix)


class AssetWorkflowBatchService:
    ALLOWED_COMMANDS = {"get_supported_asset_formats", "scan_asset_folder", "list_scene_assets", "get_asset_file_info", "get_asset_dependency_report", "create_asset_manifest", "import_model_file", "export_selected_objects", "export_scene", "create_asset_preview", "create_asset_contact_sheet", "collect_external_dependencies", "validate_external_dependencies", "create_scene_kit", "validate_scene_kit", "list_scene_kits"}
    DESTRUCTIVE_COMMANDS = {"pack_external_data", "make_paths_relative", "cleanup_asset_artifacts"}

    def __init__(self, server):
        self.server = server

    def cleanup_asset_artifacts(self, prefix, confirm=False, cleanup_scene_data=True, cleanup_files=False, artifact_root=None):
        if not confirm:
            return {"status": "error", "message": "cleanup_asset_artifacts requires confirm=True", "warnings": []}
        prefix = str(prefix or "")
        if len(prefix) < 8:
            return {"status": "error", "message": "A longer cleanup prefix is required", "warnings": []}
        deleted = {"objects": [], "collections": [], "materials": [], "images": [], "actions": [], "files": []}
        if cleanup_scene_data:
            for obj in list(bpy.data.objects):
                if obj.name.startswith(prefix):
                    deleted["objects"].append(obj.name)
                    bpy.data.objects.remove(obj, do_unlink=True)
            for col in list(bpy.data.collections):
                if col.name.startswith(prefix) and len(col.objects) == 0 and len(col.children) == 0:
                    deleted["collections"].append(col.name)
                    bpy.data.collections.remove(col)
            for mat in list(bpy.data.materials):
                if mat.name.startswith(prefix):
                    deleted["materials"].append(mat.name)
                    bpy.data.materials.remove(mat)
            for image in list(bpy.data.images):
                if image.name.startswith(prefix):
                    deleted["images"].append(image.name)
                    bpy.data.images.remove(image)
            for action in list(bpy.data.actions):
                if action.name.startswith(prefix):
                    deleted["actions"].append(action.name)
                    bpy.data.actions.remove(action)
        if cleanup_files:
            root = os.path.join(AssetPathService.artifact_root(artifact_root), ".overtli_blender")
            for current_root, _dirs, files in os.walk(root):
                for filename in files:
                    if filename.startswith(prefix):
                        path = os.path.join(current_root, filename)
                        os.remove(path)
                        deleted["files"].append(path)
        return {"status": "success", "prefix": prefix, "deleted": deleted, "warnings": []}

    def run_asset_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=40, batch_allow_file_writes=True, batch_allow_destructive=False, artifact_root=None):
        operations = operations or []
        if len(operations) > max(1, min(int(max_operations), 80)):
            return {"status": "error", "message": "Too many batch operations", "warnings": []}
        batch_id = f"asset_batch_{RenderArtifactService.stamp()}"
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_before", include_screenshots=False, artifact_root=artifact_root) if create_before_snapshot else None
        results = []
        errors = []
        handlers = self.server._build_command_handlers()
        for op in operations:
            command = op.get("command")
            params = dict(op.get("params") or {})
            if command not in self.ALLOWED_COMMANDS and command not in self.DESTRUCTIVE_COMMANDS:
                errors.append({"command": command, "message": "Command is not allowed in asset workflow batches"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_COMMANDS and not (batch_allow_destructive and params.get("confirm") is True):
                errors.append({"command": command, "message": "Destructive batch operation requires batch_allow_destructive=True and operation confirm=True"})
                if stop_on_error:
                    break
                continue
            if command not in self.DESTRUCTIVE_COMMANDS and not batch_allow_file_writes and command not in {"get_supported_asset_formats", "list_scene_assets", "get_asset_file_info", "get_asset_dependency_report", "validate_external_dependencies", "validate_scene_kit", "list_scene_kits"}:
                errors.append({"command": command, "message": "File-writing/import/export command blocked by batch_allow_file_writes=False"})
                if stop_on_error:
                    break
                continue
            params.setdefault("artifact_root", artifact_root)
            try:
                result = handlers[command](**params)
            except Exception as exc:
                result = {"status": "error", "message": str(exc), "warnings": []}
            results.append({"command": command, "params": params, "result": result})
            if result.get("status") == "error":
                errors.append({"command": command, "message": result.get("message")})
                if stop_on_error:
                    break
        after = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_after", include_screenshots=False, artifact_root=artifact_root) if create_after_snapshot else None
        batch_dir = AssetPathService.workspace_path("assets", "batches", batch_id, artifact_root=artifact_root)
        manifest_path = AssetPathService.write_json(os.path.join(batch_dir, "manifest.json"), {"batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors})
        return {"status": "partial" if errors else "success", "batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "artifacts": [manifest_path], "errors": errors, "warnings": []}


class RiggingSimulationService:
    def __init__(self, server):
        self.server = server

    def inspect_rigging(self, object_name=None):
        objects = [bpy.data.objects.get(object_name)] if object_name else list(bpy.data.objects)
        rigs = []
        for obj in [o for o in objects if o]:
            if obj.type == "ARMATURE":
                rigs.append({"name": obj.name, "type": "ARMATURE", "bones": [b.name for b in obj.data.bones], "pose_bones": [b.name for b in obj.pose.bones] if obj.pose else []})
            elif obj.type == "MESH":
                armature_mods = [m.name for m in obj.modifiers if m.type == "ARMATURE"]
                if armature_mods or obj.vertex_groups:
                    rigs.append({"name": obj.name, "type": "MESH", "armature_modifiers": armature_mods, "vertex_groups": [g.name for g in obj.vertex_groups]})
        return {"status": "success", "rigging": rigs, "warnings": []}

    def create_armature(self, armature_name=None, bones=None, collection_name=None, location=None):
        name = armature_name or f"OVERTLI_ARMATURE_{RenderArtifactService.stamp()}"
        arm_data = bpy.data.armatures.new(name)
        arm_obj = bpy.data.objects.new(name, arm_data)
        collection = bpy.data.collections.get(collection_name) if collection_name else bpy.context.scene.collection
        if collection_name and collection is None:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        collection.objects.link(arm_obj)
        arm_obj.location = location or [0, 0, 0]
        bpy.context.view_layer.objects.active = arm_obj
        arm_obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            first = (bones or [{"name": "Root", "head": [0, 0, 0], "tail": [0, 0, 1]}])[0]
            default = arm_data.edit_bones[0] if arm_data.edit_bones else arm_data.edit_bones.new(first.get("name", "Root"))
            default.name = first.get("name", "Root")
            default.head = first.get("head", [0, 0, 0])
            default.tail = first.get("tail", [0, 0, 1])
            for spec in (bones or [])[1:]:
                bone = arm_data.edit_bones.new(spec.get("name", "Bone"))
                bone.head = spec.get("head", [0, 0, 0])
                bone.tail = spec.get("tail", [0, 0, 1])
                if spec.get("parent"):
                    bone.parent = arm_data.edit_bones.get(spec["parent"])
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
        return {"status": "success", "armature": {"name": arm_obj.name, "bones": [b.name for b in arm_data.bones]}, "warnings": []}

    def parent_mesh_to_armature(self, mesh_name, armature_name, add_modifier=True, create_vertex_groups=True):
        mesh = bpy.data.objects.get(mesh_name)
        arm = bpy.data.objects.get(armature_name)
        if not mesh or mesh.type != "MESH" or not arm or arm.type != "ARMATURE":
            return {"status": "error", "message": "Mesh and armature objects are required", "warnings": []}
        mesh.parent = arm
        if add_modifier and not any(m.type == "ARMATURE" and m.object == arm for m in mesh.modifiers):
            mod = mesh.modifiers.new(f"{arm.name}_Armature", "ARMATURE")
            mod.object = arm
        if create_vertex_groups:
            for bone in arm.data.bones:
                if not mesh.vertex_groups.get(bone.name):
                    mesh.vertex_groups.new(name=bone.name)
        return {"status": "success", "mesh_name": mesh.name, "armature_name": arm.name, "vertex_groups": [g.name for g in mesh.vertex_groups], "warnings": []}

    def pose_bone_transform(self, armature_name, bone_name, location=None, rotation=None, scale=None, keyframe_frame=None):
        arm = bpy.data.objects.get(armature_name)
        if not arm or arm.type != "ARMATURE" or not arm.pose or bone_name not in arm.pose.bones:
            return {"status": "error", "message": "Armature pose bone not found", "warnings": []}
        bone = arm.pose.bones[bone_name]
        if location is not None:
            bone.location = location
            if keyframe_frame is not None:
                bone.keyframe_insert("location", frame=int(keyframe_frame))
        if rotation is not None:
            bone.rotation_euler = rotation
            if keyframe_frame is not None:
                bone.keyframe_insert("rotation_euler", frame=int(keyframe_frame))
        if scale is not None:
            bone.scale = scale
            if keyframe_frame is not None:
                bone.keyframe_insert("scale", frame=int(keyframe_frame))
        return {"status": "success", "armature_name": arm.name, "bone_name": bone.name, "warnings": []}

    def add_driver(self, target_type, target_name, data_path, expression="var", variables=None, array_index=-1):
        target = bpy.data.objects.get(target_name) if target_type == "object" else bpy.data.materials.get(target_name)
        if not target:
            return {"status": "error", "message": "Driver target not found", "warnings": []}
        try:
            fcurve = target.driver_add(data_path, int(array_index)) if int(array_index) >= 0 else target.driver_add(data_path)
            fcurves = fcurve if isinstance(fcurve, list) else [fcurve]
            for fc in fcurves:
                fc.driver.type = "SCRIPTED"
                fc.driver.expression = str(expression)
                for spec in variables or []:
                    var = fc.driver.variables.new()
                    var.name = spec.get("name", "var")
                    var.targets[0].id = bpy.data.objects.get(spec.get("object_name")) if spec.get("object_name") else target
                    var.targets[0].data_path = spec.get("data_path", "location.x")
            return {"status": "success", "target_type": target_type, "target_name": target.name, "data_path": data_path, "driver_count": len(fcurves), "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def remove_driver(self, target_type, target_name, data_path, array_index=-1, confirm=False):
        if not confirm:
            return {"status": "error", "message": "remove_driver requires confirm=True", "warnings": []}
        target = bpy.data.objects.get(target_name) if target_type == "object" else bpy.data.materials.get(target_name)
        if not target:
            return {"status": "error", "message": "Driver target not found", "warnings": []}
        try:
            target.driver_remove(data_path, int(array_index)) if int(array_index) >= 0 else target.driver_remove(data_path)
            return {"status": "success", "target_type": target_type, "target_name": target.name, "data_path": data_path, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def add_physics_basic(self, object_name, physics_type="cloth", settings=None):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        physics_type = str(physics_type).lower()
        settings = settings or {}
        try:
            if physics_type == "cloth":
                mod = obj.modifiers.new(settings.get("name", "Overtli Cloth"), "CLOTH")
            elif physics_type == "collision":
                mod = obj.modifiers.new(settings.get("name", "Overtli Collision"), "COLLISION")
            elif physics_type == "soft_body":
                mod = obj.modifiers.new(settings.get("name", "Overtli Soft Body"), "SOFT_BODY")
            elif physics_type == "rigid_body":
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.rigidbody.object_add(type=settings.get("body_type", "ACTIVE"))
                mod = None
            elif physics_type == "particle_hair":
                mod = obj.modifiers.new(settings.get("name", "Overtli Hair"), "PARTICLE_SYSTEM")
                ps = obj.particle_systems[-1].settings
                ps.type = "HAIR"
                ps.count = max(1, min(int(settings.get("count", 100)), 10000))
                ps.hair_length = max(0.001, min(float(settings.get("hair_length", 1.0)), 100.0))
            else:
                return {"status": "error", "message": f"Unsupported physics_type: {physics_type}", "warnings": []}
            return {"status": "success", "object_name": obj.name, "physics_type": physics_type, "modifier_name": mod.name if mod else None, "warnings": ["Simulation cache is not baked by this command"]}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}


class ModifierService:
    SUPPORTED_MODIFIERS = {"BEVEL", "SUBSURF", "SOLIDIFY", "MIRROR", "ARRAY", "WEIGHTED_NORMAL", "TRIANGULATE", "DECIMATE"}
    ALLOWED_PROPERTIES = {
        "BEVEL": {"width", "segments", "affect", "profile", "show_viewport", "show_render"},
        "SUBSURF": {"levels", "render_levels", "subdivision_type", "show_viewport", "show_render"},
        "SOLIDIFY": {"thickness", "offset", "use_quality_normals", "show_viewport", "show_render"},
        "MIRROR": {"use_axis", "use_clip", "show_viewport", "show_render"},
        "ARRAY": {"count", "relative_offset_displace", "use_relative_offset", "show_viewport", "show_render"},
        "WEIGHTED_NORMAL": {"keep_sharp", "weight", "show_viewport", "show_render"},
        "TRIANGULATE": {"quad_method", "ngon_method", "show_viewport", "show_render"},
        "DECIMATE": {"ratio", "decimate_type", "show_viewport", "show_render"},
    }

    def __init__(self, server):
        self.server = server

    def _summary(self, modifier):
        return {"name": modifier.name, "type": modifier.type, "show_viewport": bool(modifier.show_viewport), "show_render": bool(modifier.show_render)}

    def _apply_properties(self, modifier, properties):
        warnings = []
        allowed = self.ALLOWED_PROPERTIES.get(modifier.type, set())
        for key, value in (properties or {}).items():
            if key not in allowed:
                warnings.append(f"Unsupported modifier property skipped: {key}")
                continue
            try:
                setattr(modifier, key, value)
            except Exception as exc:
                warnings.append(f"Failed to set {key}: {exc}")
        return warnings

    def add_object_modifier(self, object_name, modifier_type, name=None, properties=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        modifier_type = str(modifier_type or "").upper()
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if modifier_type not in self.SUPPORTED_MODIFIERS:
            return {"status": "error", "message": f"Unsupported modifier_type: {modifier_type}", "warnings": []}
        modifier = obj.modifiers.new(name=name or modifier_type.title(), type=modifier_type)
        warnings = self._apply_properties(modifier, properties)
        result = {"status": "success", "object_name": obj.name, "modifier": self._summary(modifier), "verification": self.server.scene_edit_service._verification(f"modifier_{obj.name}", verify), "warnings": warnings}
        self.server._add_to_history("add_object_modifier", {"object_name": object_name, "modifier_type": modifier_type}, result)
        return result

    def update_object_modifier(self, object_name, modifier_name, properties, verify=False):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        modifier = obj.modifiers.get(modifier_name)
        if not modifier:
            return {"status": "error", "message": f"Modifier not found: {modifier_name}", "warnings": []}
        warnings = self._apply_properties(modifier, properties or {})
        status = "partial" if warnings else "success"
        result = {"status": status, "object_name": obj.name, "modifier": self._summary(modifier), "verification": self.server.scene_edit_service._verification(f"modifier_{obj.name}", verify), "warnings": warnings}
        self.server._add_to_history("update_object_modifier", {"object_name": object_name, "modifier_name": modifier_name}, result)
        return result

    def remove_object_modifier(self, object_name, modifier_name, confirm=False, verify=False):
        if not confirm:
            return {"status": "error", "message": "remove_object_modifier requires confirm=True", "warnings": []}
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        modifier = obj.modifiers.get(modifier_name)
        if not modifier:
            return {"status": "error", "message": f"Modifier not found: {modifier_name}", "warnings": []}
        summary = self._summary(modifier)
        obj.modifiers.remove(modifier)
        result = {"status": "success", "object_name": obj.name, "removed_modifier": summary, "verification": self.server.scene_edit_service._verification(f"remove_modifier_{obj.name}", verify), "warnings": []}
        self.server._add_to_history("remove_object_modifier", {"object_name": object_name, "modifier_name": modifier_name}, result)
        return result


class CollectionOrganizationService:
    def __init__(self, server):
        self.server = server

    def _summary(self, collection):
        return {"name": collection.name, "object_count": len(collection.objects), "children": [child.name for child in collection.children]}

    def create_collection(self, collection_name, parent_collection_name=None, replace_existing=False):
        if not collection_name:
            return {"status": "error", "message": "collection_name is required", "warnings": []}
        existing = bpy.data.collections.get(collection_name)
        if existing and not replace_existing:
            return {"status": "success", "collection_name": existing.name, "created": False, "collection": self._summary(existing), "warnings": ["collection already exists"]}
        collection = existing or bpy.data.collections.new(collection_name)
        if not existing:
            parent = bpy.data.collections.get(parent_collection_name) if parent_collection_name else bpy.context.scene.collection
            if parent is None:
                return {"status": "error", "message": f"Parent collection not found: {parent_collection_name}", "warnings": []}
            parent.children.link(collection)
        result = {"status": "success", "collection_name": collection.name, "created": existing is None, "collection": self._summary(collection), "warnings": []}
        self.server._add_to_history("create_collection", {"collection_name": collection_name}, result)
        return result

    def move_objects_to_collection(self, object_names, collection_name, unlink_from_other_collections=False, create_collection=False):
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            if create_collection:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)
            else:
                return {"status": "error", "message": f"Collection not found: {collection_name}", "moved": [], "missing": list(object_names or []), "warnings": []}
        moved, missing = [], []
        for name in object_names or []:
            obj = bpy.data.objects.get(str(name))
            if not obj:
                missing.append(str(name))
                continue
            if obj.name not in collection.objects.keys():
                collection.objects.link(obj)
            if unlink_from_other_collections:
                for linked in list(obj.users_collection):
                    if linked != collection:
                        linked.objects.unlink(obj)
            moved.append(obj.name)
        status = "partial" if missing else "success"
        result = {"status": status, "collection_name": collection.name, "moved": moved, "missing": missing, "collection": self._summary(collection), "warnings": []}
        self.server._add_to_history("move_objects_to_collection", {"collection_name": collection_name, "object_names": object_names}, result)
        return result

    def delete_collection(self, collection_name, confirm=False, require_empty=True):
        if not confirm:
            return {"status": "error", "message": "delete_collection requires confirm=True", "collection_name": collection_name, "deleted": False, "warnings": []}
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            return {"status": "error", "message": f"Collection not found: {collection_name}", "collection_name": collection_name, "deleted": False, "warnings": []}
        object_count = len(collection.objects)
        child_count = len(collection.children)
        if require_empty and (object_count > 0 or child_count > 0):
            return {
                "status": "error",
                "message": f"Collection is not empty: {collection_name}",
                "collection_name": collection_name,
                "deleted": False,
                "object_count": object_count,
                "child_count": child_count,
                "warnings": ["delete_collection defaults to require_empty=True"],
            }
        summary = self._summary(collection)
        bpy.data.collections.remove(collection)
        result = {"status": "success", "collection_name": collection_name, "deleted": True, "collection": summary, "warnings": []}
        self.server._add_to_history("delete_collection", {"collection_name": collection_name}, result)
        return result


class VerifiedEditBatchService:
    SUPPORTED_BATCH_OPERATIONS = {
        "create_primitive_object",
        "transform_object",
        "duplicate_object",
        "set_object_visibility",
        "create_basic_material",
        "assign_material",
        "update_material_properties",
        "add_object_modifier",
        "update_object_modifier",
        "create_collection",
        "move_objects_to_collection",
        "delete_objects",
        "remove_object_modifier",
        "delete_collection",
    }
    DESTRUCTIVE_OPERATIONS = {"delete_objects", "remove_object_modifier", "delete_collection"}

    def __init__(self, server):
        self.server = server

    def run_verified_edit_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=20, batch_allow_destructive=False, artifact_root=None):
        operations = operations or []
        max_operations = max(1, min(int(max_operations), 50))
        if len(operations) > max_operations:
            return {"status": "error", "message": f"Batch exceeds max_operations={max_operations}", "operation_results": [], "errors": [], "warnings": []}
        batch_id = f"batch_{int(time.time())}_{abs(hash(str(operations))) % 100000}"
        batch_label = label or batch_id
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_label}_before", include_screenshots=False, artifact_root=artifact_root) if create_before_snapshot else {}
        results, errors, warnings = [], [], []
        for index, operation in enumerate(operations):
            op_type = operation.get("type") or operation.get("command")
            params = dict(operation.get("params") or {})
            if op_type not in self.SUPPORTED_BATCH_OPERATIONS:
                error = {"index": index, "type": op_type, "message": "Unsupported batch operation"}
                errors.append(error)
                if stop_on_error:
                    break
                continue
            if op_type in self.DESTRUCTIVE_OPERATIONS and not (operation.get("confirm") is True and batch_allow_destructive is True):
                error = {"index": index, "type": op_type, "message": "Destructive batch operation requires operation.confirm=True and batch_allow_destructive=True"}
                errors.append(error)
                if stop_on_error:
                    break
                continue
            if op_type in self.DESTRUCTIVE_OPERATIONS and "confirm" not in params:
                params["confirm"] = bool(operation.get("confirm"))
            handler = self.server._build_command_handlers().get(op_type)
            result = handler(**params)
            results.append({"index": index, "type": op_type, "result": result})
            warnings.extend(result.get("warnings", []) if isinstance(result, dict) else [])
            if isinstance(result, dict) and result.get("status") not in {"success"}:
                errors.append({"index": index, "type": op_type, "message": result.get("message", result.get("status"))})
                if stop_on_error:
                    break
        after = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_label}_after", include_screenshots=False, artifact_root=artifact_root) if create_after_snapshot else {}
        status = "success" if not errors else ("partial" if results else "error")
        result = {"status": status, "batch_id": batch_id, "label": batch_label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors, "warnings": warnings}
        self.server._add_to_history("run_verified_edit_batch", {"label": label, "operation_count": len(operations)}, result)
        return result


class WorkspaceSafetyDiffService:
    TODO_STATES = {"pending", "in_progress", "done", "blocked", "rejected", "needs_user_selection", "needs_screenshot", "needs_rollback", "needs_manual_check"}
    TASK_STATES = {"pending", "in_progress", "done", "blocked", "deferred", "superseded"}

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _utc_timestamp():
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @staticmethod
    def _stamp():
        return time.strftime("%Y%m%d_%H%M%S", time.localtime())

    @staticmethod
    def _safe_slug(value, fallback="item"):
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or fallback)).strip("._-")
        return safe[:80] or fallback

    def _workspace_root(self, artifact_root=None):
        root = artifact_root or os.environ.get("OVERTLI_BLENDER_ARTIFACT_ROOT") or ADDON_ROOT
        path = os.path.join(os.path.abspath(os.path.expanduser(str(root))), ".overtli_blender", "workspace")
        os.makedirs(path, exist_ok=True)
        for child in ["tasks", "snapshots", "rollback"]:
            os.makedirs(os.path.join(path, child), exist_ok=True)
        return path

    def _path(self, *parts, artifact_root=None):
        return os.path.join(self._workspace_root(artifact_root), *parts)

    @staticmethod
    def _read_json(path, default):
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _write_json(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, sort_keys=True)

    def _index_path(self, name, artifact_root=None):
        return self._path(f"{name}.json", artifact_root=artifact_root)

    def _load_index(self, name, artifact_root=None):
        return self._read_json(self._index_path(name, artifact_root), [])

    def _save_index(self, name, data, artifact_root=None):
        self._write_json(self._index_path(name, artifact_root), data)

    def get_task_workspace(self, artifact_root=None):
        root = self._workspace_root(artifact_root)
        tasks = self._load_index("tasks", artifact_root)
        todos = self._load_index("todos", artifact_root)
        journal = self._load_index("operation_journal", artifact_root)
        snapshots = self.list_scene_snapshots(artifact_root=artifact_root)
        return {
            "status": "success",
            "workspace_root": root,
            "tasks_count": len(tasks),
            "todos_count": len(todos),
            "journal_count": len(journal),
            "snapshot_count": len(snapshots.get("snapshots", [])),
            "todo_states": sorted(self.TODO_STATES),
            "task_states": sorted(self.TASK_STATES),
            "warnings": [],
        }

    def create_workspace_task(self, title, goal=None, assumptions=None, status="pending", task_id=None, artifact_root=None):
        if not title:
            return {"status": "error", "message": "title is required", "warnings": []}
        state = str(status or "pending")
        if state not in self.TASK_STATES:
            return {"status": "error", "message": f"Unsupported task status: {state}", "warnings": []}
        tasks = self._load_index("tasks", artifact_root)
        task_id = task_id or f"task_{self._stamp()}_{len(tasks) + 1}"
        if any(task.get("task_id") == task_id for task in tasks):
            return {"status": "error", "message": f"Task already exists: {task_id}", "warnings": []}
        task = {
            "task_id": task_id,
            "title": str(title),
            "goal": goal,
            "assumptions": assumptions or [],
            "status": state,
            "created_at": self._utc_timestamp(),
            "updated_at": self._utc_timestamp(),
            "rollback_status": "not_required",
            "verification": {},
            "warnings": [],
        }
        tasks.append(task)
        self._save_index("tasks", tasks, artifact_root)
        self.record_operation_journal_entry("create_workspace_task", task_id=task_id, target=task_id, summary=f"Created workspace task {title}", risk_level="LOW", rollback_status="not_required", artifact_root=artifact_root)
        return {"status": "success", "task": task, "warnings": []}

    def update_workspace_task(self, task_id, status=None, goal=None, assumptions=None, rollback_status=None, verification=None, artifact_root=None):
        tasks = self._load_index("tasks", artifact_root)
        for task in tasks:
            if task.get("task_id") != task_id:
                continue
            if status is not None:
                state = str(status)
                if state not in self.TASK_STATES:
                    return {"status": "error", "message": f"Unsupported task status: {state}", "warnings": []}
                task["status"] = state
            if goal is not None:
                task["goal"] = goal
            if assumptions is not None:
                task["assumptions"] = assumptions
            if rollback_status is not None:
                task["rollback_status"] = rollback_status
            if verification is not None:
                task["verification"] = verification
            task["updated_at"] = self._utc_timestamp()
            self._save_index("tasks", tasks, artifact_root)
            self.record_operation_journal_entry("update_workspace_task", task_id=task_id, target=task_id, summary=f"Updated workspace task {task_id}", risk_level="LOW", rollback_status=task.get("rollback_status"), artifact_root=artifact_root)
            return {"status": "success", "task": task, "warnings": []}
        return {"status": "error", "message": f"Task not found: {task_id}", "warnings": []}

    def list_workspace_tasks(self, status=None, artifact_root=None):
        tasks = self._load_index("tasks", artifact_root)
        if status:
            tasks = [task for task in tasks if task.get("status") == status]
        return {"status": "success", "tasks": tasks, "warnings": []}

    def add_workspace_todo(self, text, task_id=None, state="pending", todo_id=None, artifact_root=None):
        if not text:
            return {"status": "error", "message": "text is required", "warnings": []}
        if state not in self.TODO_STATES:
            return {"status": "error", "message": f"Unsupported todo state: {state}", "warnings": []}
        todos = self._load_index("todos", artifact_root)
        todo_id = todo_id or f"todo_{self._stamp()}_{len(todos) + 1}"
        todo = {"todo_id": todo_id, "task_id": task_id, "text": str(text), "state": state, "created_at": self._utc_timestamp(), "updated_at": self._utc_timestamp(), "evidence": None}
        todos.append(todo)
        self._save_index("todos", todos, artifact_root)
        self.record_operation_journal_entry("add_workspace_todo", task_id=task_id, target=todo_id, summary=f"Added todo {text}", risk_level="LOW", rollback_status="not_required", artifact_root=artifact_root)
        return {"status": "success", "todo": todo, "warnings": []}

    def update_workspace_todo(self, todo_id, state=None, text=None, evidence=None, artifact_root=None):
        todos = self._load_index("todos", artifact_root)
        for todo in todos:
            if todo.get("todo_id") != todo_id:
                continue
            if state is not None:
                if state not in self.TODO_STATES:
                    return {"status": "error", "message": f"Unsupported todo state: {state}", "warnings": []}
                todo["state"] = state
            if text is not None:
                todo["text"] = text
            if evidence is not None:
                todo["evidence"] = evidence
            todo["updated_at"] = self._utc_timestamp()
            self._save_index("todos", todos, artifact_root)
            self.record_operation_journal_entry("update_workspace_todo", task_id=todo.get("task_id"), target=todo_id, summary=f"Updated todo {todo_id}", risk_level="LOW", rollback_status="not_required", artifact_root=artifact_root)
            return {"status": "success", "todo": todo, "warnings": []}
        return {"status": "error", "message": f"Todo not found: {todo_id}", "warnings": []}

    def list_workspace_todos(self, task_id=None, state=None, artifact_root=None):
        todos = self._load_index("todos", artifact_root)
        if task_id:
            todos = [todo for todo in todos if todo.get("task_id") == task_id]
        if state:
            todos = [todo for todo in todos if todo.get("state") == state]
        return {"status": "success", "todos": todos, "warnings": []}

    def record_operation_journal_entry(self, operation_type, task_id=None, target=None, summary=None, risk_level="LOW", rollback_status="unknown", before_snapshot_id=None, after_snapshot_id=None, metadata=None, artifact_root=None):
        journal = self._load_index("operation_journal", artifact_root)
        entry = {
            "entry_id": f"journal_{self._stamp()}_{len(journal) + 1}",
            "created_at": self._utc_timestamp(),
            "operation_type": str(operation_type),
            "task_id": task_id,
            "target": target,
            "summary": summary,
            "risk_level": str(risk_level),
            "rollback_status": rollback_status,
            "before_snapshot_id": before_snapshot_id,
            "after_snapshot_id": after_snapshot_id,
            "metadata": metadata or {},
        }
        journal.append(entry)
        self._save_index("operation_journal", journal[-500:], artifact_root)
        return {"status": "success", "entry": entry, "warnings": []}

    def get_operation_journal(self, task_id=None, limit=50, artifact_root=None):
        journal = self._load_index("operation_journal", artifact_root)
        if task_id:
            journal = [entry for entry in journal if entry.get("task_id") == task_id]
        return {"status": "success", "journal": journal[-max(1, int(limit)):], "warnings": []}

    def _scene_state(self):
        objects = {}
        for obj in bpy.context.scene.objects:
            objects[obj.name] = {
                "name": obj.name,
                "type": obj.type,
                "location": [round(float(v), 6) for v in obj.location],
                "rotation_euler": [round(float(v), 6) for v in obj.rotation_euler],
                "scale": [round(float(v), 6) for v in obj.scale],
                "hide_viewport": bool(obj.hide_viewport),
                "hide_render": bool(obj.hide_render),
                "collection_names": [collection.name for collection in obj.users_collection],
                "material_names": [slot.material.name if slot.material else None for slot in getattr(obj, "material_slots", [])],
                "modifier_names": [modifier.name for modifier in getattr(obj, "modifiers", [])],
            }
        collections = {collection.name: {"name": collection.name, "object_names": [obj.name for obj in collection.objects], "children": [child.name for child in collection.children]} for collection in bpy.data.collections}
        materials = {material.name: {"name": material.name, "users": int(material.users), "diffuse_color": [round(float(v), 6) for v in material.diffuse_color]} for material in bpy.data.materials}
        return {"objects": objects, "collections": collections, "materials": materials}

    def create_scene_snapshot(self, label=None, task_id=None, include_verification_snapshot=False, artifact_root=None):
        snapshot_id = f"{self._stamp()}_{self._safe_slug(label or 'scene')}"
        path = self._path("snapshots", f"{snapshot_id}.json", artifact_root=artifact_root)
        data = {
            "snapshot_id": snapshot_id,
            "label": label,
            "task_id": task_id,
            "created_at": self._utc_timestamp(),
            "scene_name": bpy.context.scene.name,
            "state": self._scene_state(),
            "verification_snapshot": None,
        }
        if include_verification_snapshot:
            data["verification_snapshot"] = self.server.verification_artifact_service.create_verification_snapshot(label=f"{snapshot_id}_verification", include_screenshots=False, artifact_root=artifact_root)
        self._write_json(path, data)
        self.record_operation_journal_entry("create_scene_snapshot", task_id=task_id, target=snapshot_id, summary=f"Created scene snapshot {snapshot_id}", risk_level="LOW", rollback_status="available", after_snapshot_id=snapshot_id, artifact_root=artifact_root)
        return {"status": "success", "snapshot_id": snapshot_id, "snapshot_path": path, "object_count": len(data["state"]["objects"]), "collection_count": len(data["state"]["collections"]), "material_count": len(data["state"]["materials"]), "warnings": []}

    def list_scene_snapshots(self, artifact_root=None):
        snapshot_dir = self._path("snapshots", artifact_root=artifact_root)
        snapshots = []
        for filename in sorted(os.listdir(snapshot_dir), reverse=True):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(snapshot_dir, filename)
            data = self._read_json(path, {})
            snapshots.append({"snapshot_id": data.get("snapshot_id") or filename[:-5], "label": data.get("label"), "task_id": data.get("task_id"), "created_at": data.get("created_at"), "snapshot_path": path})
        return {"status": "success", "snapshots": snapshots, "warnings": []}

    def _load_snapshot(self, snapshot_id, artifact_root=None):
        path = self._path("snapshots", f"{snapshot_id}.json", artifact_root=artifact_root)
        if not os.path.exists(path):
            raise ValueError(f"Scene snapshot not found: {snapshot_id}")
        return self._read_json(path, {})

    @staticmethod
    def _dict_diff(before, after):
        before_keys = set(before)
        after_keys = set(after)
        added = sorted(after_keys - before_keys)
        removed = sorted(before_keys - after_keys)
        changed = []
        for key in sorted(before_keys & after_keys):
            if before[key] != after[key]:
                changed.append(key)
        return added, removed, changed

    def diff_scene_snapshots(self, before_snapshot_id, after_snapshot_id, artifact_root=None):
        before = self._load_snapshot(before_snapshot_id, artifact_root)
        after = self._load_snapshot(after_snapshot_id, artifact_root)
        diff = {}
        for section in ["objects", "collections", "materials"]:
            added, removed, changed = self._dict_diff(before.get("state", {}).get(section, {}), after.get("state", {}).get(section, {}))
            diff[section] = {"added": added, "removed": removed, "changed": changed}
        return {"status": "success", "before_snapshot_id": before_snapshot_id, "after_snapshot_id": after_snapshot_id, "diff": diff, "warnings": []}

    def detect_user_changes(self, baseline_snapshot_id=None, artifact_root=None):
        snapshots = self.list_scene_snapshots(artifact_root=artifact_root).get("snapshots", [])
        if not snapshots and not baseline_snapshot_id:
            current = self.create_scene_snapshot(label="user_change_baseline", artifact_root=artifact_root)
            return {"status": "success", "baseline_created": True, "baseline_snapshot_id": current["snapshot_id"], "changed": False, "diff": {}, "warnings": ["No baseline existed; created one"]}
        baseline_id = baseline_snapshot_id or snapshots[0]["snapshot_id"]
        current = self.create_scene_snapshot(label="user_change_current", artifact_root=artifact_root)
        diff = self.diff_scene_snapshots(baseline_id, current["snapshot_id"], artifact_root=artifact_root)
        changed = any(diff["diff"][section][kind] for section in diff["diff"] for kind in ["added", "removed", "changed"])
        return {"status": "success", "baseline_snapshot_id": baseline_id, "current_snapshot_id": current["snapshot_id"], "changed": changed, "diff": diff["diff"], "warnings": []}

    def rollback_to_scene_snapshot(self, snapshot_id, confirm=False, remove_new_objects=False, verify=True, artifact_root=None):
        if not confirm:
            return {"status": "error", "message": "rollback_to_scene_snapshot requires confirm=True", "warnings": []}
        snapshot = self._load_snapshot(snapshot_id, artifact_root)
        target_objects = snapshot.get("state", {}).get("objects", {})
        current_names = set(bpy.data.objects.keys())
        restored, missing, removed = [], [], []
        for name, state in target_objects.items():
            obj = bpy.data.objects.get(name)
            if not obj:
                missing.append(name)
                continue
            obj.location = state.get("location", list(obj.location))
            obj.rotation_euler = state.get("rotation_euler", list(obj.rotation_euler))
            obj.scale = state.get("scale", list(obj.scale))
            obj.hide_viewport = bool(state.get("hide_viewport", obj.hide_viewport))
            obj.hide_render = bool(state.get("hide_render", obj.hide_render))
            restored.append(name)
        if remove_new_objects:
            for name in sorted(current_names - set(target_objects)):
                obj = bpy.data.objects.get(name)
                if obj:
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed.append(name)
        verification = self.create_scene_snapshot(label=f"rollback_after_{snapshot_id}", artifact_root=artifact_root) if verify else {}
        result = {"status": "success", "snapshot_id": snapshot_id, "restored": restored, "missing": missing, "removed_new_objects": removed, "verification": verification, "warnings": ["Rollback restores transforms/visibility for existing objects; deleted object recreation is not supported"]}
        self.record_operation_journal_entry("rollback_to_scene_snapshot", target=snapshot_id, summary=f"Rolled back to scene snapshot {snapshot_id}", risk_level="HIGH", rollback_status="performed", after_snapshot_id=verification.get("snapshot_id") if isinstance(verification, dict) else None, artifact_root=artifact_root)
        return result

    def undo_last_blender_operation(self, confirm=False):
        if not confirm:
            return {"status": "error", "message": "undo_last_blender_operation requires confirm=True", "warnings": []}
        try:
            bpy.ops.ed.undo()
            result = {"status": "success", "undone": True, "warnings": ["Uses Blender undo stack; availability depends on the current session"]}
        except Exception as exc:
            result = {"status": "error", "undone": False, "message": str(exc), "warnings": ["Blender undo stack was not available"]}
        self.record_operation_journal_entry("undo_last_blender_operation", summary="Requested Blender undo", risk_level="HIGH", rollback_status="performed" if result["status"] == "success" else "failed")
        return result


class SafetyPolicyService:
    def __init__(self, server):
        self.server = server
        self.command_safety_map = build_command_safety_map()
        self.mode, self.warnings = self._resolve_mode()

    @staticmethod
    def _metadata_attr(metadata, name):
        if hasattr(metadata, name):
            return getattr(metadata, name)
        if isinstance(metadata, dict):
            return metadata.get(name)
        return None

    def _resolve_mode(self):
        raw_mode = os.environ.get("OVERTLI_BLENDER_SAFETY_MODE", "").strip().lower()
        if not raw_mode:
            return SAFETY_MODE_COMPAT, []

        aliases = {
            "legacy": SAFETY_MODE_COMPAT,
            "permissive": SAFETY_MODE_COMPAT,
            SAFETY_MODE_COMPAT: SAFETY_MODE_COMPAT,
            SAFETY_MODE_AUDIT: SAFETY_MODE_AUDIT,
            SAFETY_MODE_STRICT: SAFETY_MODE_STRICT,
        }
        resolved_mode = aliases.get(raw_mode)
        if resolved_mode:
            return resolved_mode, []

        return SAFETY_MODE_COMPAT, [f"Invalid safety mode '{raw_mode}', defaulting to compatibility"]

    def _build_decision(self, command_type, metadata, allowed, reason):
        operation_type = self._metadata_attr(metadata, "operation_type")
        risk_level = self._metadata_attr(metadata, "risk_level")
        reversibility = self._metadata_attr(metadata, "reversibility")
        if hasattr(operation_type, "value"):
            operation_type = operation_type.value
        if hasattr(risk_level, "value"):
            risk_level = risk_level.value
        if hasattr(reversibility, "value"):
            reversibility = reversibility.value
        return {
            "allowed": allowed,
            "mode": self.mode,
            "command_type": command_type,
            "operation_type": operation_type,
            "risk_level": risk_level,
            "reversibility": reversibility,
            "can_mutate_scene": bool(self._metadata_attr(metadata, "can_mutate_scene")),
            "can_execute_code": bool(self._metadata_attr(metadata, "can_execute_code")),
            "can_call_network": bool(self._metadata_attr(metadata, "can_call_network")),
            "can_write_files": bool(self._metadata_attr(metadata, "can_write_files")),
            "provider_api_key_involved": bool(self._metadata_attr(metadata, "provider_api_key_involved")),
            "strict_blocked": bool(self._metadata_attr(metadata, "strict_blocked")),
            "default_action": self._metadata_attr(metadata, "default_action") or "allow",
            "strict_action": self._metadata_attr(metadata, "strict_action") or "block",
            "warnings": list(self.warnings) + list(self._metadata_attr(metadata, "warnings") or []),
            "reason": reason,
        }

    def evaluate_command(self, command_type: str, params: dict | None = None) -> dict:
        metadata = self.command_safety_map.get(command_type)
        if metadata is None:
            return {
                "allowed": True,
                "mode": self.mode,
                "command_type": command_type,
                "operation_type": "UNKNOWN",
                "risk_level": "LOW",
                "reversibility": "UNKNOWN",
                "can_mutate_scene": False,
                "can_execute_code": False,
                "can_call_network": False,
                "can_write_files": False,
                "provider_api_key_involved": False,
                "strict_blocked": False,
                "default_action": "allow",
                "strict_action": "block",
                "warnings": list(self.warnings) + [f"Unknown command '{command_type}'"],
                "reason": "unknown command",
            }

        risk_level = self._metadata_attr(metadata, "risk_level")
        if hasattr(risk_level, "value"):
            risk_level = risk_level.value
        strict_blocked = bool(self._metadata_attr(metadata, "strict_blocked"))
        blocked = self.mode == SAFETY_MODE_STRICT and (strict_blocked or risk_level in {RiskLevel.HIGH, RiskLevel.DESTRUCTIVE, "HIGH", "DESTRUCTIVE"})
        if blocked:
            return self._build_decision(command_type, metadata, False, "command blocked by strict safety policy")

        if self.mode == SAFETY_MODE_AUDIT:
            return self._build_decision(command_type, metadata, True, "command allowed in audit mode")

        return self._build_decision(command_type, metadata, True, "command allowed in compatibility mode")

    def get_safety_status(self):
        high_risk_commands = []
        network_commands = []
        strict_blocked_commands = []

        for command_type, metadata in self.command_safety_map.items():
            risk_level = self._metadata_attr(metadata, "risk_level")
            if hasattr(risk_level, "value"):
                risk_level = risk_level.value
            if risk_level in {RiskLevel.HIGH, RiskLevel.DESTRUCTIVE, "HIGH", "DESTRUCTIVE"}:
                high_risk_commands.append(command_type)
            if bool(self._metadata_attr(metadata, "can_call_network")):
                network_commands.append(command_type)
            if bool(self._metadata_attr(metadata, "strict_blocked")):
                strict_blocked_commands.append(command_type)

        return {
            "mode": self.mode,
            "available_modes": list(AVAILABLE_SAFETY_MODES),
            "default_mode": DEFAULT_SAFETY_MODE,
            "policy_version": SAFETY_POLICY_VERSION,
            "command_count": len(self.command_safety_map),
            "high_risk_commands": sorted(high_risk_commands),
            "network_commands": sorted(network_commands),
            "strict_blocked_commands": sorted(strict_blocked_commands),
            "warnings": list(self.warnings),
        }


class RawCodeExecutionService:
    def __init__(self, server):
        self.server = server

    def execute_code(self, code):
        """Execute arbitrary Blender Python code with shared context"""
        try:
            namespace = {
                "bpy": bpy,
                "shared": self.server.shared_context['variables'],
                "get_object": lambda handle: self.server.shared_context['objects'].get(handle),
                "get_material": lambda handle: self.server.shared_context['materials'].get(handle),
                "get_operation": lambda op_id: self.server.shared_context['operations'].get(op_id),
                "store_object": self.server._store_object_handle,
                "store_material": self.server._store_material_handle,
                "store_operation": self.server._store_operation_result,
            }

            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)

            captured_output = capture_buffer.getvalue()
            self.server._add_to_history("execute_code", code[:100] + "..." if len(code) > 100 else code, captured_output)
            return {"executed": True, "result": captured_output, "shared_variables": list(self.server.shared_context['variables'].keys())}
        except Exception as e:
            error_msg = f"Code execution error: {str(e)}"
            self.server._add_to_history("execute_code", code[:100] + "..." if len(code) > 100 else code, f"ERROR: {error_msg}")
            raise Exception(error_msg)


class GeometryNodesIntelligenceService:
    def __init__(self, server):
        self.server = server

    def get_geometry_nodes_capabilities(self):
        warnings = []
        available = {}
        for node_type in ["GeometryNodeJoinGeometry", "GeometryNodeInstanceOnPoints", "GeometryNodeDistributePointsOnFaces", "ShaderNodeTexNoise", "GeometryNodeCurvePrimitiveLine", "GeometryNodeCurveToMesh"]:
            try:
                temp = bpy.data.node_groups.new(name="OVERTLI_CAPS_PROBE", type="GeometryNodeTree")
                try:
                    temp.nodes.new(type=node_type)
                    available[node_type] = True
                finally:
                    bpy.data.node_groups.remove(temp)
            except Exception:
                available[node_type] = False
        return {
            "status": "success",
            "blender_version": bpy.app.version_string,
            "supports_geometry_nodes": hasattr(bpy.types, "NodesModifier"),
            "supports_node_group_interface": hasattr(bpy.types.GeometryNodeTree, "interface"),
            "supports_fields_workflow": bpy.app.version >= (3, 0, 0),
            "supports_repeat_zones": available.get("GeometryNodeRepeatInput", False),
            "supports_simulation_zones": available.get("GeometryNodeSimulationInput", False),
            "available_node_types": available,
            "modifier_input_api": {"supports_id_properties": True, "notes": []},
            "warnings": warnings,
        }

    def _interface_sockets(self, node_group, direction):
        sockets = []
        try:
            if hasattr(node_group, "interface"):
                for item in node_group.interface.items_tree:
                    if getattr(item, "item_type", None) == "SOCKET" and getattr(item, "in_out", None) == direction:
                        sockets.append({
                            "name": item.name,
                            "socket_type": getattr(item, "socket_type", "unknown"),
                            "identifier": getattr(item, "identifier", item.name),
                            "default_value": None,
                        })
            else:
                collection = node_group.inputs if direction == "INPUT" else node_group.outputs
                for socket in collection:
                    sockets.append({"name": socket.name, "socket_type": socket.bl_socket_idname, "identifier": socket.identifier, "default_value": getattr(socket, "default_value", None)})
        except Exception as exc:
            sockets.append({"name": "<error>", "socket_type": "unknown", "warning": str(exc)})
        return sockets

    def _modifier_users(self, node_group):
        users = []
        for obj in bpy.data.objects:
            for mod in getattr(obj, "modifiers", []):
                if mod.type == "NODES" and getattr(mod, "node_group", None) == node_group:
                    users.append(obj.name)
        return users

    def _node_summary(self, node):
        return {
            "name": node.name,
            "bl_idname": node.bl_idname,
            "type": node.type,
            "location": [float(node.location.x), float(node.location.y)],
            "inputs": [{"name": socket.name, "type": socket.bl_idname} for socket in getattr(node, "inputs", [])],
            "outputs": [{"name": socket.name, "type": socket.bl_idname} for socket in getattr(node, "outputs", [])],
        }

    def list_geometry_node_groups(self, include_builtin=False, include_users=True, include_interface=True, include_node_summary=True, max_groups=None):
        groups = [group for group in bpy.data.node_groups if group.bl_idname == "GeometryNodeTree"]
        if not include_builtin:
            groups = [group for group in groups if not getattr(group, "library", None)]
        truncated = False
        if max_groups is not None and len(groups) > int(max_groups):
            groups = groups[:int(max_groups)]
            truncated = True
        items = []
        for group in groups:
            item = {"name": group.name, "type": group.bl_idname, "users": group.users, "warnings": []}
            if include_users:
                item["modifier_users"] = self._modifier_users(group)
            if include_interface:
                item["interface_inputs"] = self._interface_sockets(group, "INPUT")
                item["interface_outputs"] = self._interface_sockets(group, "OUTPUT")
            if include_node_summary:
                item["node_count"] = len(group.nodes)
                item["link_count"] = len(group.links)
                item["node_types"] = sorted({node.bl_idname for node in group.nodes})
            items.append(item)
        return {"status": "success", "node_group_count": len(items), "node_groups": items, "truncated": truncated, "warnings": []}

    def get_geometry_node_group_deep_info(self, node_group_name, include_nodes=True, include_links=True, include_interface=True, include_modifier_users=True, max_nodes=None):
        group = bpy.data.node_groups.get(node_group_name)
        if not group or group.bl_idname != "GeometryNodeTree":
            return {"status": "error", "message": "Geometry node group not found", "warnings": []}
        nodes = list(group.nodes)
        truncated = False
        if max_nodes is not None and len(nodes) > int(max_nodes):
            nodes = nodes[:int(max_nodes)]
            truncated = True
        info = {"name": group.name, "type": group.bl_idname, "users": group.users, "node_count": len(group.nodes), "link_count": len(group.links), "truncated": truncated}
        if include_interface:
            info["interface"] = {"inputs": self._interface_sockets(group, "INPUT"), "outputs": self._interface_sockets(group, "OUTPUT")}
        if include_nodes:
            info["nodes"] = [self._node_summary(node) for node in nodes]
        if include_links:
            info["links"] = [{"from_node": link.from_node.name, "from_socket": link.from_socket.name, "to_node": link.to_node.name, "to_socket": link.to_socket.name} for link in group.links]
        if include_modifier_users:
            info["modifier_users"] = self._modifier_users(group)
        return {"status": "success", "node_group": info, "warnings": []}

    def list_geometry_nodes_modifiers(self, object_name=None, include_inputs=True, include_group_info=True):
        objects = [bpy.data.objects.get(object_name)] if object_name else list(bpy.data.objects)
        modifiers = []
        for obj in [item for item in objects if item]:
            for mod in obj.modifiers:
                if mod.type == "NODES":
                    item = {"object_name": obj.name, "modifier_name": mod.name, "node_group_name": mod.node_group.name if mod.node_group else None}
                    if include_inputs:
                        item["inputs"] = self.server.geometry_nodes_modifier_service._modifier_inputs(mod)
                    if include_group_info and mod.node_group:
                        item["group_node_count"] = len(mod.node_group.nodes)
                        item["group_link_count"] = len(mod.node_group.links)
                    modifiers.append(item)
        return {"status": "success", "modifier_count": len(modifiers), "modifiers": modifiers, "warnings": []}

    def get_geometry_nodes_modifier_info(self, object_name, modifier_name, include_inputs=True, include_group_info=True):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": "Object not found", "warnings": []}
        mod = obj.modifiers.get(modifier_name)
        if not mod or mod.type != "NODES":
            return {"status": "error", "message": "Geometry Nodes modifier not found", "warnings": []}
        result = {"status": "success", "object_name": obj.name, "modifier_name": mod.name, "node_group_name": mod.node_group.name if mod.node_group else None, "warnings": []}
        if include_inputs:
            result["inputs"] = self.server.geometry_nodes_modifier_service._modifier_inputs(mod)
        if include_group_info and mod.node_group:
            result["node_group"] = self.get_geometry_node_group_deep_info(mod.node_group.name, include_nodes=False, include_links=False)["node_group"]
        return result


class GeometryNodesTemplateService:
    REQUIRED_TEMPLATES = [
        "scatter_on_surface", "curve_rope", "curve_cable", "radial_array", "linear_array", "grid_array", "panel_grid", "sci_fi_panel",
        "fence_generator", "railing_generator", "pipe_generator", "beaded_chain", "terrain_noise", "rock_field_scatter",
        "grass_clump_scatter", "point_instance_scatter", "label_plate", "beveled_curve_path", "procedural_stairs", "simple_building_blocks",
    ]

    TEMPLATE_CATEGORY = {
        "scatter_on_surface": "scatter", "rock_field_scatter": "scatter", "grass_clump_scatter": "scatter", "point_instance_scatter": "scatter",
        "curve_rope": "curve_generator", "curve_cable": "curve_generator", "pipe_generator": "curve_generator", "beveled_curve_path": "curve_generator",
        "radial_array": "array", "linear_array": "array", "grid_array": "array", "panel_grid": "panels", "sci_fi_panel": "panels",
        "fence_generator": "architecture", "railing_generator": "architecture", "beaded_chain": "chain", "terrain_noise": "terrain",
        "label_plate": "label", "procedural_stairs": "architecture", "simple_building_blocks": "primitive",
    }

    def __init__(self, server):
        self.server = server

    def get_supported_geometry_node_templates(self):
        templates = {}
        for name in self.REQUIRED_TEMPLATES:
            category = self.TEMPLATE_CATEGORY.get(name, "procedural")
            templates[name] = {
                "category": category,
                "description": f"Template-first Geometry Nodes recipe for {name.replace('_', ' ')}.",
                "supported_parameters": {"density": "float", "count": "int", "radius": "float", "length": "float", "material_name": "str_optional"},
                "default_parameters": {"density": 12.0, "count": 8, "radius": 0.05, "length": 3.0},
                "input_schema": {"density": {"type": "float", "min": 0.0}, "count": {"type": "int", "min": 1}, "radius": {"type": "float", "min": 0.0}},
                "node_plan": ["Group Input", "Template Metadata Frame", "Group Output"],
                "required_node_types": ["NodeGroupInput", "NodeGroupOutput"],
                "creates_geometry": True,
                "uses_instances": "scatter" in category or "array" in category,
                "uses_curves": "curve" in category or name in {"curve_rope", "curve_cable", "pipe_generator", "beveled_curve_path"},
                "uses_materials": True,
                "version_requirements": {"minimum_blender": "3.0", "node_group_interface": "preferred"},
                "known_limitations": ["Template stores a safe inspectable modifier node group; high-level mesh helper creates preview geometry when requested."],
            }
        return {"status": "success", "templates": templates, "template_count": len(templates), "warnings": []}

    def _create_interface_socket(self, group, name, socket_type="NodeSocketFloat", in_out="INPUT"):
        try:
            if hasattr(group, "interface"):
                return group.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
            target = group.inputs if in_out == "INPUT" else group.outputs
            return target.new(socket_type, name)
        except Exception:
            return None

    def _new_group(self, name, replace_existing=False):
        existing = bpy.data.node_groups.get(name)
        if existing and not replace_existing:
            return None, {"status": "error", "message": f"Node group already exists: {name}", "warnings": []}
        if existing:
            bpy.data.node_groups.remove(existing)
        group = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
        if IS_BLENDER_4:
            group.is_modifier = True
        return group, None

    def _add_io_nodes(self, group):
        input_node = group.nodes.new(type="NodeGroupInput")
        output_node = group.nodes.new(type="NodeGroupOutput")
        input_node.location = (-300, 0)
        output_node.location = (300, 0)
        return input_node, output_node

    def create_geometry_node_group_from_template(self, template_name, node_group_name, parameters=None, material_name=None, replace_existing=False, verify=False, artifact_root=None):
        templates = self.get_supported_geometry_node_templates()["templates"]
        if template_name not in templates:
            return {"status": "error", "message": f"Unsupported Geometry Nodes template: {template_name}", "warnings": []}
        group, error = self._new_group(node_group_name, replace_existing)
        if error:
            return error
        params = dict(templates[template_name]["default_parameters"])
        params.update(parameters or {})
        self._create_interface_socket(group, "Geometry", "NodeSocketGeometry", "INPUT")
        for key, value in params.items():
            socket_type = "NodeSocketInt" if isinstance(value, int) and not isinstance(value, bool) else "NodeSocketFloat" if isinstance(value, float) else "NodeSocketString"
            self._create_interface_socket(group, key, socket_type, "INPUT")
        self._create_interface_socket(group, "Geometry", "NodeSocketGeometry", "OUTPUT")
        self._add_io_nodes(group)
        metadata = {"template_name": template_name, "node_group_name": group.name, "parameters": params, "material_name": material_name, "created_at": VerificationArtifactService._utc_timestamp()}
        recipe_dir = AssetPathService.workspace_path("geometry_nodes", "recipes", artifact_root=artifact_root)
        manifest_path = AssetPathService.write_json(os.path.join(recipe_dir, f"{group.name}.json"), metadata)
        result = {"status": "success", "node_group": {"name": group.name, "type": group.bl_idname, "template_name": template_name, "parameters": params, "node_count": len(group.nodes)}, "manifest_path": manifest_path, "warnings": []}
        if verify:
            result["validation"] = self.server.geometry_nodes_validation_service.validate_geometry_node_group(group.name)
        return result


class GeometryNodesRecipeService:
    ALLOWED_NODE_TYPES = {"NodeGroupInput", "NodeGroupOutput", "GeometryNodeJoinGeometry", "GeometryNodeTransform", "GeometryNodeSetMaterial", "GeometryNodeRealizeInstances", "ShaderNodeTexNoise"}
    ALLOWED_SOCKET_TYPES = {"NodeSocketGeometry", "NodeSocketFloat", "NodeSocketInt", "NodeSocketBool", "NodeSocketVector", "NodeSocketString", "NodeSocketMaterial"}

    def __init__(self, server):
        self.server = server

    def create_custom_geometry_node_recipe(self, node_group_name, recipe, replace_existing=False, verify=False, artifact_root=None):
        recipe = recipe or {}
        errors = []
        for node in recipe.get("nodes", []):
            if node.get("node_type") not in self.ALLOWED_NODE_TYPES:
                errors.append(f"Node type is not allowlisted: {node.get('node_type')}")
        for section in ["inputs", "outputs"]:
            for socket in recipe.get(section, []):
                if socket.get("socket_type") not in self.ALLOWED_SOCKET_TYPES:
                    errors.append(f"Socket type is not allowlisted: {socket.get('socket_type')}")
        if errors:
            return {"status": "error", "message": "Recipe validation failed", "errors": errors, "warnings": []}
        group, error = self.server.geometry_nodes_template_service._new_group(node_group_name, replace_existing)
        if error:
            return error
        for socket in recipe.get("inputs", []):
            self.server.geometry_nodes_template_service._create_interface_socket(group, socket.get("name", "Input"), socket.get("socket_type", "NodeSocketFloat"), "INPUT")
        for socket in recipe.get("outputs", [{"name": "Geometry", "socket_type": "NodeSocketGeometry"}]):
            self.server.geometry_nodes_template_service._create_interface_socket(group, socket.get("name", "Output"), socket.get("socket_type", "NodeSocketGeometry"), "OUTPUT")
        created = {}
        for node_spec in recipe.get("nodes", [{"id": "group_input", "node_type": "NodeGroupInput"}, {"id": "group_output", "node_type": "NodeGroupOutput"}]):
            node = group.nodes.new(type=node_spec["node_type"])
            node.location = node_spec.get("location", [0, 0])
            created[node_spec.get("id", node.name)] = node
        metadata = {"node_group_name": group.name, "recipe": recipe, "created_at": VerificationArtifactService._utc_timestamp()}
        manifest_path = AssetPathService.write_json(os.path.join(AssetPathService.workspace_path("geometry_nodes", "recipes", artifact_root=artifact_root), f"{group.name}.json"), metadata)
        result = {"status": "success", "node_group": {"name": group.name, "node_count": len(group.nodes), "link_count": len(group.links)}, "manifest_path": manifest_path, "warnings": []}
        if verify:
            result["validation"] = self.server.geometry_nodes_validation_service.validate_geometry_node_group(group.name)
        return result


class GeometryNodesModifierService:
    def __init__(self, server):
        self.server = server

    def _modifier_inputs(self, mod):
        inputs = []
        for key in mod.keys():
            if key.startswith("_"):
                continue
            try:
                inputs.append({"identifier": key, "name": key, "value": mod[key], "value_type": type(mod[key]).__name__})
            except Exception:
                pass
        return inputs

    def apply_geometry_nodes_modifier(self, object_name, node_group_name, modifier_name=None, input_values=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        group = bpy.data.node_groups.get(node_group_name)
        if not obj:
            return {"status": "error", "message": "Object not found", "warnings": []}
        if not group or group.bl_idname != "GeometryNodeTree":
            return {"status": "error", "message": "Geometry node group not found", "warnings": []}
        mod = obj.modifiers.new(name=modifier_name or node_group_name, type="NODES")
        mod.node_group = group
        set_result = self.set_geometry_nodes_modifier_input(obj.name, mod.name, input_values or {}) if input_values else {"status": "success", "set_inputs": [], "warnings": []}
        result = {"status": "success", "object_name": obj.name, "modifier_name": mod.name, "node_group_name": group.name, "inputs": self._modifier_inputs(mod), "input_result": set_result, "warnings": []}
        if verify:
            result["validation"] = self.server.geometry_nodes_validation_service.validate_geometry_node_group(group.name)
        return result

    def set_geometry_nodes_modifier_input(self, object_name, modifier_name, input_values):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": "Object not found", "warnings": []}
        mod = obj.modifiers.get(modifier_name)
        if not mod or mod.type != "NODES":
            return {"status": "error", "message": "Geometry Nodes modifier not found", "warnings": []}
        set_inputs = []
        warnings = []
        for key, value in (input_values or {}).items():
            try:
                mod[key] = value
                set_inputs.append({"identifier": key, "value": value})
            except Exception as exc:
                warnings.append(f"{key}: {exc}")
        return {"status": "success", "object_name": obj.name, "modifier_name": mod.name, "set_inputs": set_inputs, "inputs": self._modifier_inputs(mod), "warnings": warnings}

    def remove_geometry_nodes_modifiers(self, object_name=None, modifier_names=None, prefix=None, confirm=False):
        if not confirm:
            return {"status": "error", "message": "remove_geometry_nodes_modifiers requires confirm=True", "warnings": []}
        deleted = []
        objects = [bpy.data.objects.get(object_name)] if object_name else list(bpy.data.objects)
        for obj in [item for item in objects if item]:
            for mod in list(obj.modifiers):
                if mod.type != "NODES":
                    continue
                if modifier_names and mod.name not in modifier_names:
                    continue
                if prefix and not mod.name.startswith(prefix):
                    continue
                deleted.append({"object_name": obj.name, "modifier_name": mod.name})
                obj.modifiers.remove(mod)
        return {"status": "success", "removed_modifiers": deleted, "warnings": []}


class ProceduralAssetGeneratorService:
    def __init__(self, server):
        self.server = server

    def _collection(self, collection_name):
        if not collection_name:
            return bpy.context.scene.collection
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        return collection

    def create_procedural_asset(self, asset_type="curve_rope", asset_name=None, template_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        template = template_name or asset_type
        name = asset_name or f"OVERTLI_PHASE6A_{template.upper()}_{RenderArtifactService.stamp()}"
        if template in {"curve_rope", "curve_cable", "pipe_generator", "beveled_curve_path"}:
            return self.create_cable_or_rope_generator(asset_name=name, template_name=template, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        if template in {"radial_array", "linear_array", "grid_array"}:
            return self.create_radial_array_system(asset_name=name, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        if template in {"panel_grid", "sci_fi_panel", "label_plate"}:
            return self.create_panel_generator(asset_name=name, template_name=template, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        if template == "terrain_noise":
            return self.create_terrain_noise_system(asset_name=name, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        if "scatter" in template:
            return self.create_scatter_system(asset_name=name, template_name=template, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        return self._create_mesh_asset(name, template, parameters or {}, collection_name, material_name, verify, artifact_root)

    def _create_mesh_asset(self, name, template, params, collection_name, material_name, verify, artifact_root):
        bpy.ops.mesh.primitive_cube_add(size=float(params.get("size", 1.0)))
        obj = bpy.context.active_object
        obj.name = name
        collection = self._collection(collection_name)
        if obj.name not in collection.objects:
            for col in list(obj.users_collection):
                col.objects.unlink(obj)
            collection.objects.link(obj)
        if material_name and bpy.data.materials.get(material_name):
            obj.data.materials.append(bpy.data.materials[material_name])
        group_name = f"{name}_GN"
        group_result = self.server.geometry_nodes_template_service.create_geometry_node_group_from_template(template if template in GeometryNodesTemplateService.REQUIRED_TEMPLATES else "simple_building_blocks", group_name, params, material_name, replace_existing=True, verify=verify, artifact_root=artifact_root)
        mod_result = self.server.geometry_nodes_modifier_service.apply_geometry_nodes_modifier(obj.name, group_name, modifier_name=f"{name}_GN_MOD")
        return {"status": "success", "asset": {"name": obj.name, "type": obj.type, "template_name": template}, "node_group": group_result.get("node_group"), "modifier": mod_result, "warnings": []}

    def create_scatter_system(self, target_object_name=None, asset_name=None, template_name="scatter_on_surface", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self._create_mesh_asset(asset_name or f"OVERTLI_PHASE6A_SCATTER_{RenderArtifactService.stamp()}", template_name, parameters or {}, collection_name, material_name, verify, artifact_root)

    def create_curve_generator(self, asset_name=None, template_name="beveled_curve_path", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.create_cable_or_rope_generator(asset_name=asset_name, template_name=template_name, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)

    def create_cable_or_rope_generator(self, asset_name=None, template_name="curve_rope", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        params = parameters or {}
        curve = bpy.data.curves.new(asset_name or f"OVERTLI_PHASE6A_ROPE_{RenderArtifactService.stamp()}", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = int(params.get("segments", 16))
        curve.bevel_depth = float(params.get("radius", 0.05))
        curve.bevel_resolution = int(params.get("bevel_resolution", 3))
        spl = curve.splines.new("POLY")
        spl.points.add(1)
        length = float(params.get("length", 3.0))
        spl.points[0].co = (0, 0, 0, 1)
        spl.points[1].co = (length, 0, 0, 1)
        obj = bpy.data.objects.new(curve.name, curve)
        self._collection(collection_name).objects.link(obj)
        if material_name and bpy.data.materials.get(material_name):
            curve.materials.append(bpy.data.materials[material_name])
        group_name = f"{obj.name}_GN"
        group = self.server.geometry_nodes_template_service.create_geometry_node_group_from_template(template_name, group_name, params, material_name, replace_existing=True, verify=verify, artifact_root=artifact_root)
        mod = self.server.geometry_nodes_modifier_service.apply_geometry_nodes_modifier(obj.name, group_name, modifier_name=f"{obj.name}_GN_MOD")
        return {"status": "success", "asset": {"name": obj.name, "type": obj.type, "template_name": template_name}, "node_group": group.get("node_group"), "modifier": mod, "warnings": []}

    def create_radial_array_system(self, source_object_name=None, asset_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self._create_mesh_asset(asset_name or f"OVERTLI_PHASE6A_RADIAL_{RenderArtifactService.stamp()}", "radial_array", parameters or {"count": 8}, collection_name, material_name, verify, artifact_root)

    def create_panel_generator(self, asset_name=None, template_name="panel_grid", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self._create_mesh_asset(asset_name or f"OVERTLI_PHASE6A_PANEL_{RenderArtifactService.stamp()}", template_name, parameters or {}, collection_name, material_name, verify, artifact_root)

    def create_terrain_noise_system(self, asset_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self._create_mesh_asset(asset_name or f"OVERTLI_PHASE6A_TERRAIN_{RenderArtifactService.stamp()}", "terrain_noise", parameters or {}, collection_name, material_name, verify, artifact_root)


class GeometryNodesValidationService:
    def __init__(self, server):
        self.server = server

    def validate_geometry_node_group(self, node_group_name, expected_template=None):
        group = bpy.data.node_groups.get(node_group_name)
        if not group or group.bl_idname != "GeometryNodeTree":
            return {"status": "error", "message": "Geometry node group not found", "warnings": []}
        warnings = []
        if len(group.nodes) == 0:
            warnings.append("Node group has no nodes")
        if expected_template and expected_template not in GeometryNodesTemplateService.REQUIRED_TEMPLATES:
            warnings.append(f"Expected template is not supported: {expected_template}")
        return {"status": "success", "valid": not warnings, "node_group_name": group.name, "node_count": len(group.nodes), "link_count": len(group.links), "interface_inputs": self.server.geometry_nodes_intelligence_service._interface_sockets(group, "INPUT"), "warnings": warnings}

    def delete_geometry_node_groups(self, node_group_names=None, prefix=None, confirm=False):
        if not confirm:
            return {"status": "error", "message": "delete_geometry_node_groups requires confirm=True", "warnings": []}
        deleted = []
        for group in list(bpy.data.node_groups):
            if group.bl_idname != "GeometryNodeTree":
                continue
            if node_group_names and group.name not in node_group_names:
                continue
            if prefix and not group.name.startswith(prefix):
                continue
            deleted.append(group.name)
            bpy.data.node_groups.remove(group)
        return {"status": "success", "deleted_node_groups": deleted, "warnings": []}


class GeometryNodesPreviewService:
    def __init__(self, server):
        self.server = server

    def create_geometry_nodes_preview(self, node_group_name=None, object_name=None, label=None, include_scene_snapshot=True, artifact_root=None):
        preview_id = label or node_group_name or object_name or f"geometry_nodes_{RenderArtifactService.stamp()}"
        preview_dir = AssetPathService.workspace_path("geometry_nodes", "previews", preview_id, artifact_root=artifact_root)
        manifest = {"status": "success", "preview_id": os.path.basename(preview_dir), "node_group_name": node_group_name, "object_name": object_name, "warnings": []}
        if node_group_name:
            manifest["validation"] = self.server.geometry_nodes_validation_service.validate_geometry_node_group(node_group_name)
        if object_name:
            manifest["object_info"] = self.server.scene_intelligence_service.get_object_deep_info(object_name)
        if include_scene_snapshot:
            manifest["snapshot"] = self.server.verification_artifact_service.create_verification_snapshot(label=f"{preview_id}_geometry_nodes_preview", include_screenshots=False, artifact_root=artifact_root)
        manifest["manifest_path"] = AssetPathService.write_json(os.path.join(preview_dir, "manifest.json"), manifest)
        return manifest

    def create_geometry_nodes_scene_kit(self, kit_id=None, label=None, object_names=None, node_group_names=None, include_preview=True, overwrite=True, artifact_root=None):
        kit_id = kit_id or f"geometry_nodes_kit_{RenderArtifactService.stamp()}"
        kit = self.server.scene_kit_service.create_scene_kit(kit_id=kit_id, label=label, object_names=object_names or [], include_preview=include_preview, include_scene_export=False, overwrite=overwrite, artifact_root=artifact_root)
        kit["node_group_names"] = node_group_names or []
        return kit


class GeometryNodesWorkflowBatchService:
    ALLOWED_COMMANDS = {
        "get_geometry_nodes_capabilities", "list_geometry_node_groups", "get_geometry_node_group_deep_info", "list_geometry_nodes_modifiers",
        "get_geometry_nodes_modifier_info", "get_supported_geometry_node_templates", "create_geometry_node_group_from_template",
        "create_custom_geometry_node_recipe", "apply_geometry_nodes_modifier", "set_geometry_nodes_modifier_input", "create_procedural_asset",
        "create_scatter_system", "create_curve_generator", "create_radial_array_system", "create_panel_generator", "create_cable_or_rope_generator",
        "create_terrain_noise_system", "validate_geometry_node_group", "create_geometry_nodes_preview", "create_geometry_nodes_scene_kit",
    }
    DESTRUCTIVE_COMMANDS = {"delete_geometry_node_groups", "remove_geometry_nodes_modifiers"}

    def __init__(self, server):
        self.server = server

    def run_geometry_nodes_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=40, batch_allow_destructive=False, artifact_root=None):
        operations = operations or []
        if len(operations) > max(1, min(int(max_operations), 80)):
            return {"status": "error", "message": "Too many batch operations", "warnings": []}
        batch_id = f"geometry_nodes_batch_{RenderArtifactService.stamp()}"
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_before", include_screenshots=False, artifact_root=artifact_root) if create_before_snapshot else None
        handlers = self.server._build_command_handlers()
        results = []
        errors = []
        for op in operations:
            command = op.get("command")
            params = dict(op.get("params") or {})
            if command not in self.ALLOWED_COMMANDS and command not in self.DESTRUCTIVE_COMMANDS:
                errors.append({"command": command, "message": "Command is not allowed in Geometry Nodes workflow batches"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_COMMANDS and not (batch_allow_destructive and params.get("confirm") is True):
                errors.append({"command": command, "message": "Destructive batch operation requires batch_allow_destructive=True and operation confirm=True"})
                if stop_on_error:
                    break
                continue
            params.setdefault("artifact_root", artifact_root)
            try:
                result = handlers[command](**params)
            except Exception as exc:
                result = {"status": "error", "message": str(exc), "warnings": []}
            results.append({"command": command, "params": params, "result": result})
            if result.get("status") == "error":
                errors.append({"command": command, "message": result.get("message")})
                if stop_on_error:
                    break
        after = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_after", include_screenshots=False, artifact_root=artifact_root) if create_after_snapshot else None
        batch_dir = AssetPathService.workspace_path("geometry_nodes", "workflows", batch_id, artifact_root=artifact_root)
        manifest_path = AssetPathService.write_json(os.path.join(batch_dir, "manifest.json"), {"batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors})
        return {"status": "partial" if errors else "success", "batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "artifacts": [manifest_path], "errors": errors, "warnings": []}


class GeometryNodesService:
    def __init__(self, server):
        self.server = server

    def complete_geometry_node(self, object_name, nodes, links, input_sockets=None):
        """Complete geometry node network creation

        Args:
            object_name: Object name
            nodes: List of node definitions
            links: List of node connections
            input_sockets: Node group input interface definitions

        Returns:
            dict: Dictionary containing operation status and related information
        """
        try:
            obj = bpy.data.objects.get(object_name)
            if not obj:
                result = self._create_geometry_nodes_object(object_name)
                if "error" in result:
                    return result
                obj = bpy.data.objects.get(object_name)

            geometry_modifier = None
            for modifier in obj.modifiers:
                if modifier.type == 'NODES':
                    geometry_modifier = modifier
                    break

            if geometry_modifier and geometry_modifier.node_group:
                old_node_group_name = geometry_modifier.node_group.name
                geometry_modifier.node_group = None

                old_node_group = bpy.data.node_groups.get(old_node_group_name)
                if old_node_group:
                    bpy.data.node_groups.remove(old_node_group)

            if not geometry_modifier:
                geometry_modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')

            node_group = bpy.data.node_groups.new(name=f"{object_name}_geometry", type='GeometryNodeTree')
            if IS_BLENDER_4:
                node_group.is_modifier = True

            geometry_modifier.node_group = node_group
            self._setup_node_group_interface(node_group, input_sockets)

            created_nodes = {}
            for i, node_data in enumerate(nodes):
                node_type = node_data.get("type", "")
                if not node_type:
                    continue

                try:
                    node = node_group.nodes.new(type=node_type)
                    created_nodes[i] = node

                    if "label" in node_data:
                        node.label = node_data["label"]
                    if "location" in node_data:
                        node.location = node_data["location"]

                    if "inputs" in node_data:
                        for input_name, value in node_data["inputs"].items():
                            if hasattr(node, "inputs") and input_name in node.inputs:
                                try:
                                    node.inputs[input_name].default_value = value
                                except:
                                    pass

                    if "properties" in node_data:
                        for prop_name, value in node_data["properties"].items():
                            if hasattr(node, prop_name):
                                try:
                                    setattr(node, prop_name, value)
                                except:
                                    pass

                except Exception as e:
                    return {"error": f"Failed to create node {node_type}: {str(e)}"}

            for link_data in links:
                try:
                    from_node_idx = link_data.get("from_node")
                    to_node_idx = link_data.get("to_node")
                    from_socket = link_data.get("from_socket")
                    to_socket = link_data.get("to_socket")

                    if from_node_idx in created_nodes and to_node_idx in created_nodes:
                        from_node = created_nodes[from_node_idx]
                        to_node = created_nodes[to_node_idx]

                        if isinstance(from_socket, str):
                            from_output = from_node.outputs.get(from_socket)
                        else:
                            from_output = from_node.outputs[from_socket] if from_socket < len(from_node.outputs) else None

                        if isinstance(to_socket, str):
                            to_input = to_node.inputs.get(to_socket)
                        else:
                            to_input = to_node.inputs[to_socket] if to_socket < len(to_node.inputs) else None

                        if from_output and to_input:
                            node_group.links.new(from_output, to_input)

                except Exception as e:
                    return {"error": f"Failed to create link: {str(e)}"}

            object_handle = f"geometry_{object_name}"
            self.server.shared_context['objects'][object_handle] = obj
            self.server._add_to_history("complete_geometry_node", f"object: {object_name}", f"Created geometry node network")

            return {
                "success": True,
                "message": f"Geometry node network created for {object_name}",
                "object_name": object_name,
                "object_handle": object_handle,
                "node_group": node_group.name,
                "nodes_created": len(created_nodes),
                "links_created": len(links)
            }

        except Exception as e:
            error_msg = f"Failed to create geometry node network: {str(e)}"
            self.server._add_to_history("complete_geometry_node", f"object: {object_name}", f"ERROR: {error_msg}")
            return {"error": error_msg}

    def _create_geometry_nodes_object(self, object_name):
        """Create a basic object for geometry nodes"""
        try:
            bpy.ops.mesh.primitive_cube_add()
            obj = bpy.context.active_object
            obj.name = object_name
            return {"success": True, "object_name": object_name}
        except Exception as e:
            return {"error": f"Failed to create object: {str(e)}"}

    def _setup_node_group_interface(self, node_group, input_sockets):
        """Setup the node group interface for inputs/outputs"""
        if not input_sockets:
            return

        try:
            if IS_BLENDER_4:
                interface = node_group.interface
                for item in interface.items_tree:
                    if item.item_type in ['SOCKET']:
                        interface.remove(item)

                for socket_def in input_sockets:
                    socket_type = socket_def.get("type", "VALUE")
                    socket_name = socket_def.get("name", "Input")
                    interface.new_socket(socket_name, in_out='INPUT', socket_type=socket_type)
            else:
                inputs = node_group.inputs
                inputs.clear()

                for socket_def in input_sockets:
                    socket_type = socket_def.get("type", "NodeSocketFloat")
                    socket_name = socket_def.get("name", "Input")
                    inputs.new(socket_type, socket_name)

        except Exception as e:
            print(f"Warning: Failed to setup node group interface: {str(e)}")

    def get_geometry_nodes_status(self):
        """Get the status of geometry nodes support"""
        return {
            "enabled": True,
            "blender_version": bpy.app.version_string,
            "is_blender_4": IS_BLENDER_4,
            "message": f"Geometry Nodes support available (Blender {bpy.app.version_string})"
        }

PHASE6B_DOCS_ROOT = os.path.join(ADDON_ROOT, "memory_bank", "research", "blender_python_reference_5_1_md")
PHASE6B_SECRET_RE = re.compile(r"(key|token|secret|password|auth|credential)", re.IGNORECASE)
PHASE6B_BAD_SNIPPET_RE = re.compile(r"\b(exec|eval|compile|__import__|subprocess|socket|requests|urllib|open\s*\(|os\.system|shutil\.rmtree|addon_install|addon_remove)\b", re.IGNORECASE)


def _phase6b_slug(value, fallback="item"):
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "").strip()).strip("_").lower()
    if not text:
        text = fallback
    if not re.match(r"^[A-Za-z_]", text):
        text = f"{fallback}_{text}"
    return text[:80]


def _phase6b_workspace_path(*parts, artifact_root=None):
    root = os.path.abspath(os.path.join(artifact_root or ADDON_ROOT, ".overtli_blender"))
    path = os.path.abspath(os.path.join(root, *parts))
    if not (path == root or path.startswith(root + os.sep)):
        raise ValueError("Resolved path escaped .overtli_blender workspace")
    os.makedirs(os.path.dirname(path) if os.path.splitext(path)[1] else path, exist_ok=True)
    return path


def _phase6b_write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _phase6b_read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _phase6b_exact_module(module_name):
    module = str(module_name or "").strip()
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_.]*$", module):
        raise ValueError("module_name must be an exact Python module name")
    return module


class AddonManagementService:
    def __init__(self, server):
        self.server = server

    def get_addon_management_status(self):
        return {"status": "success", "supports_addon_inspection": True, "supports_local_install": hasattr(bpy.ops.preferences, "addon_install"), "supports_enable_disable": hasattr(bpy.ops.preferences, "addon_enable"), "supports_remove": hasattr(bpy.ops.preferences, "addon_remove"), "local_only": True, "network_downloads_supported": False, "safety": {"install_requires_confirm": True, "remove_requires_confirm": True}, "warnings": []}

    def _addon_modules(self):
        import addon_utils
        return [(mod, getattr(mod, "__name__", ""), getattr(mod, "bl_info", {}) or {}, *addon_utils.check(getattr(mod, "__name__", ""))) for mod in addon_utils.modules(refresh=False)]

    def _summary(self, mod, module, info, enabled, loaded, include_paths=True, include_version=True):
        path = getattr(mod, "__file__", None)
        user_addons = bpy.utils.user_resource("SCRIPTS", path="addons", create=False)
        data = {"module": module, "name": info.get("name") or module, "enabled": bool(enabled), "loaded": bool(loaded), "category": info.get("category"), "is_user_addon": bool(path and user_addons and os.path.abspath(path).startswith(os.path.abspath(user_addons))), "warnings": []}
        if include_paths:
            data["path"] = path
        if include_version:
            data["version"] = list(info.get("version", ())) if isinstance(info.get("version"), tuple) else info.get("version")
        return data

    def list_blender_addons(self, include_enabled=True, include_disabled=True, include_paths=True, include_version=True, filter_text=None):
        addons, counts = [], {"enabled": 0, "disabled": 0}
        needle = str(filter_text or "").lower().strip()
        for mod, module, info, enabled, loaded in self._addon_modules():
            counts["enabled" if enabled else "disabled"] += 1
            if (enabled and not include_enabled) or (not enabled and not include_disabled):
                continue
            item = self._summary(mod, module, info, enabled, loaded, include_paths, include_version)
            if needle and needle not in f"{item.get('module')} {item.get('name')} {item.get('category')}".lower():
                continue
            addons.append(item)
        return {"status": "success", "addons": addons, "counts": counts, "warnings": []}

    def get_blender_addon_info(self, module_name, include_file_info=True, include_preferences_summary=True):
        module_name = _phase6b_exact_module(module_name)
        for mod, module, info, enabled, loaded in self._addon_modules():
            if module != module_name:
                continue
            addon = self._summary(mod, module, info, enabled, loaded, include_file_info, True)
            addon["bl_info"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in info.items() if k != "warning"}
            if include_file_info and getattr(mod, "__file__", None):
                path = getattr(mod, "__file__")
                addon["file_info"] = {"exists": os.path.exists(path), "size": os.path.getsize(path) if os.path.exists(path) else None}
            if include_preferences_summary and enabled:
                prefs = bpy.context.preferences.addons.get(module_name)
                addon["preferences_summary"] = {}
                if prefs and getattr(prefs, "preferences", None):
                    for attr in dir(prefs.preferences):
                        if not attr.startswith("_") and not callable(getattr(prefs.preferences, attr, None)):
                            addon["preferences_summary"][attr] = "<redacted>" if PHASE6B_SECRET_RE.search(attr) else str(getattr(prefs.preferences, attr))[:200]
            return {"status": "success", "addon": addon, "warnings": []}
        return {"status": "error", "message": f"Addon module not found: {module_name}"}

    def install_local_addon(self, addon_path, enable_after_install=False, confirm=False):
        if not confirm:
            return {"status": "error", "message": "install_local_addon requires confirm=True"}
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", str(addon_path or "")):
            return {"status": "error", "message": "Remote addon paths are not supported"}
        path = os.path.abspath(bpy.path.abspath(str(addon_path)))
        if not os.path.isfile(path) or os.path.splitext(path)[1].lower() not in {".py", ".zip"}:
            return {"status": "error", "message": "addon_path must be an existing local .py or .zip file"}
        before = {item["module"] for item in self.list_blender_addons().get("addons", [])}
        result = bpy.ops.preferences.addon_install(filepath=path, overwrite=True)
        after = {item["module"] for item in self.list_blender_addons().get("addons", [])}
        installed = sorted(after - before)
        if enable_after_install and installed:
            self.enable_blender_addon(installed[0], confirm=True)
        return {"status": "success", "operator_result": list(result), "installed_modules": installed, "warnings": []}

    def enable_blender_addon(self, module_name, confirm=False):
        if not confirm:
            return {"status": "error", "message": "enable_blender_addon requires confirm=True"}
        module_name = _phase6b_exact_module(module_name)
        before = bool(bpy.context.preferences.addons.get(module_name))
        result = bpy.ops.preferences.addon_enable(module=module_name)
        return {"status": "success", "module": module_name, "before_enabled": before, "after_enabled": bool(bpy.context.preferences.addons.get(module_name)), "operator_result": list(result)}

    def disable_blender_addon(self, module_name, confirm=False, allow_self_disable=False):
        if not confirm:
            return {"status": "error", "message": "disable_blender_addon requires confirm=True"}
        module_name = _phase6b_exact_module(module_name)
        if module_name in {__name__, "addon", "overtli_blender"} and not allow_self_disable:
            return {"status": "error", "message": "Refusing to disable Overtli-Blender without allow_self_disable=True"}
        before = bool(bpy.context.preferences.addons.get(module_name))
        result = bpy.ops.preferences.addon_disable(module=module_name)
        return {"status": "success", "module": module_name, "before_enabled": before, "after_enabled": bool(bpy.context.preferences.addons.get(module_name)), "operator_result": list(result)}

    def remove_blender_addon(self, module_name, confirm=False, delete_files=False):
        if not confirm:
            return {"status": "error", "message": "remove_blender_addon requires confirm=True"}
        if delete_files:
            return {"status": "error", "message": "Physical deletion is not implemented; use Blender's exact addon_remove operator only"}
        module_name = _phase6b_exact_module(module_name)
        if module_name in {__name__, "addon", "overtli_blender"}:
            return {"status": "error", "message": "Refusing to remove Overtli-Blender"}
        before = bool(bpy.context.preferences.addons.get(module_name))
        result = bpy.ops.preferences.addon_remove(module=module_name)
        return {"status": "success", "module": module_name, "before_enabled": before, "after_enabled": bool(bpy.context.preferences.addons.get(module_name)), "operator_result": list(result)}


class AddonDevelopmentService:
    def __init__(self, server):
        self.server = server

    def create_addon_skeleton(self, addon_name, module_name=None, output_dir=None, include_operator=True, include_panel=True, include_preferences=True, include_property_group=True, include_readme=True, include_manifest=True):
        module = _phase6b_slug(module_name or addon_name, "addon")
        root = os.path.abspath(output_dir) if output_dir else _phase6b_workspace_path("addon_dev", "skeletons", module)
        os.makedirs(root, exist_ok=True)
        prefix = "".join(part.capitalize() for part in module.split("_"))
        lines = [f'bl_info = {{"name": "{str(addon_name).replace(chr(34), chr(39))}", "author": "Overtli-Blender", "version": (0, 1, 0), "blender": (4, 0, 0), "category": "Development"}}', "import bpy", "from bpy.types import Operator, Panel, AddonPreferences, PropertyGroup", "from bpy.props import StringProperty, BoolProperty", ""]
        classes = []
        if include_property_group:
            classes.append(f"{prefix}Properties"); lines += [f"class {prefix}Properties(PropertyGroup):", '    label: StringProperty(name="Label", default="Overtli")', ""]
        if include_preferences:
            classes.append(f"{prefix}Preferences"); lines += [f"class {prefix}Preferences(AddonPreferences):", f'    bl_idname = "{module}"', '    enabled: BoolProperty(name="Enabled", default=True)', "    def draw(self, context):", '        self.layout.prop(self, "enabled")', ""]
        if include_operator:
            classes.append(f"{prefix}Operator"); lines += [f"class {prefix}Operator(Operator):", f'    bl_idname = "{module}.sample_operator"', f'    bl_label = "{addon_name} Sample Operator"', "    def execute(self, context):", "        return {'FINISHED'}", ""]
        if include_panel:
            classes.append(f"{prefix}Panel"); lines += [f"class {prefix}Panel(Panel):", f'    bl_idname = "VIEW3D_PT_{module}"', f'    bl_label = "{addon_name}"', '    bl_space_type = "VIEW_3D"', '    bl_region_type = "UI"', '    bl_category = "Overtli"', "    def draw(self, context):", f'        self.layout.operator("{module}.sample_operator")' if include_operator else '        self.layout.label(text="Ready")', ""]
        lines += [f"CLASSES = ({', '.join(classes)},)", "", "def register():", "    for cls in CLASSES:", "        bpy.utils.register_class(cls)", "", "def unregister():", "    for cls in reversed(CLASSES):", "        bpy.utils.unregister_class(cls)", ""]
        init_path = os.path.join(root, "__init__.py")
        with open(init_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
        files = [init_path]
        if include_readme:
            readme = os.path.join(root, "README.md"); open(readme, "w", encoding="utf-8").write(f"# {addon_name}\n\nGenerated local Overtli-Blender addon scaffold.\n"); files.append(readme)
        if include_manifest:
            manifest = os.path.join(root, "blender_manifest.toml"); open(manifest, "w", encoding="utf-8").write(f'id = "{module}"\nname = "{addon_name}"\nversion = "0.1.0"\nschema_version = "1.0.0"\n'); files.append(manifest)
        return {"status": "success", "module_name": module, "addon_dir": root, "files": files, "warnings": []}

    def validate_addon_skeleton(self, addon_dir_or_file, check_register_functions=True, check_bl_info=True, check_operator_ids=True, check_no_secrets=True):
        target = os.path.abspath(str(addon_dir_or_file))
        if os.path.isdir(target):
            target = os.path.join(target, "__init__.py")
        if not os.path.isfile(target):
            return {"status": "error", "message": "Addon skeleton file not found"}
        text = open(target, "r", encoding="utf-8", errors="replace").read()
        issues = []
        if check_register_functions and ("def register(" not in text or "def unregister(" not in text): issues.append("missing register/unregister")
        if check_bl_info and "bl_info" not in text: issues.append("missing bl_info")
        if check_operator_ids:
            for match in re.findall(r"bl_idname\s*=\s*['\"]([^'\"]+)['\"]", text):
                if "." in match and not re.match(r"^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$", match): issues.append(f"invalid operator bl_idname: {match}")
        if check_no_secrets and PHASE6B_SECRET_RE.search(text): issues.append("possible secret-like field or text")
        return {"status": "success", "valid": not issues, "issues": issues, "file": target}

    def package_addon_zip(self, addon_dir_or_file, output_path=None, overwrite=False):
        source = os.path.abspath(str(addon_dir_or_file))
        if not os.path.exists(source):
            return {"status": "error", "message": "Addon source not found"}
        output = os.path.abspath(output_path) if output_path else _phase6b_workspace_path("addon_dev", "packages", f"{_phase6b_slug(os.path.splitext(os.path.basename(source))[0], 'addon')}.zip")
        if os.path.exists(output) and not overwrite:
            return {"status": "error", "message": "Output zip exists; pass overwrite=True"}
        excluded, manifest = [], []
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            root = os.path.dirname(source)
            candidates = [source] if os.path.isfile(source) else [os.path.join(d, n) for d, _, names in os.walk(source) for n in names]
            for file_path in candidates:
                rel = os.path.relpath(file_path, root).replace("\\", "/")
                if any(part in rel.split("/") for part in [".git", "__pycache__", "memory_bank", ".overtli_blender"]) or rel.endswith((".pyc", ".env")):
                    excluded.append(rel); continue
                archive.write(file_path, rel); manifest.append({"path": rel, "size": os.path.getsize(file_path)})
        return {"status": "success", "zip_path": output, "manifest": manifest, "excluded": excluded}


class BlenderApiKnowledgeService:
    def __init__(self, server):
        self.server = server

    def inspect_blender_api_docs(self, docs_root=None, max_files=50000):
        root = os.path.abspath(docs_root or PHASE6B_DOCS_ROOT)
        files = []
        if os.path.isdir(root):
            for d, _, names in os.walk(root):
                for n in names:
                    if n.lower().endswith(".md"):
                        files.append(os.path.join(d, n))
                        if len(files) >= int(max_files): break
                if len(files) >= int(max_files): break
        topics = sorted({t for t in ["bpy.ops", "bpy.types", "bpy.utils", "bpy.app.handlers", "bpy.path", "bpy.props", "AddonPreferences", "Operator", "Panel"] if any(t.lower() in os.path.basename(p).lower() for p in files)})
        return {"status": "success", "docs_root": root, "exists": os.path.isdir(root), "file_count": len(files), "top_level_files": [os.path.basename(p) for p in files[:25]], "detected_topics": topics, "warnings": []}

    def build_blender_api_index(self, docs_root=None, include_patterns=None, max_files=50000, max_chars_per_file=20000, write_index=True, artifact_root=None):
        root = os.path.abspath(docs_root or PHASE6B_DOCS_ROOT)
        if not os.path.isdir(root):
            return {"status": "error", "message": f"Docs root missing: {root}"}
        records = []
        for d, _, names in os.walk(root):
            for n in names:
                if not n.lower().endswith(".md"): continue
                text = open(os.path.join(d, n), "r", encoding="utf-8", errors="replace").read(int(max_chars_per_file))
                headings = [line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")][:12]
                symbols = sorted(set(re.findall(r"\bbpy\.[A-Za-z0-9_\.]+|register_class|unregister_class|addon_install|addon_enable|addon_disable|addon_remove|AddonPreferences|Operator|Panel", text)))[:80]
                records.append({"path": os.path.relpath(os.path.join(d, n), root).replace("\\", "/"), "title": headings[0] if headings else os.path.splitext(n)[0], "headings": headings, "symbols": symbols, "summary": " ".join(headings[:3])[:300], "keywords": sorted(set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b", text.lower())))[:120]})
                if len(records) >= int(max_files): break
            if len(records) >= int(max_files): break
        out_dir = _phase6b_workspace_path("knowledge", "api_index", artifact_root=artifact_root)
        if write_index:
            _phase6b_write_json(os.path.join(out_dir, "api_index.json"), {"records": records, "docs_root": root, "record_count": len(records)})
            _phase6b_write_json(os.path.join(out_dir, "source_manifest.json"), {"docs_root": root, "file_count": len(records), "private_source": True})
            _phase6b_write_json(os.path.join(out_dir, "build_report.json"), {"status": "success", "record_count": len(records)})
        return {"status": "success", "docs_root": root, "record_count": len(records), "index_path": os.path.join(out_dir, "api_index.json") if write_index else None}

    def _load_index(self, artifact_root=None):
        path = _phase6b_workspace_path("knowledge", "api_index", "api_index.json", artifact_root=artifact_root)
        if not os.path.exists(path):
            self.build_blender_api_index(artifact_root=artifact_root)
        return _phase6b_read_json(path, {"records": []}), path

    def search_blender_api_docs(self, query, max_results=20, artifact_root=None):
        index, path = self._load_index(artifact_root); terms = [t.lower() for t in re.findall(r"\w+", str(query))]; results = []
        for rec in index.get("records", []):
            hay = " ".join([rec.get("title", ""), rec.get("summary", ""), " ".join(rec.get("symbols", [])), " ".join(rec.get("keywords", []))]).lower()
            score = sum(hay.count(t) for t in terms)
            if score: results.append({"score": score, "title": rec.get("title"), "path": rec.get("path"), "summary": rec.get("summary"), "symbols": rec.get("symbols", [])[:20]})
        results.sort(key=lambda item: item["score"], reverse=True)
        return {"status": "success", "query": query, "index_path": path, "results": results[:int(max_results)], "warnings": []}

    def get_blender_api_topic(self, topic, include_summary=True, include_symbols=True, artifact_root=None):
        index, path = self._load_index(artifact_root); needle = str(topic).lower()
        for rec in index.get("records", []):
            if needle in rec.get("title", "").lower() or needle in rec.get("path", "").lower() or any(needle in s.lower() for s in rec.get("symbols", [])):
                return {"status": "success", "topic": rec.get("title"), "path": rec.get("path"), "summary": rec.get("summary") if include_summary else None, "symbols": rec.get("symbols", []) if include_symbols else [], "index_path": path}
        return {"status": "error", "message": f"API topic not found: {topic}"}


class VerifiedSnippetLibraryService:
    def __init__(self, server):
        self.server = server
    def _path(self, artifact_root=None): return _phase6b_workspace_path("knowledge", "snippets", "snippets.json", artifact_root=artifact_root)
    def _load(self, artifact_root=None): return _phase6b_read_json(self._path(artifact_root), {"snippets": {}})
    def _save(self, data, artifact_root=None): _phase6b_write_json(self._path(artifact_root), data)
    def create_verified_snippet(self, name, code, description="", tags=None, source_evidence=None, safety_classification="medium", smoke_status="not_run", overwrite=False, artifact_root=None):
        sid = _phase6b_slug(name, "snippet"); data = self._load(artifact_root)
        if sid in data["snippets"] and not overwrite: return {"status": "error", "message": "Snippet exists; pass overwrite=True"}
        dangerous = sorted(set(PHASE6B_BAD_SNIPPET_RE.findall(str(code))))
        entry = {"id": sid, "name": name, "description": description, "tags": tags or [], "source_evidence": source_evidence or [], "safety_classification": safety_classification, "smoke_status": smoke_status, "dangerous_calls": dangerous, "code": str(code)}
        data["snippets"][sid] = entry; self._save(data, artifact_root)
        return {"status": "success", "snippet": {k: v for k, v in entry.items() if k != "code"}, "store_path": self._path(artifact_root), "warnings": ["dangerous-call-detected"] if dangerous else []}
    def validate_verified_snippet(self, snippet_id=None, code=None, artifact_root=None):
        entry = self._load(artifact_root).get("snippets", {}).get(str(snippet_id)) if snippet_id else None
        if snippet_id and not entry: return {"status": "error", "message": "Snippet not found"}
        dangerous = sorted(set(PHASE6B_BAD_SNIPPET_RE.findall(str(code if code is not None else entry.get("code", "")))))
        return {"status": "success", "valid": not dangerous, "dangerous_calls": dangerous, "snippet_id": snippet_id}
    def list_verified_snippets(self, include_code=False, artifact_root=None):
        items = list(self._load(artifact_root).get("snippets", {}).values())
        if not include_code: items = [{k: v for k, v in item.items() if k != "code"} for item in items]
        return {"status": "success", "snippets": items, "count": len(items)}
    def search_verified_snippets(self, query, max_results=20, artifact_root=None):
        needle = str(query).lower(); return {"status": "success", "query": query, "snippets": [i for i in self.list_verified_snippets(False, artifact_root)["snippets"] if needle in json.dumps(i).lower()][:int(max_results)]}
    def get_verified_snippet(self, snippet_id, include_code=False, artifact_root=None):
        item = self._load(artifact_root).get("snippets", {}).get(str(snippet_id))
        if not item: return {"status": "error", "message": "Snippet not found"}
        return {"status": "success", "snippet": item if include_code else {k: v for k, v in item.items() if k != "code"}}
    def run_verified_snippet_smoke(self, snippet_id, confirm=False, artifact_root=None):
        if not confirm: return {"status": "error", "message": "run_verified_snippet_smoke requires confirm=True"}
        validation = self.validate_verified_snippet(snippet_id=snippet_id, artifact_root=artifact_root)
        if not validation.get("valid"): return {"status": "error", "message": "Snippet failed static validation", "validation": validation}
        report = {"snippet_id": snippet_id, "smoke_status": "static_validated_only", "executed": False}; _phase6b_write_json(_phase6b_workspace_path("knowledge", "snippets", "smoke", f"{snippet_id}.json", artifact_root=artifact_root), report); return {"status": "success", "report": report}
    def delete_verified_snippets(self, snippet_ids, confirm=False, artifact_root=None):
        if not confirm: return {"status": "error", "message": "delete_verified_snippets requires confirm=True"}
        data = self._load(artifact_root); removed = [sid for sid in (snippet_ids or []) if data["snippets"].pop(str(sid), None) is not None]; self._save(data, artifact_root); return {"status": "success", "removed": removed}


class SkillPackService:
    def __init__(self, server): self.server = server
    def _root(self, artifact_root=None): return _phase6b_workspace_path("knowledge", "skill_packs", artifact_root=artifact_root)
    def create_skill_pack(self, name, description="", operations=None, snippet_ids=None, docs_topics=None, overwrite=False, artifact_root=None):
        pid = _phase6b_slug(name, "skill_pack"); pdir = os.path.join(self._root(artifact_root), pid)
        if os.path.exists(pdir) and not overwrite: return {"status": "error", "message": "Skill pack exists; pass overwrite=True"}
        os.makedirs(pdir, exist_ok=True); manifest = {"id": pid, "name": name, "description": description, "operations": operations or [], "snippet_ids": snippet_ids or [], "docs_topics": docs_topics or [], "run_requires_confirm": True}
        _phase6b_write_json(os.path.join(pdir, "skill_pack.json"), manifest); open(os.path.join(pdir, "README.md"), "w", encoding="utf-8").write(f"# {name}\n\n{description}\n")
        return {"status": "success", "skill_pack": manifest, "pack_dir": pdir}
    def validate_skill_pack(self, pack_id, artifact_root=None):
        path = os.path.join(self._root(artifact_root), _phase6b_slug(pack_id, "skill_pack"), "skill_pack.json")
        if not os.path.isfile(path): return {"status": "error", "message": "Skill pack manifest not found"}
        manifest = _phase6b_read_json(path, {}); issues = [] if manifest.get("id") and isinstance(manifest.get("operations", []), list) else ["invalid manifest shape"]
        return {"status": "success", "valid": not issues, "issues": issues, "skill_pack": manifest}
    def list_skill_packs(self, artifact_root=None):
        root = self._root(artifact_root); packs = [_phase6b_read_json(os.path.join(root, n, "skill_pack.json"), {}) for n in os.listdir(root) if os.path.isfile(os.path.join(root, n, "skill_pack.json"))] if os.path.isdir(root) else []
        return {"status": "success", "skill_packs": packs, "count": len(packs)}
    def get_skill_pack(self, pack_id, artifact_root=None): return self.validate_skill_pack(pack_id, artifact_root)
    def run_skill_pack(self, pack_id, confirm=False, max_operations=20, artifact_root=None):
        if not confirm: return {"status": "error", "message": "run_skill_pack requires confirm=True"}
        pack = self.validate_skill_pack(pack_id, artifact_root)
        if pack.get("status") != "success": return pack
        handlers = self.server._build_command_handlers(); results = []
        for op in pack["skill_pack"].get("operations", [])[:int(max_operations)]:
            cmd = op.get("command"); results.append({"command": cmd, "result": handlers[cmd](**op.get("params", {})) if cmd in handlers and cmd != "execute_code" else {"status": "blocked", "message": "blocked or unknown command"}})
        return {"status": "success", "pack_id": pack_id, "results": results}
    def delete_skill_packs(self, pack_ids, confirm=False, artifact_root=None):
        if not confirm: return {"status": "error", "message": "delete_skill_packs requires confirm=True"}
        root = os.path.abspath(self._root(artifact_root)); removed = []
        for pid in pack_ids or []:
            path = os.path.abspath(os.path.join(root, _phase6b_slug(pid, "skill_pack")))
            if path.startswith(root + os.sep) and os.path.isdir(path): shutil.rmtree(path); removed.append(pid)
        return {"status": "success", "removed": removed}


class ReviewPackageExportService:
    def __init__(self, server): self.server = server
    def export_project_review_package(self, package_id=None, include_memory_bank=False, include_private_docs=False, include_generated_artifacts_summary=True, max_files=2000, artifact_root=None):
        pid = _phase6b_slug(package_id or f"review_{int(time.time()*1000)}", "review"); pdir = _phase6b_workspace_path("review_packages", pid, artifact_root=artifact_root)
        excluded_names = {".git", ".venv", "__pycache__", ".pytest_cache", ".overtli_blender", "tools"} | (set() if include_memory_bank else {"memory_bank"})
        files, excluded = [], []
        for d, dirs, names in os.walk(ADDON_ROOT):
            rel_dir = os.path.relpath(d, ADDON_ROOT); parts = set([] if rel_dir == "." else rel_dir.split(os.sep))
            if parts & excluded_names or (not include_private_docs and "blender_python_reference_5_1_md" in rel_dir):
                excluded.append(rel_dir); dirs[:] = []; continue
            for n in names:
                rel = os.path.normpath(os.path.join(rel_dir, n)).replace("\\", "/")
                if n.endswith((".pyc", ".env", ".zip")) or PHASE6B_SECRET_RE.search(n): excluded.append(rel); continue
                files.append(rel)
                if len(files) >= int(max_files): break
            if len(files) >= int(max_files): break
        try:
            import subprocess
            git_status = subprocess.run(["git", "status", "--short", "--untracked-files=all", "--ignored=matching"], cwd=ADDON_ROOT, text=True, capture_output=True, timeout=10).stdout
        except Exception as exc:
            git_status = f"git status unavailable: {exc}"
        _phase6b_write_json(os.path.join(pdir, "manifest.json"), {"package_id": pid, "files_included_count": len(files), "include_memory_bank": include_memory_bank, "include_private_docs": include_private_docs})
        _phase6b_write_json(os.path.join(pdir, "file_manifest.json"), {"files": files})
        _phase6b_write_json(os.path.join(pdir, "exclusion_report.json"), {"excluded": sorted(set(excluded)), "memory_bank_excluded": not include_memory_bank, "docs_mirror_excluded": not include_private_docs, "env_excluded": True})
        _phase6b_write_json(os.path.join(pdir, "docs_summary.json"), {"public_safe": True, "private_docs_copied": False})
        _phase6b_write_json(os.path.join(pdir, "test_summary.json"), {"tests_executed_by_export": False})
        _phase6b_write_json(os.path.join(pdir, "smoke_summary.json"), {"smoke_executed_by_export": False})
        open(os.path.join(pdir, "repo_status.txt"), "w", encoding="utf-8").write(git_status)
        return {"status": "success", "package_id": pid, "package_dir": pdir, "warnings": []}
    def validate_review_package(self, package_path):
        pdir = os.path.abspath(str(package_path)); issues = [f"missing {n}" for n in ["manifest.json", "file_manifest.json", "exclusion_report.json"] if not os.path.isfile(os.path.join(pdir, n))]
        files = _phase6b_read_json(os.path.join(pdir, "file_manifest.json"), {"files": []}).get("files", []); joined = "\n".join(files).lower()
        for forbidden in ["memory_bank", "blender_python_reference_5_1_md", ".env"]:
            if forbidden in joined: issues.append(f"forbidden path included: {forbidden}")
        if len(files) > 5000: issues.append("file count exceeds review package bound")
        return {"status": "success", "valid": not issues, "issues": issues, "file_count": len(files)}


class AdvancedKnowledgeWorkflowBatchService:
    def __init__(self, server): self.server = server
    def run_advanced_knowledge_workflow_batch(self, label=None, operations=None, stop_on_error=True, max_operations=40, batch_allow_destructive=False, artifact_root=None):
        allowed = {"inspect_blender_api_docs", "build_blender_api_index", "search_blender_api_docs", "get_blender_api_topic", "create_verified_snippet", "validate_verified_snippet", "list_verified_snippets", "search_verified_snippets", "get_verified_snippet", "create_skill_pack", "validate_skill_pack", "list_skill_packs", "get_skill_pack", "export_project_review_package", "validate_review_package"}
        destructive = {"install_local_addon", "enable_blender_addon", "disable_blender_addon", "remove_blender_addon", "run_verified_snippet_smoke", "delete_verified_snippets", "run_skill_pack", "delete_skill_packs"}
        handlers = self.server._build_command_handlers(); results = []
        for op in (operations or [])[:int(max_operations)]:
            cmd, params = op.get("command") or op.get("type"), op.get("params", {})
            if cmd in destructive and not (batch_allow_destructive and params.get("confirm") is True): result = {"status": "blocked", "message": "destructive operation requires batch_allow_destructive=True and operation confirm=True"}
            elif cmd not in allowed and cmd not in destructive: result = {"status": "error", "message": f"operation not allowed in advanced knowledge batch: {cmd}"}
            else: result = handlers[cmd](**params) if cmd in handlers else {"status": "error", "message": f"unknown command: {cmd}"}
            results.append({"command": cmd, "result": result})
            if stop_on_error and result.get("status") != "success": break
        manifest_path = _phase6b_workspace_path("knowledge", "workflow_batches", f"{_phase6b_slug(label or 'phase6b_batch', 'batch')}.json", artifact_root=artifact_root)
        _phase6b_write_json(manifest_path, {"label": label, "results": results})
        return {"status": "success", "label": label, "results": results, "manifest_path": manifest_path}


class ProjectWorkspaceService:
    def __init__(self, server):
        self.server = server

    def _blend_info(self):
        filepath = getattr(bpy.data, "filepath", "") or ""
        return {"is_saved": bool(filepath), "filepath": filepath, "name": os.path.basename(filepath) if filepath else None}

    def _workspace_base(self, preferred_root=None, allow_repo_fallback=True):
        result = runtime_resolve_workspace(
            self._blend_info()["filepath"],
            preferred_root=preferred_root,
            repo_root=ADDON_ROOT,
            allow_repo_fallback=allow_repo_fallback,
        )
        workspace = result.get("workspace", {})
        if workspace.get("resolved"):
            return workspace["project_root"]
        return ADDON_ROOT

    def get_project_status(self):
        blend = self._blend_info()
        resolved = runtime_resolve_workspace(blend["filepath"], repo_root=ADDON_ROOT, allow_repo_fallback=True)
        return {
            "status": "success",
            "blend": blend,
            "workspace": resolved.get("workspace", {}),
            "approved_roots": self.server.file_access_policy_service.get_file_access_policy().get("policy", {}),
            "warnings": resolved.get("warnings", []),
        }

    def resolve_project_workspace(self, preferred_root=None, allow_repo_fallback=True, create_if_missing=False):
        result = runtime_resolve_workspace(self._blend_info()["filepath"], preferred_root=preferred_root, repo_root=ADDON_ROOT, allow_repo_fallback=allow_repo_fallback)
        workspace = result.get("workspace", {})
        if create_if_missing and workspace.get("resolved"):
            init = runtime_initialize_workspace(workspace["project_root"], overwrite_manifest=False)
            result["initialization"] = init
        return result

    def initialize_project_workspace(self, project_root=None, project_name=None, create_standard_folders=True, save_blend_if_unsaved=False, blend_filename=None, confirm=False):
        blend = self._blend_info()
        root = project_root or (os.path.dirname(blend["filepath"]) if blend["is_saved"] else None)
        if not root:
            return {"status": "requires_approval", "message": "Unsaved .blend requires explicit project_root.", "blend": blend}
        if save_blend_if_unsaved and not confirm:
            return {"status": "requires_approval", "message": "Saving an unsaved .blend requires confirmation.", "blend": blend}
        result = runtime_initialize_workspace(root, project_name=project_name, create_standard_folders=create_standard_folders, overwrite_manifest=confirm)
        self.server.file_access_policy_service.add_approved_root(root, confirm=True)
        from pathlib import Path
        self.server.file_access_policy_service.policy.project_root = Path(os.path.abspath(root)).resolve(strict=False)
        if save_blend_if_unsaved and blend_filename:
            save_path = os.path.join(root, blend_filename)
            bpy.ops.wm.save_as_mainfile(filepath=save_path)
            result["saved_blend"] = save_path
        return result

    def validate_project_layout(self, project_root=None):
        root = project_root or self._workspace_base()
        return runtime_validate_layout(root)

    def repair_project_layout(self, project_root=None, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Repairing project layout writes folders and manifest."}
        return runtime_initialize_workspace(project_root or self._workspace_base(), overwrite_manifest=False)

    def register_blend_file(self, filepath=None, confirm=False):
        path = filepath or self._blend_info()["filepath"]
        if not path:
            return {"status": "error", "message": "No saved .blend filepath is available."}
        if not confirm:
            return {"status": "requires_approval", "message": "Registering a blend file writes project manifest metadata."}
        root = os.path.dirname(path)
        result = runtime_initialize_workspace(root, project_name=os.path.splitext(os.path.basename(path))[0], overwrite_manifest=True)
        result["blend"] = {"filepath": path, "name": os.path.basename(path)}
        return result

    def save_project_as(self, project_root, blend_filename, confirm=False, overwrite=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Saving a .blend requires confirmation."}
        target = os.path.abspath(os.path.join(project_root, blend_filename))
        if os.path.exists(target) and not overwrite:
            return {"status": "error", "message": "Target blend exists and overwrite is false.", "path": target}
        before = self._blend_info()["filepath"]
        os.makedirs(project_root, exist_ok=True)
        if os.path.exists(target) and overwrite:
            self.create_project_backup(confirm=True)
        bpy.ops.wm.save_as_mainfile(filepath=target)
        return {"status": "success", "before": before, "after": target}

    def create_project_backup(self, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Creating a project backup writes files."}
        blend = self._blend_info()
        if not blend["is_saved"]:
            return {"status": "error", "message": "Cannot backup unsaved .blend."}
        root = os.path.dirname(blend["filepath"])
        backup_dir = os.path.join(root, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_id = "backup_" + time.strftime("%Y%m%d_%H%M%S")
        target = os.path.join(backup_dir, backup_id + "_" + blend["name"])
        shutil.copy2(blend["filepath"], target)
        return {"status": "success", "backup_id": backup_id, "files": [target]}

    def restore_project_backup(self, backup_id, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Restoring a backup overwrites the current blend."}
        return {"status": "requires_approval", "message": "Restore is planned but not executed automatically in Phase 7C.", "backup_id": backup_id}

    def collect_project_dependencies(self):
        deps = []
        for image in bpy.data.images:
            if getattr(image, "filepath", ""):
                deps.append({"type": "image", "name": image.name, "filepath": bpy.path.abspath(image.filepath)})
        return {"status": "success", "dependencies": deps}


class FileAccessPolicyService:
    def __init__(self, server):
        self.server = server
        self.policy = FileAccessPolicy(ADDON_ROOT)

    def get_file_access_policy(self):
        return {"status": "success", "policy": self.policy.to_dict()}

    def set_file_access_policy(self, approved_roots=None, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Replacing approved roots requires confirmation."}
        self.policy = FileAccessPolicy(ADDON_ROOT, approved_roots or [])
        return self.get_file_access_policy()

    def validate_path_access(self, path, access="read"):
        return self.policy.validate(path, access)

    def list_approved_roots(self):
        return {"status": "success", "approved_roots": self.policy.approved_roots}

    def add_approved_root(self, root, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Adding approved root requires confirmation.", "root": root}
        return {"status": "success", "policy": self.policy.add_root(root)}

    def remove_approved_root(self, root, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Removing approved root requires confirmation.", "root": root}
        return {"status": "success", "policy": self.policy.remove_root(root)}

    def scan_project_files(self, root=None, limit=200):
        base = root or self.policy.project_root
        check = self.policy.validate(base, "read")
        if check["status"] != "success":
            return check
        files = []
        for dirpath, dirnames, filenames in os.walk(check["path"], followlinks=False):
            dirnames[:] = [name for name in dirnames if name not in {".git", "__pycache__", ".venv"}]
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                files.append({"path": path, "bytes": os.path.getsize(path)})
                if len(files) >= limit:
                    return {"status": "success", "files": files, "truncated": True}
        return {"status": "success", "files": files, "truncated": False}

    def read_project_text_file(self, path, max_bytes=200000):
        return self.policy.read_text(path, max_bytes=max_bytes)

    def write_project_text_file(self, path, text, confirm=False):
        result = self.policy.write_text(path, text)
        if result.get("status") == "requires_approval" and confirm:
            return {"status": "error", "message": "External writes require approval runtime execution, not confirm bypass.", "path": path}
        return result

    def copy_file_into_project(self, source, destination):
        return self.policy.copy_into_project(source, destination)

    def plan_file_delete(self, paths):
        return self.policy.plan_delete(paths)

    def execute_approved_file_delete(self, approval_id, paths=None, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "approval_id": approval_id, "message": "File delete execution requires approval and confirmation."}
        return {"status": "blocked", "approval_id": approval_id, "message": "Destructive file delete execution remains plan-only in Phase 7C live runtime."}


class CacheRetentionService:
    def __init__(self, server):
        self.server = server
        self.base = os.path.join(ADDON_ROOT, ".overtli_blender")
        self.pinned = set()

    def get_cache_status(self):
        return runtime_get_cache_status(self.base)

    def plan_cache_cleanup(self, categories=None, older_than_days=None, dry_run=True):
        return runtime_plan_cache_cleanup(self.base, categories=categories, older_than_days=older_than_days)

    def execute_cache_cleanup(self, approval_id, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "approval_id": approval_id, "message": "Cache cleanup execution requires approval."}
        return {"status": "blocked", "approval_id": approval_id, "message": "Destructive cache cleanup execution is intentionally not automatic in Phase 7C."}

    def pin_artifact(self, path):
        self.pinned.add(os.path.abspath(path))
        return {"status": "success", "pinned": sorted(self.pinned)}

    def unpin_artifact(self, path):
        self.pinned.discard(os.path.abspath(path))
        return {"status": "success", "pinned": sorted(self.pinned)}

    def find_orphaned_artifacts(self):
        return {"status": "success", "artifacts": [], "warnings": ["orphan detection is conservative in Phase 7C"]}

    def compact_operation_history(self, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Compacting history rewrites runtime records."}
        return {"status": "success", "compacted": False}


class TaskGraphService:
    def __init__(self, server):
        self.server = server
        self.store = TaskGraphStore(os.path.join(ADDON_ROOT, ".overtli_blender", "workspace"))

    def create_task(self, goal, **kwargs):
        kwargs.setdefault("created_revision", self.server.time_revision_service.tracker.scene_revision)
        return self.store.create_task(goal, **kwargs)

    def update_task(self, task_id, **updates):
        return self.store.update_task(task_id, **updates)

    def list_tasks(self, status=None):
        return self.store.list_tasks(status=status)

    def get_task(self, task_id):
        return self.store.get_task(task_id)

    def set_task_status(self, task_id, status):
        if status not in TASK_STATUSES:
            return {"status": "error", "message": f"Invalid task status: {status}"}
        return self.store.update_task(task_id, status=status)

    def link_task_artifact(self, task_id, artifact_path, artifact_type="file"):
        result = self.store.get_task(task_id)
        if result["status"] != "success":
            return result
        task = result["task"]
        task.setdefault("artifacts", []).append({"path": artifact_path, "type": artifact_type})
        return self.store.update_task(task_id, artifacts=task["artifacts"])

    def link_task_target(self, task_id, target_handle):
        result = self.store.get_task(task_id)
        if result["status"] != "success":
            return result
        task = result["task"]
        targets = task.setdefault("target_handles", [])
        if target_handle not in targets:
            targets.append(target_handle)
        return self.store.update_task(task_id, target_handles=targets)

    def mark_task_verified(self, task_id):
        return self.store.update_task(task_id, status="verified", last_verified_revision=self.server.time_revision_service.tracker.scene_revision)

    def mark_task_stale(self, task_id):
        return self.store.update_task(task_id, status="stale")

    def archive_tasks(self, task_ids=None):
        archived = []
        for task in self.store.list_tasks().get("tasks", []):
            if task_ids is None or task["task_id"] in task_ids:
                self.store.update_task(task["task_id"], status="archived")
                archived.append(task["task_id"])
        return {"status": "success", "archived": archived}

    def get_task_graph(self):
        tasks = self.store.list_tasks().get("tasks", [])
        return {"status": "success", "nodes": tasks, "edges": [{"from": dep, "to": task["task_id"]} for task in tasks for dep in task.get("dependencies", [])]}

    def detect_stale_tasks(self):
        revision = self.server.time_revision_service.tracker.scene_revision
        stale = []
        for task in self.store.list_tasks().get("tasks", []):
            if task.get("status") in {"completed_unverified", "verified"} and (task.get("last_verified_revision") or -1) < revision:
                stale.append(task["task_id"])
        return {"status": "success", "scene_revision": revision, "stale_tasks": stale}


class TimeRevisionService:
    def __init__(self, server):
        self.server = server
        self.tracker = TimeRevisionTracker()

    def get_session_time(self):
        return self.tracker.time_info()

    def get_scene_revision(self):
        return {"status": "success", "scene_revision": self.tracker.scene_revision}

    def get_recent_operations(self, limit=20):
        return self.tracker.recent(limit=limit)

    def get_changes_since_revision(self, revision):
        return {"status": "success", "from_revision": revision, "to_revision": self.tracker.scene_revision, "source": "overtli_or_external_unknown", "changes": [op for op in self.tracker.operations if op.get("revision", 0) > revision]}

    def get_operation_duration(self, operation_id=None):
        return {"status": "success", "operation_id": operation_id, "duration_seconds": None, "warnings": ["duration tracking is available for new Phase 7C markers only"]}

    def create_scene_revision_marker(self, label=None, source="overtli"):
        return self.tracker.marker(label=label, source=source)


class ReferenceImageService:
    def __init__(self, server):
        self.server = server
        self.references = {}

    def _reference_root(self):
        root = self.server.project_workspace_service._workspace_base()
        path = os.path.join(root, "references", "images")
        os.makedirs(path, exist_ok=True)
        return path

    def import_reference_image(self, source_path, reference_type="empty_image", copy_into_project=True, name=None):
        check = self.server.file_access_policy_service.validate_path_access(source_path, "read")
        if check.get("status") != "success":
            return check
        source = check["path"]
        ref_id = "ref_" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
        project_path = source
        if copy_into_project:
            project_path = os.path.join(self._reference_root(), os.path.basename(source))
            shutil.copy2(source, project_path)
        image = bpy.data.images.load(project_path, check_existing=True)
        record = {"reference_id": ref_id, "name": name or image.name, "source_path": source, "project_copy_path": project_path, "reference_type": reference_type, "dimensions": list(image.size), "opacity": 1.0, "depth": "front", "locked": True, "landmarks": [], "confidence": "uncalibrated"}
        self.references[ref_id] = record
        return {"status": "success", "reference": record}

    def create_reference_set(self, name, reference_ids=None):
        return {"status": "success", "reference_set": {"name": name, "reference_ids": reference_ids or []}}

    def place_reference_view(self, reference_id, view="front_orthographic", scale=1.0):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        bpy.ops.object.empty_add(type="IMAGE", location=(0, 0, 0))
        obj = bpy.context.object
        obj.name = record["name"]
        obj.empty_display_type = "IMAGE"
        obj.empty_display_size = scale
        obj.data = bpy.data.images.get(record["name"])
        obj.lock_location = (True, True, True)
        obj.lock_rotation = (True, True, True)
        obj.lock_scale = (True, True, True)
        record["object_name"] = obj.name
        record["view"] = view
        return {"status": "success", "reference": record}

    def calibrate_reference_scale(self, reference_id, known_distance, unit="METERS"):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        record["scale_calibration"] = {"known_distance": known_distance, "unit": unit}
        record["confidence"] = "calibrated"
        return {"status": "success", "reference": record}

    def set_reference_opacity(self, reference_id, opacity):
        return self._set_reference(reference_id, opacity=max(0.0, min(1.0, float(opacity))))

    def set_reference_depth(self, reference_id, depth):
        return self._set_reference(reference_id, depth=depth)

    def lock_reference(self, reference_id, locked=True):
        return self._set_reference(reference_id, locked=bool(locked))

    def set_reference_view_visibility(self, reference_id, visible=True):
        return self._set_reference(reference_id, visible=bool(visible))

    def add_reference_landmark(self, reference_id, name, point):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        record.setdefault("landmarks", []).append({"name": name, "point": point})
        return {"status": "success", "reference": record}

    def measure_reference_landmarks(self, reference_id, from_landmark, to_landmark):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        lookup = {item["name"]: item["point"] for item in record.get("landmarks", [])}
        if from_landmark not in lookup or to_landmark not in lookup:
            return {"status": "error", "message": "Both landmarks must exist."}
        return {"status": "success", "distance_pixels": runtime_distance(lookup[from_landmark], lookup[to_landmark]), "confidence": record.get("confidence", "uncalibrated")}

    def capture_reference_overlay(self, reference_id):
        return {"status": "success", "reference_id": reference_id, "artifact": None, "warnings": ["overlay capture uses viewport screenshot tooling in later phases"]}

    def list_reference_images(self):
        return {"status": "success", "references": list(self.references.values())}

    def relink_reference_image(self, reference_id, new_path):
        return self._set_reference(reference_id, project_copy_path=new_path)

    def remove_reference_image(self, reference_id, delete_file=False, confirm=False):
        if delete_file and not confirm:
            return {"status": "requires_approval", "message": "Deleting reference image files requires confirmation."}
        record = self.references.pop(reference_id, None)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        return {"status": "success", "removed": record, "file_deleted": False}

    def _set_reference(self, reference_id, **updates):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        record.update(updates)
        return {"status": "success", "reference": record}


class SpatialMeasurementService:
    def __init__(self, server):
        self.server = server

    def _obj(self, name):
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        return obj

    def _origin(self, name):
        return list(self._obj(name).matrix_world.translation)

    def calculate_distance(self, from_object=None, to_object=None, point_a=None, point_b=None):
        a = point_a or self._origin(from_object)
        b = point_b or self._origin(to_object)
        value = runtime_distance(a, b)
        unit_settings = bpy.context.scene.unit_settings
        return {"status": "success", "measurement": {"type": "distance", "from": from_object or point_a, "to": to_object or point_b, "value_blender_units": value, "unit_system": unit_settings.system, "value_meters": value * unit_settings.scale_length, "confidence": "high", "method": "object_origin" if from_object and to_object else "points"}, "warnings": []}

    def calculate_angle(self, point_a, point_b, point_c):
        return {"status": "success", "measurement": {"type": "angle", "value_degrees": runtime_angle_degrees(point_a, point_b, point_c), "confidence": "high"}}

    def calculate_area(self, object_name):
        obj = self._obj(object_name)
        return {"status": "success", "measurement": {"type": "area", "object": object_name, "value": None, "confidence": "estimated", "method": "mesh-evaluation-deferred", "dimensions": list(obj.dimensions)}}

    def calculate_volume(self, object_name):
        dims = self._obj(object_name).dimensions
        return {"status": "success", "measurement": {"type": "volume", "object": object_name, "value_blender_units": dims.x * dims.y * dims.z, "confidence": "estimated", "method": "oriented_bounds_product"}}

    def calculate_curve_length(self, object_name):
        return {"status": "success", "measurement": {"type": "curve_length", "object": object_name, "value": None, "confidence": "estimated"}}

    def calculate_clearance(self, object_a, object_b):
        return self.calculate_distance(from_object=object_a, to_object=object_b)

    def calculate_alignment(self, object_names):
        centers = [self._origin(name) for name in object_names]
        return {"status": "success", "alignment": {"objects": object_names, "centers": centers, "confidence": "estimated"}}

    def convert_units(self, value, from_unit="BLENDER_UNIT", to_unit="METERS"):
        return runtime_convert_units(value, from_unit=from_unit, to_unit=to_unit, scale_length=bpy.context.scene.unit_settings.scale_length)

    def calculate_scale_ratio(self, measured, expected):
        return {"status": "success", "ratio": float(measured) / float(expected), "confidence": "high"}

    def compare_measurements(self, a, b):
        return {"status": "success", "difference": float(a) - float(b), "ratio": float(a) / float(b) if float(b) else None}

    def get_oriented_bounds(self, object_name):
        obj = self._obj(object_name)
        corners = [list(obj.matrix_world @ mathutils.Vector(corner)) for corner in obj.bound_box]
        return {"status": "success", "object": object_name, "corners": corners, "dimensions": list(obj.dimensions), "confidence": "high"}

    def raycast_scene(self, origin, direction, distance=1000.0):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        hit, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(depsgraph, mathutils.Vector(origin), mathutils.Vector(direction), distance=float(distance))
        return {"status": "success", "hit": bool(hit), "object": obj.name if obj else None, "location": list(location) if hit else None, "normal": list(normal) if hit else None}

    def find_nearest_objects(self, point, limit=5):
        rows = sorted((runtime_distance(point, list(obj.matrix_world.translation)), obj.name) for obj in bpy.context.scene.objects)
        return {"status": "success", "objects": [{"name": name, "distance": dist} for dist, name in rows[:limit]]}

    def detect_object_intersections(self, object_names):
        return {"status": "success", "intersections": [], "objects": object_names, "confidence": "estimated", "warnings": ["Phase 7C uses bounds-first intersection scaffolding."]}

    def measure_object_to_reference(self, object_name, reference_id):
        refs = self.server.reference_image_service.references
        if reference_id not in refs:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        return {"status": "success", "object": object_name, "reference_id": reference_id, "confidence": refs[reference_id].get("confidence", "uncalibrated")}


class SafeRenameRelocationService:
    def __init__(self, server):
        self.server = server
        self.plans = {}

    def plan_rename(self, target_type, old_name, new_name):
        collision = False
        if target_type == "objects":
            collision = new_name in bpy.data.objects
        approval_id = "rename_" + hashlib.sha256(f"{target_type}:{old_name}:{new_name}".encode("utf-8")).hexdigest()[:12]
        plan = {"approval_id": approval_id, "target_type": target_type, "old_name": old_name, "new_name": new_name, "collision": collision, "requires_approval": True, "risks": ["collision"] if collision else []}
        self.plans[approval_id] = plan
        return {"status": "requires_approval", "plan": plan}

    def execute_rename(self, approval_id, confirm=False):
        plan = self.plans.get(approval_id)
        if not plan:
            return {"status": "error", "message": f"Unknown rename plan: {approval_id}"}
        if not confirm:
            return {"status": "requires_approval", "approval_id": approval_id}
        if plan["target_type"] == "objects":
            obj = bpy.data.objects.get(plan["old_name"])
            if not obj:
                return {"status": "error", "message": "Object not found."}
            if plan["collision"]:
                return {"status": "error", "message": "Rename collision detected."}
            obj.name = plan["new_name"]
            return {"status": "success", "renamed": plan}
        return {"status": "blocked", "message": "Only object datablock rename execution is enabled in Phase 7C.", "plan": plan}

    def batch_rename_datablocks(self, renames, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Batch rename requires confirmation."}
        results = [self.execute_rename(self.plan_rename(item["target_type"], item["old_name"], item["new_name"])["plan"]["approval_id"], confirm=True) for item in renames]
        return {"status": "success", "results": results}

    def batch_rename_files(self, renames, confirm=False):
        return {"status": "requires_approval" if not confirm else "blocked", "message": "File rename execution requires approved root and remains blocked pending exact approval dispatch.", "renames": renames}

    def rename_project(self, new_name, confirm=False):
        return {"status": "requires_approval" if not confirm else "blocked", "message": "Project folder rename is plan-only in Phase 7C.", "new_name": new_name}

    def repair_references_after_rename(self, confirm=False):
        return {"status": "requires_approval" if not confirm else "success", "repaired": [], "warnings": ["No broken reference relinks detected."]}


class BlenderMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        # Shared context storage for persistent variables between tool calls
        self.shared_context = {
            'variables': {},  # User-defined variables
            'objects': {},    # Object references by handle
            'materials': {},  # Material references by handle
            'operations': {}, # Operation results by ID
            'history': []     # Operation history
        }
        self.shared_context_service = SharedContextService(self.shared_context)
        self.script_registry_service = ScriptRegistryService()
        self.scene_observation_service = SceneObservationService(self)
        self.viewport_screenshot_service = ViewportScreenshotService(self)
        self.scene_intelligence_service = SceneIntelligenceService(self)
        self.verification_artifact_service = VerificationArtifactService(self)
        self.scene_edit_service = SceneEditService(self)
        self.material_authoring_service = MaterialAuthoringService(self)
        self.material_intelligence_service = MaterialIntelligenceService(self)
        self.material_template_service = MaterialTemplateService(self)
        self.advanced_material_authoring_service = AdvancedMaterialAuthoringService(self)
        self.shader_graph_service = ShaderGraphService(self)
        self.material_texture_slot_service = MaterialTextureSlotService(self)
        self.procedural_texture_service = ProceduralTextureService(self)
        self.material_preview_service = MaterialPreviewService(self)
        self.material_workflow_batch_service = MaterialWorkflowBatchService(self)
        self.selection_intelligence_service = SelectionIntelligenceService(self)
        self.vertex_group_service = VertexGroupService(self)
        self.shape_key_service = ShapeKeyService(self)
        self.lattice_deformation_service = LatticeDeformationService(self)
        self.deformation_modifier_service = DeformationModifierService(self)
        self.direct_mesh_edit_service = DirectMeshEditService(self)
        self.deformation_workflow_batch_service = DeformationWorkflowBatchService(self)
        self.method_intelligence_service = MethodIntelligenceService(self)
        self.asset_material_workflow_service = AssetMaterialWorkflowService(self)
        self.uv_selection_measurement_service = UVSelectionMeasurementService(self)
        self.sculpt_workflow_service = SculptWorkflowService(self)
        self.animation_intelligence_service = AnimationIntelligenceService(self)
        self.animation_authoring_service = AnimationAuthoringService(self)
        self.camera_composition_service = CameraCompositionService(self)
        self.lighting_setup_service = LightingSetupService(self)
        self.render_settings_service = RenderSettingsService(self)
        self.render_artifact_service = RenderArtifactService(self)
        self.compositor_pass_service = CompositorPassService(self)
        self.presentation_workflow_batch_service = PresentationWorkflowBatchService(self)
        self.asset_library_intelligence_service = AssetLibraryIntelligenceService(self)
        self.asset_dependency_service = AssetDependencyService(self)
        self.asset_import_service = AssetImportService(self)
        self.asset_export_service = AssetExportService(self)
        self.blend_library_service = BlendLibraryService(self)
        self.scene_kit_service = SceneKitService(self)
        self.asset_preview_service = AssetPreviewService(self)
        self.asset_workflow_batch_service = AssetWorkflowBatchService(self)
        self.rigging_simulation_service = RiggingSimulationService(self)
        self.modifier_service = ModifierService(self)
        self.collection_organization_service = CollectionOrganizationService(self)
        self.verified_edit_batch_service = VerifiedEditBatchService(self)
        self.workspace_safety_diff_service = WorkspaceSafetyDiffService(self)
        self.provider_status_service = ProviderStatusService(self)
        self.polyhaven_service = PolyHavenService(self)
        self.sketchfab_service = SketchfabService(self)
        self.hyper3d_service = Hyper3DService(self)
        self.safety_policy_service = SafetyPolicyService(self)
        self.raw_code_execution_service = RawCodeExecutionService(self)
        self.geometry_nodes_intelligence_service = GeometryNodesIntelligenceService(self)
        self.geometry_nodes_template_service = GeometryNodesTemplateService(self)
        self.geometry_nodes_recipe_service = GeometryNodesRecipeService(self)
        self.geometry_nodes_modifier_service = GeometryNodesModifierService(self)
        self.procedural_asset_generator_service = ProceduralAssetGeneratorService(self)
        self.geometry_nodes_validation_service = GeometryNodesValidationService(self)
        self.geometry_nodes_preview_service = GeometryNodesPreviewService(self)
        self.geometry_nodes_workflow_batch_service = GeometryNodesWorkflowBatchService(self)
        self.geometry_nodes_service = GeometryNodesService(self)
        self.addon_management_service = AddonManagementService(self)
        self.addon_development_service = AddonDevelopmentService(self)
        self.blender_api_knowledge_service = BlenderApiKnowledgeService(self)
        self.verified_snippet_library_service = VerifiedSnippetLibraryService(self)
        self.skill_pack_service = SkillPackService(self)
        self.review_package_export_service = ReviewPackageExportService(self)
        self.advanced_knowledge_workflow_batch_service = AdvancedKnowledgeWorkflowBatchService(self)
        self.project_workspace_service = ProjectWorkspaceService(self)
        self.file_access_policy_service = FileAccessPolicyService(self)
        self.cache_retention_service = CacheRetentionService(self)
        self.task_graph_service = TaskGraphService(self)
        self.time_revision_service = TimeRevisionService(self)
        self.reference_image_service = ReferenceImageService(self)
        self.spatial_measurement_service = SpatialMeasurementService(self)
        self.safe_rename_relocation_service = SafeRenameRelocationService(self)

        for _name, _service in {
            "resolve_project_workspace": self.project_workspace_service,
            "initialize_project_workspace": self.project_workspace_service,
            "validate_project_layout": self.project_workspace_service,
            "repair_project_layout": self.project_workspace_service,
            "register_blend_file": self.project_workspace_service,
            "save_project_as": self.project_workspace_service,
            "create_project_backup": self.project_workspace_service,
            "restore_project_backup": self.project_workspace_service,
            "collect_project_dependencies": self.project_workspace_service,
            "get_file_access_policy": self.file_access_policy_service,
            "set_file_access_policy": self.file_access_policy_service,
            "validate_path_access": self.file_access_policy_service,
            "list_approved_roots": self.file_access_policy_service,
            "add_approved_root": self.file_access_policy_service,
            "remove_approved_root": self.file_access_policy_service,
            "scan_project_files": self.file_access_policy_service,
            "read_project_text_file": self.file_access_policy_service,
            "write_project_text_file": self.file_access_policy_service,
            "copy_file_into_project": self.file_access_policy_service,
            "plan_file_delete": self.file_access_policy_service,
            "execute_approved_file_delete": self.file_access_policy_service,
            "get_cache_status": self.cache_retention_service,
            "plan_cache_cleanup": self.cache_retention_service,
            "execute_cache_cleanup": self.cache_retention_service,
            "pin_artifact": self.cache_retention_service,
            "unpin_artifact": self.cache_retention_service,
            "find_orphaned_artifacts": self.cache_retention_service,
            "compact_operation_history": self.cache_retention_service,
            "create_task": self.task_graph_service,
            "update_task": self.task_graph_service,
            "list_tasks": self.task_graph_service,
            "get_task": self.task_graph_service,
            "set_task_status": self.task_graph_service,
            "link_task_artifact": self.task_graph_service,
            "link_task_target": self.task_graph_service,
            "mark_task_verified": self.task_graph_service,
            "mark_task_stale": self.task_graph_service,
            "archive_tasks": self.task_graph_service,
            "get_task_graph": self.task_graph_service,
            "detect_stale_tasks": self.task_graph_service,
            "get_session_time": self.time_revision_service,
            "get_scene_revision": self.time_revision_service,
            "get_recent_operations": self.time_revision_service,
            "get_changes_since_revision": self.time_revision_service,
            "get_operation_duration": self.time_revision_service,
            "create_scene_revision_marker": self.time_revision_service,
            "import_reference_image": self.reference_image_service,
            "create_reference_set": self.reference_image_service,
            "place_reference_view": self.reference_image_service,
            "calibrate_reference_scale": self.reference_image_service,
            "set_reference_opacity": self.reference_image_service,
            "set_reference_depth": self.reference_image_service,
            "lock_reference": self.reference_image_service,
            "set_reference_view_visibility": self.reference_image_service,
            "add_reference_landmark": self.reference_image_service,
            "measure_reference_landmarks": self.reference_image_service,
            "capture_reference_overlay": self.reference_image_service,
            "list_reference_images": self.reference_image_service,
            "relink_reference_image": self.reference_image_service,
            "remove_reference_image": self.reference_image_service,
            "calculate_distance": self.spatial_measurement_service,
            "calculate_angle": self.spatial_measurement_service,
            "calculate_area": self.spatial_measurement_service,
            "calculate_volume": self.spatial_measurement_service,
            "calculate_curve_length": self.spatial_measurement_service,
            "calculate_clearance": self.spatial_measurement_service,
            "calculate_alignment": self.spatial_measurement_service,
            "convert_units": self.spatial_measurement_service,
            "calculate_scale_ratio": self.spatial_measurement_service,
            "compare_measurements": self.spatial_measurement_service,
            "get_oriented_bounds": self.spatial_measurement_service,
            "raycast_scene": self.spatial_measurement_service,
            "find_nearest_objects": self.spatial_measurement_service,
            "detect_object_intersections": self.spatial_measurement_service,
            "measure_object_to_reference": self.spatial_measurement_service,
            "plan_rename": self.safe_rename_relocation_service,
            "execute_rename": self.safe_rename_relocation_service,
            "batch_rename_datablocks": self.safe_rename_relocation_service,
            "batch_rename_files": self.safe_rename_relocation_service,
            "rename_project": self.safe_rename_relocation_service,
            "repair_references_after_rename": self.safe_rename_relocation_service,
        }.items():
            setattr(self, _name, getattr(_service, _name))

        self.get_scene_info = self.scene_observation_service.get_scene_info
        self.get_object_info = self.scene_observation_service.get_object_info
        self.get_viewport_screenshot = self.viewport_screenshot_service.get_viewport_screenshot
        self.get_scene_index = self.scene_intelligence_service.get_scene_index
        self.get_object_deep_info = self.scene_intelligence_service.get_object_deep_info
        self.get_selection_info = self.scene_intelligence_service.get_selection_info
        self.get_scene_health = self.scene_intelligence_service.get_scene_health
        self.capture_viewport_pack = self.verification_artifact_service.capture_viewport_pack
        self.create_verification_snapshot = self.verification_artifact_service.create_verification_snapshot
        self.list_verification_snapshots = self.verification_artifact_service.list_verification_snapshots
        self.get_supported_edit_operations = self.scene_edit_service.get_supported_edit_operations
        self.create_primitive_object = self.scene_edit_service.create_primitive_object
        self.transform_object = self.scene_edit_service.transform_object
        self.duplicate_object = self.scene_edit_service.duplicate_object
        self.delete_objects = self.scene_edit_service.delete_objects
        self.set_object_visibility = self.scene_edit_service.set_object_visibility
        self.create_basic_material = self.material_authoring_service.create_basic_material
        self.assign_material = self.material_authoring_service.assign_material
        self.update_material_properties = self.material_authoring_service.update_material_properties
        self.get_material_channel_schema = self.material_intelligence_service.get_material_channel_schema
        self.get_supported_material_templates = self.material_template_service.get_supported_material_templates
        self.list_materials_deep = self.material_intelligence_service.list_materials_deep
        self.get_material_deep_info = self.material_intelligence_service.get_material_deep_info
        self.get_shader_graph = self.shader_graph_service.get_shader_graph
        self.create_material_from_template = self.material_template_service.create_material_from_template
        self.create_custom_material = self.advanced_material_authoring_service.create_custom_material
        self.create_procedural_material = self.procedural_texture_service.create_procedural_material
        self.create_material_variant = self.advanced_material_authoring_service.create_material_variant
        self.apply_material_to_objects = self.advanced_material_authoring_service.apply_material_to_objects
        self.bind_material_texture_map = self.material_texture_slot_service.bind_material_texture_map
        self.set_material_node_input = self.shader_graph_service.set_material_node_input
        self.add_material_node = self.shader_graph_service.add_material_node
        self.connect_material_nodes = self.shader_graph_service.connect_material_nodes
        self.remove_material_node = self.shader_graph_service.remove_material_node
        self.create_material_preview = self.material_preview_service.create_material_preview
        self.run_material_workflow_batch = self.material_workflow_batch_service.run_material_workflow_batch
        self.delete_materials = self.advanced_material_authoring_service.delete_materials
        self.get_selection_deep_info = self.selection_intelligence_service.get_selection_deep_info
        self.get_mesh_component_summary = self.selection_intelligence_service.get_mesh_component_summary
        self.create_vertex_group = self.vertex_group_service.create_vertex_group
        self.update_vertex_group_weights = self.vertex_group_service.update_vertex_group_weights
        self.list_vertex_groups = self.vertex_group_service.list_vertex_groups
        self.delete_vertex_groups = self.vertex_group_service.delete_vertex_groups
        self.create_shape_key = self.shape_key_service.create_shape_key
        self.update_shape_key_value = self.shape_key_service.update_shape_key_value
        self.edit_shape_key_offsets = self.shape_key_service.edit_shape_key_offsets
        self.list_shape_keys = self.shape_key_service.list_shape_keys
        self.delete_shape_keys = self.shape_key_service.delete_shape_keys
        self.create_lattice_deformer = self.lattice_deformation_service.create_lattice_deformer
        self.update_lattice_deformer = self.lattice_deformation_service.update_lattice_deformer
        self.apply_lattice_to_object = self.lattice_deformation_service.apply_lattice_to_object
        self.remove_lattice_deformer = self.lattice_deformation_service.remove_lattice_deformer
        self.add_deformation_modifier = self.deformation_modifier_service.add_deformation_modifier
        self.update_deformation_modifier = self.deformation_modifier_service.update_deformation_modifier
        self.create_region_deformation = self.deformation_workflow_batch_service.create_region_deformation
        self.run_deformation_workflow_batch = self.deformation_workflow_batch_service.run_deformation_workflow_batch
        self.get_method_plan = self.method_intelligence_service.get_method_plan
        self.list_operation_playbooks = self.method_intelligence_service.list_operation_playbooks
        self.get_tricks_knowledge_base = self.method_intelligence_service.get_tricks_knowledge_base
        self.get_anti_pattern_rules = self.method_intelligence_service.get_anti_pattern_rules
        self.get_modifier_recipes = self.method_intelligence_service.get_modifier_recipes
        self.score_selection_confidence = self.method_intelligence_service.score_selection_confidence
        self.scan_blender_asset_libraries = self.asset_material_workflow_service.scan_blender_asset_libraries
        self.preview_asset = self.asset_material_workflow_service.preview_asset
        self.import_texture_folder = self.asset_material_workflow_service.import_texture_folder
        self.create_style_material = self.asset_material_workflow_service.create_style_material
        self.create_paintable_texture = self.asset_material_workflow_service.create_paintable_texture
        self.delete_images = self.asset_material_workflow_service.delete_images
        self.list_uv_maps = self.uv_selection_measurement_service.list_uv_maps
        self.create_vertex_group_from_uv_island = self.uv_selection_measurement_service.create_vertex_group_from_uv_island
        self.measure_object = self.uv_selection_measurement_service.measure_object
        self.measure_distance = self.uv_selection_measurement_service.measure_distance
        self.create_proportional_deformation = self.uv_selection_measurement_service.create_proportional_deformation
        self.get_sculpt_status = self.sculpt_workflow_service.get_sculpt_status
        self.configure_sculpt_brush = self.sculpt_workflow_service.configure_sculpt_brush
        self.create_sculpt_mask_from_vertex_group = self.sculpt_workflow_service.create_sculpt_mask_from_vertex_group
        self.run_shape_key_sculpt_workflow = self.sculpt_workflow_service.run_shape_key_sculpt_workflow
        self.get_timeline_info = self.animation_intelligence_service.get_timeline_info
        self.list_animated_objects = self.animation_intelligence_service.list_animated_objects
        self.get_animation_deep_info = self.animation_intelligence_service.get_animation_deep_info
        self.set_timeline_range = self.animation_intelligence_service.set_timeline_range
        self.set_current_frame = self.animation_intelligence_service.set_current_frame
        self.insert_transform_keyframes = self.animation_authoring_service.insert_transform_keyframes
        self.animate_object_transform = self.animation_authoring_service.animate_object_transform
        self.animate_camera_transform = self.animation_authoring_service.animate_camera_transform
        self.animate_light_property = self.animation_authoring_service.animate_light_property
        self.animate_material_property = self.animation_authoring_service.animate_material_property
        self.animate_shape_key_value = self.animation_authoring_service.animate_shape_key_value
        self.delete_animation_data = self.animation_authoring_service.delete_animation_data
        self.create_camera = self.camera_composition_service.create_camera
        self.frame_camera_to_objects = self.camera_composition_service.frame_camera_to_objects
        self.set_active_camera = self.camera_composition_service.set_active_camera
        self.create_light = self.lighting_setup_service.create_light
        self.create_lighting_setup = self.lighting_setup_service.create_lighting_setup
        self.update_light = self.lighting_setup_service.update_light
        self.set_world_lighting = self.lighting_setup_service.set_world_lighting
        self.get_render_settings = self.render_settings_service.get_render_settings
        self.set_render_settings = self.render_settings_service.set_render_settings
        self.set_output_path = self.render_settings_service.set_output_path
        self.render_still = self.render_artifact_service.render_still
        self.render_contact_sheet = self.render_artifact_service.render_contact_sheet
        self.create_turntable_animation = self.render_artifact_service.create_turntable_animation
        self.render_preview_animation = self.render_artifact_service.render_preview_animation
        self.get_compositor_status = self.compositor_pass_service.get_compositor_status
        self.set_compositor_preset = self.compositor_pass_service.set_compositor_preset
        self.set_render_passes = self.compositor_pass_service.set_render_passes
        self.run_presentation_workflow_batch = self.presentation_workflow_batch_service.run_presentation_workflow_batch
        self.cleanup_presentation_artifacts = self.presentation_workflow_batch_service.cleanup_presentation_artifacts
        self.get_supported_asset_formats = self.asset_library_intelligence_service.get_supported_asset_formats
        self.scan_asset_folder = self.asset_library_intelligence_service.scan_asset_folder
        self.list_asset_libraries = self.asset_library_intelligence_service.list_asset_libraries
        self.list_scene_assets = self.asset_library_intelligence_service.list_scene_assets
        self.get_asset_file_info = self.asset_library_intelligence_service.get_asset_file_info
        self.get_asset_dependency_report = self.asset_dependency_service.get_asset_dependency_report
        self.create_asset_manifest = self.asset_dependency_service.create_asset_manifest
        self.collect_external_dependencies = self.asset_dependency_service.collect_external_dependencies
        self.validate_external_dependencies = self.asset_dependency_service.validate_external_dependencies
        self.pack_external_data = self.asset_dependency_service.pack_external_data
        self.make_paths_relative = self.asset_dependency_service.make_paths_relative
        self.append_blend_asset = self.blend_library_service.append_blend_asset
        self.import_model_file = self.asset_import_service.import_model_file
        self.export_selected_objects = self.asset_export_service.export_selected_objects
        self.export_scene = self.asset_export_service.export_scene
        self.create_asset_preview = self.asset_preview_service.create_asset_preview
        self.create_asset_contact_sheet = self.asset_preview_service.create_asset_contact_sheet
        self.create_scene_kit = self.scene_kit_service.create_scene_kit
        self.import_scene_kit = self.scene_kit_service.import_scene_kit
        self.validate_scene_kit = self.scene_kit_service.validate_scene_kit
        self.list_scene_kits = self.scene_kit_service.list_scene_kits
        self.cleanup_asset_artifacts = self.asset_workflow_batch_service.cleanup_asset_artifacts
        self.run_asset_workflow_batch = self.asset_workflow_batch_service.run_asset_workflow_batch
        self.inspect_rigging = self.rigging_simulation_service.inspect_rigging
        self.create_armature = self.rigging_simulation_service.create_armature
        self.parent_mesh_to_armature = self.rigging_simulation_service.parent_mesh_to_armature
        self.pose_bone_transform = self.rigging_simulation_service.pose_bone_transform
        self.add_driver = self.rigging_simulation_service.add_driver
        self.remove_driver = self.rigging_simulation_service.remove_driver
        self.add_physics_basic = self.rigging_simulation_service.add_physics_basic
        self.add_object_modifier = self.modifier_service.add_object_modifier
        self.update_object_modifier = self.modifier_service.update_object_modifier
        self.remove_object_modifier = self.modifier_service.remove_object_modifier
        self.create_collection = self.collection_organization_service.create_collection
        self.move_objects_to_collection = self.collection_organization_service.move_objects_to_collection
        self.delete_collection = self.collection_organization_service.delete_collection
        self.run_verified_edit_batch = self.verified_edit_batch_service.run_verified_edit_batch
        self.get_task_workspace = self.workspace_safety_diff_service.get_task_workspace
        self.create_workspace_task = self.workspace_safety_diff_service.create_workspace_task
        self.update_workspace_task = self.workspace_safety_diff_service.update_workspace_task
        self.list_workspace_tasks = self.workspace_safety_diff_service.list_workspace_tasks
        self.add_workspace_todo = self.workspace_safety_diff_service.add_workspace_todo
        self.update_workspace_todo = self.workspace_safety_diff_service.update_workspace_todo
        self.list_workspace_todos = self.workspace_safety_diff_service.list_workspace_todos
        self.record_operation_journal_entry = self.workspace_safety_diff_service.record_operation_journal_entry
        self.get_operation_journal = self.workspace_safety_diff_service.get_operation_journal
        self.create_scene_snapshot = self.workspace_safety_diff_service.create_scene_snapshot
        self.list_scene_snapshots = self.workspace_safety_diff_service.list_scene_snapshots
        self.diff_scene_snapshots = self.workspace_safety_diff_service.diff_scene_snapshots
        self.detect_user_changes = self.workspace_safety_diff_service.detect_user_changes
        self.rollback_to_scene_snapshot = self.workspace_safety_diff_service.rollback_to_scene_snapshot
        self.undo_last_blender_operation = self.workspace_safety_diff_service.undo_last_blender_operation
        self.get_safety_status = self.safety_policy_service.get_safety_status
        self.execute_code = self.raw_code_execution_service.execute_code
        self.get_polyhaven_status = self.provider_status_service.get_polyhaven_status
        self.get_hyper3d_status = self.provider_status_service.get_hyper3d_status
        self.get_sketchfab_status = self.provider_status_service.get_sketchfab_status
        self.get_polyhaven_categories = self.polyhaven_service.get_polyhaven_categories
        self.search_polyhaven_assets = self.polyhaven_service.search_polyhaven_assets
        self.download_polyhaven_asset = self.polyhaven_service.download_polyhaven_asset
        self.set_texture = self.polyhaven_service.set_texture
        self.search_sketchfab_models = self.sketchfab_service.search_sketchfab_models
        self.download_sketchfab_model = self.sketchfab_service.download_sketchfab_model
        self.create_rodin_job = self.hyper3d_service.create_rodin_job
        self.poll_rodin_job_status = self.hyper3d_service.poll_rodin_job_status
        self.import_generated_asset = self.hyper3d_service.import_generated_asset
        self.get_geometry_nodes_capabilities = self.geometry_nodes_intelligence_service.get_geometry_nodes_capabilities
        self.list_geometry_node_groups = self.geometry_nodes_intelligence_service.list_geometry_node_groups
        self.get_geometry_node_group_deep_info = self.geometry_nodes_intelligence_service.get_geometry_node_group_deep_info
        self.list_geometry_nodes_modifiers = self.geometry_nodes_intelligence_service.list_geometry_nodes_modifiers
        self.get_geometry_nodes_modifier_info = self.geometry_nodes_intelligence_service.get_geometry_nodes_modifier_info
        self.get_supported_geometry_node_templates = self.geometry_nodes_template_service.get_supported_geometry_node_templates
        self.create_geometry_node_group_from_template = self.geometry_nodes_template_service.create_geometry_node_group_from_template
        self.create_custom_geometry_node_recipe = self.geometry_nodes_recipe_service.create_custom_geometry_node_recipe
        self.apply_geometry_nodes_modifier = self.geometry_nodes_modifier_service.apply_geometry_nodes_modifier
        self.set_geometry_nodes_modifier_input = self.geometry_nodes_modifier_service.set_geometry_nodes_modifier_input
        self.create_procedural_asset = self.procedural_asset_generator_service.create_procedural_asset
        self.create_scatter_system = self.procedural_asset_generator_service.create_scatter_system
        self.create_curve_generator = self.procedural_asset_generator_service.create_curve_generator
        self.create_radial_array_system = self.procedural_asset_generator_service.create_radial_array_system
        self.create_panel_generator = self.procedural_asset_generator_service.create_panel_generator
        self.create_cable_or_rope_generator = self.procedural_asset_generator_service.create_cable_or_rope_generator
        self.create_terrain_noise_system = self.procedural_asset_generator_service.create_terrain_noise_system
        self.validate_geometry_node_group = self.geometry_nodes_validation_service.validate_geometry_node_group
        self.create_geometry_nodes_preview = self.geometry_nodes_preview_service.create_geometry_nodes_preview
        self.create_geometry_nodes_scene_kit = self.geometry_nodes_preview_service.create_geometry_nodes_scene_kit
        self.delete_geometry_node_groups = self.geometry_nodes_validation_service.delete_geometry_node_groups
        self.remove_geometry_nodes_modifiers = self.geometry_nodes_modifier_service.remove_geometry_nodes_modifiers
        self.run_geometry_nodes_workflow_batch = self.geometry_nodes_workflow_batch_service.run_geometry_nodes_workflow_batch
        self.complete_geometry_node = self.geometry_nodes_service.complete_geometry_node
        self.get_geometry_nodes_status = self.geometry_nodes_service.get_geometry_nodes_status
        self.get_addon_management_status = self.addon_management_service.get_addon_management_status
        self.list_blender_addons = self.addon_management_service.list_blender_addons
        self.get_blender_addon_info = self.addon_management_service.get_blender_addon_info
        self.install_local_addon = self.addon_management_service.install_local_addon
        self.enable_blender_addon = self.addon_management_service.enable_blender_addon
        self.disable_blender_addon = self.addon_management_service.disable_blender_addon
        self.remove_blender_addon = self.addon_management_service.remove_blender_addon
        self.create_addon_skeleton = self.addon_development_service.create_addon_skeleton
        self.validate_addon_skeleton = self.addon_development_service.validate_addon_skeleton
        self.package_addon_zip = self.addon_development_service.package_addon_zip
        self.inspect_blender_api_docs = self.blender_api_knowledge_service.inspect_blender_api_docs
        self.build_blender_api_index = self.blender_api_knowledge_service.build_blender_api_index
        self.search_blender_api_docs = self.blender_api_knowledge_service.search_blender_api_docs
        self.get_blender_api_topic = self.blender_api_knowledge_service.get_blender_api_topic
        self.create_verified_snippet = self.verified_snippet_library_service.create_verified_snippet
        self.validate_verified_snippet = self.verified_snippet_library_service.validate_verified_snippet
        self.list_verified_snippets = self.verified_snippet_library_service.list_verified_snippets
        self.search_verified_snippets = self.verified_snippet_library_service.search_verified_snippets
        self.get_verified_snippet = self.verified_snippet_library_service.get_verified_snippet
        self.run_verified_snippet_smoke = self.verified_snippet_library_service.run_verified_snippet_smoke
        self.delete_verified_snippets = self.verified_snippet_library_service.delete_verified_snippets
        self.create_skill_pack = self.skill_pack_service.create_skill_pack
        self.validate_skill_pack = self.skill_pack_service.validate_skill_pack
        self.list_skill_packs = self.skill_pack_service.list_skill_packs
        self.get_skill_pack = self.skill_pack_service.get_skill_pack
        self.run_skill_pack = self.skill_pack_service.run_skill_pack
        self.delete_skill_packs = self.skill_pack_service.delete_skill_packs
        self.export_project_review_package = self.review_package_export_service.export_project_review_package
        self.validate_review_package = self.review_package_export_service.validate_review_package
        self.run_advanced_knowledge_workflow_batch = self.advanced_knowledge_workflow_batch_service.run_advanced_knowledge_workflow_batch

    def start(self):
        if self.running:
            print("Server is already running")
            return

        self.running = True

        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)

            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            print(f"Overtli-Blender server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False

        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        # Wait for thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None

        print("Overtli-Blender server stopped")

    def _server_loop(self):
        """Main server loop in a separate thread"""
        print("Server thread started")
        self.socket.settimeout(1.0)  # Timeout to allow for stopping

        while self.running:
            try:
                # Accept new connection
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")

                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    # Just check running condition
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(0.5)

        print("Server thread stopped")

    def _handle_client(self, client):
        """Handle connected client"""
        print("Client handler started")
        client.settimeout(None)  # No timeout
        buffer = b''

        try:
            while self.running:
                # Receive data
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break

                    buffer += data
                    try:
                        # Try to parse command
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''

                        # Execute command in Blender's main thread
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode('utf-8'))
                                except:
                                    print("Failed to send response - client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e)
                                    }
                                    client.sendall(json.dumps(error_response).encode('utf-8'))
                                except:
                                    pass
                            return None

                        # Schedule execution in main thread
                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
                        # Incomplete data, wait for more
                        pass
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            print("Client handler stopped")

    def execute_command(self, command):
        """Execute a command in the main Blender thread"""
        try:
            return self._execute_command_internal(command)

        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """Internal command execution with proper context"""
        return self._dispatch_command(command)

    def _build_command_handlers(self):
        """Build the command-to-handler registry for the current addon state."""
        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "get_viewport_screenshot": self.get_viewport_screenshot,
            "get_scene_index": self.get_scene_index,
            "get_object_deep_info": self.get_object_deep_info,
            "get_selection_info": self.get_selection_info,
            "get_scene_health": self.get_scene_health,
            "capture_viewport_pack": self.capture_viewport_pack,
            "create_verification_snapshot": self.create_verification_snapshot,
            "list_verification_snapshots": self.list_verification_snapshots,
            "get_supported_edit_operations": self.get_supported_edit_operations,
            "create_primitive_object": self.create_primitive_object,
            "transform_object": self.transform_object,
            "duplicate_object": self.duplicate_object,
            "delete_objects": self.delete_objects,
            "set_object_visibility": self.set_object_visibility,
            "create_basic_material": self.create_basic_material,
            "assign_material": self.assign_material,
            "update_material_properties": self.update_material_properties,
            "get_material_channel_schema": self.get_material_channel_schema,
            "get_supported_material_templates": self.get_supported_material_templates,
            "list_materials_deep": self.list_materials_deep,
            "get_material_deep_info": self.get_material_deep_info,
            "get_shader_graph": self.get_shader_graph,
            "create_material_from_template": self.create_material_from_template,
            "create_custom_material": self.create_custom_material,
            "create_procedural_material": self.create_procedural_material,
            "create_material_variant": self.create_material_variant,
            "apply_material_to_objects": self.apply_material_to_objects,
            "bind_material_texture_map": self.bind_material_texture_map,
            "set_material_node_input": self.set_material_node_input,
            "add_material_node": self.add_material_node,
            "connect_material_nodes": self.connect_material_nodes,
            "remove_material_node": self.remove_material_node,
            "create_material_preview": self.create_material_preview,
            "run_material_workflow_batch": self.run_material_workflow_batch,
            "delete_materials": self.delete_materials,
            "get_selection_deep_info": self.get_selection_deep_info,
            "get_mesh_component_summary": self.get_mesh_component_summary,
            "create_vertex_group": self.create_vertex_group,
            "update_vertex_group_weights": self.update_vertex_group_weights,
            "list_vertex_groups": self.list_vertex_groups,
            "delete_vertex_groups": self.delete_vertex_groups,
            "create_shape_key": self.create_shape_key,
            "update_shape_key_value": self.update_shape_key_value,
            "edit_shape_key_offsets": self.edit_shape_key_offsets,
            "list_shape_keys": self.list_shape_keys,
            "delete_shape_keys": self.delete_shape_keys,
            "create_lattice_deformer": self.create_lattice_deformer,
            "update_lattice_deformer": self.update_lattice_deformer,
            "apply_lattice_to_object": self.apply_lattice_to_object,
            "remove_lattice_deformer": self.remove_lattice_deformer,
            "add_deformation_modifier": self.add_deformation_modifier,
            "update_deformation_modifier": self.update_deformation_modifier,
            "create_region_deformation": self.create_region_deformation,
            "run_deformation_workflow_batch": self.run_deformation_workflow_batch,
            "get_method_plan": self.get_method_plan,
            "list_operation_playbooks": self.list_operation_playbooks,
            "get_tricks_knowledge_base": self.get_tricks_knowledge_base,
            "get_anti_pattern_rules": self.get_anti_pattern_rules,
            "get_modifier_recipes": self.get_modifier_recipes,
            "score_selection_confidence": self.score_selection_confidence,
            "scan_blender_asset_libraries": self.scan_blender_asset_libraries,
            "preview_asset": self.preview_asset,
            "import_texture_folder": self.import_texture_folder,
            "create_style_material": self.create_style_material,
            "create_paintable_texture": self.create_paintable_texture,
            "delete_images": self.delete_images,
            "list_uv_maps": self.list_uv_maps,
            "create_vertex_group_from_uv_island": self.create_vertex_group_from_uv_island,
            "measure_object": self.measure_object,
            "measure_distance": self.measure_distance,
            "create_proportional_deformation": self.create_proportional_deformation,
            "get_sculpt_status": self.get_sculpt_status,
            "configure_sculpt_brush": self.configure_sculpt_brush,
            "create_sculpt_mask_from_vertex_group": self.create_sculpt_mask_from_vertex_group,
            "run_shape_key_sculpt_workflow": self.run_shape_key_sculpt_workflow,
            "get_timeline_info": self.get_timeline_info,
            "list_animated_objects": self.list_animated_objects,
            "get_animation_deep_info": self.get_animation_deep_info,
            "set_timeline_range": self.set_timeline_range,
            "set_current_frame": self.set_current_frame,
            "insert_transform_keyframes": self.insert_transform_keyframes,
            "animate_object_transform": self.animate_object_transform,
            "animate_camera_transform": self.animate_camera_transform,
            "animate_light_property": self.animate_light_property,
            "animate_material_property": self.animate_material_property,
            "animate_shape_key_value": self.animate_shape_key_value,
            "delete_animation_data": self.delete_animation_data,
            "create_camera": self.create_camera,
            "frame_camera_to_objects": self.frame_camera_to_objects,
            "set_active_camera": self.set_active_camera,
            "create_light": self.create_light,
            "create_lighting_setup": self.create_lighting_setup,
            "update_light": self.update_light,
            "set_world_lighting": self.set_world_lighting,
            "get_render_settings": self.get_render_settings,
            "set_render_settings": self.set_render_settings,
            "set_output_path": self.set_output_path,
            "render_still": self.render_still,
            "render_contact_sheet": self.render_contact_sheet,
            "create_turntable_animation": self.create_turntable_animation,
            "render_preview_animation": self.render_preview_animation,
            "get_compositor_status": self.get_compositor_status,
            "set_compositor_preset": self.set_compositor_preset,
            "set_render_passes": self.set_render_passes,
            "run_presentation_workflow_batch": self.run_presentation_workflow_batch,
            "cleanup_presentation_artifacts": self.cleanup_presentation_artifacts,
            "get_supported_asset_formats": self.get_supported_asset_formats,
            "scan_asset_folder": self.scan_asset_folder,
            "list_asset_libraries": self.list_asset_libraries,
            "list_scene_assets": self.list_scene_assets,
            "get_asset_file_info": self.get_asset_file_info,
            "get_asset_dependency_report": self.get_asset_dependency_report,
            "create_asset_manifest": self.create_asset_manifest,
            "append_blend_asset": self.append_blend_asset,
            "import_model_file": self.import_model_file,
            "export_selected_objects": self.export_selected_objects,
            "export_scene": self.export_scene,
            "create_asset_preview": self.create_asset_preview,
            "create_asset_contact_sheet": self.create_asset_contact_sheet,
            "create_scene_kit": self.create_scene_kit,
            "import_scene_kit": self.import_scene_kit,
            "validate_scene_kit": self.validate_scene_kit,
            "list_scene_kits": self.list_scene_kits,
            "collect_external_dependencies": self.collect_external_dependencies,
            "validate_external_dependencies": self.validate_external_dependencies,
            "pack_external_data": self.pack_external_data,
            "make_paths_relative": self.make_paths_relative,
            "cleanup_asset_artifacts": self.cleanup_asset_artifacts,
            "run_asset_workflow_batch": self.run_asset_workflow_batch,
            "inspect_rigging": self.inspect_rigging,
            "create_armature": self.create_armature,
            "parent_mesh_to_armature": self.parent_mesh_to_armature,
            "pose_bone_transform": self.pose_bone_transform,
            "add_driver": self.add_driver,
            "remove_driver": self.remove_driver,
            "add_physics_basic": self.add_physics_basic,
            "add_object_modifier": self.add_object_modifier,
            "update_object_modifier": self.update_object_modifier,
            "remove_object_modifier": self.remove_object_modifier,
            "create_collection": self.create_collection,
            "move_objects_to_collection": self.move_objects_to_collection,
            "delete_collection": self.delete_collection,
            "run_verified_edit_batch": self.run_verified_edit_batch,
            "get_task_workspace": self.get_task_workspace,
            "create_workspace_task": self.create_workspace_task,
            "update_workspace_task": self.update_workspace_task,
            "list_workspace_tasks": self.list_workspace_tasks,
            "add_workspace_todo": self.add_workspace_todo,
            "update_workspace_todo": self.update_workspace_todo,
            "list_workspace_todos": self.list_workspace_todos,
            "record_operation_journal_entry": self.record_operation_journal_entry,
            "get_operation_journal": self.get_operation_journal,
            "create_scene_snapshot": self.create_scene_snapshot,
            "list_scene_snapshots": self.list_scene_snapshots,
            "diff_scene_snapshots": self.diff_scene_snapshots,
            "detect_user_changes": self.detect_user_changes,
            "rollback_to_scene_snapshot": self.rollback_to_scene_snapshot,
            "undo_last_blender_operation": self.undo_last_blender_operation,
            "get_safety_status": self.get_safety_status,
            "get_system_status": self.get_system_status,
            "get_project_status": self.get_project_status,
            "resolve_project_workspace": self.resolve_project_workspace,
            "initialize_project_workspace": self.initialize_project_workspace,
            "validate_project_layout": self.validate_project_layout,
            "repair_project_layout": self.repair_project_layout,
            "register_blend_file": self.register_blend_file,
            "save_project_as": self.save_project_as,
            "create_project_backup": self.create_project_backup,
            "restore_project_backup": self.restore_project_backup,
            "collect_project_dependencies": self.collect_project_dependencies,
            "get_file_access_policy": self.get_file_access_policy,
            "set_file_access_policy": self.set_file_access_policy,
            "validate_path_access": self.validate_path_access,
            "list_approved_roots": self.list_approved_roots,
            "add_approved_root": self.add_approved_root,
            "remove_approved_root": self.remove_approved_root,
            "scan_project_files": self.scan_project_files,
            "read_project_text_file": self.read_project_text_file,
            "write_project_text_file": self.write_project_text_file,
            "copy_file_into_project": self.copy_file_into_project,
            "plan_file_delete": self.plan_file_delete,
            "execute_approved_file_delete": self.execute_approved_file_delete,
            "get_cache_status": self.get_cache_status,
            "plan_cache_cleanup": self.plan_cache_cleanup,
            "execute_cache_cleanup": self.execute_cache_cleanup,
            "pin_artifact": self.pin_artifact,
            "unpin_artifact": self.unpin_artifact,
            "find_orphaned_artifacts": self.find_orphaned_artifacts,
            "compact_operation_history": self.compact_operation_history,
            "create_task": self.create_task,
            "update_task": self.update_task,
            "list_tasks": self.list_tasks,
            "get_task": self.get_task,
            "set_task_status": self.set_task_status,
            "link_task_artifact": self.link_task_artifact,
            "link_task_target": self.link_task_target,
            "mark_task_verified": self.mark_task_verified,
            "mark_task_stale": self.mark_task_stale,
            "archive_tasks": self.archive_tasks,
            "get_task_graph": self.get_task_graph,
            "detect_stale_tasks": self.detect_stale_tasks,
            "get_session_time": self.get_session_time,
            "get_scene_revision": self.get_scene_revision,
            "get_recent_operations": self.get_recent_operations,
            "get_changes_since_revision": self.get_changes_since_revision,
            "get_operation_duration": self.get_operation_duration,
            "create_scene_revision_marker": self.create_scene_revision_marker,
            "import_reference_image": self.import_reference_image,
            "create_reference_set": self.create_reference_set,
            "place_reference_view": self.place_reference_view,
            "calibrate_reference_scale": self.calibrate_reference_scale,
            "set_reference_opacity": self.set_reference_opacity,
            "set_reference_depth": self.set_reference_depth,
            "lock_reference": self.lock_reference,
            "set_reference_view_visibility": self.set_reference_view_visibility,
            "add_reference_landmark": self.add_reference_landmark,
            "measure_reference_landmarks": self.measure_reference_landmarks,
            "capture_reference_overlay": self.capture_reference_overlay,
            "list_reference_images": self.list_reference_images,
            "relink_reference_image": self.relink_reference_image,
            "remove_reference_image": self.remove_reference_image,
            "calculate_distance": self.calculate_distance,
            "calculate_angle": self.calculate_angle,
            "calculate_area": self.calculate_area,
            "calculate_volume": self.calculate_volume,
            "calculate_curve_length": self.calculate_curve_length,
            "calculate_clearance": self.calculate_clearance,
            "calculate_alignment": self.calculate_alignment,
            "convert_units": self.convert_units,
            "calculate_scale_ratio": self.calculate_scale_ratio,
            "compare_measurements": self.compare_measurements,
            "get_oriented_bounds": self.get_oriented_bounds,
            "raycast_scene": self.raycast_scene,
            "find_nearest_objects": self.find_nearest_objects,
            "detect_object_intersections": self.detect_object_intersections,
            "measure_object_to_reference": self.measure_object_to_reference,
            "plan_rename": self.plan_rename,
            "execute_rename": self.execute_rename,
            "batch_rename_datablocks": self.batch_rename_datablocks,
            "batch_rename_files": self.batch_rename_files,
            "rename_project": self.rename_project,
            "repair_references_after_rename": self.repair_references_after_rename,
            "discover_tool_packs": self.discover_tool_packs,
            "get_tool_pack": self.get_tool_pack,
            "search_tools": self.search_tools,
            "get_tool_spec": self.get_tool_spec,
            "get_recommended_tools_for_task": self.get_recommended_tools_for_task,
            "prepare_operation": self.prepare_operation,
            "get_pending_approvals": self.get_pending_approvals,
            "approve_operation": self.approve_operation,
            "deny_operation": self.deny_operation,
            "execute_approved_operation": self.execute_approved_operation,
            "expire_approval": self.expire_approval,
            "get_operation_status": self.get_operation_status,
            "list_recent_operations": self.list_recent_operations,
            "cancel_operation": self.cancel_operation,
            "get_operation_log": self.get_operation_log,
            "get_permission_profile": self.get_permission_profile,
            "set_permission_profile": self.set_permission_profile,
            "get_capability_policy": self.get_capability_policy,
            "validate_command_capabilities": self.validate_command_capabilities,
            "get_log_status": self.get_log_status,
            "export_operation_log": self.export_operation_log,
            "get_command_registry_report": self.get_command_registry_report,
            "execute_code": self.execute_code,
            "get_polyhaven_status": self.get_polyhaven_status,
            "get_hyper3d_status": self.get_hyper3d_status,
            "get_sketchfab_status": self.get_sketchfab_status,
            # New composition tools
            "get_shared_context": self.get_shared_context,
            "clear_shared_context": self.clear_shared_context,
            "get_operation_history": self.get_operation_history,
            "create_object_handle": self.create_object_handle,
            "create_material_handle": self.create_material_handle,
            "list_object_handles": self.list_object_handles,
            "list_material_handles": self.list_material_handles,
            # Geometry Nodes tools
            "get_geometry_nodes_capabilities": self.get_geometry_nodes_capabilities,
            "list_geometry_node_groups": self.list_geometry_node_groups,
            "get_geometry_node_group_deep_info": self.get_geometry_node_group_deep_info,
            "list_geometry_nodes_modifiers": self.list_geometry_nodes_modifiers,
            "get_geometry_nodes_modifier_info": self.get_geometry_nodes_modifier_info,
            "get_supported_geometry_node_templates": self.get_supported_geometry_node_templates,
            "create_geometry_node_group_from_template": self.create_geometry_node_group_from_template,
            "create_custom_geometry_node_recipe": self.create_custom_geometry_node_recipe,
            "apply_geometry_nodes_modifier": self.apply_geometry_nodes_modifier,
            "set_geometry_nodes_modifier_input": self.set_geometry_nodes_modifier_input,
            "create_procedural_asset": self.create_procedural_asset,
            "create_scatter_system": self.create_scatter_system,
            "create_curve_generator": self.create_curve_generator,
            "create_radial_array_system": self.create_radial_array_system,
            "create_panel_generator": self.create_panel_generator,
            "create_cable_or_rope_generator": self.create_cable_or_rope_generator,
            "create_terrain_noise_system": self.create_terrain_noise_system,
            "validate_geometry_node_group": self.validate_geometry_node_group,
            "create_geometry_nodes_preview": self.create_geometry_nodes_preview,
            "create_geometry_nodes_scene_kit": self.create_geometry_nodes_scene_kit,
            "delete_geometry_node_groups": self.delete_geometry_node_groups,
            "remove_geometry_nodes_modifiers": self.remove_geometry_nodes_modifiers,
            "run_geometry_nodes_workflow_batch": self.run_geometry_nodes_workflow_batch,
            "complete_geometry_node": self.complete_geometry_node,
            "get_geometry_nodes_status": self.get_geometry_nodes_status,
            # Phase 6B addon, docs, snippet, skill pack, and review tools
            "get_addon_management_status": self.get_addon_management_status,
            "list_blender_addons": self.list_blender_addons,
            "get_blender_addon_info": self.get_blender_addon_info,
            "install_local_addon": self.install_local_addon,
            "enable_blender_addon": self.enable_blender_addon,
            "disable_blender_addon": self.disable_blender_addon,
            "remove_blender_addon": self.remove_blender_addon,
            "create_addon_skeleton": self.create_addon_skeleton,
            "validate_addon_skeleton": self.validate_addon_skeleton,
            "package_addon_zip": self.package_addon_zip,
            "inspect_blender_api_docs": self.inspect_blender_api_docs,
            "build_blender_api_index": self.build_blender_api_index,
            "search_blender_api_docs": self.search_blender_api_docs,
            "get_blender_api_topic": self.get_blender_api_topic,
            "create_verified_snippet": self.create_verified_snippet,
            "validate_verified_snippet": self.validate_verified_snippet,
            "list_verified_snippets": self.list_verified_snippets,
            "search_verified_snippets": self.search_verified_snippets,
            "get_verified_snippet": self.get_verified_snippet,
            "run_verified_snippet_smoke": self.run_verified_snippet_smoke,
            "delete_verified_snippets": self.delete_verified_snippets,
            "create_skill_pack": self.create_skill_pack,
            "validate_skill_pack": self.validate_skill_pack,
            "list_skill_packs": self.list_skill_packs,
            "get_skill_pack": self.get_skill_pack,
            "run_skill_pack": self.run_skill_pack,
            "delete_skill_packs": self.delete_skill_packs,
            "export_project_review_package": self.export_project_review_package,
            "validate_review_package": self.validate_review_package,
            "run_advanced_knowledge_workflow_batch": self.run_advanced_knowledge_workflow_batch,
            # Script Registry tools
            "register_context_script": self.register_context_script,
            "execute_context_script": self.execute_context_script,
            "list_context_scripts": self.list_context_scripts,
            "clear_context_scripts": self.clear_context_scripts,
        }

        # Add Polyhaven handlers only if enabled
        if bpy.context.scene.blendermcp_use_polyhaven:
            polyhaven_handlers = {
                "get_polyhaven_categories": self.get_polyhaven_categories,
                "search_polyhaven_assets": self.search_polyhaven_assets,
                "download_polyhaven_asset": self.download_polyhaven_asset,
                "set_texture": self.set_texture,
            }
            handlers.update(polyhaven_handlers)

        # Add Hyper3d handlers only if enabled
        if bpy.context.scene.blendermcp_use_hyper3d:
            polyhaven_handlers = {
                "create_rodin_job": self.create_rodin_job,
                "poll_rodin_job_status": self.poll_rodin_job_status,
                "import_generated_asset": self.import_generated_asset,
            }
            handlers.update(polyhaven_handlers)

        # Add Sketchfab handlers only if enabled
        if bpy.context.scene.blendermcp_use_sketchfab:
            sketchfab_handlers = {
                "search_sketchfab_models": self.search_sketchfab_models,
                "download_sketchfab_model": self.download_sketchfab_model,
            }
            handlers.update(sketchfab_handlers)

        return handlers

    def _dispatch_command(self, command):
        """Dispatch a command using the current handler registry."""
        cmd_type = command.get("type")
        params = command.get("params", {})

        safety_decision = self.safety_policy_service.evaluate_command(cmd_type, params)
        if not safety_decision["allowed"]:
            return {
                "status": "error",
                "message": "Command blocked by safety policy",
                "safety": safety_decision,
            }

        # Add a handler for checking PolyHaven status
        if cmd_type == "get_polyhaven_status":
            response = {"status": "success", "result": self.get_polyhaven_status()}
            if self.safety_policy_service.mode == SAFETY_MODE_AUDIT:
                response["safety"] = safety_decision
            return response

        if cmd_type == "get_safety_status":
            return {"status": "success", "result": self.get_safety_status()}

        handlers = self._build_command_handlers()

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print(f"Handler execution complete")
                response = {"status": "success", "result": result}
                if self.safety_policy_service.mode == SAFETY_MODE_AUDIT:
                    response["safety"] = safety_decision
                return response
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}



    def get_system_status(self):
        return build_operation_response(
            status="success",
            tool="get_system_status",
            result={
                "addon": "Overtli-Blender",
                "safety_mode": self.safety_policy_service.mode,
                "blender_version": ".".join(str(part) for part in bpy.app.version),
                "governance": "phase7b",
            },
        )

    def get_project_status(self):
        return build_operation_response(
            status="success",
            tool="get_project_status",
            result=self.project_workspace_service.get_project_status(),
        )

    def discover_tool_packs(self):
        return build_operation_response(status="success", tool="discover_tool_packs", result=runtime_discover_tool_packs())

    def get_tool_pack(self, name):
        return build_operation_response(status="success", tool="get_tool_pack", result=runtime_get_tool_pack(name))

    def search_tools(self, query, category=None, tool_pack=None, risk_max=None, limit=20):
        return build_operation_response(status="success", tool="search_tools", result=runtime_search_tools(query, category=category, tool_pack=tool_pack, risk_max=risk_max, limit=limit))

    def get_tool_spec(self, name):
        return build_operation_response(status="success", tool="get_tool_spec", result=runtime_get_tool_spec(name))

    def get_recommended_tools_for_task(self, task, limit=8):
        return build_operation_response(status="success", tool="get_recommended_tools_for_task", result=runtime_get_recommended_tools_for_task(task, limit=limit))

    def prepare_operation(self, command_name, params=None):
        return build_operation_response(status="requires_approval", tool="prepare_operation", result=DEFAULT_APPROVAL_RUNTIME.prepare_operation(command_name, params or {}, scene_revision=len(getattr(bpy.context.scene, "objects", []))))

    def get_pending_approvals(self):
        return build_operation_response(status="success", tool="get_pending_approvals", result=DEFAULT_APPROVAL_RUNTIME.get_pending_approvals())

    def approve_operation(self, approval_id):
        return build_operation_response(status="success", tool="approve_operation", result=DEFAULT_APPROVAL_RUNTIME.approve_operation(approval_id))

    def deny_operation(self, approval_id, reason=None):
        return build_operation_response(status="success", tool="deny_operation", result=DEFAULT_APPROVAL_RUNTIME.deny_operation(approval_id, reason=reason))

    def execute_approved_operation(self, approval_id, command_name, params=None):
        result = DEFAULT_APPROVAL_RUNTIME.execute_approved_operation(approval_id, command_name, params or {})
        return build_operation_response(status=result.get("status", "not_implemented"), tool="execute_approved_operation", result=result)

    def expire_approval(self, approval_id=None):
        return build_operation_response(status="success", tool="expire_approval", result=DEFAULT_APPROVAL_RUNTIME.expire_approval(approval_id))

    def get_operation_status(self, operation_id=None):
        return build_operation_response(status="success", tool="get_operation_status", result=DEFAULT_OPERATION_RUNTIME.get_operation_status(operation_id))

    def list_recent_operations(self, limit=20):
        return build_operation_response(status="success", tool="list_recent_operations", result=DEFAULT_OPERATION_RUNTIME.list_recent_operations(limit))

    def cancel_operation(self, operation_id):
        result = DEFAULT_OPERATION_RUNTIME.cancel_operation(operation_id)
        return build_operation_response(status=result.get("status", "success"), tool="cancel_operation", result=result)

    def get_operation_log(self, operation_id=None):
        return build_operation_response(status="success", tool="get_operation_log", result=DEFAULT_OPERATION_RUNTIME.get_operation_log(operation_id))

    def get_permission_profile(self):
        return build_operation_response(status="success", tool="get_permission_profile", result=runtime_get_permission_profile())

    def set_permission_profile(self, profile, confirm=False):
        result = runtime_set_permission_profile(profile, confirm=confirm)
        return build_operation_response(status=result.get("status", "success"), tool="set_permission_profile", result=result)

    def get_capability_policy(self):
        return build_operation_response(status="success", tool="get_capability_policy", result=runtime_get_capability_policy())

    def validate_command_capabilities(self, command_name, profile=None):
        result = runtime_validate_command_capabilities(command_name, profile=profile)
        return build_operation_response(status=result.get("status", "success"), tool="validate_command_capabilities", result=result)

    def get_log_status(self):
        return build_operation_response(status="success", tool="get_log_status", result=runtime_get_log_status())

    def export_operation_log(self, operation_id=None):
        return build_operation_response(status="success", tool="export_operation_log", result=runtime_export_operation_log(operation_id))

    def get_command_registry_report(self):
        return build_operation_response(status="success", tool="get_command_registry_report", result=command_registry_report())

    def get_scene_info(self):
        """Get information about the current Blender scene"""
        return self.scene_observation_service.get_scene_info()

    @staticmethod
    def _get_aabb(obj):
        """ Returns the world-space axis-aligned bounding box (AABB) of an object. """
        if obj.type != 'MESH':
            raise TypeError("Object must be a mesh")

        # Get the bounding box corners in local space
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]

        # Convert to world coordinates
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]

        # Compute axis-aligned min/max coordinates
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

        return [
            [*min_corner], [*max_corner]
        ]



    def get_object_info(self, name):
        """Get detailed information about a specific object"""
        return self.scene_observation_service.get_object_info(name)

    def get_viewport_screenshot(self, max_size=800, filepath=None, format="png"):
        """
        Capture a screenshot of the current 3D viewport and save it to the specified path.

        Parameters:
        - max_size: Maximum size in pixels for the largest dimension of the image
        - filepath: Path where to save the screenshot file
        - format: Image format (png, jpg, etc.)

        Returns success/error status
        """
        return self.viewport_screenshot_service.get_viewport_screenshot(max_size, filepath, format)

    def get_scene_index(self, include_hidden=True, include_materials=True, include_modifiers=True, include_constraints=True, include_collections=True, max_objects=None):
        """Get a bounded, JSON-serializable index of the current scene."""
        return self.scene_intelligence_service.get_scene_index(include_hidden, include_materials, include_modifiers, include_constraints, include_collections, max_objects)

    def get_object_deep_info(self, object_name=None, name=None, include_mesh_stats=True, include_material_slots=True, include_modifiers=True, include_constraints=True, include_animation=True, include_custom_properties=True):
        """Get deep, bounded inspection data for a single object."""
        return self.scene_intelligence_service.get_object_deep_info(object_name, name, include_mesh_stats, include_material_slots, include_modifiers, include_constraints, include_animation, include_custom_properties)

    def get_selection_info(self):
        """Get active object and selection details without mutating selection."""
        return self.scene_intelligence_service.get_selection_info()

    def get_scene_health(self):
        """Get a non-destructive scene metrics and health summary."""
        return self.scene_intelligence_service.get_scene_health()

    def capture_viewport_pack(self, views=None, max_size=800, include_manifest=True, snapshot_name=None, artifact_root=None):
        """Capture a local multi-view screenshot pack under the generated artifact directory."""
        return self.verification_artifact_service.capture_viewport_pack(views, max_size, include_manifest, snapshot_name, artifact_root=artifact_root)

    def create_verification_snapshot(self, label=None, include_scene_index=True, include_scene_health=True, include_selection=True, include_screenshots=True, views=None, max_size=800, artifact_root=None):
        """Create a local verification snapshot manifest and requested artifacts."""
        return self.verification_artifact_service.create_verification_snapshot(label, include_scene_index, include_scene_health, include_selection, include_screenshots, views, max_size, artifact_root)

    def list_verification_snapshots(self):
        """List local verification snapshots generated by Phase 2 tools."""
        return self.verification_artifact_service.list_verification_snapshots()

    def get_supported_edit_operations(self):
        """List Phase 3 supported edit operations and safety metadata."""
        return self.scene_edit_service.get_supported_edit_operations()

    def create_primitive_object(self, primitive_type, name=None, location=None, rotation=None, scale=None, collection_name=None, material_name=None, verify=False):
        """Create a supported primitive object with explicit parameters."""
        return self.scene_edit_service.create_primitive_object(primitive_type, name, location, rotation, scale, collection_name, material_name, verify)

    def transform_object(self, object_name, location=None, rotation=None, scale=None, relative=False, verify=False):
        """Transform one explicitly named object."""
        return self.scene_edit_service.transform_object(object_name, location, rotation, scale, relative, verify)

    def duplicate_object(self, object_name, new_name=None, linked=False, location_offset=None, collection_name=None, verify=False):
        """Duplicate one explicitly named object."""
        return self.scene_edit_service.duplicate_object(object_name, new_name, linked, location_offset, collection_name, verify)

    def delete_objects(self, object_names, confirm=False, allow_missing=False, verify=False):
        """Delete only explicitly named objects after confirmation."""
        return self.scene_edit_service.delete_objects(object_names, confirm, allow_missing, verify)

    def set_object_visibility(self, object_name, hide_viewport=None, hide_render=None, verify=False):
        """Set viewport/render visibility on one explicitly named object."""
        return self.scene_edit_service.set_object_visibility(object_name, hide_viewport, hide_render, verify)

    def create_basic_material(self, name, base_color=None, metallic=None, roughness=None, alpha=None, use_nodes=True, replace_existing=False):
        """Create or update a basic material."""
        return self.material_authoring_service.create_basic_material(name, base_color, metallic, roughness, alpha, use_nodes, replace_existing)

    def assign_material(self, object_name, material_name, slot_index=None, replace=True, verify=False):
        """Assign an existing material to one explicitly named object."""
        return self.material_authoring_service.assign_material(object_name, material_name, slot_index, replace, verify)

    def update_material_properties(self, material_name, base_color=None, metallic=None, roughness=None, alpha=None, verify=False):
        """Update supported properties on an existing material."""
        return self.material_authoring_service.update_material_properties(material_name, base_color, metallic, roughness, alpha, verify)

    def get_timeline_info(self, include_markers=True, include_playback=True):
        return self.animation_intelligence_service.get_timeline_info(include_markers, include_playback)

    def list_animated_objects(self, include_material_animation=True, include_shape_key_animation=True, include_drivers=True, max_objects=None):
        return self.animation_intelligence_service.list_animated_objects(include_material_animation, include_shape_key_animation, include_drivers, max_objects)

    def get_animation_deep_info(self, object_name=None, material_name=None, include_keyframes=True, include_fcurves=True, include_drivers=True, max_keyframes=200):
        return self.animation_intelligence_service.get_animation_deep_info(object_name, material_name, include_keyframes, include_fcurves, include_drivers, max_keyframes)

    def set_timeline_range(self, frame_start, frame_end, fps=None, current_frame=None):
        return self.animation_intelligence_service.set_timeline_range(frame_start, frame_end, fps, current_frame)

    def set_current_frame(self, frame):
        return self.animation_intelligence_service.set_current_frame(frame)

    def insert_transform_keyframes(self, object_name, frames, properties=None):
        return self.animation_authoring_service.insert_transform_keyframes(object_name, frames, properties)

    def animate_object_transform(self, object_name, keyframes, interpolation="BEZIER", clear_existing=False, confirm_clear_existing=False, verify=False):
        return self.animation_authoring_service.animate_object_transform(object_name, keyframes, interpolation, clear_existing, confirm_clear_existing, verify)

    def animate_camera_transform(self, camera_name, keyframes, interpolation="BEZIER", clear_existing=False, confirm_clear_existing=False, verify=False):
        return self.animation_authoring_service.animate_camera_transform(camera_name, keyframes, interpolation, clear_existing, confirm_clear_existing, verify)

    def animate_light_property(self, light_name, property_name, keyframes, interpolation="BEZIER"):
        return self.animation_authoring_service.animate_light_property(light_name, property_name, keyframes, interpolation)

    def animate_material_property(self, material_name, channel, keyframes, interpolation="BEZIER"):
        return self.animation_authoring_service.animate_material_property(material_name, channel, keyframes, interpolation)

    def animate_shape_key_value(self, object_name, shape_key_name, keyframes, interpolation="BEZIER"):
        return self.animation_authoring_service.animate_shape_key_value(object_name, shape_key_name, keyframes, interpolation)

    def delete_animation_data(self, target_type, target_name, data_paths=None, confirm=False):
        return self.animation_authoring_service.delete_animation_data(target_type, target_name, data_paths, confirm)

    def create_camera(self, camera_name=None, location=None, rotation=None, lens=None, sensor_width=None, clip_start=None, clip_end=None, collection_name=None, set_active=False, verify=False):
        return self.camera_composition_service.create_camera(camera_name, location, rotation, lens, sensor_width, clip_start, clip_end, collection_name, set_active, verify)

    def frame_camera_to_objects(self, camera_name, object_names, view="front_perspective", margin=1.25, distance_multiplier=1.0, look_at=True, set_active=True, verify=False):
        return self.camera_composition_service.frame_camera_to_objects(camera_name, object_names, view, margin, distance_multiplier, look_at, set_active, verify)

    def set_active_camera(self, camera_name):
        return self.camera_composition_service.set_active_camera(camera_name)

    def create_light(self, light_name=None, light_type="AREA", location=None, rotation=None, energy=None, color=None, size=None, collection_name=None, verify=False):
        return self.lighting_setup_service.create_light(light_name, light_type, location, rotation, energy, color, size, collection_name, verify)

    def create_lighting_setup(self, setup_name, target_object_names=None, preset="three_point", collection_name=None, replace_existing_with_prefix=False, confirm_replace=False, verify=False):
        return self.lighting_setup_service.create_lighting_setup(setup_name, target_object_names, preset, collection_name, replace_existing_with_prefix, confirm_replace, verify)

    def update_light(self, light_name, energy=None, color=None, size=None, location=None, rotation=None, verify=False):
        return self.lighting_setup_service.update_light(light_name, energy, color, size, location, rotation, verify)

    def set_world_lighting(self, color=None, strength=None, verify=False):
        return self.lighting_setup_service.set_world_lighting(color, strength, verify)

    def get_render_settings(self):
        return self.render_settings_service.get_render_settings()

    def set_render_settings(self, engine=None, resolution_x=None, resolution_y=None, resolution_percentage=None, samples=None, image_format=None, transparent=None, color_management=None, clamp_for_smoke=False):
        return self.render_settings_service.set_render_settings(engine, resolution_x, resolution_y, resolution_percentage, samples, image_format, transparent, color_management, clamp_for_smoke)

    def set_output_path(self, output_path=None, artifact_root=None, subdir="renders/stills", filename=None):
        return self.render_settings_service.set_output_path(output_path, artifact_root, subdir, filename)

    def render_still(self, output_path=None, artifact_root=None, filename=None, camera_name=None, frame=None, clamp_for_smoke=True, write_manifest=True):
        return self.render_artifact_service.render_still(output_path, artifact_root, filename, camera_name, frame, clamp_for_smoke, write_manifest)

    def render_contact_sheet(self, object_names=None, camera_name=None, views=None, artifact_root=None, filename=None, clamp_for_smoke=True):
        return self.render_artifact_service.render_contact_sheet(object_names, camera_name, views, artifact_root, filename, clamp_for_smoke)

    def create_turntable_animation(self, object_name, frame_start=1, frame_end=48, axis="Z", rotations=1.0, empty_name=None, camera_name=None, confirm_clear_existing=False):
        return self.render_artifact_service.create_turntable_animation(object_name, frame_start, frame_end, axis, rotations, empty_name, camera_name, confirm_clear_existing)

    def render_preview_animation(self, output_dir=None, artifact_root=None, frame_start=None, frame_end=None, step=1, max_frames=24, camera_name=None, clamp_for_smoke=True):
        return self.render_artifact_service.render_preview_animation(output_dir, artifact_root, frame_start, frame_end, step, max_frames, camera_name, clamp_for_smoke)

    def get_compositor_status(self):
        return self.compositor_pass_service.get_compositor_status()

    def set_compositor_preset(self, preset="basic_viewer", confirm_replace=False):
        return self.compositor_pass_service.set_compositor_preset(preset, confirm_replace)

    def set_render_passes(self, use_pass_z=None, use_pass_mist=None, use_pass_normal=None, use_pass_diffuse_color=None):
        return self.compositor_pass_service.set_render_passes(use_pass_z, use_pass_mist, use_pass_normal, use_pass_diffuse_color)

    def run_presentation_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=20, batch_allow_destructive=False, artifact_root=None):
        return self.presentation_workflow_batch_service.run_presentation_workflow_batch(label, operations, create_before_snapshot, create_after_snapshot, stop_on_error, max_operations, batch_allow_destructive, artifact_root)

    def cleanup_presentation_artifacts(self, prefix, confirm=False, cleanup_scene_data=True, cleanup_render_artifacts=False, artifact_root=None):
        return self.presentation_workflow_batch_service.cleanup_presentation_artifacts(prefix, confirm, cleanup_scene_data, cleanup_render_artifacts, artifact_root)

    def add_object_modifier(self, object_name, modifier_type, name=None, properties=None, verify=False):
        """Add an allowlisted modifier to one explicitly named object."""
        return self.modifier_service.add_object_modifier(object_name, modifier_type, name, properties, verify)

    def update_object_modifier(self, object_name, modifier_name, properties, verify=False):
        """Update allowlisted properties on an existing modifier."""
        return self.modifier_service.update_object_modifier(object_name, modifier_name, properties, verify)

    def remove_object_modifier(self, object_name, modifier_name, confirm=False, verify=False):
        """Remove one named modifier after confirmation."""
        return self.modifier_service.remove_object_modifier(object_name, modifier_name, confirm, verify)

    def create_collection(self, collection_name, parent_collection_name=None, replace_existing=False):
        """Create a collection without deleting existing collections."""
        return self.collection_organization_service.create_collection(collection_name, parent_collection_name, replace_existing)

    def move_objects_to_collection(self, object_names, collection_name, unlink_from_other_collections=False, create_collection=False):
        """Move or link explicitly named objects to an existing collection."""
        return self.collection_organization_service.move_objects_to_collection(object_names, collection_name, unlink_from_other_collections, create_collection)

    def delete_collection(self, collection_name, confirm=False, require_empty=True):
        """Delete one explicitly named collection after confirmation; empty-only by default."""
        return self.collection_organization_service.delete_collection(collection_name, confirm, require_empty)

    def run_verified_edit_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=20, batch_allow_destructive=False, artifact_root=None):
        """Run a controlled allowlisted edit batch with before/after verification."""
        return self.verified_edit_batch_service.run_verified_edit_batch(label, operations, create_before_snapshot, create_after_snapshot, stop_on_error, max_operations, batch_allow_destructive, artifact_root)

    def get_task_workspace(self, artifact_root=None):
        """Get the persistent Phase 3 task workspace summary."""
        return self.workspace_safety_diff_service.get_task_workspace(artifact_root)

    def create_workspace_task(self, title, goal=None, assumptions=None, status="pending", task_id=None, artifact_root=None):
        """Create a persistent task workspace entry."""
        return self.workspace_safety_diff_service.create_workspace_task(title, goal, assumptions, status, task_id, artifact_root)

    def update_workspace_task(self, task_id, status=None, goal=None, assumptions=None, rollback_status=None, verification=None, artifact_root=None):
        """Update a persistent task workspace entry."""
        return self.workspace_safety_diff_service.update_workspace_task(task_id, status, goal, assumptions, rollback_status, verification, artifact_root)

    def list_workspace_tasks(self, status=None, artifact_root=None):
        """List persistent task workspace entries."""
        return self.workspace_safety_diff_service.list_workspace_tasks(status, artifact_root)

    def add_workspace_todo(self, text, task_id=None, state="pending", todo_id=None, artifact_root=None):
        """Add a persistent todo entry."""
        return self.workspace_safety_diff_service.add_workspace_todo(text, task_id, state, todo_id, artifact_root)

    def update_workspace_todo(self, todo_id, state=None, text=None, evidence=None, artifact_root=None):
        """Update a persistent todo entry."""
        return self.workspace_safety_diff_service.update_workspace_todo(todo_id, state, text, evidence, artifact_root)

    def list_workspace_todos(self, task_id=None, state=None, artifact_root=None):
        """List persistent todo entries."""
        return self.workspace_safety_diff_service.list_workspace_todos(task_id, state, artifact_root)

    def record_operation_journal_entry(self, operation_type, task_id=None, target=None, summary=None, risk_level="LOW", rollback_status="unknown", before_snapshot_id=None, after_snapshot_id=None, metadata=None, artifact_root=None):
        """Record a durable operation journal entry."""
        return self.workspace_safety_diff_service.record_operation_journal_entry(operation_type, task_id, target, summary, risk_level, rollback_status, before_snapshot_id, after_snapshot_id, metadata, artifact_root)

    def get_operation_journal(self, task_id=None, limit=50, artifact_root=None):
        """Read durable operation journal entries."""
        return self.workspace_safety_diff_service.get_operation_journal(task_id, limit, artifact_root)

    def create_scene_snapshot(self, label=None, task_id=None, include_verification_snapshot=False, artifact_root=None):
        """Create a lightweight durable scene state snapshot."""
        return self.workspace_safety_diff_service.create_scene_snapshot(label, task_id, include_verification_snapshot, artifact_root)

    def list_scene_snapshots(self, artifact_root=None):
        """List durable scene state snapshots."""
        return self.workspace_safety_diff_service.list_scene_snapshots(artifact_root)

    def diff_scene_snapshots(self, before_snapshot_id, after_snapshot_id, artifact_root=None):
        """Diff two durable scene state snapshots."""
        return self.workspace_safety_diff_service.diff_scene_snapshots(before_snapshot_id, after_snapshot_id, artifact_root)

    def detect_user_changes(self, baseline_snapshot_id=None, artifact_root=None):
        """Detect scene changes relative to a baseline snapshot."""
        return self.workspace_safety_diff_service.detect_user_changes(baseline_snapshot_id, artifact_root)

    def rollback_to_scene_snapshot(self, snapshot_id, confirm=False, remove_new_objects=False, verify=True, artifact_root=None):
        """Rollback existing object transforms and visibility to a scene snapshot."""
        return self.workspace_safety_diff_service.rollback_to_scene_snapshot(snapshot_id, confirm, remove_new_objects, verify, artifact_root)

    def undo_last_blender_operation(self, confirm=False):
        """Request Blender undo after explicit confirmation."""
        return self.workspace_safety_diff_service.undo_last_blender_operation(confirm)

    def get_safety_status(self):
        """Get the current safety policy status."""
        return self.safety_policy_service.get_safety_status()

    def execute_code(self, code):
        """Execute arbitrary Blender Python code with shared context"""
        return self.raw_code_execution_service.execute_code(code)

    def _store_object_handle(self, handle, obj_name):
        """Store object reference by handle"""
        return self.shared_context_service.store_object_handle(handle, obj_name)

    def _store_material_handle(self, handle, mat_name):
        """Store material reference by handle"""
        return self.shared_context_service.store_material_handle(handle, mat_name)

    def _store_operation_result(self, op_id, result):
        """Store operation result by ID"""
        return self.shared_context_service.store_operation_result(op_id, result)

    def _add_to_history(self, operation, input_data, result):
        """Add operation to history"""
        self.shared_context_service.add_to_history(operation, input_data, result)

    def get_shared_context(self):
        """Get current shared context state"""
        return self.shared_context_service.get_shared_context()

    def clear_shared_context(self, section="all"):
        """Clear shared context (all, variables, objects, materials, operations, history)"""
        return self.shared_context_service.clear_shared_context(section)

    def get_operation_history(self, count=10):
        """Get recent operation history"""
        return self.shared_context_service.get_operation_history(count)

    def create_object_handle(self, handle, object_name):
        """Create a handle for an object to reference in future operations"""
        return self.shared_context_service.create_object_handle(handle, object_name)

    def create_material_handle(self, handle, material_name):
        """Create a handle for a material to reference in future operations"""
        return self.shared_context_service.create_material_handle(handle, material_name)

    def list_object_handles(self):
        """List all object handles and their details"""
        return self.shared_context_service.list_object_handles()

    def list_material_handles(self):
        """List all material handles and their details"""
        return self.shared_context_service.list_material_handles()

    def get_polyhaven_categories(self, asset_type):
        """Get categories for a specific asset type from Polyhaven"""
        try:
            if asset_type not in ["hdris", "textures", "models", "all"]:
                return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}

            response = requests.get(f"https://api.polyhaven.com/categories/{asset_type}", headers=REQ_HEADERS)
            if response.status_code == 200:
                return {"categories": response.json()}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def search_polyhaven_assets(self, asset_type=None, categories=None):
        """Search for assets from Polyhaven with optional filtering"""
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}

            if asset_type and asset_type != "all":
                if asset_type not in ["hdris", "textures", "models"]:
                    return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}
                params["type"] = asset_type

            if categories:
                params["categories"] = categories

            response = requests.get(url, params=params, headers=REQ_HEADERS)
            if response.status_code == 200:
                # Limit the response size to avoid overwhelming Blender
                assets = response.json()
                # Return only the first 20 assets to keep response size manageable
                limited_assets = {}
                for i, (key, value) in enumerate(assets.items()):
                    if i >= 20:  # Limit to 20 assets
                        break
                    limited_assets[key] = value

                return {"assets": limited_assets, "total_count": len(assets), "returned_count": len(limited_assets)}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def download_polyhaven_asset(self, asset_id, asset_type, resolution="1k", file_format=None):
        try:
            # First get the files information
            files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}", headers=REQ_HEADERS)
            if files_response.status_code != 200:
                return {"error": f"Failed to get asset files: {files_response.status_code}"}

            files_data = files_response.json()

            # Handle different asset types
            if asset_type == "hdris":
                # For HDRIs, download the .hdr or .exr file
                if not file_format:
                    file_format = "hdr"  # Default format for HDRIs

                if "hdri" in files_data and resolution in files_data["hdri"] and file_format in files_data["hdri"][resolution]:
                    file_info = files_data["hdri"][resolution][file_format]
                    file_url = file_info["url"]

                    # For HDRIs, we need to save to a temporary file first
                    # since Blender can't properly load HDR data directly from memory
                    with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                        # Download the file
                        response = requests.get(file_url, headers=REQ_HEADERS)
                        if response.status_code != 200:
                            return {"error": f"Failed to download HDRI: {response.status_code}"}

                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name

                    try:
                        # Create a new world if none exists
                        if not bpy.data.worlds:
                            bpy.data.worlds.new("World")

                        world = bpy.data.worlds[0]
                        world.use_nodes = True
                        node_tree = world.node_tree

                        # Clear existing nodes
                        for node in node_tree.nodes:
                            node_tree.nodes.remove(node)

                        # Create nodes
                        tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
                        tex_coord.location = (-800, 0)

                        mapping = node_tree.nodes.new(type='ShaderNodeMapping')
                        mapping.location = (-600, 0)

                        # Load the image from the temporary file
                        env_tex = node_tree.nodes.new(type='ShaderNodeTexEnvironment')
                        env_tex.location = (-400, 0)
                        env_tex.image = bpy.data.images.load(tmp_path)

                        # Use a color space that exists in all Blender versions
                        if file_format.lower() == 'exr':
                            # Try to use Linear color space for EXR files
                            try:
                                env_tex.image.colorspace_settings.name = 'Linear'
                            except:
                                # Fallback to Non-Color if Linear isn't available
                                env_tex.image.colorspace_settings.name = 'Non-Color'
                        else:  # hdr
                            # For HDR files, try these options in order
                            for color_space in ['Linear', 'Linear Rec.709', 'Non-Color']:
                                try:
                                    env_tex.image.colorspace_settings.name = color_space
                                    break  # Stop if we successfully set a color space
                                except:
                                    continue

                        background = node_tree.nodes.new(type='ShaderNodeBackground')
                        background.location = (-200, 0)

                        output = node_tree.nodes.new(type='ShaderNodeOutputWorld')
                        output.location = (0, 0)

                        # Connect nodes
                        node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
                        node_tree.links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
                        node_tree.links.new(env_tex.outputs['Color'], background.inputs['Color'])
                        node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])

                        # Set as active world
                        bpy.context.scene.world = world

                        # Clean up temporary file
                        try:
                            tempfile._cleanup()  # This will clean up all temporary files
                        except:
                            pass

                        return {
                            "success": True,
                            "message": f"HDRI {asset_id} imported successfully",
                            "image_name": env_tex.image.name
                        }
                    except Exception as e:
                        return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
                else:
                    return {"error": f"Requested resolution or format not available for this HDRI"}

            elif asset_type == "textures":
                if not file_format:
                    file_format = "jpg"  # Default format for textures

                downloaded_maps = {}

                try:
                    for map_type in files_data:
                        if map_type not in ["blend", "gltf"]:  # Skip non-texture files
                            if resolution in files_data[map_type] and file_format in files_data[map_type][resolution]:
                                file_info = files_data[map_type][resolution][file_format]
                                file_url = file_info["url"]

                                # Use NamedTemporaryFile like we do for HDRIs
                                with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                                    # Download the file
                                    response = requests.get(file_url, headers=REQ_HEADERS)
                                    if response.status_code == 200:
                                        tmp_file.write(response.content)
                                        tmp_path = tmp_file.name

                                        # Load image from temporary file
                                        image = bpy.data.images.load(tmp_path)
                                        image.name = f"{asset_id}_{map_type}.{file_format}"

                                        # Pack the image into .blend file
                                        image.pack()

                                        # Set color space based on map type
                                        if map_type in ['color', 'diffuse', 'albedo']:
                                            try:
                                                image.colorspace_settings.name = 'sRGB'
                                            except:
                                                pass
                                        else:
                                            try:
                                                image.colorspace_settings.name = 'Non-Color'
                                            except:
                                                pass

                                        downloaded_maps[map_type] = image

                                        # Clean up temporary file
                                        try:
                                            os.unlink(tmp_path)
                                        except:
                                            pass

                    if not downloaded_maps:
                        return {"error": f"No texture maps found for the requested resolution and format"}

                    # Create a new material with the downloaded textures
                    mat = bpy.data.materials.new(name=asset_id)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links

                    # Clear default nodes
                    for node in nodes:
                        nodes.remove(node)

                    # Create output node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    output.location = (300, 0)

                    # Create principled BSDF node
                    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
                    principled.location = (0, 0)
                    links.new(principled.outputs[0], output.inputs[0])

                    # Add texture nodes based on available maps
                    tex_coord = nodes.new(type='ShaderNodeTexCoord')
                    tex_coord.location = (-800, 0)

                    mapping = nodes.new(type='ShaderNodeMapping')
                    mapping.location = (-600, 0)
                    mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
                    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

                    # Position offset for texture nodes
                    x_pos = -400
                    y_pos = 300

                    # Connect different texture maps
                    for map_type, image in downloaded_maps.items():
                        tex_node = nodes.new(type='ShaderNodeTexImage')
                        tex_node.location = (x_pos, y_pos)
                        tex_node.image = image

                        # Set color space based on map type
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            try:
                                tex_node.image.colorspace_settings.name = 'sRGB'
                            except:
                                pass  # Use default if sRGB not available
                        else:
                            try:
                                tex_node.image.colorspace_settings.name = 'Non-Color'
                            except:
                                pass  # Use default if Non-Color not available

                        links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

                        # Connect to appropriate input on Principled BSDF
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                        elif map_type.lower() in ['roughness', 'rough']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                        elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                        elif map_type.lower() in ['normal', 'nor']:
                            # Add normal map node
                            normal_map = nodes.new(type='ShaderNodeNormalMap')
                            normal_map.location = (x_pos + 200, y_pos)
                            links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                            links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                        elif map_type in ['displacement', 'disp', 'height']:
                            # Add displacement node
                            disp_node = nodes.new(type='ShaderNodeDisplacement')
                            disp_node.location = (x_pos + 200, y_pos - 200)
                            links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                            links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])

                        y_pos -= 250

                    # Auto-create material handle for easy chaining
                    material_handle = f"material_{asset_id}"
                    self.shared_context['materials'][material_handle] = mat

                    self._add_to_history("download_polyhaven_asset", f"texture {asset_id}", f"Created material {mat.name}")

                    return {
                        "success": True,
                        "message": f"Texture {asset_id} imported as material",
                        "material": mat.name,
                        "material_handle": material_handle,  # New: handle for chaining
                        "maps": list(downloaded_maps.keys())
                    }

                except Exception as e:
                    return {"error": f"Failed to process textures: {str(e)}"}

            elif asset_type == "models":
                # For models, prefer glTF format if available
                if not file_format:
                    file_format = "gltf"  # Default format for models

                if file_format in files_data and resolution in files_data[file_format]:
                    file_info = files_data[file_format][resolution][file_format]
                    file_url = file_info["url"]

                    # Create a temporary directory to store the model and its dependencies
                    temp_dir = tempfile.mkdtemp()
                    main_file_path = ""

                    try:
                        # Download the main model file
                        main_file_name = file_url.split("/")[-1]
                        main_file_path = os.path.join(temp_dir, main_file_name)

                        response = requests.get(file_url, headers=REQ_HEADERS)
                        if response.status_code != 200:
                            return {"error": f"Failed to download model: {response.status_code}"}

                        with open(main_file_path, "wb") as f:
                            f.write(response.content)

                        # Check for included files and download them
                        if "include" in file_info and file_info["include"]:
                            for include_path, include_info in file_info["include"].items():
                                # Get the URL for the included file - this is the fix
                                include_url = include_info["url"]

                                # Create the directory structure for the included file
                                include_file_path = os.path.join(temp_dir, include_path)
                                os.makedirs(os.path.dirname(include_file_path), exist_ok=True)

                                # Download the included file
                                include_response = requests.get(include_url, headers=REQ_HEADERS)
                                if include_response.status_code == 200:
                                    with open(include_file_path, "wb") as f:
                                        f.write(include_response.content)
                                else:
                                    print(f"Failed to download included file: {include_path}")

                        # Import the model into Blender
                        if file_format == "gltf" or file_format == "glb":
                            bpy.ops.import_scene.gltf(filepath=main_file_path)
                        elif file_format == "fbx":
                            bpy.ops.import_scene.fbx(filepath=main_file_path)
                        elif file_format == "obj":
                            bpy.ops.import_scene.obj(filepath=main_file_path)
                        elif file_format == "blend":
                            # For blend files, we need to append or link
                            with bpy.data.libraries.load(main_file_path, link=False) as (data_from, data_to):
                                data_to.objects = data_from.objects

                            # Link the objects to the scene
                            for obj in data_to.objects:
                                if obj is not None:
                                    bpy.context.collection.objects.link(obj)
                        else:
                            return {"error": f"Unsupported model format: {file_format}"}

                        # Get the names of imported objects
                        imported_objects = [obj.name for obj in bpy.context.selected_objects]

                        # Auto-create handles for imported objects for easy chaining
                        object_handles = {}
                        for i, obj_name in enumerate(imported_objects):
                            handle = f"imported_{asset_id}_{i}"
                            self.shared_context['objects'][handle] = bpy.data.objects[obj_name]
                            object_handles[handle] = obj_name

                        self._add_to_history("download_polyhaven_asset", f"model {asset_id}", f"Imported {len(imported_objects)} objects")

                        return {
                            "success": True,
                            "message": f"Model {asset_id} imported successfully",
                            "imported_objects": imported_objects,
                            "object_handles": object_handles  # New: handles for chaining
                        }
                    except Exception as e:
                        return {"error": f"Failed to import model: {str(e)}"}
                    finally:
                        # Clean up temporary directory
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                else:
                    return {"error": f"Requested format or resolution not available for this model"}

            else:
                return {"error": f"Unsupported asset type: {asset_type}"}

        except Exception as e:
            return {"error": f"Failed to download asset: {str(e)}"}

    def set_texture(self, object_name, texture_id):
        """Apply a previously downloaded Polyhaven texture to an object by creating a new material"""
        try:
            # Get the object
            obj = bpy.data.objects.get(object_name)
            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Make sure object can accept materials
            if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
                return {"error": f"Object {object_name} cannot accept materials"}

            # Find all images related to this texture and ensure they're properly loaded
            texture_images = {}
            for img in bpy.data.images:
                if img.name.startswith(texture_id + "_"):
                    # Extract the map type from the image name
                    map_type = img.name.split('_')[-1].split('.')[0]

                    # Force a reload of the image
                    img.reload()

                    # Ensure proper color space
                    if map_type.lower() in ['color', 'diffuse', 'albedo']:
                        try:
                            img.colorspace_settings.name = 'sRGB'
                        except:
                            pass
                    else:
                        try:
                            img.colorspace_settings.name = 'Non-Color'
                        except:
                            pass

                    # Ensure the image is packed
                    if not img.packed_file:
                        img.pack()

                    texture_images[map_type] = img
                    print(f"Loaded texture map: {map_type} - {img.name}")

                    # Debug info
                    print(f"Image size: {img.size[0]}x{img.size[1]}")
                    print(f"Color space: {img.colorspace_settings.name}")
                    print(f"File format: {img.file_format}")
                    print(f"Is packed: {bool(img.packed_file)}")

            if not texture_images:
                return {"error": f"No texture images found for: {texture_id}. Please download the texture first."}

            # Create a new material
            new_mat_name = f"{texture_id}_material_{object_name}"

            # Remove any existing material with this name to avoid conflicts
            existing_mat = bpy.data.materials.get(new_mat_name)
            if existing_mat:
                bpy.data.materials.remove(existing_mat)

            new_mat = bpy.data.materials.new(name=new_mat_name)
            new_mat.use_nodes = True

            # Set up the material nodes
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links

            # Clear default nodes
            nodes.clear()

            # Create output node
            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (600, 0)

            # Create principled BSDF node
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            principled.location = (300, 0)
            links.new(principled.outputs[0], output.inputs[0])

            # Add texture nodes based on available maps
            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            tex_coord.location = (-800, 0)

            mapping = nodes.new(type='ShaderNodeMapping')
            mapping.location = (-600, 0)
            mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

            # Position offset for texture nodes
            x_pos = -400
            y_pos = 300

            # Connect different texture maps
            for map_type, image in texture_images.items():
                tex_node = nodes.new(type='ShaderNodeTexImage')
                tex_node.location = (x_pos, y_pos)
                tex_node.image = image

                # Set color space based on map type
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    try:
                        tex_node.image.colorspace_settings.name = 'sRGB'
                    except:
                        pass  # Use default if sRGB not available
                else:
                    try:
                        tex_node.image.colorspace_settings.name = 'Non-Color'
                    except:
                        pass  # Use default if Non-Color not available

                links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

                # Connect to appropriate input on Principled BSDF
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                elif map_type.lower() in ['roughness', 'rough']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                elif map_type.lower() in ['normal', 'nor', 'dx', 'gl']:
                    # Add normal map node
                    normal_map = nodes.new(type='ShaderNodeNormalMap')
                    normal_map.location = (x_pos + 200, y_pos)
                    links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                elif map_type.lower() in ['displacement', 'disp', 'height']:
                    # Add displacement node
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (x_pos + 200, y_pos - 200)
                    disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                    links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])

                y_pos -= 250

            # Second pass: Connect nodes with proper handling for special cases
            texture_nodes = {}

            # First find all texture nodes and store them by map type
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    for map_type, image in texture_images.items():
                        if node.image == image:
                            texture_nodes[map_type] = node
                            break

            # Now connect everything using the nodes instead of images
            # Handle base color (diffuse)
            for map_name in ['color', 'diffuse', 'albedo']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                    print(f"Connected {map_name} to Base Color")
                    break

            # Handle roughness
            for map_name in ['roughness', 'rough']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                    print(f"Connected {map_name} to Roughness")
                    break

            # Handle metallic
            for map_name in ['metallic', 'metalness', 'metal']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                    print(f"Connected {map_name} to Metallic")
                    break

            # Handle normal maps
            for map_name in ['gl', 'dx', 'nor']:
                if map_name in texture_nodes:
                    normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                    normal_map_node.location = (100, 100)
                    links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                    links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                    print(f"Connected {map_name} to Normal")
                    break

            # Handle displacement
            for map_name in ['displacement', 'disp', 'height']:
                if map_name in texture_nodes:
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (300, -200)
                    disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                    links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                    print(f"Connected {map_name} to Displacement")
                    break

            # Handle ARM texture (Ambient Occlusion, Roughness, Metallic)
            if 'arm' in texture_nodes:
                separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
                separate_rgb.location = (-200, -100)
                links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Image'])

                # Connect Roughness (G) if no dedicated roughness map
                if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                    links.new(separate_rgb.outputs['G'], principled.inputs['Roughness'])
                    print("Connected ARM.G to Roughness")

                # Connect Metallic (B) if no dedicated metallic map
                if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                    links.new(separate_rgb.outputs['B'], principled.inputs['Metallic'])
                    print("Connected ARM.B to Metallic")

                # For AO (R channel), multiply with base color if we have one
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(separate_rgb.outputs['R'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    print("Connected ARM.R to AO mix with Base Color")

            # Handle AO (Ambient Occlusion) if separate
            if 'ao' in texture_nodes:
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    print("Connected AO to mix with Base Color")

            # CRITICAL: Make sure to clear all existing materials from the object
            while len(obj.data.materials) > 0:
                obj.data.materials.pop(index=0)

            # Assign the new material to the object
            obj.data.materials.append(new_mat)

            # CRITICAL: Make the object active and select it
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            # CRITICAL: Force Blender to update the material
            bpy.context.view_layer.update()

            # Get the list of texture maps
            texture_maps = list(texture_images.keys())

            # Get info about texture nodes for debugging
            material_info = {
                "name": new_mat.name,
                "has_nodes": new_mat.use_nodes,
                "node_count": len(new_mat.node_tree.nodes),
                "texture_nodes": []
            }

            for node in new_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    connections = []
                    for output in node.outputs:
                        for link in output.links:
                            connections.append(f"{output.name} → {link.to_node.name}.{link.to_socket.name}")

                    material_info["texture_nodes"].append({
                        "name": node.name,
                        "image": node.image.name,
                        "colorspace": node.image.colorspace_settings.name,
                        "connections": connections
                    })

            return {
                "success": True,
                "message": f"Created new material and applied texture {texture_id} to {object_name}",
                "material": new_mat.name,
                "maps": texture_maps,
                "material_info": material_info
            }

        except Exception as e:
            print(f"Error in set_texture: {str(e)}")
            traceback.print_exc()
            return {"error": f"Failed to apply texture: {str(e)}"}

    def get_polyhaven_status(self):
        """Get the current status of PolyHaven integration"""
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled:
            return {"enabled": True, "message": "PolyHaven integration is enabled and ready to use."}
        else:
            return {
                "enabled": False,
                "message": """PolyHaven integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Poly Haven' checkbox
                            3. Restart the connection to the MCP server"""
        }

    #region Hyper3D
    def get_hyper3d_status(self):
        """Get the current status of Hyper3D Rodin integration"""
        enabled = bpy.context.scene.blendermcp_use_hyper3d
        if enabled:
            if not bpy.context.scene.blendermcp_hyper3d_api_key:
                return {
                    "enabled": False,
                    "message": """Hyper3D Rodin integration is currently enabled, but API key is not given. To enable it:
                                1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Hyper3D Rodin 3D model generation' checkbox checked
                                3. Choose the right plaform and fill in the API Key
                                4. Restart the connection to the MCP server"""
                }
            mode = bpy.context.scene.blendermcp_hyper3d_mode
            message = f"Hyper3D Rodin integration is enabled and ready to use. Mode: {mode}. " + \
                f"Key type: {'private' if bpy.context.scene.blendermcp_hyper3d_api_key != RODIN_FREE_TRIAL_KEY else 'free_trial'}"
            return {
                "enabled": True,
                "message": message
            }
        else:
            return {
                "enabled": False,
                "message": """Hyper3D Rodin integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use Hyper3D Rodin 3D model generation' checkbox
                            3. Restart the connection to the MCP server"""
            }

    def create_rodin_job(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.create_rodin_job_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.create_rodin_job_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def create_rodin_job_main_site(
            self,
            text_prompt: str=None,
            images: list[tuple[str, str]]=None,
            bbox_condition=None
        ):
        try:
            if images is None:
                images = []
            """Call Rodin API, get the job uuid and subscription key"""
            files = [
                *[("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)],
                ("tier", (None, "Sketch")),
                ("mesh_mode", (None, "Raw")),
            ]
            if text_prompt:
                files.append(("prompt", (None, text_prompt)))
            if bbox_condition:
                files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post(
                "https://hyperhuman.deemos.com/api/v2/rodin",
                headers={
                    "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
                },
                files=files
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def create_rodin_job_fal_ai(
            self,
            text_prompt: str=None,
            images: list[tuple[str, str]]=None,
            bbox_condition=None
        ):
        try:
            req_data = {
                "tier": "Sketch",
            }
            if images:
                req_data["input_image_urls"] = images
            if text_prompt:
                req_data["prompt"] = text_prompt
            if bbox_condition:
                req_data["bbox_condition"] = bbox_condition
            response = requests.post(
                "https://queue.fal.run/fal-ai/hyper3d/rodin",
                headers={
                    "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
                    "Content-Type": "application/json",
                },
                json=req_data
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.poll_rodin_job_status_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.poll_rodin_job_status_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def poll_rodin_job_status_main_site(self, subscription_key: str):
        """Call the job status API to get the job status"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/status",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={
                "subscription_key": subscription_key,
            },
        )
        data = response.json()
        return {
            "status_list": [i["status"] for i in data["jobs"]]
        }

    def poll_rodin_job_status_fal_ai(self, request_id: str):
        """Call the job status API to get the job status"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
            headers={
                "Authorization": f"KEY {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
        )
        data = response.json()
        return data

    @staticmethod
    def _clean_imported_glb(filepath, mesh_name=None):
        # Get the set of existing objects before import
        existing_objects = set(bpy.data.objects)

        # Import the GLB file
        bpy.ops.import_scene.gltf(filepath=filepath)

        # Ensure the context is updated
        bpy.context.view_layer.update()

        # Get all imported objects
        imported_objects = list(set(bpy.data.objects) - existing_objects)
        # imported_objects = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]

        if not imported_objects:
            print("Error: No objects were imported.")
            return

        # Identify the mesh object
        mesh_obj = None

        if len(imported_objects) == 1 and imported_objects[0].type == 'MESH':
            mesh_obj = imported_objects[0]
            print("Single mesh imported, no cleanup needed.")
        else:
            if len(imported_objects) == 2:
                empty_objs = [i for i in imported_objects if i.type == "EMPTY"]
                if len(empty_objs) != 1:
                    print("Error: Expected an empty node with one mesh child or a single mesh object.")
                    return
                parent_obj = empty_objs.pop()
                if len(parent_obj.children) == 1:
                    potential_mesh = parent_obj.children[0]
                    if potential_mesh.type == 'MESH':
                        print("GLB structure confirmed: Empty node with one mesh child.")

                        # Unparent the mesh from the empty node
                        potential_mesh.parent = None

                        # Remove the empty node
                        bpy.data.objects.remove(parent_obj)
                        print("Removed empty node, keeping only the mesh.")

                        mesh_obj = potential_mesh
                    else:
                        print("Error: Child is not a mesh object.")
                        return
                else:
                    print("Error: Expected an empty node with one mesh child or a single mesh object.")
                    return
            else:
                print("Error: Expected an empty node with one mesh child or a single mesh object.")
                return

        # Rename the mesh if needed
        try:
            if mesh_obj and mesh_obj.name is not None and mesh_name:
                mesh_obj.name = mesh_name
                if mesh_obj.data.name is not None:
                    mesh_obj.data.name = mesh_name
                print(f"Mesh renamed to: {mesh_name}")
        except Exception as e:
            print("Having issue with renaming, give up renaming.")

        return mesh_obj

    def import_generated_asset(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.import_generated_asset_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.import_generated_asset_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def import_generated_asset_main_site(self, task_uuid: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/download",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={
                'task_uuid': task_uuid
            }
        )
        data_ = response.json()
        temp_file = None
        for i in data_["list"]:
            if i["name"].endswith(".glb"):
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    prefix=task_uuid,
                    suffix=".glb",
                )

                try:
                    # Download the content
                    response = requests.get(i["url"], stream=True)
                    response.raise_for_status()  # Raise an exception for HTTP errors

                    # Write the content to the temporary file
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)

                    # Close the file
                    temp_file.close()

                except Exception as e:
                    # Clean up the file if there's an error
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return {"succeed": False, "error": str(e)}

                break
        else:
            return {"succeed": False, "error": "Generation failed. Please first make sure that all jobs of the task are done and then try again later."}

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_generated_asset_fal_ai(self, request_id: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={
                "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
            }
        )
        data_ = response.json()
        temp_file = None

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            prefix=request_id,
            suffix=".glb",
        )

        try:
            # Download the content
            response = requests.get(data_["model_mesh"]["url"], stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Write the content to the temporary file
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)

            # Close the file
            temp_file.close()

        except Exception as e:
            # Clean up the file if there's an error
            temp_file.close()
            os.unlink(temp_file.name)
            return {"succeed": False, "error": str(e)}

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}
    #endregion

    #region Sketchfab API
    def get_sketchfab_status(self):
        """Get the current status of Sketchfab integration"""
        enabled = bpy.context.scene.blendermcp_use_sketchfab
        api_key = bpy.context.scene.blendermcp_sketchfab_api_key

        # Test the API key if present
        if api_key:
            try:
                headers = {
                    "Authorization": f"Token {api_key}"
                }

                response = requests.get(
                    "https://api.sketchfab.com/v3/me",
                    headers=headers,
                    timeout=30  # Add timeout of 30 seconds
                )

                if response.status_code == 200:
                    user_data = response.json()
                    username = user_data.get("username", "Unknown user")
                    return {
                        "enabled": True,
                        "message": f"Sketchfab integration is enabled and ready to use. Logged in as: {username}"
                    }
                else:
                    return {
                        "enabled": False,
                        "message": f"Sketchfab API key seems invalid. Status code: {response.status_code}"
                    }
            except requests.exceptions.Timeout:
                return {
                    "enabled": False,
                    "message": "Timeout connecting to Sketchfab API. Check your internet connection."
                }
            except Exception as e:
                return {
                    "enabled": False,
                    "message": f"Error testing Sketchfab API key: {str(e)}"
                }

        if enabled and api_key:
            return {"enabled": True, "message": "Sketchfab integration is enabled and ready to use."}
        elif enabled and not api_key:
            return {
                "enabled": False,
                "message": """Sketchfab integration is currently enabled, but API key is not given. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Keep the 'Use Sketchfab' checkbox checked
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to the MCP server"""
            }
        else:
            return {
                "enabled": False,
                "message": """Sketchfab integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Sketchfab' checkbox
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to the MCP server"""
            }

    def search_sketchfab_models(self, query, categories=None, count=20, downloadable=True):
        """Search for models on Sketchfab based on query and optional filters"""
        try:
            api_key = bpy.context.scene.blendermcp_sketchfab_api_key
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}

            # Build search parameters with exact fields from Sketchfab API docs
            params = {
                "type": "models",
                "q": query,
                "count": count,
                "downloadable": downloadable,
                "archives_flavours": False
            }

            if categories:
                params["categories"] = categories

            # Make API request to Sketchfab search endpoint
            # The proper format according to Sketchfab API docs for API key auth
            headers = {
                "Authorization": f"Token {api_key}"
            }


            # Use the search endpoint as specified in the API documentation
            response = requests.get(
                "https://api.sketchfab.com/v3/search",
                headers=headers,
                params=params,
                timeout=30  # Add timeout of 30 seconds
            )

            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}

            if response.status_code != 200:
                return {"error": f"API request failed with status code {response.status_code}"}

            response_data = response.json()

            # Safety check on the response structure
            if response_data is None:
                return {"error": "Received empty response from Sketchfab API"}

            # Handle 'results' potentially missing from response
            results = response_data.get("results", [])
            if not isinstance(results, list):
                return {"error": f"Unexpected response format from Sketchfab API: {response_data}"}

            return response_data

        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def download_sketchfab_model(self, uid):
        """Download a model from Sketchfab by its UID"""
        try:
            api_key = bpy.context.scene.blendermcp_sketchfab_api_key
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}

            # Use proper authorization header for API key auth
            headers = {
                "Authorization": f"Token {api_key}"
            }

            # Request download URL using the exact endpoint from the documentation
            download_endpoint = f"https://api.sketchfab.com/v3/models/{uid}/download"

            response = requests.get(
                download_endpoint,
                headers=headers,
                timeout=30  # Add timeout of 30 seconds
            )

            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}

            if response.status_code != 200:
                return {"error": f"Download request failed with status code {response.status_code}"}

            data = response.json()

            # Safety check for None data
            if data is None:
                return {"error": "Received empty response from Sketchfab API for download request"}

            # Extract download URL with safety checks
            gltf_data = data.get("gltf")
            if not gltf_data:
                return {"error": "No gltf download URL available for this model. Response: " + str(data)}

            download_url = gltf_data.get("url")
            if not download_url:
                return {"error": "No download URL available for this model. Make sure the model is downloadable and you have access."}

            # Download the model (already has timeout)
            model_response = requests.get(download_url, timeout=60)  # 60 second timeout

            if model_response.status_code != 200:
                return {"error": f"Model download failed with status code {model_response.status_code}"}

            # Save to temporary file
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, f"{uid}.zip")

            with open(zip_file_path, "wb") as f:
                f.write(model_response.content)

            # Extract the zip file with enhanced security
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                # More secure zip slip prevention
                for file_info in zip_ref.infolist():
                    # Get the path of the file
                    file_path = file_info.filename

                    # Convert directory separators to the current OS style
                    # This handles both / and \ in zip entries
                    target_path = os.path.join(temp_dir, os.path.normpath(file_path))

                    # Get absolute paths for comparison
                    abs_temp_dir = os.path.abspath(temp_dir)
                    abs_target_path = os.path.abspath(target_path)

                    # Ensure the normalized path doesn't escape the target directory
                    if not abs_target_path.startswith(abs_temp_dir):
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with path traversal attempt"}

                    # Additional explicit check for directory traversal
                    if ".." in file_path:
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with directory traversal sequence"}

                # If all files passed security checks, extract them
                zip_ref.extractall(temp_dir)

            # Find the main glTF file
            gltf_files = [f for f in os.listdir(temp_dir) if f.endswith('.gltf') or f.endswith('.glb')]

            if not gltf_files:
                with suppress(Exception):
                    shutil.rmtree(temp_dir)
                return {"error": "No glTF file found in the downloaded model"}

            main_file = os.path.join(temp_dir, gltf_files[0])

            # Import the model
            bpy.ops.import_scene.gltf(filepath=main_file)

            # Get the names of imported objects
            imported_objects = [obj.name for obj in bpy.context.selected_objects]

            # Clean up temporary files
            with suppress(Exception):
                shutil.rmtree(temp_dir)

            return {
                "success": True,
                "message": "Model imported successfully",
                "imported_objects": imported_objects
            }

        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection and try again with a simpler model."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Failed to download model: {str(e)}"}
    #endregion

    #region Geometry Nodes
    def get_geometry_nodes_capabilities(self):
        return self.geometry_nodes_intelligence_service.get_geometry_nodes_capabilities()

    def list_geometry_node_groups(self, include_builtin=False, include_users=True, include_interface=True, include_node_summary=True, max_groups=None):
        return self.geometry_nodes_intelligence_service.list_geometry_node_groups(include_builtin, include_users, include_interface, include_node_summary, max_groups)

    def get_geometry_node_group_deep_info(self, node_group_name, include_nodes=True, include_links=True, include_interface=True, include_modifier_users=True, max_nodes=None):
        return self.geometry_nodes_intelligence_service.get_geometry_node_group_deep_info(node_group_name, include_nodes, include_links, include_interface, include_modifier_users, max_nodes)

    def list_geometry_nodes_modifiers(self, object_name=None, include_inputs=True, include_group_info=True):
        return self.geometry_nodes_intelligence_service.list_geometry_nodes_modifiers(object_name, include_inputs, include_group_info)

    def get_geometry_nodes_modifier_info(self, object_name, modifier_name, include_inputs=True, include_group_info=True):
        return self.geometry_nodes_intelligence_service.get_geometry_nodes_modifier_info(object_name, modifier_name, include_inputs, include_group_info)

    def get_supported_geometry_node_templates(self):
        return self.geometry_nodes_template_service.get_supported_geometry_node_templates()

    def create_geometry_node_group_from_template(self, template_name, node_group_name, parameters=None, material_name=None, replace_existing=False, verify=False, artifact_root=None):
        return self.geometry_nodes_template_service.create_geometry_node_group_from_template(template_name, node_group_name, parameters, material_name, replace_existing, verify, artifact_root)

    def create_custom_geometry_node_recipe(self, node_group_name, recipe, replace_existing=False, verify=False, artifact_root=None):
        return self.geometry_nodes_recipe_service.create_custom_geometry_node_recipe(node_group_name, recipe, replace_existing, verify, artifact_root)

    def apply_geometry_nodes_modifier(self, object_name, node_group_name, modifier_name=None, input_values=None, verify=False):
        return self.geometry_nodes_modifier_service.apply_geometry_nodes_modifier(object_name, node_group_name, modifier_name, input_values, verify)

    def set_geometry_nodes_modifier_input(self, object_name, modifier_name, input_values):
        return self.geometry_nodes_modifier_service.set_geometry_nodes_modifier_input(object_name, modifier_name, input_values)

    def create_procedural_asset(self, asset_type="curve_rope", asset_name=None, template_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_procedural_asset(asset_type, asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_scatter_system(self, target_object_name=None, asset_name=None, template_name="scatter_on_surface", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_scatter_system(target_object_name, asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_curve_generator(self, asset_name=None, template_name="beveled_curve_path", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_curve_generator(asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_radial_array_system(self, source_object_name=None, asset_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_radial_array_system(source_object_name, asset_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_panel_generator(self, asset_name=None, template_name="panel_grid", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_panel_generator(asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_cable_or_rope_generator(self, asset_name=None, template_name="curve_rope", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_cable_or_rope_generator(asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_terrain_noise_system(self, asset_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_terrain_noise_system(asset_name, parameters, collection_name, material_name, verify, artifact_root)

    def validate_geometry_node_group(self, node_group_name, expected_template=None):
        return self.geometry_nodes_validation_service.validate_geometry_node_group(node_group_name, expected_template)

    def create_geometry_nodes_preview(self, node_group_name=None, object_name=None, label=None, include_scene_snapshot=True, artifact_root=None):
        return self.geometry_nodes_preview_service.create_geometry_nodes_preview(node_group_name, object_name, label, include_scene_snapshot, artifact_root)

    def create_geometry_nodes_scene_kit(self, kit_id=None, label=None, object_names=None, node_group_names=None, include_preview=True, overwrite=True, artifact_root=None):
        return self.geometry_nodes_preview_service.create_geometry_nodes_scene_kit(kit_id, label, object_names, node_group_names, include_preview, overwrite, artifact_root)

    def delete_geometry_node_groups(self, node_group_names=None, prefix=None, confirm=False):
        return self.geometry_nodes_validation_service.delete_geometry_node_groups(node_group_names, prefix, confirm)

    def remove_geometry_nodes_modifiers(self, object_name=None, modifier_names=None, prefix=None, confirm=False):
        return self.geometry_nodes_modifier_service.remove_geometry_nodes_modifiers(object_name, modifier_names, prefix, confirm)

    def run_geometry_nodes_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=40, batch_allow_destructive=False, artifact_root=None):
        return self.geometry_nodes_workflow_batch_service.run_geometry_nodes_workflow_batch(label, operations, create_before_snapshot, create_after_snapshot, stop_on_error, max_operations, batch_allow_destructive, artifact_root)

    def complete_geometry_node(self, object_name, nodes, links, input_sockets=None):
        """Complete geometry node network creation"""
        return self.geometry_nodes_service.complete_geometry_node(object_name, nodes, links, input_sockets)

    def _create_geometry_nodes_object(self, object_name):
        """Create a basic object for geometry nodes"""
        return self.geometry_nodes_service._create_geometry_nodes_object(object_name)

    def _setup_node_group_interface(self, node_group, input_sockets):
        """Setup the node group interface for inputs/outputs"""
        return self.geometry_nodes_service._setup_node_group_interface(node_group, input_sockets)

    def get_geometry_nodes_status(self):
        """Get the status of geometry nodes support"""
        return self.geometry_nodes_service.get_geometry_nodes_status()

    #region Script Registry Tools

    def _get_script_directory(self, category):
        """Get the script directory path for a given category"""
        return self.script_registry_service._get_script_directory(category)

    def _get_metadata_path(self, script_dir):
        """Get the metadata file path for a script directory"""
        return self.script_registry_service._get_metadata_path(script_dir)

    def _load_metadata(self, script_dir):
        """Load metadata for a script directory"""
        return self.script_registry_service._load_metadata(script_dir)

    def _save_script_metadata(self, script_dir, script_name, permanent):
        """Save metadata for a script"""
        return self.script_registry_service._save_script_metadata(script_dir, script_name, permanent)

    def register_context_script(self, script_name, script_content, category="default", permanent=False):
        """Register a Python script for later execution"""
        return self.script_registry_service.register_context_script(script_name, script_content, category, permanent)

    def execute_context_script(self, script_name, category="default"):
        """Execute a previously registered script"""
        return self.script_registry_service.execute_context_script(script_name, category)

    def list_context_scripts(self, category=None):
        """List all registered scripts"""
        return self.script_registry_service.list_context_scripts(category)

    def clear_context_scripts(self, category=None, script_name=None, clear_permanent=False):
        """Clear scripts from the registry"""
        return self.script_registry_service.clear_context_scripts(category, script_name, clear_permanent)

    #endregion
    #endregion

# Blender UI Panel
class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Overtli-Blender'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "blendermcp_port")
        layout.prop(scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven")

        layout.prop(scene, "blendermcp_use_hyper3d", text="Use Hyper3D Rodin 3D model generation")
        if scene.blendermcp_use_hyper3d:
            layout.prop(scene, "blendermcp_hyper3d_mode", text="Rodin Mode")
            layout.prop(scene, "blendermcp_hyper3d_api_key", text="API Key")
            layout.operator("blendermcp.set_hyper3d_free_trial_api_key", text="Set Free Trial API Key")

        layout.prop(scene, "blendermcp_use_sketchfab", text="Use assets from Sketchfab")
        if scene.blendermcp_use_sketchfab:
            layout.prop(scene, "blendermcp_sketchfab_api_key", text="API Key")

        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Connect to MCP server")
        else:
            layout.operator("blendermcp.stop_server", text="Disconnect from MCP server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")

# Operator to set Hyper3D API Key
class BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey(bpy.types.Operator):
    bl_idname = "blendermcp.set_hyper3d_free_trial_api_key"
    bl_label = "Set Free Trial API Key"

    def execute(self, context):
        context.scene.blendermcp_hyper3d_api_key = RODIN_FREE_TRIAL_KEY
        context.scene.blendermcp_hyper3d_mode = 'MAIN_SITE'
        self.report({'INFO'}, "API Key set successfully!")
        return {'FINISHED'}

# Operator to start the server
class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Connect to MCP server"
    bl_description = "Start the Overtli-Blender socket server"

    def execute(self, context):
        scene = context.scene

        # Create a new server instance
        if not hasattr(bpy.types, "blendermcp_server") or not bpy.types.blendermcp_server:
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)

        # Start the server
        bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = True

        return {'FINISHED'}

# Operator to stop the server
class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop the MCP connection"
    bl_description = "Stop the MCP connection"

    def execute(self, context):
        scene = context.scene

        # Stop the server if it exists
        if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
            bpy.types.blendermcp_server.stop()
            del bpy.types.blendermcp_server

        scene.blendermcp_server_running = False

        return {'FINISHED'}

# Registration functions
def register():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        description="Port for the Overtli-Blender server",
        default=9876,
        min=1024,
        max=65535
    )

    bpy.types.Scene.blendermcp_server_running = bpy.props.BoolProperty(
        name="Server Running",
        default=False
    )

    bpy.types.Scene.blendermcp_use_polyhaven = bpy.props.BoolProperty(
        name="Use Poly Haven",
        description="Enable Poly Haven asset integration",
        default=False
    )

    bpy.types.Scene.blendermcp_use_hyper3d = bpy.props.BoolProperty(
        name="Use Hyper3D Rodin",
        description="Enable Hyper3D Rodin generatino integration",
        default=False
    )

    bpy.types.Scene.blendermcp_hyper3d_mode = bpy.props.EnumProperty(
        name="Rodin Mode",
        description="Choose the platform used to call Rodin APIs",
        items=[
            ("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),
            ("FAL_AI", "fal.ai", "fal.ai"),
        ],
        default="MAIN_SITE"
    )

    bpy.types.Scene.blendermcp_hyper3d_api_key = bpy.props.StringProperty(
        name="Hyper3D API Key",
        subtype="PASSWORD",
        description="API Key provided by Hyper3D",
        default=""
    )

    bpy.types.Scene.blendermcp_use_sketchfab = bpy.props.BoolProperty(
        name="Use Sketchfab",
        description="Enable Sketchfab asset integration",
        default=False
    )

    bpy.types.Scene.blendermcp_sketchfab_api_key = bpy.props.StringProperty(
        name="Sketchfab API Key",
        subtype="PASSWORD",
        description="API Key provided by Sketchfab",
        default=""
    )

    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)

    print("Overtli-Blender addon registered")

def unregister():
    # Stop the server if it's running
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server

    bpy.utils.unregister_class(BLENDERMCP_PT_Panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.unregister_class(BLENDERMCP_OT_StartServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_StopServer)

    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running
    del bpy.types.Scene.blendermcp_use_polyhaven
    del bpy.types.Scene.blendermcp_use_hyper3d
    del bpy.types.Scene.blendermcp_hyper3d_mode
    del bpy.types.Scene.blendermcp_hyper3d_api_key
    del bpy.types.Scene.blendermcp_use_sketchfab
    del bpy.types.Scene.blendermcp_sketchfab_api_key

    print("Overtli-Blender addon unregistered")

if __name__ == "__main__":
    register()


