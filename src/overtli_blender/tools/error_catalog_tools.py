from __future__ import annotations

from typing import Any, Callable

from ._phase9b_send import send_command


def register_error_catalog_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_error_catalog() -> str:
        return send_command(get_blender_connection, "get_error_catalog")

    @mcp.tool()
    def explain_error(code: str, context: dict[str, Any] | None = None) -> str:
        return send_command(get_blender_connection, "explain_error", locals())

    @mcp.tool()
    def get_remediation_steps(code: str) -> str:
        return send_command(get_blender_connection, "get_remediation_steps", locals())
