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
try:
    import requests
except ModuleNotFoundError:
    class _MissingRequestsTimeout(Exception):
        pass

    class _MissingRequestsExceptions:
        Timeout = _MissingRequestsTimeout

    class _MissingRequestsUtils:
        @staticmethod
        def default_headers():
            return {}

    class _MissingRequests:
        exceptions = _MissingRequestsExceptions()
        utils = _MissingRequestsUtils()

        @staticmethod
        def get(*args, **kwargs):
            raise RuntimeError("Optional dependency 'requests' is not available in Blender Python; network provider tools are unavailable.")

        @staticmethod
        def post(*args, **kwargs):
            raise RuntimeError("Optional dependency 'requests' is not available in Blender Python; network provider tools are unavailable.")

    requests = _MissingRequests()
import tempfile
import traceback
import importlib
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
from pathlib import Path
from typing import List, Dict, Union, Any, Optional, Tuple

ADDON_ROOT = os.path.dirname(os.path.abspath(__file__))
PACKAGE_PARENT = os.path.dirname(ADDON_ROOT)
SHARED_RUNTIME_ROOT = os.path.join(ADDON_ROOT, "_shared_runtime")
if ADDON_ROOT not in sys.path:
    sys.path.insert(0, ADDON_ROOT)
for candidate in (
    os.path.join(PACKAGE_PARENT, "src"),
    os.path.join(ADDON_ROOT, "src"),
    SHARED_RUNTIME_ROOT,
):
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)

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
    from overtli_blender.runtime.bake_planning import classify_bake_pass as runtime_classify_bake_pass
    from overtli_blender.runtime.bake_planning import estimate_bake_cost as runtime_estimate_bake_cost
    from overtli_blender.runtime.bake_planning import normalize_bake_pass_name as runtime_normalize_bake_pass_name
    from overtli_blender.runtime.bake_planning import normalize_resolution as runtime_normalize_bake_resolution
    from overtli_blender.runtime.bake_planning import plan_bake_outputs as runtime_plan_bake_outputs
    from overtli_blender.runtime.channel_packing import get_channel_layout as runtime_get_channel_layout
    from overtli_blender.runtime.channel_packing import validate_channel_pack_inputs as runtime_validate_channel_pack_inputs
    from overtli_blender.runtime.image_resources import color_space_intent_for_pass as runtime_color_space_intent_for_pass
    from overtli_blender.runtime.image_resources import file_sha256 as runtime_file_sha256
    from overtli_blender.runtime.image_resources import safe_image_filename as runtime_safe_image_filename
    from overtli_blender.runtime.image_resources import write_image_manifest as runtime_write_image_manifest
    from overtli_blender.runtime.mesh_validation import validate_mesh_schema as runtime_validate_mesh_schema
    from overtli_blender.runtime.modeling_plan import plan_modifier_stack as runtime_plan_modifier_stack
    from overtli_blender.runtime.modeling_plan import plan_reference_construction as runtime_plan_reference_construction
    from overtli_blender.runtime.modeling_plan import select_modeling_method as runtime_select_modeling_method
    from overtli_blender.runtime.construction_manifest import new_workflow_id as runtime_new_workflow_id
    from overtli_blender.runtime.project_workspace import initialize_workspace as runtime_initialize_workspace
    from overtli_blender.runtime.project_workspace import initialize_temp_workspace as runtime_initialize_temp_workspace
    from overtli_blender.runtime.project_workspace import copy_project_folder as runtime_copy_project_folder
    from overtli_blender.runtime.project_workspace import detect_drive_roots as runtime_detect_drive_roots
    from overtli_blender.runtime.project_workspace import get_loaded_project_folder as runtime_get_loaded_project_folder
    from overtli_blender.runtime.project_workspace import plan_project_folder_move as runtime_plan_project_folder_move
    from overtli_blender.runtime.project_workspace import repair_workspace_layout as runtime_repair_workspace_layout
    from overtli_blender.runtime.project_workspace import resolve_artifact_workspace as runtime_resolve_artifact_workspace
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
    from overtli_blender.runtime.addon_interop import plan_operator_invocation as runtime_plan_operator_invocation
    from overtli_blender.runtime.addon_interop import scan_addon_sources as runtime_scan_addon_sources
    from overtli_blender.runtime.error_catalog import explain_error as runtime_explain_error
    from overtli_blender.runtime.error_catalog import get_error_catalog as runtime_get_error_catalog
    from overtli_blender.runtime.error_catalog import get_remediation_steps as runtime_get_remediation_steps
    from overtli_blender.runtime.onboarding import run_setup_checks as runtime_run_setup_checks
    from overtli_blender.runtime.preferences_schema import config_path as runtime_preferences_config_path
    from overtli_blender.runtime.preferences_schema import deep_update as runtime_preferences_deep_update
    from overtli_blender.runtime.preferences_schema import default_preferences as runtime_default_preferences
    from overtli_blender.runtime.preferences_schema import load_preferences as runtime_load_preferences
    from overtli_blender.runtime.preferences_schema import permission_expands as runtime_permission_expands
    from overtli_blender.runtime.preferences_schema import preferences_schema as runtime_preferences_schema
    from overtli_blender.runtime.preferences_schema import redact_sensitive_values as runtime_redact_sensitive_values
    from overtli_blender.runtime.preferences_schema import save_preferences as runtime_save_preferences
    from overtli_blender.runtime.preferences_schema import validate_preferences as runtime_validate_preferences
    from overtli_blender.runtime.skill_pack_library import BUNDLED_SKILL_PACKS as RUNTIME_BUNDLED_SKILL_PACKS
    from overtli_blender.runtime.skill_pack_library import get_bundled_skill_pack as runtime_get_bundled_skill_pack
    from overtli_blender.runtime.skill_pack_library import list_bundled_skill_packs as runtime_list_bundled_skill_packs
    from overtli_blender.runtime.skill_pack_library import recommend_skill_packs as runtime_recommend_skill_packs
    from overtli_blender.runtime.skill_pack_library import search_bundled_skill_packs as runtime_search_bundled_skill_packs
    from overtli_blender.runtime.tool_profiles import BUILTIN_TOOL_PROFILES as RUNTIME_BUILTIN_TOOL_PROFILES
    from overtli_blender.runtime.tool_profiles import get_profile as runtime_get_tool_profile
    from overtli_blender.runtime.tool_profiles import list_tool_profiles as runtime_list_tool_profiles
    from overtli_blender.runtime.tool_profiles import preview_profile_change as runtime_preview_profile_change
    from overtli_blender.runtime.tool_profiles import recommend_profile as runtime_recommend_tool_profile
    from overtli_blender.runtime.ux_status import approval_queue_summary as runtime_approval_queue_summary
    from overtli_blender.runtime.ux_status import recent_operation_summary as runtime_recent_operation_summary
    from overtli_blender.runtime.ux_status import runtime_dashboard as runtime_build_dashboard

    def command_registry_report():
        module = importlib.import_module("overtli_blender.runtime.command_registry")
        return module.command_registry_report()

    def get_command_spec(name):
        module = importlib.import_module("overtli_blender.runtime.command_registry")
        return module.get_command_spec(name)

    def runtime_discover_tool_packs():
        module = importlib.import_module("overtli_blender.runtime.tool_packs")
        return module.discover_tool_packs()

    def runtime_get_tool_pack(name):
        module = importlib.import_module("overtli_blender.runtime.tool_packs")
        return module.get_tool_pack(name)

    def runtime_search_tools(query, category=None, tool_pack=None, risk_max=None, limit=20):
        module = importlib.import_module("overtli_blender.runtime.tool_packs")
        return module.search_tools(query, category=category, tool_pack=tool_pack, risk_max=risk_max, limit=limit)

    def runtime_get_tool_spec(name):
        module = importlib.import_module("overtli_blender.runtime.tool_packs")
        return module.get_tool_spec(name)

    def runtime_get_recommended_tools_for_task(task, limit=8):
        module = importlib.import_module("overtli_blender.runtime.tool_packs")
        return module.get_recommended_tools_for_task(task, limit=limit)
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
            "approve_and_execute_operation",
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
                "params": params or {},
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

        def get_approval_record(self, approval_id):
            record = self.records.get(approval_id)
            if not record:
                return {"status": "error", "message": f"Unknown approval: {approval_id}"}
            return {"status": "success", "approval": record}

        def approve_operation(self, approval_id, execute_after_approval=True, approve_only=False):
            record = self.records.get(approval_id)
            if not record:
                return {"status": "error", "message": f"Unknown approval: {approval_id}"}
            record["status"] = "approved"
            return {"status": "success", "approval": record}

        def approve_and_validate_operation(self, approval_id, expected_command_name=None, expected_params_hash=None):
            record = self.records.get(approval_id)
            if not record:
                return {"status": "error", "message": f"Unknown approval: {approval_id}"}
            if record.get("status") in {"denied", "expired", "executed"}:
                return {"status": "error", "message": f"Approval is {record.get('status')}", "approval": record}
            if expected_command_name and record.get("command_name") != expected_command_name:
                return {"status": "error", "message": "Approval command changed", "approval": record}
            if expected_params_hash and record.get("params_hash") != expected_params_hash:
                return {"status": "error", "message": "Approval parameters changed", "approval": record}
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

        def execute_approved_operation(self, approval_id, command_name=None, params=None):
            record = self.records.get(approval_id)
            if not record:
                return {"status": "error", "message": f"Unknown approval: {approval_id}"}
            command_name = command_name or record.get("command_name")
            params = params if params is not None else record.get("params", {})
            if record.get("status") != "approved":
                return {"status": "error", "message": f"Approval is {record.get('status')}", "approval": record}
            if record.get("command_name") != command_name or record.get("params_hash") != canonical_params_hash(command_name, params):
                return {"status": "error", "message": "Approval parameters changed", "approval": record}
            record["status"] = "executed"
            return {"status": "success", "approval": record}

        def validate_approved_operation(self, approval_id, command_name, params=None):
            record = self.records.get(approval_id)
            if not record:
                return {"status": "error", "message": f"Unknown approval: {approval_id}"}
            if record.get("status") != "approved":
                return {"status": "error", "message": f"Approval is {record.get('status')}", "approval": record}
            if record.get("command_name") != command_name or record.get("params_hash") != canonical_params_hash(command_name, params):
                return {"status": "error", "message": "Approval parameters changed", "approval": record}
            return {"status": "success", "approval": record}

        def mark_executed(self, approval_id):
            record = self.records.get(approval_id)
            if not record:
                return {"status": "error", "message": f"Unknown approval: {approval_id}"}
            record["status"] = "executed"
            return {"status": "success", "approval": record}

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
        "blend", "screenshots", "verification", "logs", "tasks", "manifests",
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

    def runtime_initialize_temp_workspace(session_id=None, project_name=None):
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("TMP") or os.environ.get("TEMP") or os.path.expanduser("~")
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(session_id or f"session_{int(time.time())}")).strip("._-") or "session"
        root = _phase7c_canonical_path(Path(base) / "Overtli-Blender" / "temp_workspaces" / safe)
        result = runtime_repair_workspace_layout(root, project_name=project_name or root.name)
        result["temporary"] = True
        result["session_id"] = root.name
        result["warnings"] = ["Unsaved .blend artifacts are stored in a user-local Overtli-Blender temp workspace, not the addon installation folder."]
        return result

    def runtime_resolve_artifact_workspace(blend_filepath=None, preferred_root=None, session_id=None, create_if_missing=True):
        resolved = runtime_resolve_workspace(blend_filepath, preferred_root=preferred_root, allow_repo_fallback=False)
        workspace = resolved.get("workspace", {})
        if workspace.get("resolved"):
            if create_if_missing:
                runtime_repair_workspace_layout(workspace["project_root"], blend_filepath=blend_filepath)
            return {**resolved, "temporary": False}
        temp = runtime_initialize_temp_workspace(session_id=session_id) if create_if_missing else {"workspace": {"resolved": True, "project_root": str(_phase7c_canonical_path(Path(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")) / "Overtli-Blender" / "temp_workspaces" / str(session_id or "session"))), "source": "temporary"}}
        return {"status": "success", "workspace": temp["workspace"], "temporary": True, "unsaved_blend": True, "warnings": ["Unsaved .blend has no trusted project root; using dedicated temp workspace."]}

    def runtime_validate_layout(project_root):
        root = _phase7c_canonical_path(project_root)
        missing = [folder for folder in _PHASE7C_STANDARD_FOLDERS if not (root / folder).exists()]
        return {"status": "success" if not missing else "warning", "project_root": str(root), "missing": missing, "standard_folders": list(_PHASE7C_STANDARD_FOLDERS)}

    def runtime_repair_workspace_layout(project_root, project_name=None, blend_filepath=None):
        root = _phase7c_canonical_path(project_root)
        created = []
        for folder in _PHASE7C_STANDARD_FOLDERS:
            path = root / folder
            if not path.exists():
                created.append(folder)
            path.mkdir(parents=True, exist_ok=True)
        manifest = root / ".overtli" / "project.json"
        payload = {"project_name": project_name or root.name, "project_root": str(root), "standard_folders": list(_PHASE7C_STANDARD_FOLDERS)}
        if blend_filepath:
            payload["active_blend_file"] = str(_phase7c_canonical_path(blend_filepath))
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return {"status": "success", "workspace": {"resolved": True, "project_root": str(root), "workspace_dir": str(root / ".overtli"), "manifest_path": str(manifest), "source": "explicit"}, "created_folders": created, "manifest": payload}

    def runtime_get_loaded_project_folder(blend_filepath=None, preferred_root=None):
        resolved = runtime_resolve_workspace(blend_filepath, preferred_root=preferred_root, allow_repo_fallback=False)
        workspace = resolved.get("workspace", {})
        if not workspace.get("resolved"):
            return {**resolved, "project_folder": None, "layout": None}
        return {"status": "success", "blend_filepath": blend_filepath, "project_folder": workspace["project_root"], "workspace": workspace, "layout": runtime_validate_layout(workspace["project_root"])}

    def runtime_detect_drive_roots(preferred=("C", "D")):
        roots = []
        if os.name == "nt":
            for drive in preferred:
                letter = str(drive).rstrip(":\\/").upper()
                root = Path(f"{letter}:\\")
                if root.exists():
                    roots.append(str(root))
        else:
            roots.append(str(Path("/")))
        return {"status": "success", "drive_roots": sorted(set(roots)), "platform": os.name}

    def runtime_plan_project_folder_move(source_project_root, destination_root, new_project_name=None, blend_filepath=None, copy_mode="copy"):
        source = _phase7c_canonical_path(source_project_root)
        target = _phase7c_canonical_path(Path(destination_root) / (new_project_name or source.name))
        blend = _phase7c_canonical_path(blend_filepath) if blend_filepath else None
        return {"status": "requires_approval", "source_project_root": str(source), "target_project_root": str(target), "target_blend_filepath": str(target / (blend.name if blend else f"{target.name}.blend")), "copy_mode": copy_mode, "conflicts": [{"path": str(target), "type": "directory_exists"}] if target.exists() else []}

    def runtime_copy_project_folder(source_project_root, target_project_root, overwrite=False):
        source = _phase7c_canonical_path(source_project_root)
        target = _phase7c_canonical_path(target_project_root)
        if target.exists() and any(target.iterdir()) and not overwrite:
            return {"status": "error", "message": "Target project root exists and is not empty.", "target_project_root": str(target)}
        shutil.copytree(source, target, dirs_exist_ok=True)
        return {"status": "success", "source_project_root": str(source), "target_project_root": str(target)}

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
        destructive_terms = {"delete", "clear", "reset", "purge", "cleanup", "remove"}
        destructive_intent = any(term in destructive_terms for term in terms)
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
            if destructive_intent and spec["name"].startswith("create_") and not any(term in spec["name"].lower() for term in destructive_terms):
                continue
            if destructive_intent and not (spec.get("destructive") or any(term in haystack for term in destructive_terms)):
                continue
            if not terms or any(term in haystack for term in terms):
                results.append(spec)
        warnings = ["No matching callable destructive/cleanup tool was found; unrelated mutating create tools were intentionally not returned."] if destructive_intent and not results else []
        return {"status": "success", "query": query, "results": results[: max(1, min(int(limit), 50))], "warnings": warnings}
    def runtime_get_tool_spec(name):
        spec = _fallback_command_specs().get(name)
        if not spec:
            return {"status": "error", "message": f"Unknown tool: {name}"}
        tool = dict(spec)
        if name == "run_verified_edit_batch":
            tool["accepted_operation_schema"] = {"preferred": {"command_name": "transform_object", "params": {"object_name": "Cube", "location": [0, 0, 1]}}, "legacy": {"type": "transform_object", "params": {"object_name": "Cube"}}, "prevalidation": "Set prevalidate_only=true to validate before mutation."}
        return {"status": "success", "tool": tool}
    def runtime_get_recommended_tools_for_task(task, limit=8):
        return runtime_search_tools(task, limit=limit)

    def runtime_preferences_config_path(repo_root=None, project_root=None):
        base = Path(project_root) if project_root else Path(repo_root or os.getcwd())
        if project_root:
            return base / ".overtli" / "config.json"
        return base / ".overtli_blender" / "config" / "runtime_preferences.json"

    def runtime_default_preferences():
        return {
            "schema_version": 1,
            "project": {"project_specific": True, "auto_initialize_workspace": False, "require_saved_blend_for_writes": True},
            "filesystem": {"approved_roots": [], "approved_addon_source_roots": [], "permission_profile": "standard", "allow_external_reads": False, "allow_external_writes": False},
            "security": {"strict_mode": False, "raw_python_enabled": False, "addon_interop_enabled": False, "require_approval_for_permission_expansion": True},
            "artifacts": {"cache_policy": "project_scoped", "log_retention_days": 14, "operation_timeout_seconds": 120},
            "mcp": {"host": "localhost", "port": 9876, "max_response_items": 200},
            "knowledge": {"knowledge_roots": [], "docs_index_enabled": True},
            "tool_profiles": {"active_profile": "safe_scene", "enabled_tool_packs": [], "active_skill_packs": [], "max_visible_tools": 80},
            "providers": {"network_providers_enabled": False, "provider_downloads_enabled": False},
            "diagnostics": {"log_level": "INFO", "diagnostics_enabled": True, "support_bundle_redaction": True},
        }

    def runtime_preferences_schema():
        return {
            "status": "success",
            "schema_version": 1,
            "sections": {
                "Project": ["auto_initialize_workspace", "project_specific", "require_saved_blend_for_writes"],
                "Filesystem": ["allow_external_reads", "allow_external_writes", "approved_addon_source_roots", "approved_roots", "permission_profile"],
                "Security": ["addon_interop_enabled", "raw_python_enabled", "require_approval_for_permission_expansion", "strict_mode"],
                "Artifacts": ["cache_policy", "log_retention_days", "operation_timeout_seconds"],
                "MCP": ["host", "max_response_items", "port"],
                "Knowledge": ["docs_index_enabled", "knowledge_roots"],
                "Tool Profiles": ["active_profile", "active_skill_packs", "enabled_tool_packs", "max_visible_tools"],
                "Providers": ["network_providers_enabled", "provider_downloads_enabled"],
                "Diagnostics": ["diagnostics_enabled", "log_level", "support_bundle_redaction"],
            },
            "fallback": True,
        }

    def runtime_preferences_deep_update(target, changes):
        for key, value in (changes or {}).items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                runtime_preferences_deep_update(target[key], value)
            else:
                target[key] = value
        return target

    def runtime_redact_sensitive_values(value):
        markers = ("api_key", "apikey", "token", "secret", "password", "credential")
        if isinstance(value, dict):
            return {key: "<redacted>" if any(marker in str(key).lower() for marker in markers) else runtime_redact_sensitive_values(item) for key, item in value.items()}
        if isinstance(value, list):
            return [runtime_redact_sensitive_values(item) for item in value]
        return value

    def runtime_load_preferences(path=None):
        target = Path(path) if path else runtime_preferences_config_path()
        if not target.exists():
            return runtime_default_preferences()
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            return runtime_default_preferences()
        prefs = runtime_default_preferences()
        runtime_preferences_deep_update(prefs, data)
        return prefs

    def runtime_save_preferences(preferences, path=None):
        target = Path(path) if path else runtime_preferences_config_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(runtime_redact_sensitive_values(preferences), indent=2, sort_keys=True), encoding="utf-8")
        return target

    def runtime_validate_preferences(preferences):
        errors = []
        warnings = []
        profile = preferences.get("filesystem", {}).get("permission_profile", "standard")
        if profile not in {"read_only", "standard", "trusted_project", "developer", "custom"}:
            errors.append(f"Unknown permission profile: {profile}")
        if preferences.get("security", {}).get("raw_python_enabled"):
            warnings.append("Raw Python is enabled and should remain approval-gated.")
        providers = preferences.get("providers", {})
        if providers.get("provider_downloads_enabled") and not providers.get("network_providers_enabled"):
            errors.append("Provider downloads require network providers to be enabled.")
        return {"status": "success" if not errors else "error", "valid": not errors, "errors": errors, "warnings": warnings, "fallback": True}

    def runtime_permission_expands(current, requested):
        current_fs = current.get("filesystem", {})
        requested_fs = requested.get("filesystem", {})
        if set(requested_fs.get("approved_roots", [])) - set(current_fs.get("approved_roots", [])):
            return True
        if set(requested_fs.get("approved_addon_source_roots", [])) - set(current_fs.get("approved_addon_source_roots", [])):
            return True
        rank = {"read_only": 0, "standard": 1, "trusted_project": 2, "developer": 3, "custom": 1}
        if rank.get(requested_fs.get("permission_profile", current_fs.get("permission_profile", "standard")), 1) > rank.get(current_fs.get("permission_profile", "standard"), 1):
            return True
        for section, key in [("security", "raw_python_enabled"), ("security", "addon_interop_enabled"), ("providers", "network_providers_enabled"), ("providers", "provider_downloads_enabled")]:
            if requested.get(section, {}).get(key) and not current.get(section, {}).get(key):
                return True
        return False

    @dataclass(frozen=True)
    class _FallbackToolProfile:
        name: str
        label: str
        description: str
        enabled_tool_packs: tuple[str, ...]
        max_visible_tools: int = 80
        permission_profile: str = "standard"
        hidden_risky_tools: bool = True

        def to_dict(self):
            return {
                "name": self.name,
                "label": self.label,
                "description": self.description,
                "enabled_tool_packs": list(self.enabled_tool_packs),
                "max_visible_tools": self.max_visible_tools,
                "permission_profile": self.permission_profile,
                "hidden_risky_tools": self.hidden_risky_tools,
                "fallback": True,
            }

    RUNTIME_BUILTIN_TOOL_PROFILES = {
        "safe_scene": _FallbackToolProfile("safe_scene", "Safe Scene", "Conservative scene inspection and structured edit profile.", ("core", "scene_intelligence", "verified_editing")),
        "artist": _FallbackToolProfile("artist", "Artist", "Broader artist workflow profile with approval-gated risky tools.", ("core", "scene_intelligence", "verified_editing", "materials", "asset_workflows"), 100),
        "technical_director": _FallbackToolProfile("technical_director", "Technical Director", "Advanced project and addon workflow profile.", ("core", "scene_intelligence", "verified_editing", "materials", "asset_workflows", "addon_knowledge"), 120, "developer"),
    }

    def runtime_list_tool_profiles():
        return {"status": "success", "profiles": [profile.to_dict() for profile in RUNTIME_BUILTIN_TOOL_PROFILES.values()], "fallback": True}

    def runtime_get_tool_profile(name):
        return RUNTIME_BUILTIN_TOOL_PROFILES.get(name)

    def runtime_preview_profile_change(current, requested):
        profile = runtime_get_tool_profile(requested)
        if not profile:
            return {"status": "error", "message": f"Unknown tool profile: {requested}"}
        requires_approval = profile.permission_profile == "developer" and current != requested
        return {"status": "success", "current_profile": current, "requested_profile": profile.to_dict(), "requires_approval": requires_approval, "fallback": True}

    def runtime_recommend_tool_profile(task_description, current_context=None):
        text = f"{task_description} {current_context or {}}".lower()
        if any(term in text for term in ("addon", "operator", "python", "developer", "source")):
            name = "technical_director"
        elif any(term in text for term in ("material", "texture", "bake", "uv", "pbr")):
            name = "artist"
        elif any(term in text for term in ("review", "diagnose", "inspect", "read only")):
            name = "safe_scene"
        else:
            name = "safe_scene"
        return {"status": "success", "recommended_profile": RUNTIME_BUILTIN_TOOL_PROFILES[name].to_dict(), "reason": f"Matched task terms to {name} fallback profile.", "fallback": True}

    @dataclass(frozen=True)
    class _FallbackSkillPack:
        skill_pack_id: str
        title: str
        intent_patterns: tuple[str, ...]
        tool_packs: tuple[str, ...]
        risk_level: str = "LOW"

        def to_dict(self):
            return {
                "skill_pack_id": self.skill_pack_id,
                "title": self.title,
                "intent_patterns": list(self.intent_patterns),
                "method_rules": ["inspect first", "prefer non-destructive workflow", "verify before claiming success"],
                "anti_patterns": ["blind execution", "overwriting user assets", "claiming visual success without evidence"],
                "required_inspection": ["scene summary", "selection state", "workspace status"],
                "tool_packs": list(self.tool_packs),
                "preflight": ["project initialized", "approved roots configured", "relevant tools enabled"],
                "execution_stages": ["plan", "prepare", "execute gated operations", "verify"],
                "verification_stages": ["structural check", "artifact or screenshot when applicable", "operation summary"],
                "rollback_strategy": "scene snapshot or generated artifact cleanup depending on operation",
                "blender_version_notes": "Fallback metadata active because bundled runtime package was unavailable.",
                "known_limitations": ["Does not execute workflows automatically.", "High-risk operations still require explicit approval."],
                "examples": list(self.intent_patterns),
                "risk_level": self.risk_level,
                "fallback": True,
            }

    def _fallback_skill_pack(skill_pack_id, title, intents, tool_packs, risk="LOW"):
        return _FallbackSkillPack(skill_pack_id, title, tuple(intents), tuple(tool_packs), risk)

    RUNTIME_BUNDLED_SKILL_PACKS = {
        "reference_modeling": _fallback_skill_pack("reference_modeling", "Reference Modeling", ("match a reference image", "model from reference"), ("reference_construction", "spatial_measurement", "advanced_modeling")),
        "hard_surface_modeling": _fallback_skill_pack("hard_surface_modeling", "Hard Surface Modeling", ("hard surface armor", "panel lines", "beveled prop"), ("advanced_modeling", "geometry_nodes", "verified_editing")),
        "organic_proportion_editing": _fallback_skill_pack("organic_proportion_editing", "Organic Proportion Editing", ("bigger body part", "stylized proportion"), ("verified_editing", "sculpt_workflows", "spatial_measurement")),
        "procedural_modeling": _fallback_skill_pack("procedural_modeling", "Procedural Modeling", ("procedural building", "scatter", "radial array"), ("geometry_nodes", "advanced_modeling")),
        "geometry_nodes_patterns": _fallback_skill_pack("geometry_nodes_patterns", "Geometry Nodes Patterns", ("geometry nodes recipe", "node group"), ("geometry_nodes",)),
        "pbr_material_authoring": _fallback_skill_pack("pbr_material_authoring", "PBR Material Authoring", ("pbr material", "normal roughness metallic"), ("materials", "texture_baking")),
        "texture_baking": _fallback_skill_pack("texture_baking", "Texture Baking", ("bake normal and ORM maps", "bake textures"), ("texture_baking", "materials"), "MEDIUM"),
        "texture_painting_preflight": _fallback_skill_pack("texture_painting_preflight", "Texture Painting Preflight", ("paint decal", "texture paint"), ("materials", "texture_baking")),
        "sculpt_refinement": _fallback_skill_pack("sculpt_refinement", "Sculpt Refinement", ("sculpt refinement", "smooth region"), ("sculpt_workflows", "verified_editing"), "MEDIUM"),
        "cloth_pattern_workflow": _fallback_skill_pack("cloth_pattern_workflow", "Cloth Pattern Workflow", ("cloth cape", "cloth panel"), ("cloth_patterns", "simulation_workflows"), "MEDIUM"),
        "character_rigging": _fallback_skill_pack("character_rigging", "Character Rigging", ("character rig", "ik chain"), ("rigging", "pose_library"), "MEDIUM"),
        "animation_blocking": _fallback_skill_pack("animation_blocking", "Animation Blocking", ("animation shot", "blocking keys"), ("advanced_animation", "action_library", "shot_workflows")),
        "product_rendering": _fallback_skill_pack("product_rendering", "Product Rendering", ("product render", "studio shot"), ("animation_presentation", "materials")),
        "cinematic_lighting": _fallback_skill_pack("cinematic_lighting", "Cinematic Lighting", ("cinematic lighting", "shot lighting"), ("animation_presentation", "shot_workflows")),
        "game_asset_export": _fallback_skill_pack("game_asset_export", "Game Asset Export", ("game-ready prop", "export glb"), ("asset_workflows", "texture_baking"), "MEDIUM"),
        "scene_cleanup": _fallback_skill_pack("scene_cleanup", "Scene Cleanup", ("clean imported model", "scene cleanup"), ("verified_editing", "cache_management"), "MEDIUM"),
        "addon_development": _fallback_skill_pack("addon_development", "Addon Development", ("create addon", "validate addon"), ("addon_knowledge", "addon_interop", "release_diagnostics"), "HIGH"),
        "project_repair": _fallback_skill_pack("project_repair", "Project Repair", ("repair broken project textures", "missing assets"), ("project_runtime", "file_access", "asset_workflows")),
        "diagnostics_review": _fallback_skill_pack("diagnostics_review", "Diagnostics Review", ("diagnose addon connection", "why failed"), ("release_diagnostics", "error_help", "onboarding")),
    }

    def runtime_list_bundled_skill_packs():
        return {"status": "success", "skill_packs": [pack.to_dict() for pack in RUNTIME_BUNDLED_SKILL_PACKS.values()], "fallback": True}

    def runtime_get_bundled_skill_pack(pack_id):
        pack = RUNTIME_BUNDLED_SKILL_PACKS.get(pack_id)
        return {"status": "success", "skill_pack": pack.to_dict(), "fallback": True} if pack else {"status": "error", "message": f"Unknown bundled skill pack: {pack_id}"}

    def runtime_search_bundled_skill_packs(query, top_k=10):
        q = str(query or "").lower()
        terms = [term for term in q.split() if term.strip()]
        matches = []
        for pack in RUNTIME_BUNDLED_SKILL_PACKS.values():
            haystack = " ".join([pack.skill_pack_id, pack.title, *pack.intent_patterns, *pack.tool_packs]).lower()
            score = sum(3 if term in pack.skill_pack_id else 1 for term in terms if term in haystack)
            if not terms or score:
                matches.append((score, pack))
        matches.sort(key=lambda item: (-item[0], item[1].skill_pack_id))
        results = [pack.to_dict() for _, pack in matches[: max(1, min(int(top_k), 25))]]
        return {"status": "success", "query": query, "results": results, "fallback": True}

    def runtime_recommend_skill_packs(task, limit=5):
        results = runtime_search_bundled_skill_packs(task, top_k=limit)["results"]
        return {"status": "success", "recommendations": results, "reason": "Ranked by task term matches.", "fallback": True}

    def runtime_scan_addon_sources(root, approved_roots=None, max_files=80, max_bytes=1000000):
        candidate = Path(root).expanduser().resolve()
        approved = []
        for item in approved_roots or []:
            try:
                approved.append(Path(item).expanduser().resolve())
            except Exception:
                continue
        if not candidate.exists() or not candidate.is_dir():
            return {"status": "error", "message": f"Addon source root does not exist: {str(candidate).replace(str(Path.home()), '~')}", "fallback": True}
        if approved and not any(candidate == item or item in candidate.parents for item in approved):
            return {"status": "requires_approval", "message": "Addon source root is not approved for read-only inspection.", "root": str(candidate).replace(str(Path.home()), "~"), "fallback": True}
        return {
            "status": "success",
            "root": str(candidate).replace(str(Path.home()), "~"),
            "files_scanned": 0,
            "files_skipped": 0,
            "operators": [],
            "panels": [],
            "properties": [],
            "bl_info": {},
            "scan_id": hashlib.sha256(str(candidate).encode("utf-8")).hexdigest()[:16],
            "warnings": ["Phase 9B fallback mode: metadata-only scan placeholder; no addon code imported or executed."],
            "limits": {"max_files": max_files, "max_bytes": max_bytes},
            "fallback": True,
        }

    def runtime_plan_operator_invocation(operator_id, parameters=None, confirm=False):
        return {"status": "requires_approval", "approval_required": True, "operator_id": operator_id, "parameters": parameters or {}, "message": "Third-party addon operator execution is approval-gated.", "fallback": True}

    def runtime_get_error_catalog():
        return {"status": "success", "errors": [{"code": "RUNTIME_FALLBACK_ACTIVE", "summary": "The bundled runtime package was unavailable and addon fallback mode is active."}], "fallback": True}

    def runtime_explain_error(error_code=None, message=None):
        return {"status": "success", "error_code": error_code or "RUNTIME_FALLBACK_ACTIVE", "summary": message or "Addon fallback mode is active.", "fallback": True}

    def runtime_get_remediation_steps(error_code=None):
        return {"status": "success", "steps": ["Install or refresh the addon package with its bundled src/overtli_blender runtime.", "Restart the Overtli-Blender socket server."], "fallback": True}

    def runtime_run_setup_checks(repo_root=None, blend_path=None, preferences=None):
        return {"status": "success", "checks": [{"name": "addon_server", "status": "warning", "message": "Running in fallback mode."}], "fallback": True}

    def runtime_approval_queue_summary(queue=None):
        if hasattr(queue, "get_pending_approvals"):
            queue = queue.get_pending_approvals()
        approvals = (queue or {}).get("approvals", [])
        return {"status": "success", "pending_count": len(approvals), "approvals": approvals, "fallback": True}

    def runtime_recent_operation_summary(operations=None, limit=20):
        if hasattr(operations, "list_recent_operations"):
            operations = operations.list_recent_operations(limit)
        items = (operations or {}).get("operations") or (operations or {}).get("recent_operations") or []
        failures = [item for item in items if item.get("status") not in {None, "success"}]
        return {"status": "success", "operation_count": len(items), "failure_count": len(failures), "operations": items[:limit], "failures": failures[:10], "fallback": True}

    def runtime_build_dashboard(preferences=None, active_profile=None, setup=None, approvals=None, operations=None):
        return {"status": "success", "preferences": runtime_redact_sensitive_values(preferences or runtime_default_preferences()), "active_profile": active_profile, "setup": setup, "approvals": approvals, "operations": operations, "fallback": True}

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


if "runtime_normalize_bake_pass_name" not in globals():
    def runtime_normalize_bake_pass_name(pass_name):
        value = str(pass_name or "").strip().replace("-", "_").replace(" ", "_").upper()
        return {"AMBIENT_OCCLUSION": "AO", "COLOR": "DIFFUSE"}.get(value, value)

    def runtime_normalize_bake_resolution(resolution):
        if isinstance(resolution, int):
            width = height = resolution
        else:
            values = list(resolution or [1024, 1024])
            width, height = int(values[0]), int(values[1])
        if width < 4 or height < 4 or width > 10000 or height > 10000:
            raise ValueError("resolution must be between 4 and 10000 pixels per side")
        return width, height

    def runtime_classify_bake_pass(pass_name):
        name = runtime_normalize_bake_pass_name(pass_name)
        if name in {"COMBINED", "DIFFUSE", "GLOSSY", "TRANSMISSION", "EMIT", "AO", "SHADOW", "NORMAL", "UV", "ROUGHNESS"}:
            return "native"
        if name in {"METALLIC", "ALPHA", "HEIGHT", "OBJECT_ID", "MATERIAL_ID", "BASE_COLOR", "ALBEDO"}:
            return "derived"
        if name in {"CURVATURE", "THICKNESS"}:
            return "approximated"
        return "unsupported"

    def runtime_estimate_bake_cost(passes, resolution=1024, object_count=1):
        width, height = runtime_normalize_bake_resolution(resolution)
        pixels = width * height * max(1, len(passes or [])) * max(1, int(object_count))
        return {"status": "success", "resolution": [width, height], "pixels": pixels, "estimated_bytes": pixels * 16, "estimated_disk_bytes": max(1024, pixels * 4), "time_category": "small" if pixels <= 524288 else "medium", "memory_category": "small" if pixels * 16 < 67108864 else "medium", "risk_flags": []}

    def runtime_color_space_intent_for_pass(pass_name):
        return "sRGB" if runtime_normalize_bake_pass_name(pass_name) in {"DIFFUSE", "BASE_COLOR", "ALBEDO", "EMIT", "COMBINED"} else "Non-Color"

    def runtime_safe_image_filename(prefix, pass_name, image_format="PNG"):
        ext = {"PNG": ".png", "JPEG": ".jpg", "JPG": ".jpg", "TARGA": ".tga", "TIFF": ".tif", "OPEN_EXR": ".exr", "EXR": ".exr"}.get(str(image_format).upper(), "." + str(image_format).lower())
        clean = lambda value: re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "texture")).strip("._") or "texture"
        return f"{clean(prefix)}_{clean(pass_name).lower()}{ext}"

    def runtime_plan_bake_outputs(target_object_names, passes, resolution=1024, output_dir=None, prefix=None, image_format="PNG"):
        width, height = runtime_normalize_bake_resolution(resolution)
        root = output_dir or os.path.join("textures", "baked")
        return [{"object_name": obj, "pass_name": runtime_normalize_bake_pass_name(p), "classification": str(runtime_classify_bake_pass(p)), "resolution": [width, height], "color_space_intent": runtime_color_space_intent_for_pass(p), "file_path": os.path.join(root, runtime_safe_image_filename(prefix or obj, p, image_format)), "image_format": image_format} for obj in (target_object_names or []) for p in (passes or [])]

    def runtime_file_sha256(path):
        if not os.path.isfile(path):
            return None
        h = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1048576), b""):
                h.update(chunk)
        return h.hexdigest()

    def runtime_write_image_manifest(path, payload):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        return path

    def runtime_get_channel_layout(layout, custom_layout=None):
        layouts = {"ORM": {"R": "AO", "G": "ROUGHNESS", "B": "METALLIC"}, "RMA": {"R": "ROUGHNESS", "G": "METALLIC", "B": "AO"}, "MRA": {"R": "METALLIC", "G": "ROUGHNESS", "B": "AO"}, "GLTF_METALLIC_ROUGHNESS": {"G": "ROUGHNESS", "B": "METALLIC"}}
        return custom_layout or layouts.get(str(layout or "ORM").upper(), layouts["ORM"])

    def runtime_validate_channel_pack_inputs(source_images, layout="ORM", overwrite=False, output_path=None, custom_layout=None):
        missing = [path for path in (source_images or {}).values() if path and not os.path.exists(path)]
        return {"status": "success" if not missing else "error", "valid": not missing, "missing_files": missing, "requires_approval": bool(output_path and os.path.exists(output_path) and not overwrite), "layout": layout, "channels": runtime_get_channel_layout(layout, custom_layout), "color_space_intent": "Non-Color"}

    def runtime_validate_mesh_schema(schema, max_vertices=10000, max_faces=20000, check_non_manifold=True):
        errors = []
        warnings = []
        if not isinstance(schema, dict):
            return {"status": "error", "valid": False, "errors": ["schema-must-be-dict"], "warnings": warnings}
        vertices = schema.get("vertices", [])
        edges = schema.get("edges", [])
        faces = schema.get("faces", [])
        if not isinstance(vertices, list) or not isinstance(edges, list) or not isinstance(faces, list):
            errors.append("vertices-edges-faces-must-be-lists")
            vertices, edges, faces = [], [], []
        if len(vertices) > max_vertices:
            errors.append(f"vertex-count-exceeds-limit:{len(vertices)}>{max_vertices}")
        if len(faces) > max_faces:
            errors.append(f"face-count-exceeds-limit:{len(faces)}>{max_faces}")
        clean_vertices = []
        for index, vertex in enumerate(vertices):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
                errors.append(f"invalid-vertex-{index}")
                continue
            try:
                clean_vertices.append(tuple(float(axis) for axis in vertex))
            except (TypeError, ValueError):
                errors.append(f"invalid-vertex-{index}")
        seen = set()
        duplicates = 0
        for vertex in clean_vertices:
            if vertex in seen:
                duplicates += 1
            seen.add(vertex)
        if duplicates:
            warnings.append(f"duplicate-vertices:{duplicates}")
        face_edge_counts = {}
        for index, face in enumerate(faces):
            if not isinstance(face, (list, tuple)) or len(face) < 3 or not all(isinstance(item, int) for item in face):
                errors.append(f"invalid-face-{index}")
                continue
            if len(set(face)) != len(face):
                errors.append(f"degenerate-face-{index}")
            if any(item < 0 or item >= len(clean_vertices) for item in face):
                errors.append(f"face-index-out-of-range-{index}")
                continue
            for a, b in zip(face, list(face[1:]) + [face[0]]):
                key = tuple(sorted((a, b)))
                face_edge_counts[key] = face_edge_counts.get(key, 0) + 1
        if check_non_manifold:
            boundary = sum(1 for count in face_edge_counts.values() if count == 1)
            overused = sum(1 for count in face_edge_counts.values() if count > 2)
            if boundary:
                warnings.append(f"boundary-edge-risk:{boundary}")
            if overused:
                warnings.append(f"non-manifold-edge-risk:{overused}")
        bounds = None
        if clean_vertices:
            bounds = {"min": [min(v[axis] for v in clean_vertices) for axis in range(3)], "max": [max(v[axis] for v in clean_vertices) for axis in range(3)]}
        return {"status": "success" if not errors else "error", "valid": not errors, "errors": errors, "warnings": warnings, "summary": {"vertices": len(clean_vertices), "edges": len(edges), "faces": len(faces), "estimated_memory_bytes": len(clean_vertices) * 32 + len(edges) * 16 + len(faces) * 48, "bounds": bounds}}

    def runtime_plan_modifier_stack(modifiers):
        allowed = {"BEVEL", "ARRAY", "MIRROR", "SOLIDIFY", "WEIGHTED_NORMAL", "BOOLEAN", "SHRINKWRAP", "SIMPLE_DEFORM", "CURVE", "SKIN", "WIREFRAME", "LATTICE", "DISPLACE", "SCREW"}
        invalid = [item.get("type") for item in (modifiers or []) if str(item.get("type", "")).upper() not in allowed]
        return {"status": "error" if invalid else "success", "invalid_types": invalid, "allowed_types": sorted(allowed), "modifier_count": len(modifiers or [])}

    def runtime_select_modeling_method(intent, constraints=None):
        text = str(intent or "").lower()
        if any(term in text for term in ("reference", "silhouette", "measurement", "calibrated")):
            method = "reference_guided"
        elif any(term in text for term in ("pipe", "rail", "cable", "rope", "curve", "trim")):
            method = "curve_profile"
        elif any(term in text for term in ("cloth", "fabric", "seam", "pin")):
            method = "cloth_pattern"
        elif any(term in text for term in ("sculpt", "organic", "smooth", "mask")):
            method = "sculpt_shape_key"
        else:
            method = "mesh_schema" if (constraints or {}).get("exact_geometry") else "modifier_stack"
        return {"status": "success", "method": method}

    def runtime_plan_reference_construction(reference_set_id, target_description, measurement_ids=None):
        return {"status": "planned", "reference_set_id": reference_set_id, "target_description": target_description, "measurement_ids": measurement_ids or [], "steps": ["verify_reference_calibration", "create_guides", "construct_primary_forms", "validate_alignment"], "warnings": [] if reference_set_id else ["reference-set-not-provided"]}

    def runtime_new_workflow_id(prefix="construct"):
        return f"{prefix}_{uuid4().hex[:12]}"

