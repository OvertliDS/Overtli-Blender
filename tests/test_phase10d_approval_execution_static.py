from __future__ import annotations


def test_approve_and_execute_operation_is_registered_everywhere() -> None:
    from overtli_blender.runtime.command_registry import build_command_registry
    from overtli_blender.server import create_mcp_server

    registry = build_command_registry()
    assert "execute_approved_operation" in registry
    assert "approve_and_execute_operation" in registry
    assert registry["approve_and_execute_operation"].supports_progress

    server = create_mcp_server(profile="browser_full_standard", remote_safety="browser_standard")
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    assert "execute_approved_operation" in tools
    assert "approve_and_execute_operation" in tools


def test_approval_runtime_stores_params_and_validates_approve_and_execute() -> None:
    from overtli_blender.runtime.approval import ApprovalRuntime, canonical_params_hash

    runtime = ApprovalRuntime(ttl_seconds=60)
    params = {"primitive_type": "CUBE", "name": "OVERTLI_TEST"}
    prepared = runtime.prepare_operation("create_primitive_object", params)
    approval_id = prepared["approval"]["approval_id"]
    assert prepared["approval"]["params"] == params
    expected_hash = canonical_params_hash("create_primitive_object", params)
    valid = runtime.approve_and_validate_operation(approval_id, expected_command_name="create_primitive_object", expected_params_hash=expected_hash)
    assert valid["status"] == "success"
    assert valid["approval"]["status"] == "approved"


def test_shared_approval_runtime_approve_operation_only_marks_approved() -> None:
    from overtli_blender.runtime.approval import ApprovalRuntime

    runtime = ApprovalRuntime(ttl_seconds=60)
    prepared = runtime.prepare_operation("create_primitive_object", {"primitive_type": "CUBE"})
    approval_id = prepared["approval"]["approval_id"]
    approved = runtime.approve_operation(approval_id)
    assert approved["status"] == "success"
    assert approved["approval"]["status"] == "approved"
