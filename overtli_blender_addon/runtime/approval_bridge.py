"""Bridge from packaged addon code to the shared approval runtime."""

from __future__ import annotations

from overtli_blender.runtime.approval import ApprovalRecord, ApprovalRuntime, DEFAULT_APPROVAL_RUNTIME

__all__ = ["ApprovalRecord", "ApprovalRuntime", "DEFAULT_APPROVAL_RUNTIME"]
