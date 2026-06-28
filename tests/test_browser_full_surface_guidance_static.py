from __future__ import annotations


def test_browser_full_standard_equals_full_source_mcp_surface() -> None:
    from overtli_blender.server import create_mcp_server

    full_server = create_mcp_server(profile=None, remote_safety=None)
    browser_server = create_mcp_server(profile="browser_full_standard", remote_safety="browser_standard")
    full_tools = set(full_server._tool_manager._tools)  # type: ignore[attr-defined]
    browser_tools = set(browser_server._tool_manager._tools)  # type: ignore[attr-defined]

    assert browser_tools == full_tools
    assert {"execute_code", "execute_blender_code", "register_context_script", "execute_context_script", "run_skill_pack"} <= browser_tools


def test_browser_standard_capabilities_cover_every_known_capability() -> None:
    from overtli_blender.runtime.capabilities import CAPABILITIES, PROFILE_CAPABILITIES

    assert PROFILE_CAPABILITIES["browser_standard"] == set(CAPABILITIES)
    assert PROFILE_CAPABILITIES["remote_browser_safe"] == set(CAPABILITIES)


def test_mcp_instructions_inject_tool_workflow_guidance() -> None:
    from overtli_blender.server import build_mcp_instructions

    instructions = build_mcp_instructions()
    for phrase in [
        "get_scene_info",
        "create_scene_plan",
        "create_verification_snapshot",
        "discover_tool_packs",
        "search_tools",
        "get_tool_spec",
        "search_bundled_skill_packs",
        "execute_code",
        "register_context_script",
        "Spatial discipline",
        "approved roots",
        "approval mode",
    ]:
        assert phrase in instructions


def test_bundled_skill_packs_include_full_blender_workflow_guides() -> None:
    from overtli_blender.runtime.skill_pack_library import BUNDLED_SKILL_PACKS

    required = {
        "blender_scene_planning",
        "spatial_snap_transform",
        "scripted_blender_workflows",
        "workspace_project_safety",
        "cleanup_snapshot_recovery",
    }
    assert required <= set(BUNDLED_SKILL_PACKS)
    scripted = BUNDLED_SKILL_PACKS["scripted_blender_workflows"].to_dict()
    assert "execute_code" in scripted["execution_stages"]
    assert "structured MCP tools first" in " ".join(scripted["method_rules"])
    spatial = BUNDLED_SKILL_PACKS["spatial_snap_transform"].to_dict()
    assert "validate_ground_contact" in spatial["required_inspection"]


def test_context_scripts_use_static_safety_scanner() -> None:
    from tests._addon_source import ADDON_PACKAGE_SOURCE

    assert "class ScriptRegistryService" in ADDON_PACKAGE_SOURCE
    assert "CONTEXT_SCRIPT_STATIC_SCAN_BLOCK" in ADDON_PACKAGE_SOURCE
    assert "Context script registration blocked by static safety scanner" in ADDON_PACKAGE_SOURCE
    assert "Context script execution blocked by static safety scanner" in ADDON_PACKAGE_SOURCE
