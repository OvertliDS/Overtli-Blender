from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chatgpt_browser_connector_docs_cover_required_flow() -> None:
    text = (ROOT / "docs" / "chatgpt_browser_connector.md").read_text(encoding="utf-8")
    for required in [
        "Start_ChatGPT_MCP_Server.bat",
        "Start_ChatGPT_Connector.bat",
        "Start_ChatGPT_Server_URL.bat",
        "Start_ChatGPT_Ngrok_URL.bat",
        "Start_OpenAI_MCP_Tunnel.bat",
        "Reset_ChatGPT_Connector_Credentials.bat",
        "tunnel-client",
        "OVERTLI_TUNNEL_ID",
        "tunnel_0123456789abcdef0123456789abcdef",
        "Developer mode",
        "Settings -> Connectors -> Create",
        "/mcp",
        "MCP Inspector",
        "Secure MCP Tunnel",
        "ngrok",
        "Cloudflare Tunnel",
        "Always allow",
        "local/tunnel development",
    ]:
        assert required in text


def test_mcp_setup_links_to_browser_connector_docs() -> None:
    text = (ROOT / "docs" / "mcp_setup.md").read_text(encoding="utf-8")
    assert "chatgpt_browser_connector.md" in text
    assert "Start_ChatGPT_MCP_Server.bat" in text
    assert "Start_ChatGPT_Connector.bat" in text
    assert "Start_ChatGPT_Server_URL.bat" in text
    assert "Start_OpenAI_MCP_Tunnel.bat" in text
    assert "--transport http" in text
    assert "http://127.0.0.1:2091/mcp" in text


def test_chatgpt_browser_root_launcher_is_foreground_bat() -> None:
    text = (ROOT / "Start_ChatGPT_MCP_Server.bat").read_text(encoding="utf-8")
    assert "overtli_blender.server" in text
    assert "--transport http" in text
    assert "--profile %PROFILE%" in text
    assert "--remote-safety %REMOTE_SAFETY%" in text
    assert "start " not in text.lower()
    assert "Start-Process" not in text


def test_openai_secure_mcp_tunnel_root_launcher_uses_tunnel_client() -> None:
    text = (ROOT / "Start_OpenAI_MCP_Tunnel.bat").read_text(encoding="utf-8")
    assert "tools\\tunnel-client.exe" in text
    assert '"%TUNNEL_CLIENT_EXE%" init' in text
    assert "--sample sample_mcp_remote_no_auth" in text
    assert "--force" in text
    assert '"%TUNNEL_CLIENT_EXE%" doctor' in text
    assert '"%TUNNEL_CLIENT_EXE%" run' in text
    assert "--mcp-server-url" in text
    assert "OVERTLI_TUNNEL_ID" in text
    assert "CONTROL_PLANE_API_KEY" in text
    assert "http://127.0.0.1:2091/mcp" in text


def test_combined_chatgpt_connector_launcher_starts_bridge_and_tunnel() -> None:
    bat = (ROOT / "Start_ChatGPT_Connector.bat").read_text(encoding="utf-8")
    script = (ROOT / "scripts" / "start_chatgpt_connector.ps1").read_text(encoding="utf-8")
    assert "start_chatgpt_connector.ps1" in bat
    assert "overtli_blender.server" in script
    assert "Start-Process" in script
    assert "tunnel-client.exe" in script
    assert "--sample sample_mcp_remote_no_auth" in script
    assert "--force" in script
    assert "OVERTLI_TUNNEL_ID" in script
    assert "CONTROL_PLANE_API_KEY" in script
    assert "ConvertFrom-SecureString" in script
    assert "control_plane_api_key.dpapi" in script
    assert "tunnel.json" in script
    assert "Test-TunnelId" in script
    assert "Test-PlaceholderTunnelId" in script
    assert "example/placeholder" in script
    assert "^tunnel_[a-z0-9]{32}$" in script
    assert "Read-Host" in script
    assert "-AsSecureString" in script
    assert "Stop-Process" in script
    assert "http://${HostAddress}:${Port}/mcp" in script
    assert "real OpenAI tunnel ID" in script


def test_chatgpt_server_url_launcher_starts_bridge_and_cloudflared() -> None:
    bat = (ROOT / "Start_ChatGPT_Server_URL.bat").read_text(encoding="utf-8")
    script = (ROOT / "scripts" / "start_chatgpt_server_url.ps1").read_text(encoding="utf-8")
    assert "start_chatgpt_server_url.ps1" in bat
    assert "overtli_blender.server" in script
    assert "cloudflared.exe" in script
    assert "cloudflared-windows-amd64.exe" in script
    assert "trycloudflare.com" in script
    assert "Server URL" in script
    assert "No Auth" in script
    assert "--allow-public-tunnel-hosts" in script
    assert "/mcp" in script
    assert "Stop-Process" in script
    assert "chatgpt_server_url" in script


def test_chatgpt_ngrok_stable_url_launcher_starts_bridge_and_ngrok() -> None:
    bat = (ROOT / "Start_ChatGPT_Ngrok_URL.bat").read_text(encoding="utf-8")
    script = (ROOT / "scripts" / "start_chatgpt_ngrok_url.ps1").read_text(encoding="utf-8")
    assert "start_chatgpt_ngrok_url.ps1" in bat
    assert "overtli_blender.server" in script
    assert "ngrok.exe" in script
    assert "OVERTLI_NGROK_URL" in script
    assert "OVERTLI_NGROK_EXE" in script
    assert "ngrok_url.txt" in script
    assert "chatgpt_ngrok_url" in script
    assert "--url" in script
    assert "--allow-public-tunnel-hosts" in script
    assert "/mcp" in script
    assert "Stop-StaleNgrokTunnels" in script
    assert "Get-NgrokApiTunnels" in script
    assert "ERR_NGROK_334" in script
    assert "already online" in script
    assert "CommandLine" in script
    assert "Server URL" in script
    assert "No Auth" in script
    assert "[regex]::Matches" in script
    assert "browser_full_standard" in script
    assert "browser_standard" in script
    assert "chatgpt_browser_default" not in script
    assert "remote_browser_safe" not in script


def test_chatgpt_connector_reset_launcher_removes_local_state_only() -> None:
    text = (ROOT / "Reset_ChatGPT_Connector_Credentials.bat").read_text(encoding="utf-8")
    assert ".overtli_blender\\local\\chatgpt_connector" in text
    assert "rmdir /s /q" in text
    assert "did not revoke keys or delete tunnels" in text
