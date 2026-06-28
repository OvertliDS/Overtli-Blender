from __future__ import annotations


def test_server_status_reports_streamable_http_mcp_url() -> None:
    from overtli_blender.server import _parse_args, build_server_status

    args = _parse_args(["--transport", "http", "--host", "127.0.0.1", "--port", "2091", "--profile", "chatgpt_browser_default"])
    status = build_server_status(args)
    assert status["transport"] == "streamable-http"
    assert status["mcp_url"] == "http://127.0.0.1:2091/mcp"
    assert status["health_url"] == "http://127.0.0.1:2091/health"
    assert status["allow_public_tunnel_hosts"] is False
    assert status["dns_rebinding_protection"] is True


def test_server_status_can_allow_public_tunnel_hosts() -> None:
    from overtli_blender.server import _parse_args, build_server_status, create_mcp_server

    args = _parse_args(["--transport", "http", "--allow-public-tunnel-hosts"])
    status = build_server_status(args)
    server = create_mcp_server(allow_public_tunnel_hosts=status["allow_public_tunnel_hosts"])

    assert status["allow_public_tunnel_hosts"] is True
    assert status["dns_rebinding_protection"] is False
    assert server.settings.transport_security.enable_dns_rebinding_protection is False


def test_chatgpt_profile_filters_http_visible_tools() -> None:
    from overtli_blender.server import create_mcp_server

    server = create_mcp_server(profile="chatgpt_browser_default", remote_safety="remote_browser_safe")
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    assert len(tools) <= 160
    assert "search_tools" in tools
    assert "get_tool_spec" in tools
    assert "prepare_operation" in tools
    assert "approve_operation" in tools
    assert "execute_approved_operation" in tools
    assert "approve_and_execute_operation" in tools
    assert "create_primitive_object" in tools
    assert "create_basic_material" in tools
    assert "assign_material" in tools
    assert "create_camera" in tools
    assert "execute_code" not in tools
    assert "execute_approved_addon_operator" not in tools
    assert "download_polyhaven_asset" not in tools


def test_http_bridge_exposes_tunnel_client_oauth_discovery_routes() -> None:
    from overtli_blender.server import create_mcp_server

    server = create_mcp_server(profile="chatgpt_browser_default", remote_safety="remote_browser_safe")
    route_paths = {getattr(route, "path", "") for route in server._custom_starlette_routes}  # type: ignore[attr-defined]
    assert "/.well-known/oauth-protected-resource/mcp" in route_paths
    assert "/.well-known/oauth-protected-resource" in route_paths
    assert "/.well-known/oauth-authorization-server" in route_paths
