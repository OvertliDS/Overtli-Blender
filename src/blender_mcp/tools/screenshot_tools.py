"""MCP tool registration for viewport screenshot tools."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from typing import Any


def register_screenshot_tools(
    mcp: Any,
    get_blender_connection: Callable[[], Any],
    *,
    image_type: Any | None = None,
) -> None:
    """Register viewport screenshot MCP tools on the provided FastMCP app."""

    @mcp.tool()
    def get_viewport_screenshot(ctx: Any, max_size: int = 800) -> Any:
        """
        Capture a screenshot of the current Blender 3D viewport.

        Parameters:
        - max_size: Maximum size in pixels for the largest dimension (default: 800)

        Returns the screenshot as an Image.
        """
        try:
            blender = get_blender_connection()

            # Create temp file path
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"blender_screenshot_{os.getpid()}.png")

            result = blender.send_command("get_viewport_screenshot", {
                "max_size": max_size,
                "filepath": temp_path,
                "format": "png"
            })

            if "error" in result:
                raise Exception(result["error"])

            if not os.path.exists(temp_path):
                raise Exception("Screenshot file was not created")

            # Read the file
            with open(temp_path, "rb") as f:
                image_bytes = f.read()

            # Delete the temp file
            os.remove(temp_path)

            image_factory = image_type
            if image_factory is None:
                raise Exception("Image type is not available")

            return image_factory(data=image_bytes, format="png")

        except Exception as e:
            raise Exception(f"Screenshot failed: {str(e)}")

