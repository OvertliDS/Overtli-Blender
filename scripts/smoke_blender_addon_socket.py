from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import tempfile
import time


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def receive_json_response(sock: socket.socket, timeout_seconds: float) -> dict:
    sock.settimeout(timeout_seconds)
    chunks: list[bytes] = []

    while True:
        try:
            chunk = sock.recv(8192)
        except socket.timeout as exc:
            if chunks:
                break
            raise TimeoutError("Timed out waiting for Blender addon response") from exc

        if not chunk:
            if not chunks:
                raise ConnectionError("Connection closed before receiving a response")
            break

        chunks.append(chunk)

        try:
            return json.loads(b"".join(chunks).decode("utf-8"))
        except json.JSONDecodeError:
            continue

    payload = b"".join(chunks)
    try:
        return json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Incomplete JSON response received from Blender addon") from exc


def send_command(sock: socket.socket, timeout_seconds: float, command_type: str, params: dict | None = None) -> dict:
    payload = {"type": command_type, "params": params or {}}
    sock.sendall(json.dumps(payload).encode("utf-8"))
    return receive_json_response(sock, timeout_seconds)


def assert_success(name: str, response: dict, require_result_dict: bool = True) -> dict:
    if response.get("status") != "success":
        raise RuntimeError(f"{name}: {response.get('message', response)}")

    result = response.get("result")
    if require_result_dict and not isinstance(result, dict):
        raise RuntimeError(f"{name}: expected a JSON object result, got {type(result).__name__}")

    print(f"PASS {name}")
    return result if isinstance(result, dict) else {}


def run_required_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    for command_name in [
        "get_scene_info",
        "get_shared_context",
        "get_operation_history",
        "list_object_handles",
        "list_material_handles",
        "list_context_scripts",
    ]:
        response = send_command(sock, timeout_seconds, command_name)
        result = assert_success(command_name, response)
        if command_name == "get_scene_info" and "object_count" not in result:
            raise RuntimeError("get_scene_info: missing object_count in result")
        if command_name == "get_shared_context" and "history_count" not in result:
            raise RuntimeError("get_shared_context: missing history_count in result")
        if command_name == "get_operation_history" and "history" not in result:
            raise RuntimeError("get_operation_history: missing history in result")
        if command_name == "list_context_scripts" and "scripts" not in result:
            raise RuntimeError("list_context_scripts: missing scripts in result")


def run_optional_screenshot_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    screenshot_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="overtli_blender_smoke_", suffix=".png", delete=False) as temp_file:
            screenshot_path = temp_file.name

        response = send_command(
            sock,
            timeout_seconds,
            "get_viewport_screenshot",
            {"max_size": 400, "filepath": screenshot_path, "format": "png"},
        )
        result = assert_success("get_viewport_screenshot", response)
        if not result.get("success"):
            raise RuntimeError(f"get_viewport_screenshot: {result}")
        if result.get("filepath") != screenshot_path:
            raise RuntimeError("get_viewport_screenshot: returned filepath did not match request")
        print(f"PASS get_viewport_screenshot {result.get('width')}x{result.get('height')}")
    finally:
        if screenshot_path:
            try:
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
            except Exception:
                pass


def run_optional_provider_status_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    for command_name in [
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
    ]:
        response = send_command(sock, timeout_seconds, command_name)
        result = assert_success(command_name, response)
        if "enabled" not in result or "message" not in result:
            raise RuntimeError(f"{command_name}: missing enabled/message in result")


def run_optional_safety_status_smoke(sock: socket.socket, timeout_seconds: float) -> dict:
    response = send_command(sock, timeout_seconds, "get_safety_status")
    result = assert_success("get_safety_status", response)
    if "mode" not in result or "policy_version" not in result:
        raise RuntimeError("get_safety_status: missing mode/policy_version in result")
    return result


def run_optional_scene_index_smoke(sock: socket.socket, timeout_seconds: float) -> dict:
    response = send_command(sock, timeout_seconds, "get_scene_index", {"max_objects": 25})
    result = assert_success("get_scene_index", response)
    if result.get("status") != "success" or "scene" not in result or "objects" not in result:
        raise RuntimeError(f"get_scene_index: malformed result {result}")
    return result


