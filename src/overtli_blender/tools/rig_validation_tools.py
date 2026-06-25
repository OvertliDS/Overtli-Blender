from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_rig_validation_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def add_rig_constraint(armature_name: str, bone_name: str, constraint_type: str, target_object: str | None = None, target_bone: str | None = None, settings: dict[str, Any] | None = None) -> str: return _send(get_blender_connection, "add_rig_constraint", locals())
    @mcp.tool()
    def remove_rig_constraints(armature_name: str, bone_name: str, constraint_names: list[str], confirm: bool = False) -> str: return _send(get_blender_connection, "remove_rig_constraints", locals())
    @mcp.tool()
    def validate_rig(armature_name: str) -> str: return _send(get_blender_connection, "validate_rig", locals())
