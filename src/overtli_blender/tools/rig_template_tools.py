from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_rig_template_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_rig_template(armature_name: str, template: str = "basic_biped", bones: list[dict[str, Any]] | None = None, collection_name: str | None = None, location: list[float] | None = None) -> str: return _send(get_blender_connection, "create_rig_template", locals())
    @mcp.tool()
    def create_control_bones(armature_name: str, controls: list[dict[str, Any]] | None = None) -> str: return _send(get_blender_connection, "create_control_bones", locals())
    @mcp.tool()
    def create_ik_chain(armature_name: str, owner_bone: str, target_object: str | None = None, target_bone: str | None = None, chain_count: int = 2, confirm: bool = False) -> str: return _send(get_blender_connection, "create_ik_chain", locals())
    @mcp.tool()
    def add_custom_rig_properties(armature_name: str, properties: list[dict[str, Any]]) -> str: return _send(get_blender_connection, "add_custom_rig_properties", locals())
