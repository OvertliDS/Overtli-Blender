from __future__ import annotations

from typing import Any, Callable

from ._phase9b_send import send_command


def register_onboarding_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def get_setup_status() -> str:
        return send_command(get_blender_connection, "get_setup_status")

    @mcp.tool()
    def run_onboarding_checklist(fix_safe_defaults: bool = False, confirm: bool = False) -> str:
        return send_command(get_blender_connection, "run_onboarding_checklist", locals())