if "runtime_validate_mesh_schema" not in globals():
    def runtime_validate_mesh_schema(schema, max_vertices=10000, max_faces=20000, check_non_manifold=True):
        errors = []
        warnings = []
        if not isinstance(schema, dict):
            return {"status": "error", "valid": False, "errors": ["schema-must-be-dict"], "warnings": warnings}
        vertices = schema.get("vertices", [])
        edges = schema.get("edges", [])
        faces = schema.get("faces", [])
        if not isinstance(vertices, list) or not isinstance(edges, list) or not isinstance(faces, list):
            errors.append("vertices-edges-faces-must-be-lists")
            vertices, edges, faces = [], [], []
        if len(vertices) > max_vertices:
            errors.append(f"vertex-count-exceeds-limit:{len(vertices)}>{max_vertices}")
        if len(faces) > max_faces:
            errors.append(f"face-count-exceeds-limit:{len(faces)}>{max_faces}")
        clean_vertices = []
        for index, vertex in enumerate(vertices):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
                errors.append(f"invalid-vertex-{index}")
                continue
            try:
                clean_vertices.append(tuple(float(axis) for axis in vertex))
            except (TypeError, ValueError):
                errors.append(f"invalid-vertex-{index}")
        seen = set()
        duplicates = 0
        for vertex in clean_vertices:
            if vertex in seen:
                duplicates += 1
            seen.add(vertex)
        if duplicates:
            warnings.append(f"duplicate-vertices:{duplicates}")
        face_edge_counts = {}
        for index, face in enumerate(faces):
            if not isinstance(face, (list, tuple)) or len(face) < 3 or not all(isinstance(item, int) for item in face):
                errors.append(f"invalid-face-{index}")
                continue
            if len(set(face)) != len(face):
                errors.append(f"degenerate-face-{index}")
            if any(item < 0 or item >= len(clean_vertices) for item in face):
                errors.append(f"face-index-out-of-range-{index}")
                continue
            for a, b in zip(face, list(face[1:]) + [face[0]]):
                key = tuple(sorted((a, b)))
                face_edge_counts[key] = face_edge_counts.get(key, 0) + 1
        if check_non_manifold:
            boundary = sum(1 for count in face_edge_counts.values() if count == 1)
            overused = sum(1 for count in face_edge_counts.values() if count > 2)
            if boundary:
                warnings.append(f"boundary-edge-risk:{boundary}")
            if overused:
                warnings.append(f"non-manifold-edge-risk:{overused}")
        bounds = None
        if clean_vertices:
            bounds = {"min": [min(v[axis] for v in clean_vertices) for axis in range(3)], "max": [max(v[axis] for v in clean_vertices) for axis in range(3)]}
        return {"status": "success" if not errors else "error", "valid": not errors, "errors": errors, "warnings": warnings, "summary": {"vertices": len(clean_vertices), "edges": len(edges), "faces": len(faces), "estimated_memory_bytes": len(clean_vertices) * 32 + len(edges) * 16 + len(faces) * 48, "bounds": bounds}}

