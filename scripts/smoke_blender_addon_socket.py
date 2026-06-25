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


def run_optional_material_channel_schema_smoke(sock: socket.socket, timeout_seconds: float) -> dict:
    result = assert_success("get_material_channel_schema", send_command(sock, timeout_seconds, "get_material_channel_schema"))
    for key in ["base_color", "roughness", "metallic", "normal", "height", "displacement", "ambient_occlusion"]:
        if key not in result.get("channels", {}):
            raise RuntimeError(f"get_material_channel_schema missing channel: {key}")
    for key in ["ORM", "RMA", "MRA", "glTF_metallic_roughness"]:
        if key not in result.get("packed_map_conventions", {}):
            raise RuntimeError(f"get_material_channel_schema missing packed convention: {key}")
    return result


def run_optional_material_templates_smoke(sock: socket.socket, timeout_seconds: float) -> dict:
    result = assert_success("get_supported_material_templates", send_command(sock, timeout_seconds, "get_supported_material_templates"))
    for key in ["pbr_metal_gold", "glass_clear", "fabric_woven", "wood_procedural", "sci_fi_panel", "car_paint_basic"]:
        if key not in result.get("templates", {}):
            raise RuntimeError(f"get_supported_material_templates missing template: {key}")
    return result


def run_phase4a_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = int(time.time())
    collection_name = f"OVERTLI_PHASE4A_SMOKE_{stamp}"
    cube_name = f"OVERTLI_PHASE4A_CUBE_{stamp}"
    sphere_name = f"OVERTLI_PHASE4A_SPHERE_{stamp}"
    gold_name = f"OVERTLI_PHASE4A_GOLD_{stamp}"
    proc_name = f"OVERTLI_PHASE4A_PROC_{stamp}"
    custom_name = f"OVERTLI_PHASE4A_CUSTOM_{stamp}"
    created_objects = [cube_name, sphere_name]
    created_materials = [gold_name, proc_name, custom_name]

    try:
        run_optional_material_channel_schema_smoke(sock, timeout_seconds)
        run_optional_material_templates_smoke(sock, timeout_seconds)
        assert_success("create_collection phase4a", send_command(sock, timeout_seconds, "create_collection", {"collection_name": collection_name}))
        assert_success("create_primitive_object phase4a cube", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": cube_name, "collection_name": collection_name}))
        assert_success("create_primitive_object phase4a sphere", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "uv_sphere", "name": sphere_name, "collection_name": collection_name}))
        assert_success("create_material_from_template phase4a gold", send_command(sock, timeout_seconds, "create_material_from_template", {"template_name": "pbr_metal_gold", "material_name": gold_name, "assign_to_object": cube_name, "replace_existing": True, "verify": True}))
        assert_success("create_procedural_material phase4a proc", send_command(sock, timeout_seconds, "create_procedural_material", {"material_name": proc_name, "procedural_type": "noise", "base_color": [0.22, 0.18, 0.14, 1.0], "assign_to_object": sphere_name, "replace_existing": True, "verify": True}))
        assert_success("create_custom_material phase4a custom", send_command(sock, timeout_seconds, "create_custom_material", {"material_name": custom_name, "recipe": {"channels": {"base_color": [0.03, 0.07, 0.12, 1.0], "metallic": 0.5, "roughness": 0.34, "emission_color": [0.0, 0.8, 1.0, 1.0], "emission_strength": 1.5}, "procedural": {"enabled": True, "noise_scale": 32.0, "bump_strength": 0.025}, "preview_shape": "cube"}, "replace_existing": True, "verify": True}))
        assert_success("apply_material_to_objects phase4a", send_command(sock, timeout_seconds, "apply_material_to_objects", {"material_name": custom_name, "object_names": [cube_name], "verify": True}))
        assert_success("list_materials_deep phase4a", send_command(sock, timeout_seconds, "list_materials_deep", {"max_materials": 200}))
        assert_success("get_material_deep_info phase4a", send_command(sock, timeout_seconds, "get_material_deep_info", {"material_name": custom_name}))
        graph = assert_success("get_shader_graph phase4a", send_command(sock, timeout_seconds, "get_shader_graph", {"material_name": custom_name}))
        if "nodes" not in graph:
            raise RuntimeError(f"get_shader_graph missing nodes: {graph}")
        assert_success("add_material_node phase4a", send_command(sock, timeout_seconds, "add_material_node", {"material_name": custom_name, "node_type": "ShaderNodeTexNoise", "name": f"OVERTLI_PHASE4A_NOISE_{stamp}"}))
        assert_success("set_material_node_input phase4a", send_command(sock, timeout_seconds, "set_material_node_input", {"material_name": custom_name, "node_name": "Principled BSDF", "input_name": "Roughness", "value": 0.41}))
        missing_map = send_command(sock, timeout_seconds, "bind_material_texture_map", {"material_name": custom_name, "map_kind": "roughness_map", "texture_path": os.path.join(REPO_ROOT, ".overtli_blender", "material_test_textures", "missing_roughness.png"), "strict_file_exists": True})
        if missing_map.get("status") != "success" or missing_map.get("result", {}).get("status") != "error":
            raise RuntimeError(f"bind_material_texture_map should reject missing strict file: {missing_map}")
        print("PASS bind_material_texture_map missing-file validation")
        assert_success("bind_material_texture_map phase4a metadata", send_command(sock, timeout_seconds, "bind_material_texture_map", {"material_name": custom_name, "map_kind": "orm_map", "texture_path": os.path.join(REPO_ROOT, ".overtli_blender", "material_test_textures", "OVERTLI_PHASE4A_ORM.png"), "strict_file_exists": False, "connect": True, "verify": True}))
        assert_success("create_material_preview phase4a", send_command(sock, timeout_seconds, "create_material_preview", {"material_name": custom_name, "preview_shape": "sphere", "artifact_root": REPO_ROOT}))
        assert_success("run_material_workflow_batch phase4a", send_command(sock, timeout_seconds, "run_material_workflow_batch", {"label": "Phase 4A smoke batch", "artifact_root": REPO_ROOT, "operations": [{"command": "create_material_variant", "params": {"source_material_name": custom_name, "variant_name": f"{custom_name}_VARIANT", "overrides": {"roughness": 0.52}, "replace_existing": True, "verify": True}}, {"command": "create_material_preview", "params": {"material_name": f"{custom_name}_VARIANT", "artifact_root": REPO_ROOT, "include_snapshot": False}}]}))
        created_materials.append(f"{custom_name}_VARIANT")
        assert_success("get_scene_health phase4a", send_command(sock, timeout_seconds, "get_scene_health"))
        assert_success("get_scene_index phase4a", send_command(sock, timeout_seconds, "get_scene_index", {"max_objects": 200}))
    finally:
        cleanup = assert_success("delete_objects phase4a_cleanup", send_command(sock, timeout_seconds, "delete_objects", {"object_names": created_objects, "confirm": True, "allow_missing": True}))
        if cleanup.get("status") not in {"success", "partial"}:
            raise RuntimeError(f"Phase 4A object cleanup failed: {cleanup}")
        material_cleanup = assert_success("delete_materials phase4a_cleanup", send_command(sock, timeout_seconds, "delete_materials", {"material_names": created_materials, "confirm": True, "allow_missing": True}))
        if material_cleanup.get("status") not in {"success", "partial"}:
            raise RuntimeError(f"Phase 4A material cleanup failed: {material_cleanup}")
        collection_cleanup = assert_success("delete_collection phase4a_cleanup", send_command(sock, timeout_seconds, "delete_collection", {"collection_name": collection_name, "confirm": True, "require_empty": True}))
        if collection_cleanup.get("status") != "success":
            raise RuntimeError(f"Phase 4A collection cleanup failed: {collection_cleanup}")
        scene_index = assert_success("get_scene_index phase4a_cleanup_probe", send_command(sock, timeout_seconds, "get_scene_index", {"max_objects": 500}))
        materials = assert_success("list_materials_deep phase4a_cleanup_probe", send_command(sock, timeout_seconds, "list_materials_deep", {"max_materials": 500}))
        object_leftovers = [obj.get("name") for obj in scene_index.get("objects", []) if str(obj.get("name", "")).startswith("OVERTLI_PHASE4A_")]
        collection_leftovers = [col.get("name") for col in scene_index.get("collections", []) if str(col.get("name", "")).startswith("OVERTLI_PHASE4A_")]
        material_leftovers = [mat.get("name") for mat in materials.get("materials", []) if str(mat.get("name", "")).startswith("OVERTLI_PHASE4A_")]
        if object_leftovers or collection_leftovers or material_leftovers:
            raise RuntimeError(f"Phase 4A cleanup leaked data: objects={object_leftovers}, collections={collection_leftovers}, materials={material_leftovers}")
        print("PASS phase4a cleanup removed smoke objects, collection, and materials")


