from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER_TEXT = (ROOT / "src/blender_mcp/server.py").read_text(encoding="utf-8")
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
CONTEXT_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/context_tools.py").read_text(encoding="utf-8")
OBSERVATION_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/observation_tools.py").read_text(encoding="utf-8")
SCREENSHOT_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/screenshot_tools.py").read_text(encoding="utf-8")
SCRIPT_REGISTRY_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/script_registry_tools.py").read_text(encoding="utf-8")
PROVIDER_STATUS_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/provider_status_tools.py").read_text(encoding="utf-8")
POLYHAVEN_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/polyhaven_tools.py").read_text(encoding="utf-8")
SKETCHFAB_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/sketchfab_tools.py").read_text(encoding="utf-8")
HYPER3D_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/hyper3d_tools.py").read_text(encoding="utf-8")
GEOMETRY_NODES_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/geometry_nodes_tools.py").read_text(encoding="utf-8")


def _has_def(source: str, name: str) -> bool:
    pattern = rf"^\s*def\s+{re.escape(name)}\s*\("
    return re.search(pattern, source, flags=re.MULTILINE) is not None


def test_server_static_surface_includes_expected_wrappers() -> None:
    expected = [
        "execute_blender_code",
    ]

    missing = [name for name in expected if not _has_def(SERVER_TEXT, name)]
    assert missing == [], f"Missing server wrappers: {missing}"


def test_observation_tool_module_includes_extracted_wrappers() -> None:
    observation_text = (ROOT / "src/blender_mcp/tools/observation_tools.py").read_text(encoding="utf-8")
    expected = [
        "get_scene_info",
        "get_object_info",
    ]

    missing = [name for name in expected if f"def {name}(" not in observation_text]
    assert missing == [], f"Missing extracted observation tools: {missing}"


def test_screenshot_tool_module_includes_extracted_wrapper() -> None:
    screenshot_text = (ROOT / "src/blender_mcp/tools/screenshot_tools.py").read_text(encoding="utf-8")
    assert "def get_viewport_screenshot(" in screenshot_text


def test_script_registry_tool_module_includes_extracted_wrappers() -> None:
    script_registry_text = (ROOT / "src/blender_mcp/tools/script_registry_tools.py").read_text(encoding="utf-8")
    expected = [
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "clear_context_scripts",
    ]

    missing = [name for name in expected if f"def {name}(" not in script_registry_text]
    assert missing == [], f"Missing extracted script registry tools: {missing}"


def test_provider_status_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
    ]

    missing = [name for name in expected if f"def {name}(" not in PROVIDER_STATUS_TOOLS_TEXT]
    assert missing == [], f"Missing extracted provider status tools: {missing}"


def test_polyhaven_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "get_polyhaven_categories",
        "search_polyhaven_assets",
        "download_polyhaven_asset",
        "set_texture",
    ]

    missing = [name for name in expected if f"def {name}(" not in POLYHAVEN_TOOLS_TEXT]
    assert missing == [], f"Missing extracted PolyHaven tools: {missing}"


def test_sketchfab_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "search_sketchfab_models",
        "download_sketchfab_model",
    ]

    missing = [name for name in expected if f"def {name}(" not in SKETCHFAB_TOOLS_TEXT]
    assert missing == [], f"Missing extracted Sketchfab tools: {missing}"


def test_hyper3d_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "generate_hyper3d_model_via_text",
        "generate_hyper3d_model_via_images",
        "poll_rodin_job_status",
        "import_generated_asset",
    ]

    missing = [name for name in expected if f"def {name}(" not in HYPER3D_TOOLS_TEXT]
    assert missing == [], f"Missing extracted Hyper3D tools: {missing}"


def test_geometry_nodes_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "complete_geometry_node",
        "get_geometry_nodes_status",
    ]

    missing = [name for name in expected if f"def {name}(" not in GEOMETRY_NODES_TOOLS_TEXT]
    assert missing == [], f"Missing extracted geometry nodes tools: {missing}"


def test_context_tool_module_includes_extracted_wrappers() -> None:
    expected = [
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
    ]

    missing = [name for name in expected if f"def {name}(" not in CONTEXT_TOOLS_TEXT]
    assert missing == [], f"Missing extracted context tools: {missing}"


def test_addon_static_surface_includes_expected_commands() -> None:
    expected = [
        "get_scene_info",
        "get_object_info",
        "get_viewport_screenshot",
        "execute_code",
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
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
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "clear_context_scripts",
    ]

    missing = [name for name in expected if f'"{name}":' not in ADDON_TEXT and f"'{name}':" not in ADDON_TEXT]
    assert missing == [], f"Missing addon command strings: {missing}"


def test_documented_mapping_differences_are_present_in_source() -> None:
    assert "execute_blender_code" in SERVER_TEXT
    assert '"execute_code": self.execute_code' in ADDON_TEXT
    assert "create_rodin_job" in ADDON_TEXT
    assert "generate_hyper3d_model_via_text" in SERVER_TEXT
    assert "generate_hyper3d_model_via_images" in SERVER_TEXT
    assert "blendermcp_use_polyhaven" in ADDON_TEXT
