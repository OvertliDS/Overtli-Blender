"""MCP tool registration for raw Blender Python code execution."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any


logger = logging.getLogger("BlenderMCPServer")


def register_code_execution_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register raw code execution MCP tools on the provided FastMCP app."""

    @mcp.tool()
    def execute_blender_code(ctx: Any, code: str) -> str:
        """
        Execute arbitrary Python code in Blender. Make sure to do it step-by-step by breaking it into smaller chunks.

        Now includes shared context between executions! You can use:
        - shared['variable_name'] = value  # Store variables for later use
        - get_object('handle_name')       # Get stored object references
        - get_material('handle_name')     # Get stored material references
        - store_object('handle', 'obj_name')    # Store object reference
        - store_material('handle', 'mat_name')  # Store material reference

        Parameters:
        - code: The Python code to execute
        """
        try:
            # Get the global connection
            blender = get_blender_connection()
            result = blender.send_command("execute_code", {"code": code})

            # Show shared variables if any
            shared_vars = result.get('shared_variables', [])
            output = f"Code executed successfully: {result.get('result', '')}"
            if shared_vars:
                output += f"\nShared variables: {', '.join(shared_vars)}"
            return output
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            return f"Error executing code: {str(e)}"
