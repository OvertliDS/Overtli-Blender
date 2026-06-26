from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def test_skill_packs_are_local_manifest_based_and_confirm_gated_for_run_delete() -> None:
    for text in [
        "skill_pack.json",
        "run_requires_confirm",
        "run_skill_pack requires confirm=True",
        "delete_skill_packs requires confirm=True",
        "blocked or unknown command",
    ]:
        assert text in ADDON_TEXT
