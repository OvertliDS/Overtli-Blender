from __future__ import annotations

from typing import Any, Callable

from ._phase9b_send import send_command


def register_addon_interop_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def list_addon_source_roots() -> str:
        return send_command(get_blender_connection, "list_addon_source_roots")

    @mcp.tool()
    def scan_addon_sources_readonly(root: str, max_files: int = 80, max_bytes: int = 1000000) -> str:
        return send_command(get_blender_connection, "scan_addon_sources_readonly", locals())

    @mcp.tool()
    def get_addon_source_summary(scan_id: str | None = None) -> str:
        return send_command(get_blender_connection, "get_addon_source_summary", locals())

    @mcp.tool()
    def search_addon_operators(query: str, scan_id: str | None = None, limit: int = 20) -> str:
        return send_command(get_blender_connection, "search_addon_operators", locals())

    @mcp.tool()
    def search_addon_panels(query: str, scan_id: str | None = None, limit: int = 20) -> str:
        return send_command(get_blender_connection, "search_addon_panels", locals())

    @mcp.tool()
    def search_addon_properties(query: str, scan_id: str | None = None, limit: int = 20) -> str:
        return send_command(get_blender_connection, "search_addon_properties", locals())

    @mcp.tool()
    def plan_addon_operator_invocation(operator_id: str, addon_module: str | None = None, properties: dict[str, Any] | None = None) -> str:
        return send_command(get_blender_connection, "plan_addon_operator_invocation", locals())

    @mcp.tool()
    def execute_approved_addon_operator(approval_id: str, operator_id: str, properties: dict[str, Any] | None = None) -> str:
        return send_command(get_blender_connection, "execute_approved_addon_operator", locals())
