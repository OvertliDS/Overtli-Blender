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
        "src/blender_mcp/server.py",
        "src/blender_mcp/__init__.py",
        "docs/README.md",
        "tests/test_repo_baseline.py",
        "tests/test_static_contract_inventory.py",
    ]

    missing = [rel for rel in required_files if not (ROOT / rel).exists()]
    assert missing == [], f"Missing required files: {missing}"


def test_pyproject_parses_and_has_baseline_package_name() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "blender-mcp-enhanced"  # baseline before rebrand


def test_readme_still_contains_inherited_identity_terms() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "BlenderMCP" in readme
    assert "blender-mcp-enhanced" in readme


def test_private_planning_is_not_required_for_public_baseline() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "memory_bank/" in gitignore
    assert "tools/" in gitignore
    assert "docs/architecture_refactor_plan.md" in gitignore
