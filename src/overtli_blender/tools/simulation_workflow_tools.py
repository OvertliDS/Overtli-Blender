from __future__ import annotations
import json
from typing import Any, Callable

def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    return json.dumps(get_blender_connection().send_command(command, params or {}), indent=2)

def register_simulation_workflow_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_simulation_capabilities() -> str: return _send(get_blender_connection, "get_simulation_capabilities")
    @mcp.tool()
    def inspect_simulation_state(object_names: list[str] | None = None) -> str: return _send(get_blender_connection, "inspect_simulation_state", locals())
    @mcp.tool()
    def configure_rigidbody_basic(object_name: str, body_type: str = "ACTIVE", mass: float = 1.0) -> str: return _send(get_blender_connection, "configure_rigidbody_basic", locals())
    @mcp.tool()
    def configure_cloth_simulation_advanced(object_name: str, frame_start: int = 1, frame_end: int = 48, settings: dict[str, Any] | None = None) -> str: return _send(get_blender_connection, "configure_cloth_simulation_advanced", locals())
    @mcp.tool()
    def configure_softbody_basic(object_name: str, frame_start: int = 1, frame_end: int = 48) -> str: return _send(get_blender_connection, "configure_softbody_basic", locals())
    @mcp.tool()
    def configure_hair_curve_dynamics_basic(object_name: str, frame_start: int = 1, frame_end: int = 48) -> str: return _send(get_blender_connection, "configure_hair_curve_dynamics_basic", locals())
    @mcp.tool()
    def get_simulation_cache_status(object_name: str | None = None) -> str: return _send(get_blender_connection, "get_simulation_cache_status", locals())
    @mcp.tool()
    def simulate_preview_range(object_name: str, frame_start: int = 1, frame_end: int = 24, max_frames: int = 48, confirm: bool = False) -> str: return _send(get_blender_connection, "simulate_preview_range", locals())
    @mcp.tool()
    def bake_simulation_cache(object_name: str | None = None, world: bool = False, confirm: bool = False) -> str: return _send(get_blender_connection, "bake_simulation_cache", locals())
    @mcp.tool()
    def clear_simulation_cache(object_name: str | None = None, world: bool = False, confirm: bool = False) -> str: return _send(get_blender_connection, "clear_simulation_cache", locals())
