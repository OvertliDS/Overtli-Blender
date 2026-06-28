from __future__ import annotations


def test_browser_profile_keeps_dangerous_tools_not_default_visible() -> None:
    from overtli_blender.server import create_mcp_server

    server = create_mcp_server(profile="browser_full_standard", remote_safety="browser_standard")
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    for hidden in [
        "execute_blender_code",
        "download_polyhaven_asset",
        "delete_objects",
        "execute_approved_file_delete",
        "run_verified_snippet_smoke",
        "execute_approved_addon_operator",
        "install_local_addon",
        "enable_blender_addon",
        "disable_blender_addon",
        "remove_blender_addon",
    ]:
        assert hidden not in tools
