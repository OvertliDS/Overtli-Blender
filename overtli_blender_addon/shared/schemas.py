"""Addon-local lightweight schema markers."""

from __future__ import annotations


UNKNOWN_COMMAND_ERROR = {
    "status": "error",
    "errors": [
        {
            "code": "COMMAND_NOT_AVAILABLE",
            "message": "Command is not available.",
            "remediation": "Use search_tools or discover_tool_packs.",
        }
    ],
}