def run_optional_selection_info_smoke(sock: socket.socket, timeout_seconds: float) -> dict:
    response = send_command(sock, timeout_seconds, "get_selection_info")
    result = assert_success("get_selection_info", response)
    if result.get("status") != "success" or "selected_objects" not in result:
        raise RuntimeError(f"get_selection_info: malformed result {result}")
    return result


def run_optional_scene_health_smoke(sock: socket.socket, timeout_seconds: float) -> dict:
    response = send_command(sock, timeout_seconds, "get_scene_health")
    result = assert_success("get_scene_health", response)
    if result.get("status") != "success" or "summary" not in result or "issues" not in result:
        raise RuntimeError(f"get_scene_health: malformed result {result}")
    return result


def _resolve_object_for_deep_info(sock: socket.socket, timeout_seconds: float) -> str | None:
    selection = run_optional_selection_info_smoke(sock, timeout_seconds)
    active_object = selection.get("active_object")
    if active_object:
        return str(active_object)

    scene_index = run_optional_scene_index_smoke(sock, timeout_seconds)
    objects = scene_index.get("objects", [])
    if objects:
        return str(objects[0].get("name"))
    return None


def run_optional_object_deep_info_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    object_name = _resolve_object_for_deep_info(sock, timeout_seconds)
    if not object_name:
        print("WARN get_object_deep_info skipped: scene has no objects")
        return

    response = send_command(sock, timeout_seconds, "get_object_deep_info", {"object_name": object_name})
    result = assert_success("get_object_deep_info", response)
    if result.get("status") != "success" or "object" not in result:
        raise RuntimeError(f"get_object_deep_info: malformed result {result}")


def run_optional_screenshot_pack_smoke(sock: socket.socket, timeout_seconds: float) -> dict:
    response = send_command(
        sock,
        timeout_seconds,
        "capture_viewport_pack",
        {
            "views": ["perspective", "front", "right", "top"],
            "max_size": 400,
            "snapshot_name": "smoke_pack",
            "artifact_root": REPO_ROOT,
        },
    )
    result = assert_success("capture_viewport_pack", response)
    if result.get("status") != "success" or "artifact_dir" not in result or "screenshots" not in result:
        raise RuntimeError(f"capture_viewport_pack: malformed result {result}")
    print(f"ARTIFACT capture_viewport_pack {result.get('artifact_dir')}")
    return result


def run_optional_verification_snapshot_smoke(sock: socket.socket, timeout_seconds: float) -> dict:
    response = send_command(
        sock,
        timeout_seconds,
        "create_verification_snapshot",
        {
            "label": "phase2_smoke",
            "views": ["perspective", "front", "right", "top"],
            "max_size": 400,
            "artifact_root": REPO_ROOT,
        },
    )
    result = assert_success("create_verification_snapshot", response)
    if result.get("status") != "success" or "manifest_path" not in result or "artifacts" not in result:
        raise RuntimeError(f"create_verification_snapshot: malformed result {result}")
    print(f"ARTIFACT create_verification_snapshot {result.get('artifact_dir')}")
    return result


def run_phase2_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    run_optional_safety_status_smoke(sock, timeout_seconds)
    run_optional_scene_index_smoke(sock, timeout_seconds)
    run_optional_selection_info_smoke(sock, timeout_seconds)
    run_optional_scene_health_smoke(sock, timeout_seconds)
    run_optional_object_deep_info_smoke(sock, timeout_seconds)
    run_optional_screenshot_pack_smoke(sock, timeout_seconds)
    run_optional_verification_snapshot_smoke(sock, timeout_seconds)


def run_optional_edit_ops_smoke(sock: socket.socket, timeout_seconds: float) -> dict:
    result = assert_success("get_supported_edit_operations", send_command(sock, timeout_seconds, "get_supported_edit_operations"))
    if result.get("status") != "success" or "operations" not in result:
        raise RuntimeError(f"get_supported_edit_operations: malformed result {result}")
    return result


