from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/context_tools.py").read_text(encoding="utf-8")
SERVER_TEXT = (ROOT / "src/blender_mcp/server.py").read_text(encoding="utf-8")
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")


def test_context_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/context_tools.py").exists()
    assert "def register_context_tools" in CONTEXT_TOOLS_TEXT


def test_context_tools_contains_expected_tool_names() -> None:
    for name in [
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
    ]:
        assert f"def {name}(" in CONTEXT_TOOLS_TEXT


def test_server_imports_and_registers_context_tools() -> None:
    assert "from blender_mcp.tools.context_tools import register_context_tools" in SERVER_TEXT
    assert "register_context_tools(mcp, get_blender_connection)" in SERVER_TEXT


def test_server_still_contains_high_risk_tool_definitions() -> None:
    for name in [
        "execute_blender_code",
        "complete_geometry_node",
        "download_polyhaven_asset",
        "generate_hyper3d_model_via_text",
    ]:
        assert f"def {name}(" in SERVER_TEXT


def test_addon_command_strings_are_still_present() -> None:
    for name in [
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
    ]:
        assert f'"{name}":' in ADDON_TEXT or f"'{name}':" in ADDON_TEXT

