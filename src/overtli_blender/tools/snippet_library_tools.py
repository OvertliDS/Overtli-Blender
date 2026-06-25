from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_snippet_library_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def create_verified_snippet(name: str, code: str, description: str = "", tags: list[str] | None = None, source_evidence: list[str] | None = None, safety_classification: str = "medium", smoke_status: str = "not_run", overwrite: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "create_verified_snippet", locals())

    @mcp.tool()
    def validate_verified_snippet(snippet_id: str | None = None, code: str | None = None, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "validate_verified_snippet", locals())

    @mcp.tool()
    def list_verified_snippets(include_code: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "list_verified_snippets", locals())

    @mcp.tool()
    def search_verified_snippets(query: str, max_results: int = 20, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "search_verified_snippets", locals())

    @mcp.tool()
    def get_verified_snippet(snippet_id: str, include_code: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "get_verified_snippet", locals())

    @mcp.tool()
    def run_verified_snippet_smoke(snippet_id: str, confirm: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "run_verified_snippet_smoke", locals())

    @mcp.tool()
    def delete_verified_snippets(snippet_ids: list[str], confirm: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "delete_verified_snippets", locals())
