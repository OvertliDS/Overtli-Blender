from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_addon_zip_builder_is_package_only_and_allowlisted() -> None:
    text = (ROOT / "scripts" / "build_addon_zip.py").read_text(encoding="utf-8")
    for marker in [
        "PACKAGE_ROOT",
        "iter_package_files",
        "iter_shared_runtime_files",
        "EXCLUDED_PATTERNS",
        "validate_zip",
        "included_files",
        "file_hashes",
        "root_entries",
        "--mode",
        "--verify",
        "--list",
        "--json",
    ]:
        assert marker in text
    assert "legacy-shim" not in text
    assert "iter_legacy_shim_files" not in text


def test_zip_validation_rejects_private_or_generated_inputs() -> None:
    text = (ROOT / "scripts" / "build_addon_zip.py").read_text(encoding="utf-8")
    for marker in [
        "memory_bank/",
        ".overtli_blender/",
        "tests/",
        "scripts/",
        "AGENTS.md",
        ".env",
        "blender_python_reference_5_1_md/",
        "AIReview.config.json",
    ]:
        assert marker in text
