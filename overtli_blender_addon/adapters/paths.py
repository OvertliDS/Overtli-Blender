"""Path adapter helpers for Blender and non-Blender validation."""

from __future__ import annotations

from pathlib import Path


def addon_package_root() -> Path:
    return Path(__file__).resolve().parents[1]
