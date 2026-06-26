from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_addon_modularity_check_exists_and_enforces_thin_entrypoint() -> None:
    text = (ROOT / "scripts" / "addon_modularity_check.py").read_text(encoding="utf-8")
    for marker in [
        "TARGET_LINE_CAP = 300",
        "HARD_LINE_CAP = 500",
        "overtli_blender_addon",
        "runtime/socket_server.py",
        "runtime/dispatcher.py",
        "services/scene.py",
        "ui/panels.py",
        "FORBIDDEN_ENTRYPOINT_MARKERS",
        "--json",
    ]:
        assert marker in text


def test_addon_py_remains_thin_bootstrap() -> None:
    text = (ROOT / "addon.py").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 300
    assert "importlib.import_module(\"overtli_blender_addon\")" in text
    assert "class BlenderMCPServer" not in text
    assert "_build_command_handlers" not in text
