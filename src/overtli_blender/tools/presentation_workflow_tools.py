from __future__ import annotations

import json
from typing import Any, Callable


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    return json.dumps(blender.send_command(command, params), indent=2)


def register_presentation_workflow_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    @mcp.tool()
    def run_presentation_workflow_batch(label: str | None = None, operations: list[dict[str, Any]] | None = None, create_before_snapshot: bool = True, create_after_snapshot: bool = True, stop_on_error: bool = True, max_operations: int = 20, batch_allow_destructive: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "run_presentation_workflow_batch", locals())

    @mcp.tool()
    def cleanup_presentation_artifacts(prefix: str, confirm: bool = False, cleanup_scene_data: bool = True, cleanup_render_artifacts: bool = False, artifact_root: str | None = None) -> str:
        return _send(get_blender_connection, "cleanup_presentation_artifacts", locals())
