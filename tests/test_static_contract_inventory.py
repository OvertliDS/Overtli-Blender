from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER_TEXT = (ROOT / "src/blender_mcp/server.py").read_text(encoding="utf-8")
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
CONTEXT_TOOLS_TEXT = (ROOT / "src/blender_mcp/tools/context_tools.py").read_text(encoding="utf-8")


def _has_def(source: str, name: str) -> bool:
    pattern = rf"^\s*def\s+{re.escape(name)}\s*\("
    return re.search(pattern, source, flags=re.MULTILINE) is not None


def test_server_static_surface_includes_expected_wrappers() -> None:
    expected = [
        "get_scene_info",
        "get_object_info",
        "get_viewport_screenshot",
        "execute_blender_code",
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
        "complete_geometry_node",
        "get_geometry_nodes_status",
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
    ]

    missing = [name for name in expected if not _has_def(SERVER_TEXT, name)]
    assert missing == [], f"Missing server wrappers: {missing}"


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
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
        "get_shared_context",
        "clear_shared_context",
        "get_operation_history",
        "create_object_handle",
        "create_material_handle",
        "list_object_handles",
        "list_material_handles",
        "complete_geometry_node",
        "get_geometry_nodes_status",
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
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
