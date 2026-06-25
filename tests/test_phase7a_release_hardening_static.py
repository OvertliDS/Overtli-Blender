from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase7a_release_scripts_exist_and_do_not_import_bpy() -> None:
    for rel in [
        "scripts/release_check.py",
        "scripts/build_addon_zip.py",
        "scripts/build_python_package.py",
        "scripts/export_diagnostic_bundle.py",
        "scripts/check_install_docs.py",
    ]:
        path = ROOT / rel
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "\nimport bpy" not in text


def test_release_check_fast_gate_contract() -> None:
    text = (ROOT / "scripts" / "release_check.py").read_text(encoding="utf-8")
    for needle in [
        "--fast",
        "--full",
        "--skip-build",
        "--skip-package",
        "--skip-privacy",
        "--json",
        "compileall",
        "pytest",
        "import_overtli_blender",
        "privacy_scan",
        "stale_identity_scan",
        "addon_entrypoint",
        "smoke_script_static",
    ]:
        assert needle in text
    assert "smoke_blender_addon_socket.py --phase" not in text
    assert "download_polyhaven_asset" not in text
    assert "execute_code" not in text


def test_version_metadata_is_consistent() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    namespace: dict[str, str] = {}
    exec((ROOT / "src" / "overtli_blender" / "__init__.py").read_text(encoding="utf-8"), namespace)
    assert pyproject["project"]["version"] == namespace["__version__"]
    assert pyproject["project"]["name"] == "overtli-blender"
    assert pyproject["project"]["license"] == "MIT"
    assert pyproject["project"]["license-files"] == ["LICENSE"]
    assert pyproject["project"]["scripts"]["overtli-blender"] == "overtli_blender.server:main"
    assert "blender-mcp-enhanced" not in pyproject["project"]["scripts"]


def test_release_docs_exist_and_reference_current_commands() -> None:
    for rel in ["CHANGELOG.md", "docs/install.md", "docs/addon_install.md", "docs/release_check.md", "docs/development.md"]:
        assert (ROOT / rel).is_file()
    combined = "\n".join((ROOT / rel).read_text(encoding="utf-8") for rel in ["README.md", "docs/install.md", "docs/release_check.md", "docs/development.md"])
    for needle in [
        "overtli-blender",
        "src/overtli_blender",
        "scripts\\release_check.py --fast",
        "scripts\\build_addon_zip.py",
        "scripts\\export_diagnostic_bundle.py",
        "smoke_blender_addon_socket.py",
    ]:
        assert needle in combined
