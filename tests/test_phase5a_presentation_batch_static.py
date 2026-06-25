from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/presentation_workflow_tools.py").read_text(encoding="utf-8")
SMOKE_TEXT = (ROOT / "scripts/smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_phase5a_presentation_batch_service_and_wrappers_exist() -> None:
    for text in [
        "class PresentationWorkflowBatchService",
        "self.presentation_workflow_batch_service = PresentationWorkflowBatchService(self)",
        "run_presentation_workflow_batch",
        "cleanup_presentation_artifacts",
        "def register_presentation_workflow_tools",
    ]:
        assert text in ADDON_TEXT or text in TOOLS_TEXT


def test_phase5a_smoke_flags_and_forbidden_commands() -> None:
    for flag in [
        "--include-timeline-info",
        "--include-animation-ops",
        "--include-camera-ops",
        "--include-lighting-ops",
        "--include-render-settings",
        "--include-render-still",
        "--include-contact-sheet",
        "--include-turntable",
        "--include-preview-animation",
        "--include-compositor-ops",
        "--include-presentation-batch",
        "--phase5a-full",
    ]:
        assert flag in SMOKE_TEXT
    phase5a = SMOKE_TEXT[SMOKE_TEXT.index("def run_phase5a_full_smoke"):SMOKE_TEXT.index("def run_optional_modifier_ops_smoke")]
    for forbidden in ["execute_code", "download_polyhaven_asset", "download_sketchfab_model", "create_rodin_job"]:
        assert forbidden not in phase5a
