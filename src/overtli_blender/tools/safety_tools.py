"""MCP tool registration for addon safety status inspection."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any


logger = logging.getLogger("OvertliBlenderServer")


def register_safety_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register safety introspection MCP tools on the provided FastMCP app."""

    @mcp.tool()
    def get_safety_status(ctx: Any) -> str:
        """Inspect the current addon safety policy mode and risk summary."""
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_safety_status")
            if result.get("status") != "success":
                return f"Error: {result.get('message', 'Unable to query safety status')}"

            safety = result.get("result", {})
            mode = safety.get("mode", "unknown")
            policy_version = safety.get("policy_version", "unknown")
            high_risk = ", ".join(safety.get("high_risk_commands", []))
            return (
                f"Safety mode: {mode}\n"
                f"Policy version: {policy_version}\n"
                f"High-risk commands: {high_risk if high_risk else 'none'}"
            )
        except Exception as e:
            logger.error(f"Error querying safety status: {str(e)}")
            return f"Error querying safety status: {str(e)}"

