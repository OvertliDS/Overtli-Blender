from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any] | None = None) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params or {}), indent=2)


def register_review_package_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def export_project_review_package(package_id: str | None = None, include_memory_bank: bool = False, include_private_docs: bool = False, include_generated_artifacts_summary: bool = True, max_files: int = 2000, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "export_project_review_package", locals())

    @mcp.tool()
    def validate_review_package(package_path: str) -> str:
        return _send(get_blender_connection, "validate_review_package", locals())
