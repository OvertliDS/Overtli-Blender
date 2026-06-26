from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_artifact_docs_and_gitignore_exclude_generated_outputs() -> None:
    docs = (ROOT / "docs" / "release_artifacts.md").read_text(encoding="utf-8")
    for marker in [
        "build_addon_zip.py --mode package --verify --json",
        "build_python_package.py",
        "export_diagnostic_bundle.py",
        "final_release_handoff.py --json",
        "memory_bank/",
        "AGENTS.md",
    ]:
        assert marker in docs

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for marker in [".overtli_blender/", "memory_bank/", "dist/", "build/", "*.zip", "AIReview.config.json"]:
        assert marker in gitignore
