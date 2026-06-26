from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_final_release_handoff_script_aggregates_required_gates() -> None:
    text = (ROOT / "scripts" / "final_release_handoff.py").read_text(encoding="utf-8")
    for marker in [
        "release_check.py",
        "release_candidate_check.py",
        "addon_modularity_check.py",
        "build_addon_zip.py",
        "import_boundary_check.py",
        "docs_lockdown_check.py",
        "security_audit.py",
        "compatibility_check.py",
        "performance_check.py",
        "fault_injection_check.py",
        "export_diagnostic_bundle.py",
        "handoff_manifest.json",
        "ship_decision.json",
        "artifact_manifest.json",
        "addon_zip_manifest_pointer.json",
        "diagnostic_bundle_pointer.json",
        "test_summary.json",
        "smoke_summary.json",
        "known_limitations.md",
        "next_steps.md",
        "ship_candidate",
        "needs_fixes",
        "blocked",
    ]:
        assert marker in text
