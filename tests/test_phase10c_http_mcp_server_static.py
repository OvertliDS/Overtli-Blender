from __future__ import annotations


def test_server_status_reports_streamable_http_mcp_url() -> None:
    from overtli_blender.server import _parse_args, build_server_status

    args = _parse_args(["--transport", "http", "--host", "127.0.0.1", "--port", "2091", "--profile", "chatgpt_browser_default"])
    status = build_server_status(args)
    assert status["transport"] == "streamable-http"
    assert status["mcp_url"] == "http://127.0.0.1:2091/mcp"
    assert status["health_url"] == "http://127.0.0.1:2091/health"


def test_chatgpt_profile_filters_http_visible_tools() -> None:
    from overtli_blender.server import create_mcp_server

    server = create_mcp_server(profile="chatgpt_browser_default", remote_safety="remote_browser_safe")
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    assert len(tools) <= 100
    assert "search_tools" in tools
    assert "get_tool_spec" in tools
    assert "execute_code" not in tools
    assert "execute_approved_addon_operator" not in tools
    assert "download_polyhaven_asset" not in tools
