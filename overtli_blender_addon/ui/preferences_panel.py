"""Preferences panel ownership marker for the packaged addon UI."""

from __future__ import annotations


PREFERENCE_FIELDS = (
    "host",
    "port",
    "permission_profile",
    "tool_profile",
    "local_permission_profile",
    "local_approval_mode",
    "browser_tool_profile",
    "browser_permission_profile",
    "browser_approval_mode",
    "browser_mutation_path_status",
    "approval_timeout_seconds",
    "require_approval_for_raw_python",
    "require_approval_for_provider_downloads",
    "require_approval_for_file_delete",
    "require_approval_for_external_writes",
    "approved_roots",
    "log_root",
    "cache_root",
)
