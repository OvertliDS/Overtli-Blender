from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_repo_files_exist() -> None:
    required_files = [
        "README.md",
        "pyproject.toml",
        "addon.py",
        "main.py",
        "src/overtli_blender/server.py",
        "src/overtli_blender/__init__.py",
        "docs/README.md",
        "docs/chatgpt_browser_connector.md",
        "config/chatgpt_connector_metadata.json",
        "scripts/chatgpt_connector_check.py",
        "tests/test_repo_baseline.py",
        "tests/test_static_contract_inventory.py",
    ]

    missing = [rel for rel in required_files if not (ROOT / rel).exists()]
    assert missing == [], f"Missing required files: {missing}"


def test_pyproject_parses_and_has_baseline_package_name() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "overtli-blender"
    assert "overtli-blender" in data["project"]["scripts"]
    assert "blender-mcp-enhanced" not in data["project"]["scripts"]
    assert data["project"]["scripts"]["overtli-blender"] == "overtli_blender.server:main"


def test_readme_contains_current_identity_and_upstream_credit() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Overtli-Blender" in readme
    assert "blender-mcp-enhanced" not in readme
    assert "BlenderMCP" in readme  # upstream credit only
    assert "Original Project" in readme or "Upstream Credit" in readme


def test_old_package_path_is_removed_from_source_tree() -> None:
    assert not (ROOT / "src/blender_mcp").exists()
    assert (ROOT / "src/overtli_blender").exists()


def test_private_planning_is_not_required_for_public_baseline() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "memory_bank/" in gitignore
    assert ".overtli_blender/" in gitignore
    assert "tools/" in gitignore
    assert "!src/overtli_blender/tools/" in gitignore
    assert "!src/overtli_blender/tools/*.py" in gitignore
    assert "docs/architecture_refactor_plan.md" in gitignore

