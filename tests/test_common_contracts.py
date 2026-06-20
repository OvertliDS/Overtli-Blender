from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_common_modules_import_without_blender() -> None:
    import overtli_blender.common  # noqa: F401
    from overtli_blender.common import contracts, errors, handles, operation_types, permissions  # noqa: F401

    assert True


def test_operation_type_values_cover_key_entries() -> None:
    from overtli_blender.common.operation_types import OperationType, operation_type_values

    values = operation_type_values()
    assert values == [item.value for item in OperationType]
    for expected in ["OBSERVE", "DEFORM", "SCULPT", "GEOMETRY_NODES", "EXPORT"]:
        assert expected in values


def test_handle_helpers_round_trip() -> None:
    from overtli_blender.common.handles import HandleType, make_handle, split_handle

    handle = make_handle(HandleType.OBJECT, "Cube")
    assert handle == "object:Cube"
    assert split_handle(handle) == ("object", "Cube")


def test_empty_handle_name_raises_value_error() -> None:
    from overtli_blender.common.handles import HandleType, make_handle

    try:
        make_handle(HandleType.MATERIAL, "")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for empty handle name")


def test_success_result_serializes_to_expected_shape() -> None:
    from overtli_blender.common.contracts import success_result
    from overtli_blender.common.operation_types import OperationType

    result = success_result("demo_tool", OperationType.OBSERVE, {"ok": True})
    data = result.to_dict()

    for key in ["status", "tool", "operation_type", "result", "warnings", "errors", "verification", "rollback"]:
        assert key in data
    assert data["operation_type"] == "OBSERVE"
    assert data["status"] == "success"
    assert data["tool"] == "demo_tool"
    assert data["result"] == {"ok": True}


def test_success_result_json_loads() -> None:
    from overtli_blender.common.contracts import success_result
    from overtli_blender.common.operation_types import OperationType

    payload = success_result("demo_tool", OperationType.CREATE, {"created": 1}).to_json()
    parsed = json.loads(payload)
    assert parsed["status"] == "success"
    assert parsed["operation_type"] == "CREATE"


def test_error_result_includes_error_information() -> None:
    from overtli_blender.common.contracts import error_result
    from overtli_blender.common.operation_types import OperationType

    result = error_result("demo_tool", OperationType.EDIT, "VALIDATION_ERROR", "Bad input")
    data = result.to_dict()
    assert data["status"] == "error"
    assert data["errors"][0]["code"] == "VALIDATION_ERROR"
    assert data["errors"][0]["message"] == "Bad input"


def test_overtli_blender_error_to_dict_is_json_serializable() -> None:
    from overtli_blender.common.errors import ErrorCode, OvertliBlenderError

    error = OvertliBlenderError(ErrorCode.NOT_FOUND, "Missing thing", {"id": 7})
    payload = error.to_dict()
    assert json.loads(json.dumps(payload)) == payload


