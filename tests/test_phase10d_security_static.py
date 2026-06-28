from __future__ import annotations


def test_browser_profile_exposes_high_risk_tools_under_full_profile() -> None:
    from overtli_blender.server import create_mcp_server

    server = create_mcp_server(profile="browser_full_standard", remote_safety="browser_standard")
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    for visible in [
        "execute_code",
        "execute_blender_code",
        "register_context_script",
        "execute_context_script",
        "run_verified_snippet_smoke",
        "run_skill_pack",
        "execute_approved_addon_operator",
        "install_local_addon",
        "enable_blender_addon",
        "disable_blender_addon",
        "remove_blender_addon",
    ]:
        assert visible in tools
    assert "execute_approved_file_delete" in tools
    assert "download_polyhaven_asset" in tools
