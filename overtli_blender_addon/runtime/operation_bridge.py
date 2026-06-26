"""Lazy operation runtime bridge."""

from __future__ import annotations


def get_default_operation_runtime():
    from overtli_blender.runtime.operations import DEFAULT_OPERATION_RUNTIME

    return DEFAULT_OPERATION_RUNTIME
