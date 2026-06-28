from __future__ import annotations


REQUIRED_BROWSER_TOOLS = {
    "prepare_operation",
    "approve_operation",
    "execute_approved_operation",
    "approve_and_execute_operation",
    "get_pending_approvals",
    "get_scene_info",
    "search_tools",
    "get_tool_spec",
    "get_runtime_dashboard",
    "create_primitive_object",
    "transform_object",
    "duplicate_object",
    "delete_objects",
    "clear_scene",
    "create_collection",
    "move_objects_to_collection",
    "delete_collection",
    "measure_object",
    "create_basic_material",
    "assign_material",
    "update_material_properties",
    "create_material_from_template",
    "apply_material_to_objects",
    "create_camera",
    "frame_camera_to_objects",
    "set_active_camera",
    "create_light",
    "create_lighting_setup",
    "update_light",
    "set_world_lighting",
    "create_verification_snapshot",
    "run_verified_edit_batch",
    "run_presentation_workflow_batch",
}

FULL_BROWSER_CORE_TOOLS = {
    "disable_blender_addon",
    "enable_blender_addon",
    "execute_approved_addon_operator",
    "execute_blender_code",
    "execute_code",
    "execute_context_script",
    "install_local_addon",
    "register_context_script",
    "remove_blender_addon",
    "run_skill_pack",
    "run_verified_snippet_smoke",
}


def test_browser_full_standard_profile_exposes_safe_mutation_tools() -> None:
    from overtli_blender.server import create_mcp_server
    from overtli_blender.runtime.tool_profiles import get_profile

    profile = get_profile("browser_full_standard")
    legacy = get_profile("chatgpt_browser_default")
    assert profile is not None
    assert legacy is not None
    assert legacy.to_dict() == profile.to_dict()
    assert profile.permission_profile == "browser_standard"

    server = create_mcp_server(profile="browser_full_standard", remote_safety="browser_standard")
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    assert not (REQUIRED_BROWSER_TOOLS - tools)
    assert FULL_BROWSER_CORE_TOOLS <= tools
    assert "download_polyhaven_asset" in tools
    assert "execute_approved_file_delete" in tools


def test_browser_full_standard_exposes_all_source_mcp_tools() -> None:
    from overtli_blender.server import create_mcp_server

    full_server = create_mcp_server(profile=None, remote_safety=None)
    browser_server = create_mcp_server(profile="browser_full_standard", remote_safety="browser_standard")
    all_tools = set(full_server._tool_manager._tools)  # type: ignore[attr-defined]
    browser_tools = set(browser_server._tool_manager._tools)  # type: ignore[attr-defined]

    assert FULL_BROWSER_CORE_TOOLS <= all_tools
    assert browser_tools == all_tools


def test_browser_tool_surface_matches_discovery_for_required_public_tools() -> None:
    from overtli_blender.runtime.tool_packs import search_tools
    from overtli_blender.server import create_mcp_server

    server = create_mcp_server(profile="browser_full_standard", remote_safety="browser_standard")
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    required_queries = {
        "clear_scene": "clear scene",
        "delete_objects": "delete objects",
        "delete_collection": "delete collection",
        "measure_object": "measure object dimension",
    }
    for expected_tool, query in required_queries.items():
        result = search_tools(query, limit=20)
        discovered = {tool["name"] for tool in result["results"]}
        assert expected_tool in discovered
        assert expected_tool in tools


def test_profiled_browser_search_only_returns_registered_callable_tools() -> None:
    import json

    from overtli_blender.server import create_mcp_server

    server = create_mcp_server(profile="browser_full_standard", remote_safety="browser_standard")
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    search_tool = server._tool_manager._tools["search_tools"]  # type: ignore[attr-defined]
    for query in ("clear scene", "delete objects", "delete collection", "measure dimension", "execute python"):
        result = json.loads(search_tool.fn(query))
        discovered = {tool["name"] for tool in result.get("results", [])}
        assert discovered <= tools
        assert result["active_tool_surface_contract"]


def test_browser_standard_permission_profile_allows_safe_writes_but_blocks_dangerous_caps() -> None:
    from overtli_blender.runtime.capabilities import PROFILE_CAPABILITIES

    browser = PROFILE_CAPABILITIES["browser_standard"]
    assert PROFILE_CAPABILITIES["remote_browser_safe"] == browser
    assert {"scene.read", "scene.write", "filesystem.project.write", "product.ux"} <= browser
    assert {"network.providers", "filesystem.delete", "raw_python", "filesystem.external.write", "addon.manage", "addon.execute", "external_process"} <= browser
