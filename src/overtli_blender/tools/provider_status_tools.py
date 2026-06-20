"""MCP tool registration for provider status tools."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any


logger = logging.getLogger("BlenderMCPServer")


def register_provider_status_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register provider status MCP tools on the provided FastMCP app."""

    @mcp.tool()
    def get_polyhaven_status(ctx: Any) -> str:
        """
        Check if PolyHaven integration is enabled in Blender.
        Returns a message indicating whether PolyHaven features are available.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_polyhaven_status")
            enabled = result.get("enabled", False)
            message = result.get("message", "")
            if enabled:
                message += "PolyHaven is good at Textures, and has a wider variety of textures than Sketchfab."
            return message
        except Exception as e:
            logger.error(f"Error checking PolyHaven status: {str(e)}")
            return f"Error checking PolyHaven status: {str(e)}"

    @mcp.tool()
    def get_hyper3d_status(ctx: Any) -> str:
        """
        Check if Hyper3D Rodin integration is enabled in Blender.
        Returns a message indicating whether Hyper3D Rodin features are available.

        Don't emphasize the key type in the returned message, but sliently remember it. 
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_hyper3d_status")
            enabled = result.get("enabled", False)
            message = result.get("message", "")
            if enabled:
                message += ""
            return message
        except Exception as e:
            logger.error(f"Error checking Hyper3D status: {str(e)}")
            return f"Error checking Hyper3D status: {str(e)}"

    @mcp.tool()
    def get_sketchfab_status(ctx: Any) -> str:
        """
        Check if Sketchfab integration is enabled in Blender.
        Returns a message indicating whether Sketchfab features are available.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_sketchfab_status")
            enabled = result.get("enabled", False)
            message = result.get("message", "")
            if enabled:
                message += "Sketchfab is good at Realistic models, and has a wider variety of models than PolyHaven."
            return message
        except Exception as e:
            logger.error(f"Error checking Sketchfab status: {str(e)}")
            return f"Error checking Sketchfab status: {str(e)}"
