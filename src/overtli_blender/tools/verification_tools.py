"""MCP tool registration for Phase 2 verification artifact tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def register_verification_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register local verification snapshot and screenshot-pack MCP tools."""

    @mcp.tool()
    def capture_viewport_pack(
        ctx: Any,
        views: list[str] | None = None,
        max_size: int = 800,
        include_manifest: bool = True,
        snapshot_name: str | None = None,
        artifact_root: str | None = None,
    ) -> str:
        """Capture a local multi-view viewport screenshot pack and return its manifest paths."""
        try:
            blender = get_blender_connection()
            result = blender.send_command(
                "capture_viewport_pack",
                {
                    "views": views,
                    "max_size": max_size,
                    "include_manifest": include_manifest,
                    "snapshot_name": snapshot_name,
                    "artifact_root": artifact_root,
                },
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error capturing viewport pack: {str(e)}"

    @mcp.tool()
    def create_verification_snapshot(
        ctx: Any,
        label: str | None = None,
        include_scene_index: bool = True,
        include_scene_health: bool = True,
        include_selection: bool = True,
        include_screenshots: bool = True,
        views: list[str] | None = None,
        max_size: int = 800,
        artifact_root: str | None = None,
    ) -> str:
        """Create a local verification snapshot with manifest, scene JSON, selection JSON, and screenshots."""
        try:
            blender = get_blender_connection()
            result = blender.send_command(
                "create_verification_snapshot",
                {
                    "label": label,
                    "include_scene_index": include_scene_index,
                    "include_scene_health": include_scene_health,
                    "include_selection": include_selection,
                    "include_screenshots": include_screenshots,
                    "views": views,
                    "max_size": max_size,
                    "artifact_root": artifact_root,
                },
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating verification snapshot: {str(e)}"

    @mcp.tool()
    def list_verification_snapshots(ctx: Any) -> str:
        """List generated local verification snapshots."""
        try:
            blender = get_blender_connection()
            result = blender.send_command("list_verification_snapshots")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error listing verification snapshots: {str(e)}"
