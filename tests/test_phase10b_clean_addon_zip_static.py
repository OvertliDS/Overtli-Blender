from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_clean_addon_zip_builder_rejects_root_bloat() -> None:
    text = (ROOT / "scripts" / "build_addon_zip.py").read_text(encoding="utf-8")
    for marker in [
        "iter_package_files",
        "iter_shared_runtime_files",
        "zip entry is outside addon package root",
        "memory_bank/",
        ".overtli_blender/",
        "tests/",
        "docs/",
        "scripts/",
        "tools/",
        "AGENTS.md",
        ".env",
        "AIReview.config.json",
        "release_candidate/",
        "final_handoff/",
        "review_packages/",
    ]:
        assert marker in text


def test_clean_addon_zip_required_files_are_package_files() -> None:
    text = (ROOT / "scripts" / "build_addon_zip.py").read_text(encoding="utf-8")
    for marker in [
        "overtli_blender_addon/__init__.py",
        "overtli_blender_addon/registration.py",
        "overtli_blender_addon/preferences.py",
        "overtli_blender_addon/runtime/dispatcher.py",
        "overtli_blender_addon/runtime/socket_server.py",
    ]:
        assert marker in text
