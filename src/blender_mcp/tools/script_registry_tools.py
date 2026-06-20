"""MCP tool registration for script registry tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_script_registry_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register script registry MCP tools on the provided FastMCP app."""

    @mcp.tool()
    def register_context_script(ctx: Any, script_name: str, script_content: str, category: str = "default", permanent: bool = False) -> str:
        """
        Register a Python script for later execution in Blender.

        Args:
            script_name: Name for the script (without .py extension)
            script_content: The Python code to save
            category: Category/folder to organize scripts (default: "default")
            permanent: If True, script survives context clearing operations (default: False)

        Returns:
            Success/error message
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("register_context_script", {
                "script_name": script_name,
                "script_content": script_content,
                "category": category,
                "permanent": permanent
            })

            if result.get("status") == "success":
                permanence = "permanent" if permanent else "temporary"
                return f"Script '{script_name}' registered as {permanence} in category '{category}'"
            else:
                return f"Error registering script: {result.get('message', 'Unknown error')}"

        except Exception as e:
            return f"Error registering script: {str(e)}"

    @mcp.tool()
    def execute_context_script(ctx: Any, script_name: str, category: str = "default") -> str:
        """
        Execute a previously registered Python script in Blender.

        Args:
            script_name: Name of the script to execute (without .py extension)
            category: Category/folder the script is in (default: "default")

        Returns:
            Script execution results
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("execute_context_script", {
                "script_name": script_name,
                "category": category
            })

            if result.get("status") == "success":
                output = result.get("output", "")
                return f"Script '{script_name}' executed successfully.\nOutput:\n{output}"
            else:
                return f"Error executing script: {result.get('message', 'Unknown error')}"

        except Exception as e:
            return f"Error executing context script: {str(e)}"

    @mcp.tool()
    def list_context_scripts(ctx: Any, category: str = None) -> str:
        """
        List all registered context scripts.

        Args:
            category: Optional category to filter by. If None, lists all scripts.

        Returns:
            List of available scripts with metadata
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("list_context_scripts", {
                "category": category
            })

            if result.get("status") == "success":
                scripts = result.get("scripts", {})
                if not scripts:
                    return "No context scripts registered."

                output = "Registered context scripts:\n"
                total_permanent = 0
                total_temporary = 0

                for cat, script_list in scripts.items():
                    permanent_scripts = [s for s in script_list if s.get("permanent", False)]
                    temporary_scripts = [s for s in script_list if not s.get("permanent", False)]

                    total_permanent += len(permanent_scripts)
                    total_temporary += len(temporary_scripts)

                    output += f"\nCategory '{cat}' ({len(permanent_scripts)} permanent, {len(temporary_scripts)} temporary):\n"

                    # Show permanent scripts first
                    if permanent_scripts:
                        output += "  🔒 Permanent scripts:\n"
                        for script_info in permanent_scripts:
                            name = script_info.get("name", "unknown")
                            size = script_info.get("size", 0)
                            created = script_info.get("created", "unknown")
                            output += f"    - {name} ({size} bytes, created: {created})\n"

                    # Show temporary scripts
                    if temporary_scripts:
                        output += "  📝 Temporary scripts:\n"
                        for script_info in temporary_scripts:
                            name = script_info.get("name", "unknown")
                            size = script_info.get("size", 0)
                            created = script_info.get("created", "unknown")
                            output += f"    - {name} ({size} bytes, created: {created})\n"

                output += f"\nTotal: {total_permanent} permanent, {total_temporary} temporary scripts"
                return output
            else:
                return f"Error listing scripts: {result.get('message', 'Unknown error')}"

        except Exception as e:
            return f"Error listing context scripts: {str(e)}"

