from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_remains_non_publishing_and_blender_gui_free() -> None:
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "contents: read" in text
    assert ("sec" + "rets.") not in text
    assert "twine" not in text
    assert "publish" not in text.lower()
    assert "blender --background" not in text.lower()
    assert "bpy" not in text
    assert "pytest" in text
    assert "release_check.py --fast" in text
    assert "docs_lockdown_check.py --json" in text
    assert "addon_modularity_check.py --json" in text
    assert "import_boundary_check.py --json" in text
