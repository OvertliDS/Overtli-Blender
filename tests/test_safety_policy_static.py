from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
SAFETY_TEXT = (ROOT / "src/overtli_blender/common/safety.py").read_text(encoding="utf-8")
SMOKE_TEXT = (ROOT / "scripts" / "smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_addon_defines_safety_policy_service() -> None:
    for text in [
        "class SafetyPolicyService",
        "self.safety_policy_service = SafetyPolicyService(self)",
        "self.get_safety_status = self.safety_policy_service.get_safety_status",
        "def get_safety_status(self):",
        '"get_safety_status": self.get_safety_status',
    ]:
        assert text in ADDON_TEXT


def test_addon_dispatch_evaluates_safety_before_execution() -> None:
    for text in [
        "safety_decision = self.safety_policy_service.evaluate_command(cmd_type, params)",
        "Command blocked by safety policy",
        "self.safety_policy_service.mode == SAFETY_MODE_AUDIT",
        "if cmd_type == \"get_safety_status\":",
    ]:
        assert text in ADDON_TEXT


def test_common_safety_module_defines_policy_metadata() -> None:
    for text in [
        "SAFETY_MODE_COMPAT = \"compatibility\"",
        "SAFETY_MODE_AUDIT = \"audit\"",
        "SAFETY_MODE_STRICT = \"strict\"",
        "SAFETY_POLICY_VERSION = \"1.0\"",
        "CommandSafetyMetadata",
        "build_command_safety_map",
    ]:
        assert text in SAFETY_TEXT


def test_common_safety_module_classifies_high_risk_commands() -> None:
    for text in [
        '"execute_code"',
        '"execute_context_script"',
        '"complete_geometry_node"',
        '"download_polyhaven_asset"',
        '"download_sketchfab_model"',
        '"create_rodin_job"',
        '"import_generated_asset"',
        '"clear_context_scripts"',
    ]:
        assert text in SAFETY_TEXT


def test_common_safety_module_classifies_phase2_commands() -> None:
    for text in [
        '"get_scene_index", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_object_deep_info", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_selection_info", OperationType.OBSERVE, RiskLevel.LOW',
        '"get_scene_health", OperationType.VERIFY, RiskLevel.LOW',
        '"capture_viewport_pack"',
        '"create_verification_snapshot"',
        '"list_verification_snapshots", OperationType.VERIFY, RiskLevel.LOW',
        "can_write_files=True",
        '"writes-local-verification-artifacts"',
    ]:
        assert text in SAFETY_TEXT


def test_phase2_strict_mode_behavior_is_documented_in_policy() -> None:
    for command in [
        "get_scene_index",
        "get_object_deep_info",
        "get_selection_info",
        "get_scene_health",
        "capture_viewport_pack",
        "create_verification_snapshot",
    ]:
        command_index = SAFETY_TEXT.index(f'"{command}"')
        command_block = SAFETY_TEXT[command_index:command_index + 500]
        assert "strict_blocked=True" not in command_block


def test_smoke_script_exposes_safety_mode_flags() -> None:
    for text in [
        "--include-safety-status",
        "--expect-strict-blocks",
        "run_optional_safety_status_smoke",
        "run_optional_strict_block_smoke",
        "execute_code",
        "get_safety_status",
    ]:
        assert text in SMOKE_TEXT

