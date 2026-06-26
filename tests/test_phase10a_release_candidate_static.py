from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_candidate_scripts_exist() -> None:
    for rel in [
        "scripts/compatibility_check.py",
        "scripts/performance_check.py",
        "scripts/security_audit.py",
        "scripts/fault_injection_check.py",
        "scripts/docs_lockdown_check.py",
        "scripts/release_candidate_check.py",
    ]:
        assert (ROOT / rel).is_file()


def test_release_check_enforces_modular_addon_structure() -> None:
    text = (ROOT / "scripts" / "release_check.py").read_text(encoding="utf-8")
    assert "check_addon_package_structure" in text
    assert "legacy_runtime.py monolith must not exist" in text
    assert "addon.py must remain a thin Blender entrypoint" in text
