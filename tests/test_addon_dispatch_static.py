from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
SERVER_TEXT = (ROOT / "src/blender_mcp/server.py").read_text(encoding="utf-8")


def test_addon_entrypoint_symbols_remain_present() -> None:
    for name in [
        "bl_info",
        "register",
        "unregister",
        "class BlenderMCPServer",
        "def _build_command_handlers(",
        "def _dispatch_command(",
    ]:
        assert name in ADDON_TEXT


def test_addon_command_inventory_is_stable() -> None:
    for name in [
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
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
        "get_polyhaven_categories",
        "search_polyhaven_assets",
        "download_polyhaven_asset",
        "set_texture",
        "create_rodin_job",
        "poll_rodin_job_status",
        "import_generated_asset",
        "search_sketchfab_models",
        "download_sketchfab_model",
        "complete_geometry_node",
        "get_geometry_nodes_status",
        "register_context_script",
        "execute_context_script",
        "list_context_scripts",
        "clear_context_scripts",
    ]:
        assert f'"{name}":' in ADDON_TEXT or f"'{name}':" in ADDON_TEXT


def test_addon_dispatch_logic_preserves_gating_and_unknown_command_behavior() -> None:
    for name in [
        "blendermcp_use_polyhaven",
        "blendermcp_use_hyper3d",
        "blendermcp_use_sketchfab",
        "Unknown command type",
        "handler = handlers.get(cmd_type)",
        "result = handler(**params)",
    ]:
        assert name in ADDON_TEXT


def test_addon_and_server_mapping_differences_remain_documented() -> None:
    assert '"execute_code": self.execute_code' in ADDON_TEXT
    assert "create_rodin_job" in ADDON_TEXT
    assert "execute_blender_code" not in ADDON_TEXT
    assert "def execute_blender_code(" not in ADDON_TEXT
    assert "def execute_blender_code(" not in SERVER_TEXT