def run_phase4b_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = time.time_ns()
    collection_name = f"OVERTLI_PHASE4B_SMOKE_{stamp}"
    mesh_name = f"OVERTLI_PHASE4B_MESH_{stamp}"
    material_name = f"OVERTLI_PHASE4B_MAT_{stamp}"
    group_name = f"OVERTLI_PHASE4B_TOP_{stamp}"
    shape_name = f"OVERTLI_PHASE4B_SHAPE_{stamp}"
    region_shape_name = f"OVERTLI_PHASE4B_REGION_{stamp}"
    sculpt_shape_name = f"OVERTLI_PHASE4B_SCULPT_SHAPE_{stamp}"
    lattice_name = f"OVERTLI_PHASE4B_LATTICE_{stamp}"
    modifier_name = f"OVERTLI_PHASE4B_SIMPLE_DEFORM_{stamp}"
    style_material_name = f"OVERTLI_PHASE4B_STYLE_MAT_{stamp}"
    paint_material_name = f"OVERTLI_PHASE4B_PAINT_MAT_{stamp}"
    paint_image_name = f"OVERTLI_PHASE4B_PAINT_IMAGE_{stamp}"

    try:
        assert_success("get_method_plan phase4b", send_command(sock, timeout_seconds, "get_method_plan", {"intent": "make a selected region larger safely"}))
        assert_success("list_operation_playbooks phase4b", send_command(sock, timeout_seconds, "list_operation_playbooks"))
        assert_success("get_tricks_knowledge_base phase4b", send_command(sock, timeout_seconds, "get_tricks_knowledge_base", {"category": "deformation"}))
        assert_success("get_anti_pattern_rules phase4b", send_command(sock, timeout_seconds, "get_anti_pattern_rules"))
        assert_success("get_modifier_recipes phase4b", send_command(sock, timeout_seconds, "get_modifier_recipes"))
        assert_success("scan_blender_asset_libraries phase4b", send_command(sock, timeout_seconds, "scan_blender_asset_libraries", {"max_items": 50}))
        assert_success("create_collection phase4b", send_command(sock, timeout_seconds, "create_collection", {"collection_name": collection_name}))
        assert_success("create_basic_material phase4b", send_command(sock, timeout_seconds, "create_basic_material", {"name": material_name, "base_color": [0.25, 0.55, 0.95, 1.0], "replace_existing": True}))
        created = assert_success("create_primitive_object phase4b mesh", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": mesh_name, "collection_name": collection_name, "material_name": material_name}))
        mesh_name = created.get("object_name", mesh_name)
        assert_success("create_style_material phase4b", send_command(sock, timeout_seconds, "create_style_material", {"style_name": "sci_fi", "material_name": style_material_name, "assign_to_object": mesh_name, "verify": True}))
        assert_success("create_paintable_texture phase4b", send_command(sock, timeout_seconds, "create_paintable_texture", {"object_name": mesh_name, "material_name": paint_material_name, "image_name": paint_image_name, "width": 64, "height": 64, "base_color": [0.1, 0.2, 0.3, 1.0], "verify": True}))
        assert_success("preview_asset phase4b", send_command(sock, timeout_seconds, "preview_asset", {"asset_name": style_material_name, "asset_type": "material", "artifact_root": REPO_ROOT, "include_snapshot": True}))
        assert_success("get_selection_deep_info phase4b", send_command(sock, timeout_seconds, "get_selection_deep_info", {"max_components": 128}))
        summary = assert_success("get_mesh_component_summary phase4b", send_command(sock, timeout_seconds, "get_mesh_component_summary", {"object_name": mesh_name}))
        if summary.get("mesh_stats", {}).get("vertices", 0) <= 0:
            raise RuntimeError(f"get_mesh_component_summary missing vertices: {summary}")
        assert_success("list_uv_maps phase4b", send_command(sock, timeout_seconds, "list_uv_maps", {"object_name": mesh_name}))
        assert_success("measure_object phase4b", send_command(sock, timeout_seconds, "measure_object", {"object_name": mesh_name}))
        assert_success("create_vertex_group phase4b", send_command(sock, timeout_seconds, "create_vertex_group", {"object_name": mesh_name, "group_name": group_name, "selection_mode": "by_axis", "rule": {"axis": "z", "operator": ">=", "threshold": 0.0}, "weight": 1.0, "replace_existing": True}))
        groups = assert_success("list_vertex_groups phase4b", send_command(sock, timeout_seconds, "list_vertex_groups", {"object_name": mesh_name}))
        if not any(group.get("name") == group_name for group in groups.get("vertex_groups", [])):
            raise RuntimeError(f"list_vertex_groups missing smoke group: {groups}")
        assert_success("score_selection_confidence phase4b", send_command(sock, timeout_seconds, "score_selection_confidence", {"object_name": mesh_name, "region": {"vertex_group": group_name}}))
        assert_success("update_vertex_group_weights phase4b", send_command(sock, timeout_seconds, "update_vertex_group_weights", {"object_name": mesh_name, "group_name": group_name, "weight": 0.9, "mode": "replace", "rule": {"selection_mode": "by_axis", "axis": "z", "operator": ">=", "threshold": 0.0}}))
        assert_success("create_shape_key phase4b", send_command(sock, timeout_seconds, "create_shape_key", {"object_name": mesh_name, "shape_key_name": shape_name, "replace_existing": True}))
        assert_success("edit_shape_key_offsets phase4b", send_command(sock, timeout_seconds, "edit_shape_key_offsets", {"object_name": mesh_name, "shape_key_name": shape_name, "vertex_group_name": group_name, "deformation": {"mode": "inflate_along_normals", "amount": 0.05}, "confirm": True, "verify": True}))
        assert_success("update_shape_key_value phase4b", send_command(sock, timeout_seconds, "update_shape_key_value", {"object_name": mesh_name, "shape_key_name": shape_name, "value": 0.75}))
        keys = assert_success("list_shape_keys phase4b", send_command(sock, timeout_seconds, "list_shape_keys", {"object_name": mesh_name}))
        if not any(key.get("name") == shape_name for key in keys.get("shape_keys", [])):
            raise RuntimeError(f"list_shape_keys missing smoke key: {keys}")
        lattice = assert_success("create_lattice_deformer phase4b", send_command(sock, timeout_seconds, "create_lattice_deformer", {"target_object_name": mesh_name, "lattice_name": lattice_name, "collection_name": collection_name, "resolution": [2, 2, 2], "padding": 0.1, "add_modifier": True, "verify": True}))
        assert_success("update_lattice_deformer phase4b", send_command(sock, timeout_seconds, "update_lattice_deformer", {"lattice_name": lattice.get("lattice_name", lattice_name), "deformation": {"mode": "move_top", "amount": 0.03}, "confirm": True, "verify": True}))
        assert_success("apply_lattice_to_object phase4b", send_command(sock, timeout_seconds, "apply_lattice_to_object", {"target_object_name": mesh_name, "lattice_name": lattice.get("lattice_name", lattice_name), "create_if_missing": True}))
        assert_success("add_deformation_modifier phase4b", send_command(sock, timeout_seconds, "add_deformation_modifier", {"object_name": mesh_name, "modifier_type": "SIMPLE_DEFORM", "name": modifier_name, "properties": {"deform_method": "TAPER", "deform_axis": "Z", "factor": 0.05}, "vertex_group_name": group_name, "verify": True}))
        assert_success("update_deformation_modifier phase4b", send_command(sock, timeout_seconds, "update_deformation_modifier", {"object_name": mesh_name, "modifier_name": modifier_name, "properties": {"factor": 0.04}, "vertex_group_name": group_name}))
        assert_success("create_region_deformation phase4b", send_command(sock, timeout_seconds, "create_region_deformation", {"object_name": mesh_name, "region": {"selector": "vertex_group", "vertex_group": group_name}, "method": "shape_key", "name": region_shape_name, "deformation": {"mode": "translate", "vector": [0.0, 0.0, 0.04]}, "confirm": True, "verify": True}))
        assert_success("create_proportional_deformation phase4b", send_command(sock, timeout_seconds, "create_proportional_deformation", {"object_name": mesh_name, "region": {"selector": "vertex_group", "vertex_group": group_name}, "method": "shape_key", "name": f"OVERTLI_PHASE4B_PROP_{stamp}", "deformation": {"mode": "translate", "vector": [0.0, 0.0, 0.02], "falloff": "smooth"}, "confirm": True, "verify": True}))
        assert_success("get_sculpt_status phase4b", send_command(sock, timeout_seconds, "get_sculpt_status", {"object_name": mesh_name}))
        assert_success("create_sculpt_mask_from_vertex_group phase4b", send_command(sock, timeout_seconds, "create_sculpt_mask_from_vertex_group", {"object_name": mesh_name, "vertex_group_name": group_name, "mask_name": f"OVERTLI_PHASE4B_MASK_{stamp}", "confirm": True}))
        assert_success("run_shape_key_sculpt_workflow phase4b", send_command(sock, timeout_seconds, "run_shape_key_sculpt_workflow", {"object_name": mesh_name, "vertex_group_name": group_name, "shape_key_name": sculpt_shape_name, "brush_action": "inflate", "amount": 0.025, "confirm": True, "verify": True}))
        batch = assert_success("run_deformation_workflow_batch phase4b", send_command(sock, timeout_seconds, "run_deformation_workflow_batch", {"label": f"phase4b_batch_{stamp}", "operations": [{"command": "get_mesh_component_summary", "params": {"object_name": mesh_name}}, {"command": "update_shape_key_value", "params": {"object_name": mesh_name, "shape_key_name": shape_name, "value": 0.5}}]}))
        if batch.get("status") != "success":
            raise RuntimeError(f"run_deformation_workflow_batch failed: {batch}")
        assert_success("get_scene_health phase4b", send_command(sock, timeout_seconds, "get_scene_health"))
        assert_success("get_scene_index phase4b", send_command(sock, timeout_seconds, "get_scene_index", {"max_objects": 300}))
    finally:
        try:
            send_command(sock, timeout_seconds, "remove_lattice_deformer", {"target_object_name": mesh_name, "lattice_name": lattice_name, "remove_modifier": True, "delete_lattice_object": True, "confirm": True})
        except Exception as exc:
            print(f"WARN phase4b lattice cleanup: {exc}")
        try:
            send_command(sock, timeout_seconds, "delete_shape_keys", {"object_name": mesh_name, "shape_key_names": [shape_name, region_shape_name, sculpt_shape_name, f"OVERTLI_PHASE4B_PROP_{stamp}"], "confirm": True, "allow_basis": False})
        except Exception as exc:
            print(f"WARN phase4b shape key cleanup: {exc}")
        try:
            send_command(sock, timeout_seconds, "delete_vertex_groups", {"object_name": mesh_name, "group_names": [group_name], "confirm": True})
        except Exception as exc:
            print(f"WARN phase4b vertex group cleanup: {exc}")
        assert_success("delete_objects phase4b_cleanup", send_command(sock, timeout_seconds, "delete_objects", {"object_names": [mesh_name, lattice_name], "confirm": True, "allow_missing": True}))
        assert_success("delete_materials phase4b_cleanup", send_command(sock, timeout_seconds, "delete_materials", {"material_names": [material_name, style_material_name, paint_material_name], "confirm": True, "allow_missing": True}))
        assert_success("delete_images phase4b_cleanup", send_command(sock, timeout_seconds, "delete_images", {"image_names": [paint_image_name], "confirm": True, "allow_missing": True}))
        assert_success("delete_collection phase4b_cleanup", send_command(sock, timeout_seconds, "delete_collection", {"collection_name": collection_name, "confirm": True, "require_empty": True}))
        scene_index = assert_success("get_scene_index phase4b_cleanup_probe", send_command(sock, timeout_seconds, "get_scene_index", {"max_objects": 500}))
        materials = assert_success("list_materials_deep phase4b_cleanup_probe", send_command(sock, timeout_seconds, "list_materials_deep", {"max_materials": 500}))
        assets = assert_success("scan_blender_asset_libraries phase4b_cleanup_probe", send_command(sock, timeout_seconds, "scan_blender_asset_libraries", {"max_items": 1000}))
        object_leftovers = [obj.get("name") for obj in scene_index.get("objects", []) if str(obj.get("name", "")).startswith("OVERTLI_PHASE4B_")]
        collection_leftovers = [col.get("name") for col in scene_index.get("collections", []) if str(col.get("name", "")).startswith("OVERTLI_PHASE4B_")]
        material_leftovers = [mat.get("name") for mat in materials.get("materials", []) if str(mat.get("name", "")).startswith("OVERTLI_PHASE4B_")]
        image_leftovers = [asset.get("name") for asset in assets.get("assets", []) if asset.get("type") == "image" and str(asset.get("name", "")).startswith("OVERTLI_PHASE4B_")]
        if object_leftovers or collection_leftovers or material_leftovers or image_leftovers:
            raise RuntimeError(f"Phase 4B cleanup leaked data: objects={object_leftovers}, collections={collection_leftovers}, materials={material_leftovers}, images={image_leftovers}")
        print("PASS phase4b cleanup removed smoke objects, collection, materials, images, lattice, groups, and shape keys")


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
    parser.add_argument("--include-material-intelligence", action="store_true", help="Run Phase 4A material intelligence schema, template, list, and graph smoke.")
    parser.add_argument("--include-material-channel-schema", action="store_true", help="Run the Phase 4A material channel schema smoke.")
    parser.add_argument("--include-material-templates", action="store_true", help="Run the Phase 4A supported material templates smoke.")
    parser.add_argument("--include-procedural-material", action="store_true", help="Run the Phase 4A procedural material path via the full contained scenario.")
    parser.add_argument("--include-custom-material", action="store_true", help="Run the Phase 4A custom material path via the full contained scenario.")
    parser.add_argument("--include-texture-map-slots", action="store_true", help="Run the Phase 4A texture map slot validation path via the full contained scenario.")
    parser.add_argument("--include-shader-graph", action="store_true", help="Run the Phase 4A shader graph path via the full contained scenario.")
    parser.add_argument("--include-material-preview", action="store_true", help="Run the Phase 4A material preview path via the full contained scenario.")
    parser.add_argument("--include-material-workflow-batch", action="store_true", help="Run the Phase 4A material workflow batch path via the full contained scenario.")
    parser.add_argument("--include-selection-deep-info", action="store_true", help="Run the Phase 4B deep selection info smoke.")
    parser.add_argument("--include-vertex-group-ops", action="store_true", help="Run Phase 4B vertex group operations via the full contained scenario.")
    parser.add_argument("--include-shape-key-ops", action="store_true", help="Run Phase 4B shape key operations via the full contained scenario.")
    parser.add_argument("--include-lattice-ops", action="store_true", help="Run Phase 4B lattice operations via the full contained scenario.")
    parser.add_argument("--include-deformation-modifier-ops", action="store_true", help="Run Phase 4B deformation modifier operations via the full contained scenario.")
    parser.add_argument("--include-region-deformation", action="store_true", help="Run Phase 4B region deformation via the full contained scenario.")
    parser.add_argument("--include-deformation-workflow-batch", action="store_true", help="Run Phase 4B deformation workflow batch via the full contained scenario.")
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
    parser.add_argument(
        "--phase4a-full",
        action="store_true",
        help="Run a contained Phase 4A material intelligence, shader graph, texture slot, preview, batch, and cleanup scenario.",
    )
    parser.add_argument(
        "--phase4b-full",
        action="store_true",
        help="Run a contained Phase 4B selection, vertex group, shape key, lattice, deformation modifier, batch, and cleanup scenario.",
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

            if args.include_material_channel_schema:
                run_optional_material_channel_schema_smoke(sock, args.timeout)

            if args.include_material_templates:
                run_optional_material_templates_smoke(sock, args.timeout)

            if args.include_material_intelligence:
                run_optional_material_channel_schema_smoke(sock, args.timeout)
                run_optional_material_templates_smoke(sock, args.timeout)
                assert_success("list_materials_deep", send_command(sock, args.timeout, "list_materials_deep", {"max_materials": 100}))

            if (
                args.phase4a_full
                or args.include_procedural_material
                or args.include_custom_material
                or args.include_texture_map_slots
                or args.include_shader_graph
                or args.include_material_preview
                or args.include_material_workflow_batch
            ):
                run_phase4a_full_smoke(sock, args.timeout)

            if args.include_selection_deep_info:
                assert_success("get_selection_deep_info", send_command(sock, args.timeout, "get_selection_deep_info", {"max_components": 100}))

            if (
                args.phase4b_full
                or args.include_vertex_group_ops
                or args.include_shape_key_ops
                or args.include_lattice_ops
                or args.include_deformation_modifier_ops
                or args.include_region_deformation
                or args.include_deformation_workflow_batch
            ):
                run_phase4b_full_smoke(sock, args.timeout)

        print("PASS smoke harness completed")
        return 0
    except Exception as exc:
        print(f"FAIL smoke harness: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

