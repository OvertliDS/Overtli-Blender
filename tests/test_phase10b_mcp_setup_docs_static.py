from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mcp_setup_docs_cover_required_client_flow() -> None:
    text = (ROOT / "docs" / "mcp_setup.md").read_text(encoding="utf-8")
    for marker in [
        "py -3.12 -m venv .venv",
        ".\\.venv\\Scripts\\python -m pip install -e .",
        "import overtli_blender; import overtli_blender.server",
        ".\\.venv\\Scripts\\python -m overtli_blender.server",
        "[mcp_servers.\"overtli-blender\"]",
        "\"mcpServers\"",
        "smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status",
        "smoke_blender_addon_socket.py --timeout 30 --release-candidate-full",
        "PATH_NOT_APPROVED",
        "final_release_handoff.py",
    ]:
        assert marker in text


def test_install_doc_check_includes_mcp_setup_doc() -> None:
    text = (ROOT / "scripts" / "check_install_docs.py").read_text(encoding="utf-8")
    assert "mcp_setup.md" in text
    assert "[mcp_servers.\\\"overtli-blender\\\"]" in text
