from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_api_knowledge_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def inspect_blender_api_docs(docs_root: str | None = None, max_files: int = 50000) -> str:
        return _send(get_blender_connection, "inspect_blender_api_docs", locals())

    @mcp.tool()
    def build_blender_api_index(docs_root: str | None = None, include_patterns: list[str] | None = None, max_files: int = 50000, max_chars_per_file: int = 20000, write_index: bool = True, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "build_blender_api_index", locals())

    @mcp.tool()
    def search_blender_api_docs(query: str, max_results: int = 20, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "search_blender_api_docs", locals())

    @mcp.tool()
    def get_blender_api_topic(topic: str, include_summary: bool = True, include_symbols: bool = True, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "get_blender_api_topic", locals())