if "runtime_plan_modifier_stack" not in globals():
    def runtime_plan_modifier_stack(modifiers):
        allowed = {"BEVEL", "ARRAY", "MIRROR", "SOLIDIFY", "WEIGHTED_NORMAL", "BOOLEAN", "SHRINKWRAP", "SIMPLE_DEFORM", "CURVE", "SKIN", "WIREFRAME", "LATTICE", "DISPLACE", "SCREW"}
        invalid = [item.get("type") for item in (modifiers or []) if str(item.get("type", "")).upper() not in allowed]
        return {"status": "error" if invalid else "success", "invalid_types": invalid, "allowed_types": sorted(allowed), "modifier_count": len(modifiers or [])}

if "runtime_select_modeling_method" not in globals():
    def runtime_select_modeling_method(intent, constraints=None):
        text = str(intent or "").lower()
        if any(term in text for term in ("reference", "silhouette", "measurement", "calibrated")):
            method = "reference_guided"
        elif any(term in text for term in ("pipe", "rail", "cable", "rope", "curve", "trim")):
            method = "curve_profile"
        elif any(term in text for term in ("cloth", "fabric", "seam", "pin")):
            method = "cloth_pattern"
        elif any(term in text for term in ("sculpt", "organic", "smooth", "mask")):
            method = "sculpt_shape_key"
        else:
            method = "mesh_schema" if (constraints or {}).get("exact_geometry") else "modifier_stack"
        return {"status": "success", "method": method}

if "runtime_plan_reference_construction" not in globals():
    def runtime_plan_reference_construction(reference_set_id, target_description, measurement_ids=None):
        return {"status": "planned", "reference_set_id": reference_set_id, "target_description": target_description, "measurement_ids": measurement_ids or [], "steps": ["verify_reference_calibration", "create_guides", "construct_primary_forms", "validate_alignment"], "warnings": [] if reference_set_id else ["reference-set-not-provided"]}

if "runtime_new_workflow_id" not in globals():
    def runtime_new_workflow_id(prefix="construct"):
        return f"{prefix}_{uuid4().hex[:12]}"


