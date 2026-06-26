from __future__ import annotations

from typing import Any, Callable

from ._phase9b_send import send_command


def register_tool_profile_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_tool_profiles() -> str:
        return send_command(get_blender_connection, "get_tool_profiles")

    @mcp.tool()
    def get_active_tool_profile() -> str:
        return send_command(get_blender_connection, "get_active_tool_profile")

    @mcp.tool()
    def set_active_tool_profile(profile_name: str, confirm: bool = False) -> str:
        return send_command(get_blender_connection, "set_active_tool_profile", locals())

    @mcp.tool()
    def preview_tool_profile(profile_name: str) -> str:
        return send_command(get_blender_connection, "preview_tool_profile", locals())

    @mcp.tool()
    def get_visible_tool_budget() -> str:
        return send_command(get_blender_connection, "get_visible_tool_budget")

    @mcp.tool()
    def get_enabled_tool_packs() -> str:
        return send_command(get_blender_connection, "get_enabled_tool_packs")

    @mcp.tool()
    def set_enabled_tool_packs(tool_packs: list[str], confirm: bool = False) -> str:
        return send_command(get_blender_connection, "set_enabled_tool_packs", locals())

    @mcp.tool()
    def recommend_tool_profile(task_description: str, current_context: dict[str, Any] | None = None) -> str:
        return send_command(get_blender_connection, "recommend_tool_profile", locals())
