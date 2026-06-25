from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")


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
