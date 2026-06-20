"""MCP tool registration for basic scene and object observation tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def register_observation_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register basic scene/object observation MCP tools on the provided FastMCP app."""

    @mcp.tool()
    def get_scene_info(ctx: Any) -> str:
        """
        Get detailed information about the current Blender scene.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_scene_info")

            # Just return the JSON representation of what Blender sent us
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting scene info: {str(e)}"

    @mcp.tool()
    def get_object_info(ctx: Any, object_name: str) -> str:
        """
        Get detailed information about a specific object in the Blender scene.

        Parameters:
        - object_name: The name of the object to get information about
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_object_info", {"name": object_name})

            # Just return the JSON representation of what Blender sent us
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting object info: {str(e)}"

