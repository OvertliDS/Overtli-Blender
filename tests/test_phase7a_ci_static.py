from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_exists_and_uses_non_blender_static_gates() -> None:
    ci = ROOT / ".github" / "workflows" / "ci.yml"
    assert ci.is_file()
    text = ci.read_text(encoding="utf-8")
    for needle in [
        "contents: read",
        "static-tests",
        "package-check",
        "privacy-check",
        "python -m pip install -e .",
        "python -m compileall addon.py main.py src scripts tests",
        "python -m pytest",
        "import overtli_blender",
        "python scripts/release_check.py --fast --json",
    ]:
        assert needle in text
    assert "blender" not in text.lower() or "overtli_blender" in text
    for forbidden in ["gh-action-pypi-publish", "twine upload", "release.yml", "secrets.", "memory_bank"]:
        assert forbidden not in text


def test_old_publish_workflow_removed() -> None:
    assert not (ROOT / ".github" / "workflows" / "publish-pypi.yml").exists()
