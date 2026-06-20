from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE_TEXT = (ROOT / "scripts" / "smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_runtime_smoke_script_exists() -> None:
    assert (ROOT / "scripts" / "smoke_blender_addon_socket.py").is_file()


def test_runtime_smoke_script_uses_standard_library_only() -> None:
    assert "import argparse" in SMOKE_TEXT
    assert "import json" in SMOKE_TEXT
    assert "import socket" in SMOKE_TEXT
    assert "import sys" in SMOKE_TEXT
    assert "import time" in SMOKE_TEXT
    assert "import bpy" not in SMOKE_TEXT
    assert "subprocess" not in SMOKE_TEXT
    assert "os.system" not in SMOKE_TEXT
    assert "shutil.rmtree" not in SMOKE_TEXT


def test_runtime_smoke_script_has_expected_defaults_and_entrypoint() -> None:
    for text in [
        'DEFAULT_HOST = "localhost"',
        "DEFAULT_PORT = 9876",
        "def main(",
        "return 1",
        "return 0",
        "raise SystemExit(main())",
    ]:
        assert text in SMOKE_TEXT


def test_runtime_smoke_script_mentions_expected_commands_and_flags() -> None:
    for text in [
        "get_scene_info",
        "get_shared_context",
        "get_operation_history",
        "list_object_handles",
        "list_material_handles",
        "list_context_scripts",
        "execute_code",
        "get_geometry_nodes_status",
        "get_safety_status",
        "--include-screenshot",
        "--include-script-registry",
        "--include-provider-status",
        "--include-safety-status",
        "--include-geometry-nodes-status",
        "--include-code-execution",
        "--expect-strict-blocks",
    ]:
        assert text in SMOKE_TEXT
