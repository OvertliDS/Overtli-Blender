from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def test_snippet_library_is_metadata_and_validation_first() -> None:
    for text in [
        "PHASE6B_BAD_SNIPPET_RE",
        "dangerous_calls",
        "source_evidence",
        "safety_classification",
        "smoke_status",
        "run_verified_snippet_smoke requires confirm=True",
        '"executed": False',
    ]:
        assert text in ADDON_TEXT
