"""Lazy operation logging bridge."""

from __future__ import annotations


def get_log_status():
    from overtli_blender.runtime.logging import get_log_status as _get_log_status

    return _get_log_status()