def run_phase3_workspace_safety_diff_smoke(sock: socket.socket, timeout_seconds: float, stamp: str) -> None:
    task_id = f"phase3_master_{stamp}"
    before_label = f"phase3_master_before_{stamp}"
    after_label = f"phase3_master_after_{stamp}"
    workspace = assert_success("get_task_workspace", send_command(sock, timeout_seconds, "get_task_workspace", {"artifact_root": REPO_ROOT}))
    if workspace.get("status") != "success" or "workspace_root" not in workspace:
        raise RuntimeError(f"get_task_workspace: {workspace}")

    task = assert_success(
        "create_workspace_task",
        send_command(sock, timeout_seconds, "create_workspace_task", {"task_id": task_id, "title": "Phase 3 master smoke", "goal": "Verify workspace, todos, journal, scene diff, rollback, and change detection", "artifact_root": REPO_ROOT}),
    )
    if task.get("status") != "success":
        raise RuntimeError(f"create_workspace_task: {task}")

    todo = assert_success(
        "add_workspace_todo",
        send_command(sock, timeout_seconds, "add_workspace_todo", {"task_id": task_id, "todo_id": f"todo_{task_id}", "text": "Verify Phase 3 master systems", "artifact_root": REPO_ROOT}),
    )
    if todo.get("status") != "success":
        raise RuntimeError(f"add_workspace_todo: {todo}")

    assert_success("update_workspace_todo", send_command(sock, timeout_seconds, "update_workspace_todo", {"todo_id": f"todo_{task_id}", "state": "in_progress", "evidence": {"smoke": True}, "artifact_root": REPO_ROOT}))

    before = assert_success("create_scene_snapshot", send_command(sock, timeout_seconds, "create_scene_snapshot", {"label": before_label, "task_id": task_id, "artifact_root": REPO_ROOT}))
    if before.get("status") != "success":
        raise RuntimeError(f"create_scene_snapshot before: {before}")

    probe_name = f"OVERTLI_PHASE3_MASTER_CUBE_{stamp}"
    created_objects: list[str] = []
    try:
        created = assert_success("create_primitive_object phase3_master", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": probe_name, "collection_name": f"OVERTLI_PHASE3_MASTER_{stamp}"}))
        if created.get("status") != "success":
            raise RuntimeError(f"create_primitive_object phase3_master: {created}")
        probe_name = created["object_name"]
        created_objects.append(probe_name)
        moved = assert_success("transform_object phase3_master", send_command(sock, timeout_seconds, "transform_object", {"object_name": probe_name, "location": [2.0, 0.0, 0.0]}))
        if moved.get("status") != "success":
            raise RuntimeError(f"transform_object phase3_master: {moved}")

        after = assert_success("create_scene_snapshot", send_command(sock, timeout_seconds, "create_scene_snapshot", {"label": after_label, "task_id": task_id, "artifact_root": REPO_ROOT}))
        if after.get("status") != "success":
            raise RuntimeError(f"create_scene_snapshot after: {after}")

        diff = assert_success("diff_scene_snapshots", send_command(sock, timeout_seconds, "diff_scene_snapshots", {"before_snapshot_id": before["snapshot_id"], "after_snapshot_id": after["snapshot_id"], "artifact_root": REPO_ROOT}))
        if probe_name not in diff.get("diff", {}).get("objects", {}).get("added", []):
            raise RuntimeError(f"diff_scene_snapshots: expected added object {probe_name}, got {diff}")

        changes = assert_success("detect_user_changes", send_command(sock, timeout_seconds, "detect_user_changes", {"baseline_snapshot_id": before["snapshot_id"], "artifact_root": REPO_ROOT}))
        if not changes.get("changed"):
            raise RuntimeError(f"detect_user_changes: expected changed scene, got {changes}")

        rollback = assert_success(
            "rollback_to_scene_snapshot",
            send_command(sock, timeout_seconds, "rollback_to_scene_snapshot", {"snapshot_id": before["snapshot_id"], "confirm": True, "remove_new_objects": True, "artifact_root": REPO_ROOT}),
        )
        if rollback.get("status") != "success" or probe_name not in rollback.get("removed_new_objects", []):
            raise RuntimeError(f"rollback_to_scene_snapshot: {rollback}")
        created_objects.clear()

        journal = assert_success("get_operation_journal", send_command(sock, timeout_seconds, "get_operation_journal", {"task_id": task_id, "artifact_root": REPO_ROOT}))
        if journal.get("status") != "success" or not journal.get("journal"):
            raise RuntimeError(f"get_operation_journal: {journal}")

        assert_success("update_workspace_task", send_command(sock, timeout_seconds, "update_workspace_task", {"task_id": task_id, "status": "done", "rollback_status": "verified", "artifact_root": REPO_ROOT}))
        assert_success("update_workspace_todo", send_command(sock, timeout_seconds, "update_workspace_todo", {"todo_id": f"todo_{task_id}", "state": "done", "artifact_root": REPO_ROOT}))
    finally:
        if created_objects:
            assert_success("delete_objects phase3_master_cleanup", send_command(sock, timeout_seconds, "delete_objects", {"object_names": created_objects, "confirm": True, "allow_missing": True}))
        try:
            cleanup = send_command(sock, timeout_seconds, "delete_collection", {"collection_name": f"OVERTLI_PHASE3_MASTER_{stamp}", "confirm": True, "require_empty": True})
            if cleanup.get("status") == "success":
                assert_success("delete_collection phase3_master_cleanup", cleanup)
        except Exception as exc:
            print(f"WARN delete_collection phase3_master_cleanup: {exc}")


def run_phase3_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(int(time.time()))
    collection_name = f"OVERTLI_PHASE3_SMOKE_{stamp}"
    cube_name = f"OVERTLI_PHASE3_CUBE_{stamp}"
    duplicate_name = f"OVERTLI_PHASE3_CUBE_DUP_{stamp}"
    material_name = f"OVERTLI_PHASE3_MAT_{stamp}"
    created_objects: list[str] = []

    run_optional_edit_ops_smoke(sock, timeout_seconds)
    before = assert_success(
        "create_verification_snapshot phase3_before",
        send_command(sock, timeout_seconds, "create_verification_snapshot", {"label": f"phase3_before_{stamp}", "include_screenshots": False, "artifact_root": REPO_ROOT}),
    )
    print(f"ARTIFACT phase3_before {before.get('artifact_dir')}")

    try:
        collection = assert_success("create_collection", send_command(sock, timeout_seconds, "create_collection", {"collection_name": collection_name}))
        if collection.get("status") != "success":
            raise RuntimeError(f"create_collection: {collection}")

        material = assert_success(
            "create_basic_material",
            send_command(sock, timeout_seconds, "create_basic_material", {"name": material_name, "base_color": [1.0, 0.72, 0.18, 1.0], "metallic": 0.2, "roughness": 0.35}),
        )
        if material.get("status") != "success":
            raise RuntimeError(f"create_basic_material: {material}")

        created = assert_success(
            "create_primitive_object",
            send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": cube_name, "collection_name": collection_name}),
        )
        if created.get("status") != "success":
            raise RuntimeError(f"create_primitive_object: {created}")
        cube_name = created["object_name"]
        created_objects.append(cube_name)

        for command_name, params in [
            ("assign_material", {"object_name": cube_name, "material_name": material_name}),
            ("transform_object", {"object_name": cube_name, "location": [1.0, 2.0, 0.5], "rotation": [0.0, 0.0, 0.25], "scale": [1.2, 1.2, 1.2]}),
            ("add_object_modifier", {"object_name": cube_name, "modifier_type": "BEVEL", "name": "OVERTLI_PHASE3_BEVEL", "properties": {"width": 0.08, "segments": 2}}),
            ("update_object_modifier", {"object_name": cube_name, "modifier_name": "OVERTLI_PHASE3_BEVEL", "properties": {"width": 0.12, "segments": 3}}),
        ]:
            result = assert_success(command_name, send_command(sock, timeout_seconds, command_name, params))
            if result.get("status") not in {"success", "partial"}:
                raise RuntimeError(f"{command_name}: {result}")

        duplicate = assert_success(
            "duplicate_object",
            send_command(sock, timeout_seconds, "duplicate_object", {"object_name": cube_name, "new_name": duplicate_name, "location_offset": [1.5, 0.0, 0.0], "collection_name": collection_name}),
        )
        if duplicate.get("status") != "success":
            raise RuntimeError(f"duplicate_object: {duplicate}")
        duplicate_name = duplicate["object_name"]
        created_objects.append(duplicate_name)

        moved = assert_success(
            "move_objects_to_collection",
            send_command(sock, timeout_seconds, "move_objects_to_collection", {"object_names": created_objects, "collection_name": collection_name, "unlink_from_other_collections": True}),
        )
        if moved.get("status") not in {"success", "partial"}:
            raise RuntimeError(f"move_objects_to_collection: {moved}")

        batch = assert_success(
            "run_verified_edit_batch",
            send_command(
                sock,
                timeout_seconds,
                "run_verified_edit_batch",
                {
                    "label": f"phase3_batch_{stamp}",
                    "artifact_root": REPO_ROOT,
                    "operations": [
                        {"type": "set_object_visibility", "params": {"object_name": duplicate_name, "hide_render": True}},
                        {"type": "update_material_properties", "params": {"material_name": material_name, "roughness": 0.45}},
                    ],
                },
            ),
        )
        if batch.get("status") != "success":
            raise RuntimeError(f"run_verified_edit_batch: {batch}")
        print(f"ARTIFACT phase3_batch_before {batch.get('before_snapshot', {}).get('artifact_dir')}")
        print(f"ARTIFACT phase3_batch_after {batch.get('after_snapshot', {}).get('artifact_dir')}")

        run_optional_scene_index_smoke(sock, timeout_seconds)
        for object_name in created_objects:
            deep = assert_success("get_object_deep_info", send_command(sock, timeout_seconds, "get_object_deep_info", {"object_name": object_name}))
            if deep.get("status") != "success":
                raise RuntimeError(f"get_object_deep_info {object_name}: {deep}")

        after = assert_success(
            "create_verification_snapshot phase3_after",
            send_command(sock, timeout_seconds, "create_verification_snapshot", {"label": f"phase3_after_{stamp}", "include_screenshots": False, "artifact_root": REPO_ROOT}),
        )
        print(f"ARTIFACT phase3_after {after.get('artifact_dir')}")
        print(f"PHASE3 created_objects {created_objects}")
        run_phase3_workspace_safety_diff_smoke(sock, timeout_seconds, stamp)
    finally:
        if created_objects:
            cleanup = assert_success(
                "delete_objects phase3_cleanup",
                send_command(sock, timeout_seconds, "delete_objects", {"object_names": created_objects, "confirm": True, "allow_missing": True}),
            )
            if cleanup.get("status") not in {"success", "partial"}:
                raise RuntimeError(f"delete_objects cleanup failed: {cleanup}")
            scene_index = run_optional_scene_index_smoke(sock, timeout_seconds)
            remaining = {item.get("name") for item in scene_index.get("objects", [])}
            leaked = [name for name in created_objects if name in remaining]
            if leaked:
                raise RuntimeError(f"Phase 3 cleanup leaked objects: {leaked}")
            collection_cleanup = assert_success(
                "delete_collection phase3_cleanup",
                send_command(sock, timeout_seconds, "delete_collection", {"collection_name": collection_name, "confirm": True, "require_empty": True}),
            )
            if collection_cleanup.get("status") != "success" or not collection_cleanup.get("deleted"):
                raise RuntimeError(f"delete_collection cleanup failed: {collection_cleanup}")
            print(f"PASS phase3 cleanup removed {created_objects}")


def run_optional_material_ops_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(int(time.time()))
    name = f"OVERTLI_PHASE3_MAT_ONLY_{stamp}"
    result = assert_success("create_basic_material", send_command(sock, timeout_seconds, "create_basic_material", {"name": name, "base_color": [0.2, 0.5, 1.0, 1.0]}))
    if result.get("status") != "success":
        raise RuntimeError(f"create_basic_material: {result}")


def run_optional_modifier_ops_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(int(time.time()))
    collection = f"OVERTLI_PHASE3_MOD_SMOKE_{stamp}"
    obj_name = f"OVERTLI_PHASE3_MOD_CUBE_{stamp}"
    created = assert_success("create_primitive_object", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": obj_name, "collection_name": collection}))
    obj_name = created.get("object_name", obj_name)
    try:
        added = assert_success("add_object_modifier", send_command(sock, timeout_seconds, "add_object_modifier", {"object_name": obj_name, "modifier_type": "WEIGHTED_NORMAL", "name": "OVERTLI_PHASE3_WEIGHTED_NORMAL"}))
        if added.get("status") != "success":
            raise RuntimeError(f"add_object_modifier: {added}")
    finally:
        assert_success("delete_objects modifier_cleanup", send_command(sock, timeout_seconds, "delete_objects", {"object_names": [obj_name], "confirm": True, "allow_missing": True}))
        assert_success("delete_collection modifier_cleanup", send_command(sock, timeout_seconds, "delete_collection", {"collection_name": collection, "confirm": True, "require_empty": True}))


def run_optional_collection_ops_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(int(time.time()))
    collection = f"OVERTLI_PHASE3_COLLECTION_ONLY_{stamp}"
    try:
        result = assert_success("create_collection", send_command(sock, timeout_seconds, "create_collection", {"collection_name": collection}))
        if result.get("status") != "success":
            raise RuntimeError(f"create_collection: {result}")
    finally:
        cleanup = assert_success("delete_collection collection_cleanup", send_command(sock, timeout_seconds, "delete_collection", {"collection_name": collection, "confirm": True, "require_empty": True}))
        if cleanup.get("status") != "success":
            raise RuntimeError(f"delete_collection collection_cleanup: {cleanup}")


def run_optional_verified_edit_batch_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(int(time.time()))
    collection = f"OVERTLI_PHASE3_BATCH_ONLY_{stamp}"
    obj_name = f"OVERTLI_PHASE3_BATCH_CUBE_{stamp}"
    batch = assert_success(
        "run_verified_edit_batch",
        send_command(
            sock,
            timeout_seconds,
            "run_verified_edit_batch",
            {
                "label": f"phase3_flag_batch_{stamp}",
                "artifact_root": REPO_ROOT,
                "operations": [
                    {"type": "create_collection", "params": {"collection_name": collection}},
                    {"type": "create_primitive_object", "params": {"primitive_type": "cube", "name": obj_name, "collection_name": collection}},
                ],
            },
        ),
    )
    if batch.get("status") != "success":
        raise RuntimeError(f"run_verified_edit_batch: {batch}")
    assert_success("delete_objects batch_cleanup", send_command(sock, timeout_seconds, "delete_objects", {"object_names": [obj_name], "confirm": True, "allow_missing": True}))
    assert_success("delete_collection batch_cleanup", send_command(sock, timeout_seconds, "delete_collection", {"collection_name": collection, "confirm": True, "require_empty": True}))


def run_optional_strict_block_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    response = send_command(sock, timeout_seconds, "execute_code", {"code": 'print("SMOKE_CODE_OK")'})
    if response.get("status") != "error":
        raise RuntimeError("execute_code: expected strict-mode block, but command succeeded")

    message = str(response.get("message", ""))
    if "blocked by safety policy" not in message.lower():
        raise RuntimeError(f"execute_code: expected safety-policy block, got {response}")

    safety = response.get("safety", {})
    if safety.get("mode") != "strict":
        raise RuntimeError(f"execute_code: expected strict safety metadata, got {safety}")

    print("PASS execute_code blocked by strict safety policy")


def run_optional_geometry_nodes_status_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    response = send_command(sock, timeout_seconds, "get_geometry_nodes_status")
    result = assert_success("get_geometry_nodes_status", response)
    if "enabled" not in result or "message" not in result:
        raise RuntimeError("get_geometry_nodes_status: missing enabled/message in result")


def run_optional_code_execution_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    response = send_command(sock, timeout_seconds, "execute_code", {"code": 'print("SMOKE_CODE_OK")'})
    result = assert_success("execute_code", response)
    if not result.get("executed"):
        raise RuntimeError(f"execute_code: {result}")
    if "SMOKE_CODE_OK" not in result.get("result", ""):
        raise RuntimeError("execute_code: expected smoke output not found")


def run_optional_script_registry_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    category = "phase1e_smoke"
    script_name = f"runtime_smoke_{time.time_ns()}"
    script_content = 'print("SMOKE_SCRIPT_OK")\nsmoke_value = 2 + 2\n'

    response = send_command(
        sock,
        timeout_seconds,
        "register_context_script",
        {
            "script_name": script_name,
            "script_content": script_content,
            "category": category,
            "permanent": False,
        },
    )
    register_result = assert_success("register_context_script", response)
    if register_result.get("status") != "success":
        raise RuntimeError(f"register_context_script: {register_result}")

    try:
        response = send_command(sock, timeout_seconds, "list_context_scripts", {"category": category})
        list_result = assert_success("list_context_scripts", response)
        scripts = list_result.get("scripts", {}).get(category, [])
        if not any(script.get("name") == script_name for script in scripts):
            raise RuntimeError("list_context_scripts: registered script not found")

        response = send_command(
            sock,
            timeout_seconds,
            "execute_context_script",
            {"script_name": script_name, "category": category},
        )
        execute_result = assert_success("execute_context_script", response)
        if execute_result.get("status") != "success":
            raise RuntimeError(f"execute_context_script: {execute_result}")
        output = execute_result.get("output", "")
        if "SMOKE_SCRIPT_OK" not in output:
            raise RuntimeError("execute_context_script: expected smoke output not found")
    finally:
        try:
            response = send_command(
                sock,
                timeout_seconds,
                "clear_context_scripts",
                {
                    "category": category,
                    "script_name": script_name,
                    "clear_permanent": True,
                },
            )
            clear_result = assert_success("clear_context_scripts", response)
            if clear_result.get("status") != "success":
                print(f"WARN clear_context_scripts: {clear_result}")
        except Exception as exc:
            print(f"WARN clear_context_scripts: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-test the Overtli-Blender addon socket directly.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Addon socket host (default: localhost)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Addon socket port (default: 9876)")
    parser.add_argument("--timeout", type=float, default=15.0, help="Socket timeout in seconds (default: 15.0)")
    parser.add_argument("--include-screenshot", action="store_true", help="Run the optional viewport screenshot smoke.")
    parser.add_argument(
        "--include-script-registry",
        action="store_true",
        help="Run the optional harmless script registry smoke.",
    )
    parser.add_argument(
        "--include-provider-status",
        action="store_true",
        help="Run the optional provider status smoke.",
    )
    parser.add_argument(
        "--include-safety-status",
        action="store_true",
        help="Run the optional safety status smoke.",
    )
    parser.add_argument(
        "--expect-strict-blocks",
        action="store_true",
        help="Require the addon to report strict mode and block a harmless code execution request.",
    )
    parser.add_argument(
        "--include-geometry-nodes-status",
        action="store_true",
        help="Run the optional Geometry Nodes status smoke.",
    )
    parser.add_argument(
        "--include-code-execution",
        action="store_true",
        help="Run the optional harmless code execution smoke.",
    )
    parser.add_argument("--include-scene-index", action="store_true", help="Run the Phase 2 scene index smoke.")
    parser.add_argument("--include-object-deep-info", action="store_true", help="Run the Phase 2 object deep info smoke.")
    parser.add_argument("--include-selection-info", action="store_true", help="Run the Phase 2 selection info smoke.")
    parser.add_argument("--include-scene-health", action="store_true", help="Run the Phase 2 scene health smoke.")
    parser.add_argument("--include-screenshot-pack", action="store_true", help="Run the Phase 2 viewport screenshot pack smoke.")
    parser.add_argument("--include-verification-snapshot", action="store_true", help="Run the Phase 2 verification snapshot smoke.")
    parser.add_argument("--include-edit-ops", action="store_true", help="Run the Phase 3 supported edit operations smoke.")
    parser.add_argument("--include-material-ops", action="store_true", help="Run the Phase 3 material operations smoke.")
    parser.add_argument("--include-modifier-ops", action="store_true", help="Run the Phase 3 modifier operations smoke.")
    parser.add_argument("--include-collection-ops", action="store_true", help="Run the Phase 3 collection operations smoke.")
    parser.add_argument("--include-verified-edit-batch", action="store_true", help="Run the Phase 3 verified edit batch smoke.")
    parser.add_argument("--include-workspace-safety-diff", action="store_true", help="Run the Phase 3 workspace, todo, journal, scene diff, rollback, and change-detection smoke.")
    parser.add_argument(
        "--phase2-full",
        action="store_true",
        help="Run default smoke plus safe Phase 2 inspection, screenshot-pack, and verification snapshot checks.",
    )
    parser.add_argument(
        "--phase3-full",
        action="store_true",
        help="Run a contained Phase 3 scene edit, material, modifier, collection, batch, and cleanup scenario.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
            print(f"Connected to {args.host}:{args.port}")
            run_required_smoke(sock, args.timeout)

            if args.include_screenshot:
                run_optional_screenshot_smoke(sock, args.timeout)

            if args.include_script_registry:
                run_optional_script_registry_smoke(sock, args.timeout)

            if args.include_provider_status:
                run_optional_provider_status_smoke(sock, args.timeout)

            safety_status = None
            if args.include_safety_status or args.expect_strict_blocks:
                safety_status = run_optional_safety_status_smoke(sock, args.timeout)

            if args.expect_strict_blocks:
                if safety_status is None:
                    safety_status = run_optional_safety_status_smoke(sock, args.timeout)
                if safety_status.get("mode") != "strict":
                    raise RuntimeError(f"Expected strict safety mode, got {safety_status.get('mode', 'unknown')}")
                run_optional_strict_block_smoke(sock, args.timeout)

            if args.include_geometry_nodes_status:
                run_optional_geometry_nodes_status_smoke(sock, args.timeout)

            if args.include_code_execution:
                run_optional_code_execution_smoke(sock, args.timeout)

            if args.include_scene_index:
                run_optional_scene_index_smoke(sock, args.timeout)

            if args.include_selection_info:
                run_optional_selection_info_smoke(sock, args.timeout)

            if args.include_scene_health:
                run_optional_scene_health_smoke(sock, args.timeout)

            if args.include_object_deep_info:
                run_optional_object_deep_info_smoke(sock, args.timeout)

            if args.include_screenshot_pack:
                run_optional_screenshot_pack_smoke(sock, args.timeout)

            if args.include_verification_snapshot:
                run_optional_verification_snapshot_smoke(sock, args.timeout)

            if args.phase2_full:
                run_phase2_full_smoke(sock, args.timeout)

            if args.include_edit_ops:
                run_optional_edit_ops_smoke(sock, args.timeout)

            if args.include_material_ops:
                run_optional_material_ops_smoke(sock, args.timeout)

            if args.include_modifier_ops:
                run_optional_modifier_ops_smoke(sock, args.timeout)

            if args.include_collection_ops:
                run_optional_collection_ops_smoke(sock, args.timeout)

            if args.include_verified_edit_batch:
                run_optional_verified_edit_batch_smoke(sock, args.timeout)

            if args.include_workspace_safety_diff:
                run_phase3_workspace_safety_diff_smoke(sock, args.timeout, str(int(time.time())))

            if args.phase3_full:
                run_phase3_full_smoke(sock, args.timeout)

        print("PASS smoke harness completed")
        return 0
    except Exception as exc:
        print(f"FAIL smoke harness: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

