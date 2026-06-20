"""MCP tool registration for shared context and handle tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def register_context_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register shared-context and handle MCP tools on the provided FastMCP app."""

    @mcp.tool()
    def get_shared_context(ctx: Any) -> str:
        """
        Get the current shared context state - shows persistent variables, object handles,
        material handles, and operation history that persists between tool calls.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_shared_context")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting shared context: {str(e)}"

    @mcp.tool()
    def clear_shared_context(ctx: Any, section: str = "all") -> str:
        """
        Clear shared context. Useful for starting fresh.

        Parameters:
        - section: What to clear (all, variables, objects, materials, operations, history)
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("clear_shared_context", {"section": section})
            return result
        except Exception as e:
            return f"Error clearing shared context: {str(e)}"

    @mcp.tool()
    def get_operation_history(ctx: Any, count: int = 10) -> str:
        """
        Get recent operation history for debugging.

        Parameters:
        - count: Number of recent operations to show (default 10)
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_operation_history", {"count": count})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting operation history: {str(e)}"

    @mcp.tool()
    def create_object_handle(ctx: Any, handle: str, object_name: str) -> str:
        """
        Create a handle for an object to reference in future operations.
        This allows you to easily reference objects across multiple tool calls.

        Parameters:
        - handle: The handle name to create (e.g., 'my_cube', 'main_character')
        - object_name: The name of the Blender object
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("create_object_handle", {"handle": handle, "object_name": object_name})

            if "error" in result:
                return f"Error: {result['error']}"

            return f"Created handle '{handle}' for object '{object_name}' at location {result['location']}"
        except Exception as e:
            return f"Error creating object handle: {str(e)}"

    @mcp.tool()
    def create_material_handle(ctx: Any, handle: str, material_name: str) -> str:
        """
        Create a handle for a material to reference in future operations.
        This allows you to easily reference materials across multiple tool calls.

        Parameters:
        - handle: The handle name to create (e.g., 'wood_mat', 'metal_shader')
        - material_name: The name of the Blender material
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("create_material_handle", {"handle": handle, "material_name": material_name})

            if "error" in result:
                return f"Error: {result['error']}"

            return f"Created handle '{handle}' for material '{material_name}'"
        except Exception as e:
            return f"Error creating material handle: {str(e)}"

    @mcp.tool()
    def list_object_handles(ctx: Any) -> str:
        """
        List all object handles and their details.
        Shows which objects you can reference with get_object() in scripts.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("list_object_handles")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error listing object handles: {str(e)}"

    @mcp.tool()
    def list_material_handles(ctx: Any) -> str:
        """
        List all material handles and their details.
        Shows which materials you can reference with get_material() in scripts.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("list_material_handles")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error listing material handles: {str(e)}"
