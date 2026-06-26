from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chatgpt_browser_connector_docs_cover_required_flow() -> None:
    text = (ROOT / "docs" / "chatgpt_browser_connector.md").read_text(encoding="utf-8")
    for required in [
        "Developer mode",
        "Settings -> Connectors -> Create",
        "/mcp",
        "MCP Inspector",
        "Secure MCP Tunnel",
        "ngrok",
        "Cloudflare Tunnel",
        "Always ask",
        "local/tunnel development",
    ]:
        assert required in text


def test_mcp_setup_links_to_browser_connector_docs() -> None:
    text = (ROOT / "docs" / "mcp_setup.md").read_text(encoding="utf-8")
    assert "chatgpt_browser_connector.md" in text
    assert "--transport http" in text
    assert "http://127.0.0.1:2091/mcp" in text
