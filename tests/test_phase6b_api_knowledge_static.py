from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")


def test_api_knowledge_uses_local_docs_mirror_and_public_safe_index_paths() -> None:
    for text in [
        "blender_python_reference_5_1_md",
        "api_index.json",
        "source_manifest.json",
        "build_report.json",
        "AddonPreferences",
        "Operator",
        "Panel",
        "register_class",
        "unregister_class",
        "addon_install",
        "addon_enable",
        "addon_disable",
        "addon_remove",
    ]:
        assert text in ADDON_TEXT
