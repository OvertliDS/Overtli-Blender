from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_packaged_addon_scaffold_exists() -> None:
    for rel in [
        "overtli_blender_addon/__init__.py",
        "overtli_blender_addon/registration.py",
        "overtli_blender_addon/preferences.py",
        "overtli_blender_addon/runtime/dispatcher.py",
        "overtli_blender_addon/runtime/command_registry_bridge.py",
        "overtli_blender_addon/runtime/approval_bridge.py",
        "overtli_blender_addon/services/README.md",
    ]:
        assert (ROOT / rel).is_file()


def test_build_script_mentions_packaged_layout() -> None:
    text = (ROOT / "scripts" / "build_addon_zip.py").read_text(encoding="utf-8")
    assert "--layout" in text
    assert "experimental_package_layout" in text
    assert "overtli_blender_addon" in text
