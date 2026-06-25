from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params), indent=2)


def register_lighting_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_light(light_name: str | None = None, light_type: str = "AREA", location: list[float] | None = None, rotation: list[float] | None = None, energy: float | None = None, color: list[float] | None = None, size: float | None = None, collection_name: str | None = None, verify: bool = False) -> str:
        return _send(get_blender_connection, "create_light", locals())

    @mcp.tool()
    def create_lighting_setup(setup_name: str, target_object_names: list[str] | None = None, preset: str = "three_point", collection_name: str | None = None, replace_existing_with_prefix: bool = False, confirm_replace: bool = False, verify: bool = False) -> str:
        return _send(get_blender_connection, "create_lighting_setup", locals())

    @mcp.tool()
    def update_light(light_name: str, energy: float | None = None, color: list[float] | None = None, size: float | None = None, location: list[float] | None = None, rotation: list[float] | None = None, verify: bool = False) -> str:
        return _send(get_blender_connection, "update_light", locals())

    @mcp.tool()
    def set_world_lighting(color: list[float] | None = None, strength: float | None = None, verify: bool = False) -> str:
        return _send(get_blender_connection, "set_world_lighting", locals())
