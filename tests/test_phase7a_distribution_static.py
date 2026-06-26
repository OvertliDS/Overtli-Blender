from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_addon_zip_builder_public_safe_contract() -> None:
    text = (ROOT / "scripts" / "build_addon_zip.py").read_text(encoding="utf-8")
    for needle in [
        "PACKAGE_ROOT",
        "overtli_blender_addon_",
        ".overtli_blender",
        "release",
        "addon_zip",
        "included_files",
        "zip_sha256",
        "source_commit",
        "memory_bank",
        "AGENTS.md",
        ".env",
        "--overwrite",
    ]:
        assert needle in text
    assert "publish" not in text.lower()
    assert "upload" not in text.lower()


def test_python_package_builder_builds_without_publish_or_upload() -> None:
    text = (ROOT / "scripts" / "build_python_package.py").read_text(encoding="utf-8")
    for needle in [
        "python -m pip install -e \".[dev]\"",
        "python -m build",
        "dist",
        "overtli[_-]blender",
        "overtli_blender/",
        "--allow-missing-build",
    ]:
        assert needle in text
    assert "twine" not in text
    assert "publish" not in text.lower()
    assert "upload" not in text.lower()


def test_diagnostic_bundle_excludes_private_generated_inputs() -> None:
    text = (ROOT / "scripts" / "export_diagnostic_bundle.py").read_text(encoding="utf-8")
    for needle in [
        "manifest.json",
        "git_status.txt",
        "python_env.txt",
        "pyproject_summary.json",
        "test_summary.json",
        "smoke_script_summary.json",
        "public_docs_summary.json",
        "file_manifest_public.json",
        "privacy_exclusion_report.json",
        "memory_bank",
        "blender_python_reference_5_1_md",
        "AGENTS.md",
        ".env",
    ]:
        assert needle in text


def test_gitignore_keeps_release_and_diagnostic_artifacts_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for needle in [".overtli_blender/", "dist/", "build/", "*.zip", "memory_bank/"]:
        assert needle in gitignore
