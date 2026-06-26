from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chatgpt_connector_metadata_exists_and_uses_mcp_endpoint() -> None:
    path = ROOT / "config" / "chatgpt_connector_metadata.json"
    assert path.is_file()
    metadata = json.loads(path.read_text(encoding="utf-8"))
    assert metadata["name"] == "Overtli-Blender"
    assert metadata["connector_url_placeholder"].endswith("/mcp")
    assert metadata["local_http_url"] == "http://127.0.0.1:2091/mcp"
    assert metadata["default_tool_profile"] == "chatgpt_browser_default"
    assert metadata["recommended_permission"] == "Always ask"


def test_chatgpt_connector_check_script_exists() -> None:
    text = (ROOT / "scripts" / "chatgpt_connector_check.py").read_text(encoding="utf-8")
    assert "--static" in text
    assert "--live-http" in text
    assert "--live-blender" in text
    assert "chatgpt_browser_default" in text
