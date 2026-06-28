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
    "create_collection",
    "move_objects_to_collection",
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
    assert "execute_code" not in tools
    assert "execute_blender_code" not in tools
    assert "download_polyhaven_asset" not in tools
    assert "execute_approved_file_delete" not in tools
    assert "execute_approved_addon_operator" not in tools


def test_browser_standard_permission_profile_allows_safe_writes_but_blocks_dangerous_caps() -> None:
    from overtli_blender.runtime.capabilities import PROFILE_CAPABILITIES

    browser = PROFILE_CAPABILITIES["browser_standard"]
    assert PROFILE_CAPABILITIES["remote_browser_safe"] == browser
    assert {"scene.read", "scene.write", "filesystem.project.write", "product.ux"} <= browser
    assert not {"raw_python", "network.providers", "filesystem.delete", "filesystem.external.write", "addon.manage", "addon.execute", "external_process"}.intersection(browser)
