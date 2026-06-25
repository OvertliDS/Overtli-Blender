# Code created by Siddharth Ahuja: www.github.com/ahujasid © 2025

import bpy
import mathutils
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
        self.geometry_nodes_service = GeometryNodesService(self)

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
        self.complete_geometry_node = self.geometry_nodes_service.complete_geometry_node
        self.get_geometry_nodes_status = self.geometry_nodes_service.get_geometry_nodes_status

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
            "complete_geometry_node": self.complete_geometry_node,
            "get_geometry_nodes_status": self.get_geometry_nodes_status,
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


