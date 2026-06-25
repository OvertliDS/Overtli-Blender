from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_rigging_simulation_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def inspect_rigging(object_name: str | None = None) -> str:
        return _send(get_blender_connection, "inspect_rigging", locals())

    @mcp.tool()
    def create_armature(armature_name: str | None = None, bones: list[dict[str, Any]] | None = None, collection_name: str | None = None, location: list[float] | None = None) -> str:
        return _send(get_blender_connection, "create_armature", locals())

    @mcp.tool()
    def parent_mesh_to_armature(mesh_name: str, armature_name: str, add_modifier: bool = True, create_vertex_groups: bool = True) -> str:
        return _send(get_blender_connection, "parent_mesh_to_armature", locals())

    @mcp.tool()
    def pose_bone_transform(armature_name: str, bone_name: str, location: list[float] | None = None, rotation: list[float] | None = None, scale: list[float] | None = None, keyframe_frame: int | None = None) -> str:
        return _send(get_blender_connection, "pose_bone_transform", locals())

    @mcp.tool()
    def add_driver(target_type: str, target_name: str, data_path: str, expression: str = "var", variables: list[dict[str, Any]] | None = None, array_index: int = -1) -> str:
        return _send(get_blender_connection, "add_driver", locals())

    @mcp.tool()
    def remove_driver(target_type: str, target_name: str, data_path: str, array_index: int = -1, confirm: bool = False) -> str:
        return _send(get_blender_connection, "remove_driver", locals())

    @mcp.tool()
    def add_physics_basic(object_name: str, physics_type: str = "cloth", settings: dict[str, Any] | None = None) -> str:
        return _send(get_blender_connection, "add_physics_basic", locals())
