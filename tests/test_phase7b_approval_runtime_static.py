from __future__ import annotations

from overtli_blender.runtime.approval import ApprovalRecord, ApprovalRuntime, canonical_params_hash


def test_approval_record_and_hashing_are_stable() -> None:
    assert ApprovalRecord
    assert canonical_params_hash("delete_objects", {"a": 1, "b": 2}) == canonical_params_hash("delete_objects", {"b": 2, "a": 1})
    assert canonical_params_hash("delete_objects", {"a": 1}) != canonical_params_hash("delete_objects", {"a": 2})


def test_prepare_approve_deny_and_execute_guards_params() -> None:
    runtime = ApprovalRuntime(ttl_seconds=60)
    prepared = runtime.prepare_operation("delete_objects", {"object_names": [], "confirm": True})
    assert prepared["status"] == "requires_approval"
    approval_id = prepared["approval"]["approval_id"]
    assert runtime.get_pending_approvals()["approvals"]
    assert runtime.approve_operation(approval_id)["status"] == "success"
    valid = runtime.validate_approved_operation(approval_id, "delete_objects", {"object_names": [], "confirm": True})
    assert valid["status"] == "success"
    changed = runtime.execute_approved_operation(approval_id, "delete_objects", {"object_names": ["changed"], "confirm": True})
    assert changed["status"] == "error"
    ready = runtime.execute_approved_operation(approval_id, "delete_objects", {"object_names": [], "confirm": True})
    assert ready["status"] == "success"
    assert ready["dispatch_required"] is True
    assert runtime.get_approval_record(approval_id)["approval"]["status"] == "approved"
    denied = runtime.prepare_operation("remove_object_modifier", {"object_name": "NOOP", "modifier_name": "NOOP"})
    assert runtime.deny_operation(denied["approval"]["approval_id"])["status"] == "success"
