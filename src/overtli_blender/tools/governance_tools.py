"""MCP wrappers for Phase 7B runtime governance commands."""

from __future__ import annotations

import json
from typing import Any, Callable

from overtli_blender.runtime.tool_packs import search_tools as runtime_search_tools


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def _profile_filtered_search(
    query: str,
    category: str | None,
    tool_pack: str | None,
    risk_max: str | None,
    visible_tool_names: set[str] | None,
) -> str:
    result = runtime_search_tools(query, category=category, tool_pack=tool_pack, risk_max=risk_max)
    if visible_tool_names is None:
        return json.dumps(result, indent=2)
    all_results = list(result.get("results", []))
    result["results"] = [tool for tool in all_results if tool.get("name") in visible_tool_names]
    hidden_count = len(all_results) - len(result["results"])
    if hidden_count:
        result.setdefault("warnings", []).append(
            f"{hidden_count} registry matches are hidden by the active MCP tool profile and were omitted from browser discovery."
        )
    result["active_tool_surface_contract"] = "Every returned result is registered as a callable MCP tool in the active profile."
    return json.dumps(result, indent=2)


def register_governance_tools(mcp: Any, get_blender_connection: Callable[[], Any], *, visible_tool_names: set[str] | None = None) -> None:
    @mcp.tool()
    def discover_tool_packs() -> str:
        return _send(get_blender_connection, "discover_tool_packs")

    @mcp.tool()
    def get_tool_pack(name: str) -> str:
        return _send(get_blender_connection, "get_tool_pack", {"name": name})

    @mcp.tool()
    def search_tools(query: str, category: str | None = None, tool_pack: str | None = None, risk_max: str | None = None) -> str:
        if visible_tool_names is not None:
            return _profile_filtered_search(query, category, tool_pack, risk_max, visible_tool_names)
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
