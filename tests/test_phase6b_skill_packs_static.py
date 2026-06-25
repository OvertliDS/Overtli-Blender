from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")


def test_skill_packs_are_local_manifest_based_and_confirm_gated_for_run_delete() -> None:
    for text in [
        "skill_pack.json",
        "run_requires_confirm",
        "run_skill_pack requires confirm=True",
        "delete_skill_packs requires confirm=True",
        "blocked or unknown command",
    ]:
        assert text in ADDON_TEXT
