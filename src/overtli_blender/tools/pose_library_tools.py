from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_pose_library_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def inspect_pose(armature_name: str) -> str: return _send(get_blender_connection, "inspect_pose", locals())
    @mcp.tool()
    def create_pose_snapshot(armature_name: str, snapshot_id: str | None = None, include_custom_properties: bool = True) -> str: return _send(get_blender_connection, "create_pose_snapshot", locals())
    @mcp.tool()
    def apply_pose_snapshot(snapshot_id: str, armature_name: str | None = None, confirm: bool = False) -> str: return _send(get_blender_connection, "apply_pose_snapshot", locals())
    @mcp.tool()
    def create_pose_asset(snapshot_id: str, asset_name: str, native_asset: bool = False) -> str: return _send(get_blender_connection, "create_pose_asset", locals())
    @mcp.tool()
    def list_pose_assets(armature_name: str | None = None) -> str: return _send(get_blender_connection, "list_pose_assets", locals())
    @mcp.tool()
    def compare_poses(source_snapshot_id: str, target_snapshot_id: str) -> str: return _send(get_blender_connection, "compare_poses", locals())
    @mcp.tool()
    def delete_pose_assets(asset_ids: list[str], confirm: bool = False) -> str: return _send(get_blender_connection, "delete_pose_assets", locals())
