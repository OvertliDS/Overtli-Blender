from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

SERVER_TEXT = (ROOT / "src/blender_mcp/server.py").read_text(encoding="utf-8")
CONTEXT_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/context_tools.py").read_text(encoding="utf-8")
OBSERVATION_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/observation_tools.py").read_text(encoding="utf-8")
SCREENSHOT_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/screenshot_tools.py").read_text(encoding="utf-8")
SCRIPT_REGISTRY_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/script_registry_tools.py").read_text(encoding="utf-8")
CODE_EXECUTION_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/code_execution_tools.py").read_text(encoding="utf-8")
REGISTRY_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/registry.py").read_text(encoding="utf-8")
PROVIDER_STATUS_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/provider_status_tools.py").read_text(encoding="utf-8")
POLYHAVEN_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/polyhaven_tools.py").read_text(encoding="utf-8")
SKETCHFAB_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/sketchfab_tools.py").read_text(encoding="utf-8")
HYPER3D_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/hyper3d_tools.py").read_text(encoding="utf-8")
GEOMETRY_NODES_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/geometry_nodes_tools.py").read_text(encoding="utf-8")


def _has_def(source: str, name: str) -> bool:
    pattern = rf"^\s*def\s+{re.escape(name)}\s*\("
    return re.search(pattern, source, flags=re.MULTILINE) is not None


def test_server_config_imports_without_mcp_or_blender() -> None:
    importlib.import_module("blender_mcp.server_config")


def test_transport_imports_without_mcp_or_blender() -> None:
    importlib.import_module("blender_mcp.transport")


def test_connection_imports_without_mcp_or_blender() -> None:
    importlib.import_module("blender_mcp.connection")


def test_default_server_config_matches_baseline() -> None:
    from blender_mcp.server_config import DEFAULT_HOST, DEFAULT_PORT, BlenderServerConfig, get_default_config

    config = get_default_config()
    assert DEFAULT_HOST == "localhost"
    assert DEFAULT_PORT == 9876
    assert config.host == "localhost"
    assert config.port == 9876
    assert config.timeout_seconds == 15.0
    assert BlenderServerConfig().host == "localhost"
    assert BlenderServerConfig().port == 9876


def test_encode_and_decode_round_trip_json_bytes() -> None:
    from blender_mcp.transport import decode_response, encode_command

    payload = {"type": "ping", "params": {"value": 1}}
    encoded = encode_command(payload)
    assert isinstance(encoded, bytes)
    assert encoded.decode("utf-8")
    assert decode_response(encoded) == payload


def test_decode_response_rejects_invalid_json() -> None:
    from blender_mcp.transport import decode_response

    try:
        decode_response(b"not json")
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("Expected JSONDecodeError for invalid JSON bytes")


def test_blender_connection_can_be_instantiated_without_connecting() -> None:
    from blender_mcp.connection import BlenderConnection

    connection = BlenderConnection(host="localhost", port=9876)
    assert connection.host == "localhost"
    assert connection.port == 9876
    assert connection.sock is None


def test_server_py_still_defines_key_tool_wrappers() -> None:
    assert not _has_def(SERVER_TEXT, "execute_blender_code")


def test_code_execution_tools_py_contains_extracted_tool_name() -> None:
    assert _has_def(CODE_EXECUTION_TOOLS_TEXT, "execute_blender_code")


def test_registry_py_contains_all_registration_helpers() -> None:
    assert _has_def(REGISTRY_TOOLS_TEXT, "register_all_tools")
    for name in [
        "register_context_tools",
        "register_observation_tools",
        "register_screenshot_tools",
        "register_script_registry_tools",
        "register_provider_status_tools",
        "register_polyhaven_tools",
        "register_sketchfab_tools",
        "register_hyper3d_tools",
        "register_geometry_nodes_tools",
        "register_code_execution_tools",
    ]:
        assert name in REGISTRY_TOOLS_TEXT


def test_context_tools_py_contains_extracted_tool_names() -> None:
    for name in [
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
    ]:
        assert _has_def(CONTEXT_TOOLS_TEXT, name), f"Missing extracted tool: {name}"


def test_observation_tools_py_contains_extracted_tool_names() -> None:
    for name in [
        "get_scene_info",
        "get_object_info",
    ]:
        assert _has_def(OBSERVATION_TOOLS_TEXT, name), f"Missing extracted tool: {name}"


def test_screenshot_tools_py_contains_extracted_tool_name() -> None:
    assert _has_def(SCREENSHOT_TOOLS_TEXT, "get_viewport_screenshot")


def test_script_registry_tools_py_contains_extracted_tool_names() -> None:
    for name in [
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "clear_context_scripts",
    ]:
        assert _has_def(SCRIPT_REGISTRY_TOOLS_TEXT, name), f"Missing extracted tool: {name}"


def test_provider_status_tools_py_contains_extracted_tool_names() -> None:
    for name in [
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
    ]:
        assert _has_def(PROVIDER_STATUS_TOOLS_TEXT, name), f"Missing extracted tool: {name}"


def test_polyhaven_tools_py_contains_extracted_tool_names() -> None:
    for name in [
        "get_polyhaven_categories",
        "search_polyhaven_assets",
        "download_polyhaven_asset",
        "set_texture",
    ]:
        assert _has_def(POLYHAVEN_TOOLS_TEXT, name), f"Missing extracted tool: {name}"


def test_sketchfab_tools_py_contains_extracted_tool_names() -> None:
    for name in [
        "search_sketchfab_models",
        "download_sketchfab_model",
    ]:
        assert _has_def(SKETCHFAB_TOOLS_TEXT, name), f"Missing extracted tool: {name}"


def test_hyper3d_tools_py_contains_extracted_tool_names() -> None:
    for name in [
        "generate_hyper3d_model_via_text",
        "generate_hyper3d_model_via_images",
        "poll_rodin_job_status",
        "import_generated_asset",
    ]:
        assert _has_def(HYPER3D_TOOLS_TEXT, name), f"Missing extracted tool: {name}"


def test_geometry_nodes_tools_py_contains_extracted_tool_names() -> None:
    for name in [
        "complete_geometry_node",
        "get_geometry_nodes_status",
    ]:
        assert _has_def(GEOMETRY_NODES_TOOLS_TEXT, name), f"Missing extracted tool: {name}"


def test_addon_py_is_unmodified_in_worktree() -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "addon.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
