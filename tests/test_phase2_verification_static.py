from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
VERIFICATION_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/verification_tools.py").read_text(encoding="utf-8")
GITIGNORE_TEXT = (ROOT / ".gitignore").read_text(encoding="utf-8")
RUNTIME_DOCS_TEXT = (ROOT / "docs/runtime_smoke.md").read_text(encoding="utf-8")
README_TEXT = (ROOT / "README.md").read_text(encoding="utf-8")


PHASE2_VERIFICATION_COMMANDS = [
    "capture_viewport_pack",
    "create_verification_snapshot",
    "list_verification_snapshots",
]


def test_addon_defines_verification_artifact_service() -> None:
    assert "class VerificationArtifactService" in ADDON_TEXT
    assert "self.verification_artifact_service = VerificationArtifactService(self)" in ADDON_TEXT


def test_addon_maps_phase2_verification_commands() -> None:
    for command in PHASE2_VERIFICATION_COMMANDS:
        assert f'"{command}": self.{command}' in ADDON_TEXT
        assert f"def {command}(" in ADDON_TEXT


def test_verification_artifact_source_uses_local_generated_workspace() -> None:
    for text in [
        '".overtli_blender"',
        '"verification"',
        '"snapshots"',
        '"manifest.json"',
        '"scene_index.json"',
        '"scene_health.json"',
        '"selection_info.json"',
        '"screenshots"',
        "OVERTLI_BLENDER_ARTIFACT_ROOT",
        "artifact_root",
        '"perspective"',
        '"front"',
        '"right"',
        '"top"',
    ]:
        assert text in ADDON_TEXT


def test_verification_manifest_keys_are_present() -> None:
    for key in [
        '"snapshot_id"',
        '"label"',
        '"created_at"',
        '"blender_file"',
        '"scene_name"',
        '"safety_mode"',
        '"commands"',
        '"artifacts"',
        '"warnings"',
    ]:
        assert key in ADDON_TEXT


def test_verification_tool_module_registers_phase2_tools() -> None:
    assert "def register_verification_tools" in VERIFICATION_TOOLS_TEXT
    for command in PHASE2_VERIFICATION_COMMANDS:
        assert f"def {command}(" in VERIFICATION_TOOLS_TEXT
        assert f'"{command}"' in VERIFICATION_TOOLS_TEXT
    assert "artifact_root" in VERIFICATION_TOOLS_TEXT


def test_phase2_artifacts_are_ignored_and_documented() -> None:
    assert ".overtli_blender/" in GITIGNORE_TEXT
    assert ".overtli_blender/verification/" in RUNTIME_DOCS_TEXT
    assert ".overtli_blender/verification/" in README_TEXT
