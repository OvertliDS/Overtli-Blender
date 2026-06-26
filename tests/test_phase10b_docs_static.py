from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase10b_docs_exist_and_cover_handoff_topics() -> None:
    docs = [
        "docs/final_handoff.md",
        "docs/release_artifacts.md",
        "docs/known_limitations.md",
        "docs/troubleshooting.md",
    ]
    for rel in docs:
        assert (ROOT / rel).is_file()

    handoff = (ROOT / "docs" / "final_handoff.md").read_text(encoding="utf-8")
    for marker in [
        "final_release_handoff.py --json",
        "Create_AI_Review_Zip.bat",
        "Overtli-Blender_AIReview_Drive",
        "Do not edit the Drive mirror directly",
        "ship_candidate",
        "needs_fixes",
        "blocked",
    ]:
        assert marker in handoff

    troubleshooting = (ROOT / "docs" / "troubleshooting.md").read_text(encoding="utf-8")
    for marker in ["PATH_NOT_APPROVED", "PACKAGED_RUNTIME_LIVE_VERIFIED", "smoke_blender_addon_socket.py"]:
        assert marker in troubleshooting
