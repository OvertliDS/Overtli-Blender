from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase10a_docs_exist() -> None:
    for rel in [
        "docs/addon_architecture.md",
        "docs/addon_packaging.md",
        "docs/compatibility_matrix.md",
        "docs/performance_budgets.md",
        "docs/security_audit.md",
        "docs/privacy_model.md",
        "docs/threat_model.md",
        "docs/fault_injection.md",
        "docs/release_candidate.md",
        "docs/migration_audit.md",
        "docs/mcp_setup.md",
    ]:
        assert (ROOT / rel).is_file()


def test_public_install_docs_make_zip_primary() -> None:
    text = (ROOT / "docs" / "addon_install.md").read_text(encoding="utf-8")
    assert "addon zip" in text.lower()
    assert "should not be copied by itself" in text


def test_mcp_setup_docs_include_venv_and_client_registration() -> None:
    text = (ROOT / "docs" / "mcp_setup.md").read_text(encoding="utf-8")
    for needle in [
        "py -3.12 -m venv .venv",
        ".\\.venv\\Scripts\\python -m pip install -e .",
        ".\\.venv\\Scripts\\python -m overtli_blender.server",
        "[mcp_servers.\"overtli-blender\"]",
        "BLENDER_HOST = \"localhost\"",
        "BLENDER_PORT = \"9876\"",
        "\"mcpServers\"",
        "smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status",
        "smoke_blender_addon_socket.py --timeout 30 --release-candidate-full",
    ]:
        assert needle in text
