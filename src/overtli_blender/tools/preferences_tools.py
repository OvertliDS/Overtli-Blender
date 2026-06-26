from __future__ import annotations

from typing import Any, Callable

from ._phase9b_send import send_command


def register_preferences_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_preferences_schema() -> str:
        return send_command(get_blender_connection, "get_preferences_schema")

    @mcp.tool()
    def get_runtime_preferences() -> str:
        return send_command(get_blender_connection, "get_runtime_preferences")

    @mcp.tool()
    def update_runtime_preferences(changes: dict[str, Any], confirm: bool = False) -> str:
        return send_command(get_blender_connection, "update_runtime_preferences", locals())

    @mcp.tool()
    def validate_runtime_preferences() -> str:
        return send_command(get_blender_connection, "validate_runtime_preferences")

    @mcp.tool()
    def reset_runtime_preferences(confirm: bool = False, preview: bool = True) -> str:
        return send_command(get_blender_connection, "reset_runtime_preferences", locals())
