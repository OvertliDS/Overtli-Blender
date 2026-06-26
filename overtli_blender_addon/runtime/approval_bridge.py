"""Lazy bridge from packaged addon code to the shared approval runtime."""

from __future__ import annotations


def get_default_approval_runtime():
    from overtli_blender.runtime.approval import DEFAULT_APPROVAL_RUNTIME

    return DEFAULT_APPROVAL_RUNTIME


__all__ = ["get_default_approval_runtime"]
