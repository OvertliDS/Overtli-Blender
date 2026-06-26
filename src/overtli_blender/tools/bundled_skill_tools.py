from __future__ import annotations

from typing import Any, Callable

from ._phase9b_send import send_command


def register_bundled_skill_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def list_bundled_skill_packs() -> str:
        return send_command(get_blender_connection, "list_bundled_skill_packs")

    @mcp.tool()
    def get_bundled_skill_pack(skill_pack_id: str) -> str:
        return send_command(get_blender_connection, "get_bundled_skill_pack", locals())

    @mcp.tool()
    def search_bundled_skill_packs(query: str, top_k: int = 10) -> str:
        return send_command(get_blender_connection, "search_bundled_skill_packs", locals())

    @mcp.tool()
    def activate_skill_pack(skill_pack_id: str, confirm: bool = False) -> str:
        return send_command(get_blender_connection, "activate_skill_pack", locals())

    @mcp.tool()
    def deactivate_skill_pack(skill_pack_id: str) -> str:
        return send_command(get_blender_connection, "deactivate_skill_pack", locals())

    @mcp.tool()
    def recommend_skill_packs(task_description: str) -> str:
        return send_command(get_blender_connection, "recommend_skill_packs", locals())

    @mcp.tool()
    def validate_skill_pack_readiness(skill_pack_id: str, context: dict[str, Any] | None = None) -> str:
        return send_command(get_blender_connection, "validate_skill_pack_readiness", locals())
