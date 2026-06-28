"""MCP wrappers for Phase 7B runtime governance commands."""

from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_governance_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def discover_tool_packs() -> str:
        return _send(get_blender_connection, "discover_tool_packs")

    @mcp.tool()
    def get_tool_pack(name: str) -> str:
        return _send(get_blender_connection, "get_tool_pack", {"name": name})

    @mcp.tool()
    def search_tools(query: str, category: str | None = None, tool_pack: str | None = None, risk_max: str | None = None) -> str:
        return _send(get_blender_connection, "search_tools", {"query": query, "category": category, "tool_pack": tool_pack, "risk_max": risk_max})

    @mcp.tool()
    def get_tool_spec(name: str) -> str:
        return _send(get_blender_connection, "get_tool_spec", {"name": name})

    @mcp.tool()
    def prepare_operation(command_name: str, params: dict[str, Any] | None = None) -> str:
        return _send(get_blender_connection, "prepare_operation", {"command_name": command_name, "params": params or {}})

    @mcp.tool()
    def get_pending_approvals() -> str:
        return _send(get_blender_connection, "get_pending_approvals")

    @mcp.tool()
    def approve_operation(approval_id: str, execute_after_approval: bool = True, approve_only: bool = False) -> str:
        return _send(get_blender_connection, "approve_operation", {"approval_id": approval_id, "execute_after_approval": execute_after_approval, "approve_only": approve_only})

    @mcp.tool()
    def deny_operation(approval_id: str, reason: str | None = None) -> str:
        return _send(get_blender_connection, "deny_operation", {"approval_id": approval_id, "reason": reason})

    @mcp.tool()
    def execute_approved_operation(approval_id: str, command_name: str | None = None, params: dict[str, Any] | None = None) -> str:
        return _send(get_blender_connection, "execute_approved_operation", {"approval_id": approval_id, "command_name": command_name, "params": params})

    @mcp.tool()
    def approve_and_execute_operation(approval_id: str, expected_command_name: str | None = None, expected_params_hash: str | None = None, reason: str | None = None) -> str:
        return _send(
            get_blender_connection,
            "approve_and_execute_operation",
            {
                "approval_id": approval_id,
                "expected_command_name": expected_command_name,
                "expected_params_hash": expected_params_hash,
                "reason": reason,
            },
        )

    @mcp.tool()
    def get_operation_status(operation_id: str | None = None) -> str:
        return _send(get_blender_connection, "get_operation_status", {"operation_id": operation_id})

    @mcp.tool()
    def list_recent_operations(limit: int = 20) -> str:
        return _send(get_blender_connection, "list_recent_operations", {"limit": limit})

    @mcp.tool()
    def cancel_operation(operation_id: str) -> str:
        return _send(get_blender_connection, "cancel_operation", {"operation_id": operation_id})

    @mcp.tool()
    def get_permission_profile() -> str:
        return _send(get_blender_connection, "get_permission_profile")

    @mcp.tool()
    def get_capability_policy() -> str:
        return _send(get_blender_connection, "get_capability_policy")

    @mcp.tool()
    def validate_command_capabilities(command_name: str, profile: str | None = None) -> str:
        return _send(get_blender_connection, "validate_command_capabilities", {"command_name": command_name, "profile": profile})

    @mcp.tool()
    def get_log_status() -> str:
        return _send(get_blender_connection, "get_log_status")
