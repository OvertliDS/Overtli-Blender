from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def test_review_package_has_privacy_exclusion_reports() -> None:
    for text in [
        "manifest.json",
        "file_manifest.json",
        "exclusion_report.json",
        "memory_bank_excluded",
        "docs_mirror_excluded",
        "env_excluded",
        "blender_python_reference_5_1_md",
    ]:
        assert text in ADDON_TEXT
