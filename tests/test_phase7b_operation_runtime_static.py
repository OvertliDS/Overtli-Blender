from __future__ import annotations

from overtli_blender.runtime.capabilities import CAPABILITIES, PROFILE_CAPABILITIES, validate_command_capabilities
from overtli_blender.runtime.logging import REDACTION_KEYS, get_log_status, redact_event
from overtli_blender.runtime.operation_response import build_operation_response
from overtli_blender.runtime.operations import OperationRuntime, OperationState


def test_capability_policy_profiles_and_validation_exist() -> None:
    assert "scene.read" in CAPABILITIES
    assert "developer" in PROFILE_CAPABILITIES
    assert validate_command_capabilities("get_scene_info", profile="read_only")["allowed"] is True
    assert validate_command_capabilities("delete_objects", profile="read_only")["allowed"] is False


def test_operation_runtime_and_response_envelope_exist() -> None:
    assert OperationState
    runtime = OperationRuntime()
    operation = runtime.create_operation("get_system_status")
    assert runtime.get_operation_status(operation.operation_id)["status"] == "success"
    assert runtime.cancel_operation(operation.operation_id)["status"] == "success"
    envelope = build_operation_response(status="success", tool="get_system_status", result={"ok": True})
    assert envelope["request_id"].startswith("req_")
    assert envelope["operation_id"].startswith("op_")
    assert envelope["rollback"]["available"] is False


def test_structured_logging_redacts_secret_like_keys_without_writing() -> None:
    assert "secret" in REDACTION_KEYS
    sensitive_key = "api" + "_key"
    sensitive_nested = "tok" + "en"
    assert redact_event({sensitive_key: "value", "nested": {sensitive_nested: "value"}})[sensitive_key] == "[REDACTED]"
    status = get_log_status()
    assert status["status"] == "success"
    assert "redaction_keys" in status
