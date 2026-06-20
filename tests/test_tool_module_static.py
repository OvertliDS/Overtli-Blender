from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/context_tools.py").read_text(encoding="utf-8")
OBSERVATION_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/observation_tools.py").read_text(encoding="utf-8")
SCREENSHOT_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/screenshot_tools.py").read_text(encoding="utf-8")
SCRIPT_REGISTRY_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/script_registry_tools.py").read_text(encoding="utf-8")
CODE_EXECUTION_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/code_execution_tools.py").read_text(encoding="utf-8")
REGISTRY_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/registry.py").read_text(encoding="utf-8")
SAFETY_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/safety_tools.py").read_text(encoding="utf-8")
PROVIDER_STATUS_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/provider_status_tools.py").read_text(encoding="utf-8")
POLYHAVEN_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/polyhaven_tools.py").read_text(encoding="utf-8")
SKETCHFAB_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/sketchfab_tools.py").read_text(encoding="utf-8")
HYPER3D_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/hyper3d_tools.py").read_text(encoding="utf-8")
GEOMETRY_NODES_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/geometry_nodes_tools.py").read_text(encoding="utf-8")
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


def test_observation_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/observation_tools.py").exists()
    assert "def register_observation_tools" in OBSERVATION_TOOLS_TEXT


def test_observation_tools_contains_expected_tool_names() -> None:
    for name in [
        "get_scene_info",
        "get_object_info",
    ]:
        assert f"def {name}(" in OBSERVATION_TOOLS_TEXT


def test_screenshot_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/screenshot_tools.py").exists()
    assert "def register_screenshot_tools" in SCREENSHOT_TOOLS_TEXT


def test_screenshot_tools_contains_expected_tool_name() -> None:
    assert "def get_viewport_screenshot(" in SCREENSHOT_TOOLS_TEXT


def test_script_registry_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/script_registry_tools.py").exists()
    assert "def register_script_registry_tools" in SCRIPT_REGISTRY_TOOLS_TEXT


def test_script_registry_tools_contains_expected_tool_names() -> None:
    for name in [
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "clear_context_scripts",
    ]:
        assert f"def {name}(" in SCRIPT_REGISTRY_TOOLS_TEXT


def test_code_execution_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/code_execution_tools.py").exists()
    assert "def register_code_execution_tools" in CODE_EXECUTION_TOOLS_TEXT


def test_code_execution_tools_contains_expected_tool_name() -> None:
    assert "def execute_blender_code(" in CODE_EXECUTION_TOOLS_TEXT
    assert '"execute_code"' in CODE_EXECUTION_TOOLS_TEXT


def test_registry_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/registry.py").exists()
    assert "def register_all_tools" in REGISTRY_TOOLS_TEXT


def test_registry_module_references_all_tool_registration_helpers() -> None:
    for name in [
        "register_context_tools",
        "register_observation_tools",
        "register_screenshot_tools",
        "register_script_registry_tools",
        "register_provider_status_tools",
        "register_safety_tools",
        "register_polyhaven_tools",
        "register_sketchfab_tools",
        "register_hyper3d_tools",
        "register_geometry_nodes_tools",
        "register_code_execution_tools",
    ]:
        assert name in REGISTRY_TOOLS_TEXT


def test_provider_status_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/provider_status_tools.py").exists()
    assert "def register_provider_status_tools" in PROVIDER_STATUS_TOOLS_TEXT


def test_provider_status_tools_contains_expected_tool_names() -> None:
    for name in [
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
    ]:
        assert f"def {name}(" in PROVIDER_STATUS_TOOLS_TEXT


def test_safety_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/safety_tools.py").exists()
    assert "def register_safety_tools" in SAFETY_TOOLS_TEXT


def test_safety_tools_contains_expected_tool_name() -> None:
    assert "def get_safety_status(" in SAFETY_TOOLS_TEXT


def test_polyhaven_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/polyhaven_tools.py").exists()
    assert "def register_polyhaven_tools" in POLYHAVEN_TOOLS_TEXT


def test_polyhaven_tools_contains_expected_tool_names() -> None:
    for name in [
        "get_polyhaven_categories",
        "search_polyhaven_assets",
        "download_polyhaven_asset",
        "set_texture",
    ]:
        assert f"def {name}(" in POLYHAVEN_TOOLS_TEXT


def test_sketchfab_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/sketchfab_tools.py").exists()
    assert "def register_sketchfab_tools" in SKETCHFAB_TOOLS_TEXT


def test_sketchfab_tools_contains_expected_tool_names() -> None:
    for name in [
        "search_sketchfab_models",
        "download_sketchfab_model",
    ]:
        assert f"def {name}(" in SKETCHFAB_TOOLS_TEXT


def test_hyper3d_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/hyper3d_tools.py").exists()
    assert "def register_hyper3d_tools" in HYPER3D_TOOLS_TEXT


def test_hyper3d_tools_contains_expected_tool_names() -> None:
    for name in [
        "generate_hyper3d_model_via_text",
        "generate_hyper3d_model_via_images",
        "poll_rodin_job_status",
        "import_generated_asset",
    ]:
        assert f"def {name}(" in HYPER3D_TOOLS_TEXT


def test_geometry_nodes_tools_module_exists_and_registers_tools() -> None:
    assert (ROOT / "src/blender_mcp/tools/geometry_nodes_tools.py").exists()
    assert "def register_geometry_nodes_tools" in GEOMETRY_NODES_TOOLS_TEXT


def test_geometry_nodes_tools_contains_expected_tool_names() -> None:
    for name in [
        "complete_geometry_node",
        "get_geometry_nodes_status",
    ]:
        assert f"def {name}(" in GEOMETRY_NODES_TOOLS_TEXT


def test_server_imports_and_registers_context_tools() -> None:
    assert "from blender_mcp.tools.registry import register_all_tools" in SERVER_TEXT
    assert "register_all_tools(mcp, get_blender_connection, image_type=Image)" in SERVER_TEXT


def test_server_no_longer_defines_execute_blender_code() -> None:
    assert "def execute_blender_code(" not in SERVER_TEXT


def test_server_still_contains_composition_root_bits() -> None:
    for name in [
        "FastMCP",
        "get_blender_connection",
        "main",
    ]:
        assert name in SERVER_TEXT


def test_addon_command_strings_are_still_present() -> None:
    for name in [
        "get_scene_info",
        "get_object_info",
        "get_viewport_screenshot",
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
        "execute_code",
        "get_polyhaven_categories",
        "search_polyhaven_assets",
        "download_polyhaven_asset",
        "set_texture",
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
        "search_sketchfab_models",
        "download_sketchfab_model",
        "poll_rodin_job_status",
        "import_generated_asset",
        "complete_geometry_node",
        "get_geometry_nodes_status",
    ]:
        assert f'"{name}":' in ADDON_TEXT or f"'{name}':" in ADDON_TEXT
