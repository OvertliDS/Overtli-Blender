from __future__ import annotations

import json


def test_browser_mutation_smoke_flags_and_guards_exist() -> None:
    text = open("scripts/smoke_blender_addon_socket.py", encoding="utf-8").read()
    assert "--include-browser-mutation-path" in text
    assert "--include-browser-approval-execution-path" in text
    assert "run_browser_mutation_path_smoke" in text
    assert "run_browser_approval_execution_path_smoke" in text
    assert "OVERTLI_BROWSER_SMOKE_CUBE_" in text
    assert "OVERTLI_BROWSER_APPROVAL_CUBE_" in text
    assert "approve_and_execute_operation" in text
    assert "object_count did not increase" in text
    assert "execute_code" not in text[text.index("def run_browser_mutation_path_smoke"): text.index("def run_required_smoke")]


def test_connector_check_has_browser_write_modes() -> None:
    text = open("scripts/chatgpt_connector_check.py", encoding="utf-8").read()
    assert "--browser-write-profile" in text
    assert "--browser-mutation-smoke" in text
    assert "REQUIRED_BROWSER_TOOLS" in text
    assert "DANGEROUS_BROWSER_TOOLS" in text


def test_transport_strips_callable_connector_metadata_before_json_encoding() -> None:
    from overtli_blender.transport import encode_command

    payload = {
        "type": "create_primitive_object",
        "params": {
            "primitive_type": "CUBE",
            "ctx": {"source": "chatgpt"},
            "get_blender_connection": lambda: None,
            "nested": {"tool_context": object()},
        },
    }

    encoded = encode_command(payload)
    decoded = json.loads(encoded.decode("utf-8"))
    assert decoded["params"] == {"primitive_type": "CUBE", "nested": {}}


def test_browser_scene_edit_wrappers_do_not_forward_raw_locals() -> None:
    text = open("src/overtli_blender/tools/scene_edit_tools.py", encoding="utf-8").read()
    scene_edit_section = text[text.index("def register_scene_edit_tools") :]
    assert "locals()" not in scene_edit_section
    assert '"primitive_type": primitive_type' in scene_edit_section
    assert '"ctx":' not in scene_edit_section
