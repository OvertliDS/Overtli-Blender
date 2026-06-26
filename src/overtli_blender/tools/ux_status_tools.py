from __future__ import annotations

from typing import Any, Callable

from ._phase9b_send import send_command


def register_ux_status_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_runtime_dashboard() -> str:
        return send_command(get_blender_connection, "get_runtime_dashboard")

    @mcp.tool()
    def get_approval_queue_summary() -> str:
        return send_command(get_blender_connection, "get_approval_queue_summary")

    @mcp.tool()
    def get_recent_operation_summary() -> str:
        return send_command(get_blender_connection, "get_recent_operation_summary")

    @mcp.tool()
    def run_product_polish_workflow_batch() -> str:
        return send_command(get_blender_connection, "run_product_polish_workflow_batch")
