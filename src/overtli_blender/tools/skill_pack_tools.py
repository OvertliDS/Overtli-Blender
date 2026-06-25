from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_skill_pack_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_skill_pack(name: str, description: str = "", operations: list[dict[str, Any]] | None = None, snippet_ids: list[str] | None = None, docs_topics: list[str] | None = None, overwrite: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "create_skill_pack", locals())

    @mcp.tool()
    def validate_skill_pack(pack_id: str, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "validate_skill_pack", locals())

    @mcp.tool()
    def list_skill_packs(artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "list_skill_packs", locals())

    @mcp.tool()
    def get_skill_pack(pack_id: str, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "get_skill_pack", locals())

    @mcp.tool()
    def run_skill_pack(pack_id: str, confirm: bool = False, max_operations: int = 20, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "run_skill_pack", locals())

    @mcp.tool()
    def delete_skill_packs(pack_ids: list[str], confirm: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "delete_skill_packs", locals())
