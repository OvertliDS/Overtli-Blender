"""MCP tool registration for Phase 3 collection organization tools."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _send(get_blender_connection: Callable[[], Any], command: str, params: dict[str, Any]) -> str:
    blender = get_blender_connection()
    params.pop("ctx", None)
    return json.dumps(blender.send_command(command, params), indent=2)


def register_collection_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register collection creation and explicit object organization tools."""

    @mcp.tool()
    def create_collection(ctx: Any, collection_name: str, parent_collection_name: str | None = None, replace_existing: bool = False) -> str:
        """Create a collection without deleting or replacing existing collections."""
        try:
            return _send(get_blender_connection, "create_collection", locals())
        except Exception as e:
            return f"Error creating collection: {str(e)}"

    @mcp.tool()
    def move_objects_to_collection(ctx: Any, object_names: list[str], collection_name: str, unlink_from_other_collections: bool = False, create_collection: bool = False) -> str:
        """Link or move explicitly named objects to a collection."""
        try:
            return _send(get_blender_connection, "move_objects_to_collection", locals())
        except Exception as e:
            return f"Error moving objects to collection: {str(e)}"

    @mcp.tool()
    def delete_collection(ctx: Any, collection_name: str, confirm: bool = False, require_empty: bool = True) -> str:
        """Delete one explicitly named collection after confirmation; empty-only by default."""
        try:
            return _send(get_blender_connection, "delete_collection", locals())
        except Exception as e:
            return f"Error deleting collection: {str(e)}"
