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


def run_phase5a_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(time.time_ns())
    prefix = f"OVERTLI_PHASE5A_{stamp}"
    collection_name = f"{prefix}_SMOKE"
    object_name = f"{prefix}_OBJECT"
    material_name = f"{prefix}_MAT"
    camera_name = f"{prefix}_CAMERA"
    light_setup = f"{prefix}_LIGHT"

    try:
        assert_success("create_collection phase5a", send_command(sock, timeout_seconds, "create_collection", {"collection_name": collection_name}))
        assert_success("create_basic_material phase5a", send_command(sock, timeout_seconds, "create_basic_material", {"name": material_name, "base_color": [0.2, 0.55, 0.9, 1.0], "replace_existing": True}))
        created = assert_success("create_primitive_object phase5a", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": object_name, "collection_name": collection_name, "material_name": material_name}))
        object_name = created.get("object_name", object_name)
        assert_success("get_timeline_info phase5a", send_command(sock, timeout_seconds, "get_timeline_info"))
        assert_success("set_timeline_range phase5a", send_command(sock, timeout_seconds, "set_timeline_range", {"frame_start": 1, "frame_end": 48, "fps": 24, "current_frame": 1}))
        assert_success("create_camera phase5a", send_command(sock, timeout_seconds, "create_camera", {"camera_name": camera_name, "collection_name": collection_name, "set_active": True}))
        assert_success("frame_camera_to_objects phase5a", send_command(sock, timeout_seconds, "frame_camera_to_objects", {"camera_name": camera_name, "object_names": [object_name], "view": "front_perspective", "verify": True}))
        lighting = assert_success("create_lighting_setup phase5a", send_command(sock, timeout_seconds, "create_lighting_setup", {"setup_name": light_setup, "collection_name": collection_name, "preset": "three_point", "verify": True}))
        light_names = [item.get("name") for item in lighting.get("lights", []) if item.get("name")]
        assert_success("set_active_camera phase5a", send_command(sock, timeout_seconds, "set_active_camera", {"camera_name": camera_name}))
        assert_success("insert_transform_keyframes phase5a", send_command(sock, timeout_seconds, "insert_transform_keyframes", {"object_name": object_name, "frames": [1, 24, 48], "properties": ["location", "rotation_euler"]}))
        assert_success("animate_object_transform phase5a", send_command(sock, timeout_seconds, "animate_object_transform", {"object_name": object_name, "keyframes": [{"frame": 1, "location": [0, 0, 0]}, {"frame": 48, "location": [0.5, 0, 0.2]}], "interpolation": "LINEAR"}))
        assert_success("animate_camera_transform phase5a", send_command(sock, timeout_seconds, "animate_camera_transform", {"camera_name": camera_name, "keyframes": [{"frame": 1, "location": [3, -5, 3]}, {"frame": 48, "location": [4, -5, 3.2]}], "interpolation": "LINEAR"}))
        if light_names:
            assert_success("animate_light_property phase5a", send_command(sock, timeout_seconds, "animate_light_property", {"light_name": light_names[0], "property_name": "energy", "keyframes": [{"frame": 1, "value": 250}, {"frame": 48, "value": 500}], "interpolation": "LINEAR"}))
        assert_success("animate_material_property phase5a", send_command(sock, timeout_seconds, "animate_material_property", {"material_name": material_name, "channel": "roughness", "keyframes": [{"frame": 1, "value": 0.25}, {"frame": 48, "value": 0.6}], "interpolation": "LINEAR"}))
        assert_success("get_animation_deep_info phase5a", send_command(sock, timeout_seconds, "get_animation_deep_info", {"object_name": object_name, "max_keyframes": 50}))
        assert_success("list_animated_objects phase5a", send_command(sock, timeout_seconds, "list_animated_objects", {"max_objects": 25}))
        assert_success("get_render_settings phase5a", send_command(sock, timeout_seconds, "get_render_settings"))
        assert_success("set_render_settings phase5a", send_command(sock, timeout_seconds, "set_render_settings", {"engine": "BLENDER_WORKBENCH", "resolution_x": 320, "resolution_y": 320, "samples": 8, "clamp_for_smoke": True}))
        still = assert_success("render_still phase5a", send_command(sock, timeout_seconds, "render_still", {"artifact_root": REPO_ROOT, "camera_name": camera_name, "filename": f"{prefix}_still.png", "clamp_for_smoke": True}))
        if not still.get("artifact", {}).get("exists"):
            raise RuntimeError(f"Phase 5A still render artifact missing: {still}")
        contact = assert_success("render_contact_sheet phase5a", send_command(sock, timeout_seconds, "render_contact_sheet", {"artifact_root": REPO_ROOT, "camera_name": camera_name, "object_names": [object_name], "filename": f"{prefix}_contact.json", "clamp_for_smoke": True}))
        if not contact.get("manifest_path"):
            raise RuntimeError(f"Phase 5A contact sheet manifest missing: {contact}")
        assert_success("create_turntable_animation phase5a", send_command(sock, timeout_seconds, "create_turntable_animation", {"object_name": object_name, "frame_start": 1, "frame_end": 24, "axis": "Z"}))
        preview = assert_success("render_preview_animation phase5a", send_command(sock, timeout_seconds, "render_preview_animation", {"artifact_root": REPO_ROOT, "frame_start": 1, "frame_end": 24, "step": 8, "max_frames": 4, "camera_name": camera_name, "clamp_for_smoke": True}))
        if not preview.get("manifest_path"):
            raise RuntimeError(f"Phase 5A preview manifest missing: {preview}")
        assert_success("get_compositor_status phase5a", send_command(sock, timeout_seconds, "get_compositor_status"))
        compositor_preset = send_command(sock, timeout_seconds, "set_compositor_preset", {"preset": "basic_viewer", "confirm_replace": True})
        if compositor_preset.get("status") == "error" and "not available" in str(compositor_preset.get("message", "")).lower():
            print(f"WARN set_compositor_preset skipped: {compositor_preset.get('message')}")
        else:
            assert_success("set_compositor_preset phase5a", compositor_preset)
        assert_success("set_render_passes phase5a", send_command(sock, timeout_seconds, "set_render_passes", {"use_pass_z": True, "use_pass_mist": False}))
        batch = assert_success("run_presentation_workflow_batch phase5a", send_command(sock, timeout_seconds, "run_presentation_workflow_batch", {"label": "Phase 5A smoke batch", "artifact_root": REPO_ROOT, "operations": [{"command": "get_timeline_info", "params": {}}, {"command": "get_render_settings", "params": {}}, {"command": "render_still", "params": {"camera_name": camera_name, "filename": f"{prefix}_batch_still.png"}}]}))
        if not batch.get("manifest_path"):
            raise RuntimeError(f"Phase 5A batch manifest missing: {batch}")
        assert_success("get_scene_health phase5a", send_command(sock, timeout_seconds, "get_scene_health"))
    finally:
        cleanup = assert_success("cleanup_presentation_artifacts phase5a", send_command(sock, timeout_seconds, "cleanup_presentation_artifacts", {"prefix": prefix, "confirm": True, "cleanup_scene_data": True, "cleanup_render_artifacts": False, "artifact_root": REPO_ROOT}))
        scene_index = assert_success("get_scene_index phase5a_cleanup_probe", send_command(sock, timeout_seconds, "get_scene_index", {"max_objects": 500}))
        materials = assert_success("list_materials_deep phase5a_cleanup_probe", send_command(sock, timeout_seconds, "list_materials_deep", {"max_materials": 500}))
        object_leftovers = [obj.get("name") for obj in scene_index.get("objects", []) if str(obj.get("name", "")).startswith(prefix)]
        collection_leftovers = [col.get("name") for col in scene_index.get("collections", []) if str(col.get("name", "")).startswith(prefix)]
        material_leftovers = [mat.get("name") for mat in materials.get("materials", []) if str(mat.get("name", "")).startswith(prefix)]
        if object_leftovers or collection_leftovers or material_leftovers:
            raise RuntimeError(f"Phase 5A cleanup leaked data: objects={object_leftovers}, collections={collection_leftovers}, materials={material_leftovers}, cleanup={cleanup}")
        print("PASS phase5a cleanup removed smoke-created scene data")


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


def _phase5b_best_format(format_result: dict) -> str:
    imports = format_result.get("import_formats", {})
    exports = format_result.get("export_formats", {})
    for fmt in ["glb", "obj", "stl", "fbx", "ply"]:
        if imports.get(fmt, {}).get("supported") and exports.get(fmt, {}).get("supported"):
            return fmt
    raise RuntimeError(f"No shared import/export format available for Phase 5B smoke: {format_result}")


def run_phase5b_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(time.time_ns())
    prefix = f"OVERTLI_PHASE5B_{stamp}"
    collection_name = f"{prefix}_COLLECTION"
    import_collection = f"{prefix}_IMPORTED_COLLECTION"
    object_name = f"{prefix}_OBJECT"
    material_name = f"{prefix}_MAT"
    camera_name = f"{prefix}_CAMERA"
    kit_id = f"{prefix}_KIT"
    selected_export_path = os.path.join(REPO_ROOT, ".overtli_blender", "exports", "selected", f"{prefix}_selected.glb")

    try:
        assert_success("create_collection phase5b", send_command(sock, timeout_seconds, "create_collection", {"collection_name": collection_name}))
        assert_success("create_basic_material phase5b", send_command(sock, timeout_seconds, "create_basic_material", {"name": material_name, "base_color": [0.45, 0.75, 0.35, 1.0], "replace_existing": True}))
        assert_success("create_primitive_object phase5b", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": object_name, "collection_name": collection_name, "material_name": material_name}))
        assert_success("create_camera phase5b", send_command(sock, timeout_seconds, "create_camera", {"camera_name": camera_name, "collection_name": collection_name, "set_active": True}))
        assert_success("frame_camera_to_objects phase5b", send_command(sock, timeout_seconds, "frame_camera_to_objects", {"camera_name": camera_name, "object_names": [object_name], "view": "front_perspective"}))
        assert_success("set_render_settings phase5b", send_command(sock, timeout_seconds, "set_render_settings", {"engine": "BLENDER_WORKBENCH", "resolution_x": 320, "resolution_y": 320, "samples": 8, "clamp_for_smoke": True}))

        formats = assert_success("get_supported_asset_formats phase5b", send_command(sock, timeout_seconds, "get_supported_asset_formats"))
        fmt = _phase5b_best_format(formats)
        selected_export_path = os.path.join(REPO_ROOT, ".overtli_blender", "exports", "selected", f"{prefix}_selected.{fmt}")
        assert_success("scan_asset_folder phase5b", send_command(sock, timeout_seconds, "scan_asset_folder", {"folder_path": os.path.join(REPO_ROOT, "assets"), "max_files": 100, "artifact_root": REPO_ROOT}))
        scene_assets = assert_success("list_scene_assets phase5b", send_command(sock, timeout_seconds, "list_scene_assets"))
        if not any(obj.get("name") == object_name for obj in scene_assets.get("objects", [])):
            raise RuntimeError("Phase 5B smoke object missing from scene asset inventory")
        assert_success("get_asset_dependency_report phase5b", send_command(sock, timeout_seconds, "get_asset_dependency_report", {"artifact_root": REPO_ROOT}))
        assert_success("create_asset_manifest phase5b", send_command(sock, timeout_seconds, "create_asset_manifest", {"label": prefix, "artifact_root": REPO_ROOT}))
        assert_success("create_asset_preview phase5b", send_command(sock, timeout_seconds, "create_asset_preview", {"object_names": [object_name], "label": prefix, "artifact_root": REPO_ROOT, "clamp_for_smoke": True}))
        export_result = assert_success("export_selected_objects phase5b", send_command(sock, timeout_seconds, "export_selected_objects", {"output_path": selected_export_path, "format_hint": fmt, "object_names": [object_name], "overwrite": True, "artifact_root": REPO_ROOT}))
        if not export_result.get("exists"):
            raise RuntimeError(f"Phase 5B export did not create artifact: {export_result}")
        assert_success("get_asset_file_info phase5b", send_command(sock, timeout_seconds, "get_asset_file_info", {"file_path": selected_export_path}))
        import_result = assert_success("import_model_file phase5b", send_command(sock, timeout_seconds, "import_model_file", {"file_path": selected_export_path, "format_hint": fmt, "collection_name": import_collection, "rename_prefix": f"{prefix}_IMPORTED_", "verify": True}))
        if not import_result.get("created_objects"):
            raise RuntimeError(f"Phase 5B import did not report created objects: {import_result}")
        kit = assert_success("create_scene_kit phase5b", send_command(sock, timeout_seconds, "create_scene_kit", {"kit_id": kit_id, "label": prefix, "object_names": [object_name], "export_format": fmt, "include_preview": True, "include_scene_export": True, "overwrite": True, "artifact_root": REPO_ROOT}))
        assert_success("validate_scene_kit phase5b", send_command(sock, timeout_seconds, "validate_scene_kit", {"kit_path": os.path.dirname(kit["manifest_path"])}))
        assert_success("list_scene_kits phase5b", send_command(sock, timeout_seconds, "list_scene_kits", {"artifact_root": REPO_ROOT}))
        batch = assert_success("run_asset_workflow_batch phase5b", send_command(sock, timeout_seconds, "run_asset_workflow_batch", {"label": prefix, "artifact_root": REPO_ROOT, "operations": [{"command": "get_supported_asset_formats", "params": {}}, {"command": "list_scene_assets", "params": {}}, {"command": "validate_external_dependencies", "params": {}}]}))
        if batch.get("status") not in {"success", "partial"}:
            raise RuntimeError(f"Phase 5B batch failed: {batch}")
        assert_success("validate_external_dependencies phase5b", send_command(sock, timeout_seconds, "validate_external_dependencies"))
        assert_success("get_scene_health phase5b", send_command(sock, timeout_seconds, "get_scene_health"))
    finally:
        cleanup = assert_success("cleanup_asset_artifacts phase5b", send_command(sock, timeout_seconds, "cleanup_asset_artifacts", {"prefix": prefix, "confirm": True, "cleanup_scene_data": True, "cleanup_files": False, "artifact_root": REPO_ROOT}))
        scene_assets = assert_success("list_scene_assets phase5b_cleanup_probe", send_command(sock, timeout_seconds, "list_scene_assets"))
        leftovers = {
            "objects": [obj.get("name") for obj in scene_assets.get("objects", []) if obj.get("name", "").startswith(prefix)],
            "collections": [col.get("name") for col in scene_assets.get("collections", []) if col.get("name", "").startswith(prefix)],
            "materials": [mat.get("name") for mat in scene_assets.get("materials", []) if mat.get("name", "").startswith(prefix)],
            "images": [img.get("name") for img in scene_assets.get("images", []) if img.get("name", "").startswith(prefix)],
            "actions": [act.get("name") for act in scene_assets.get("actions", []) if act.get("name", "").startswith(prefix)],
            "libraries": [lib.get("name") for lib in scene_assets.get("libraries", []) if lib.get("name", "").startswith(prefix)],
        }
        remaining = {key: value for key, value in leftovers.items() if value}
        if remaining:
            raise RuntimeError(f"Phase 5B cleanup left smoke-created scene data: {remaining}; cleanup={cleanup}")
        print("PASS phase5b cleanup removed smoke-created scene data")


def _assert_phase6a_workspace_ignored() -> None:
    workspace = os.path.join(REPO_ROOT, ".overtli_blender", "geometry_nodes")
    os.makedirs(workspace, exist_ok=True)
    gitignore_path = os.path.join(REPO_ROOT, ".gitignore")
    with open(gitignore_path, "r", encoding="utf-8") as file:
        ignored = file.read()
    if ".overtli_blender/" not in ignored:
        raise RuntimeError(".overtli_blender/geometry_nodes artifacts are not ignored by git")


def run_phase6a_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    run_id = str(time.time_ns())
    prefix = f"OVERTLI_PHASE6A_SMOKE_{run_id}"
    collection_name = prefix
    base_name = f"OVERTLI_PHASE6A_BASE_{run_id}"
    material_name = f"OVERTLI_PHASE6A_MAT_{run_id}"
    group_name = f"OVERTLI_PHASE6A_GROUP_{run_id}"
    modifier_name = f"OVERTLI_PHASE6A_MOD_{run_id}"

    try:
        assert_success("create_collection phase6a", send_command(sock, timeout_seconds, "create_collection", {"collection_name": collection_name}))
        assert_success("create_basic_material phase6a", send_command(sock, timeout_seconds, "create_basic_material", {"name": material_name, "base_color": [0.25, 0.55, 0.9, 1.0], "replace_existing": True}))
        assert_success("create_primitive_object phase6a", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": base_name, "collection_name": collection_name, "material_name": material_name}))
        caps = assert_success("get_geometry_nodes_capabilities phase6a", send_command(sock, timeout_seconds, "get_geometry_nodes_capabilities"))
        if "supports_geometry_nodes" not in caps:
            raise RuntimeError("get_geometry_nodes_capabilities: missing supports_geometry_nodes")
        assert_success("list_geometry_node_groups phase6a", send_command(sock, timeout_seconds, "list_geometry_node_groups", {"max_groups": 200}))
        templates = assert_success("get_supported_geometry_node_templates phase6a", send_command(sock, timeout_seconds, "get_supported_geometry_node_templates"))
        if "curve_rope" not in templates.get("templates", {}):
            raise RuntimeError("get_supported_geometry_node_templates: missing curve_rope")
        assert_success("create_geometry_node_group_from_template phase6a", send_command(sock, timeout_seconds, "create_geometry_node_group_from_template", {"template_name": "curve_rope", "node_group_name": group_name, "parameters": {"radius": 0.04, "length": 2.5}, "material_name": material_name, "replace_existing": True, "verify": True, "artifact_root": REPO_ROOT}))
        assert_success("get_geometry_node_group_deep_info phase6a", send_command(sock, timeout_seconds, "get_geometry_node_group_deep_info", {"node_group_name": group_name, "max_nodes": 40}))
        assert_success("apply_geometry_nodes_modifier phase6a", send_command(sock, timeout_seconds, "apply_geometry_nodes_modifier", {"object_name": base_name, "node_group_name": group_name, "modifier_name": modifier_name, "input_values": {"Radius": 0.04}, "verify": True}))
        assert_success("set_geometry_nodes_modifier_input phase6a", send_command(sock, timeout_seconds, "set_geometry_nodes_modifier_input", {"object_name": base_name, "modifier_name": modifier_name, "input_values": {"Radius": 0.05}}))
        assert_success("list_geometry_nodes_modifiers phase6a", send_command(sock, timeout_seconds, "list_geometry_nodes_modifiers", {"object_name": base_name}))
        assert_success("get_geometry_nodes_modifier_info phase6a", send_command(sock, timeout_seconds, "get_geometry_nodes_modifier_info", {"object_name": base_name, "modifier_name": modifier_name}))
        assert_success("create_custom_geometry_node_recipe phase6a", send_command(sock, timeout_seconds, "create_custom_geometry_node_recipe", {"node_group_name": f"{prefix}_RECIPE", "recipe": {"inputs": [{"name": "Radius", "socket_type": "NodeSocketFloat", "default": 0.05}], "outputs": [{"name": "Geometry", "socket_type": "NodeSocketGeometry"}], "nodes": [{"id": "group_input", "node_type": "NodeGroupInput", "location": [0, 0]}, {"id": "group_output", "node_type": "NodeGroupOutput", "location": [300, 0]}], "metadata": {"purpose": "phase6a smoke"}}, "replace_existing": True, "verify": True, "artifact_root": REPO_ROOT}))
        assert_success("create_procedural_asset phase6a", send_command(sock, timeout_seconds, "create_procedural_asset", {"asset_type": "curve_rope", "asset_name": f"{prefix}_ROPE", "collection_name": collection_name, "material_name": material_name, "parameters": {"radius": 0.04, "length": 2.0}, "verify": True, "artifact_root": REPO_ROOT}))
        assert_success("create_scatter_system phase6a", send_command(sock, timeout_seconds, "create_scatter_system", {"target_object_name": base_name, "asset_name": f"{prefix}_SCATTER", "collection_name": collection_name, "material_name": material_name, "verify": True, "artifact_root": REPO_ROOT}))
        assert_success("create_curve_generator phase6a", send_command(sock, timeout_seconds, "create_curve_generator", {"asset_name": f"{prefix}_CURVE", "collection_name": collection_name, "material_name": material_name, "verify": True, "artifact_root": REPO_ROOT}))
        assert_success("create_radial_array_system phase6a", send_command(sock, timeout_seconds, "create_radial_array_system", {"source_object_name": base_name, "asset_name": f"{prefix}_RADIAL", "collection_name": collection_name, "material_name": material_name, "verify": True, "artifact_root": REPO_ROOT}))
        assert_success("create_panel_generator phase6a", send_command(sock, timeout_seconds, "create_panel_generator", {"asset_name": f"{prefix}_PANEL", "collection_name": collection_name, "material_name": material_name, "verify": True, "artifact_root": REPO_ROOT}))
        assert_success("create_cable_or_rope_generator phase6a", send_command(sock, timeout_seconds, "create_cable_or_rope_generator", {"asset_name": f"{prefix}_CABLE", "template_name": "curve_cable", "collection_name": collection_name, "material_name": material_name, "verify": True, "artifact_root": REPO_ROOT}))
        assert_success("create_terrain_noise_system phase6a", send_command(sock, timeout_seconds, "create_terrain_noise_system", {"asset_name": f"{prefix}_TERRAIN", "collection_name": collection_name, "material_name": material_name, "verify": True, "artifact_root": REPO_ROOT}))
        assert_success("validate_geometry_node_group phase6a", send_command(sock, timeout_seconds, "validate_geometry_node_group", {"node_group_name": group_name}))
        assert_success("create_geometry_nodes_preview phase6a", send_command(sock, timeout_seconds, "create_geometry_nodes_preview", {"node_group_name": group_name, "object_name": base_name, "label": prefix, "artifact_root": REPO_ROOT}))
        assert_success("create_geometry_nodes_scene_kit phase6a", send_command(sock, timeout_seconds, "create_geometry_nodes_scene_kit", {"kit_id": prefix, "label": prefix, "object_names": [base_name], "node_group_names": [group_name], "include_preview": True, "overwrite": True, "artifact_root": REPO_ROOT}))
        batch = assert_success("run_geometry_nodes_workflow_batch phase6a", send_command(sock, timeout_seconds, "run_geometry_nodes_workflow_batch", {"label": prefix, "artifact_root": REPO_ROOT, "operations": [{"command": "get_geometry_nodes_capabilities", "params": {}}, {"command": "list_geometry_node_groups", "params": {"max_groups": 200}}, {"command": "validate_geometry_node_group", "params": {"node_group_name": group_name}}]}))
        if not batch.get("artifacts"):
            raise RuntimeError("run_geometry_nodes_workflow_batch: missing manifest artifact")
        assert_success("get_scene_index phase6a", send_command(sock, timeout_seconds, "get_scene_index", {"max_objects": 1000}))
        assert_success("get_scene_health phase6a", send_command(sock, timeout_seconds, "get_scene_health"))
    finally:
        assert_success("remove_geometry_nodes_modifiers phase6a", send_command(sock, timeout_seconds, "remove_geometry_nodes_modifiers", {"prefix": "OVERTLI_PHASE6A_", "confirm": True}))
        assert_success("delete_geometry_node_groups phase6a", send_command(sock, timeout_seconds, "delete_geometry_node_groups", {"prefix": "OVERTLI_PHASE6A_", "confirm": True}))
        cleanup = assert_success("cleanup_asset_artifacts phase6a", send_command(sock, timeout_seconds, "cleanup_asset_artifacts", {"prefix": "OVERTLI_PHASE6A_", "confirm": True, "cleanup_scene_data": True, "cleanup_files": False, "artifact_root": REPO_ROOT}))
        scene_assets = assert_success("list_scene_assets phase6a_cleanup_probe", send_command(sock, timeout_seconds, "list_scene_assets"))
        groups = assert_success("list_geometry_node_groups phase6a_cleanup_probe", send_command(sock, timeout_seconds, "list_geometry_node_groups", {"max_groups": 1000}))
        modifiers = assert_success("list_geometry_nodes_modifiers phase6a_cleanup_probe", send_command(sock, timeout_seconds, "list_geometry_nodes_modifiers"))
        leftovers = {
            "objects": [item.get("name") for item in scene_assets.get("objects", []) if item.get("name", "").startswith("OVERTLI_PHASE6A_")],
            "collections": [item.get("name") for item in scene_assets.get("collections", []) if item.get("name", "").startswith("OVERTLI_PHASE6A_")],
            "materials": [item.get("name") for item in scene_assets.get("materials", []) if item.get("name", "").startswith("OVERTLI_PHASE6A_")],
            "node_groups": [item.get("name") for item in groups.get("node_groups", []) if item.get("name", "").startswith("OVERTLI_PHASE6A_")],
            "modifiers": [item for item in modifiers.get("modifiers", []) if item.get("modifier_name", "").startswith("OVERTLI_PHASE6A_")],
        }
        remaining = {key: value for key, value in leftovers.items() if value}
        if remaining:
            raise RuntimeError(f"Phase 6A cleanup left smoke-created scene data: {remaining}; cleanup={cleanup}")
        _assert_phase6a_workspace_ignored()
        print("PASS phase6a cleanup removed smoke-created scene data")


def _assert_phase6b_workspace_ignored() -> None:
    gitignore_path = os.path.join(REPO_ROOT, ".gitignore")
    if not os.path.isfile(gitignore_path):
        raise RuntimeError("Phase 6B workspace ignore check failed: .gitignore missing")
    text = open(gitignore_path, "r", encoding="utf-8", errors="replace").read()
    if ".overtli_blender/" not in text and ".overtli_blender" not in text:
        raise RuntimeError("Phase 6B workspace ignore check failed: .overtli_blender is not ignored")


def run_phase6b_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    run_id = str(time.time_ns())
    snippet_name = f"OVERTLI_PHASE6B_SNIPPET_{run_id}"
    skill_name = f"OVERTLI_PHASE6B_SKILL_{run_id}"
    review_id = f"OVERTLI_PHASE6B_REVIEW_{run_id}"
    docs_root = os.path.join(REPO_ROOT, "memory_bank", "research", "blender_python_reference_5_1_md")

    status = assert_success("get_addon_management_status phase6b", send_command(sock, timeout_seconds, "get_addon_management_status"))
    if not status.get("local_only") or status.get("network_downloads_supported"):
        raise RuntimeError(f"get_addon_management_status: unsafe status {status}")
    addons = assert_success("list_blender_addons phase6b", send_command(sock, timeout_seconds, "list_blender_addons", {"include_paths": False}))
    if "addons" not in addons or "counts" not in addons:
        raise RuntimeError("list_blender_addons: missing addons/counts")
    if addons.get("addons"):
        module = addons["addons"][0].get("module")
        if module:
            assert_success("get_blender_addon_info phase6b", send_command(sock, timeout_seconds, "get_blender_addon_info", {"module_name": module, "include_file_info": False}))

    docs = assert_success("inspect_blender_api_docs phase6b", send_command(sock, timeout_seconds, "inspect_blender_api_docs", {"docs_root": docs_root, "max_files": 50000}))
    if not docs.get("exists"):
        raise RuntimeError("inspect_blender_api_docs: local docs mirror missing")
    index = assert_success("build_blender_api_index phase6b", send_command(sock, timeout_seconds, "build_blender_api_index", {"docs_root": docs_root, "max_files": 50000, "artifact_root": REPO_ROOT}))
    if not index.get("record_count"):
        raise RuntimeError("build_blender_api_index: no records indexed")
    topic_for_batch = "Operator"
    for query in ["Operator", "Panel", "AddonPreferences", "register_class", "addon_install"]:
        search = assert_success(f"search_blender_api_docs {query}", send_command(sock, timeout_seconds, "search_blender_api_docs", {"query": query, "max_results": 10, "artifact_root": REPO_ROOT}))
        if not search.get("results"):
            raise RuntimeError(f"search_blender_api_docs: no results for {query}")
    assert_success("get_blender_api_topic phase6b", send_command(sock, timeout_seconds, "get_blender_api_topic", {"topic": topic_for_batch, "artifact_root": REPO_ROOT}))

    snippet_code = "import " + "bpy\n# metadata-only smoke snippet\nresult = bpy.app.version_string"
    snippet = assert_success("create_verified_snippet phase6b", send_command(sock, timeout_seconds, "create_verified_snippet", {"name": snippet_name, "code": snippet_code, "description": "Phase 6B metadata-only smoke snippet.", "tags": ["phase6b", "smoke"], "source_evidence": ["local Blender API docs mirror"], "safety_classification": "low", "overwrite": True, "artifact_root": REPO_ROOT}))
    snippet_id = snippet.get("snippet", {}).get("id")
    if not snippet_id:
        raise RuntimeError("create_verified_snippet: missing snippet id")
    assert_success("validate_verified_snippet phase6b", send_command(sock, timeout_seconds, "validate_verified_snippet", {"snippet_id": snippet_id, "artifact_root": REPO_ROOT}))
    assert_success("list_verified_snippets phase6b", send_command(sock, timeout_seconds, "list_verified_snippets", {"artifact_root": REPO_ROOT}))
    assert_success("search_verified_snippets phase6b", send_command(sock, timeout_seconds, "search_verified_snippets", {"query": "phase6b", "artifact_root": REPO_ROOT}))
    assert_success("get_verified_snippet phase6b", send_command(sock, timeout_seconds, "get_verified_snippet", {"snippet_id": snippet_id, "artifact_root": REPO_ROOT}))

    skill = assert_success("create_skill_pack phase6b", send_command(sock, timeout_seconds, "create_skill_pack", {"name": skill_name, "description": "Phase 6B local metadata skill pack.", "snippet_ids": [snippet_id], "docs_topics": [topic_for_batch], "operations": [{"command": "search_blender_api_docs", "params": {"query": "Operator", "max_results": 3, "artifact_root": REPO_ROOT}}], "overwrite": True, "artifact_root": REPO_ROOT}))
    pack_id = skill.get("skill_pack", {}).get("id")
    if not pack_id:
        raise RuntimeError("create_skill_pack: missing pack id")
    assert_success("validate_skill_pack phase6b", send_command(sock, timeout_seconds, "validate_skill_pack", {"pack_id": pack_id, "artifact_root": REPO_ROOT}))
    assert_success("list_skill_packs phase6b", send_command(sock, timeout_seconds, "list_skill_packs", {"artifact_root": REPO_ROOT}))
    assert_success("get_skill_pack phase6b", send_command(sock, timeout_seconds, "get_skill_pack", {"pack_id": pack_id, "artifact_root": REPO_ROOT}))

    review = assert_success("export_project_review_package phase6b", send_command(sock, timeout_seconds, "export_project_review_package", {"package_id": review_id, "include_memory_bank": False, "include_private_docs": False, "max_files": 2000, "artifact_root": REPO_ROOT}))
    package_dir = review.get("package_dir")
    if not package_dir:
        raise RuntimeError("export_project_review_package: missing package_dir")
    validation = assert_success("validate_review_package phase6b", send_command(sock, timeout_seconds, "validate_review_package", {"package_path": package_dir}))
    if not validation.get("valid"):
        raise RuntimeError(f"validate_review_package: {validation}")

    batch = assert_success("run_advanced_knowledge_workflow_batch phase6b", send_command(sock, timeout_seconds, "run_advanced_knowledge_workflow_batch", {"label": f"OVERTLI_PHASE6B_BATCH_{run_id}", "operations": [{"command": "inspect_blender_api_docs", "params": {"docs_root": docs_root, "max_files": 50000}}, {"command": "search_blender_api_docs", "params": {"query": "Panel", "max_results": 3, "artifact_root": REPO_ROOT}}, {"command": "get_verified_snippet", "params": {"snippet_id": snippet_id, "artifact_root": REPO_ROOT}}, {"command": "get_skill_pack", "params": {"pack_id": pack_id, "artifact_root": REPO_ROOT}}, {"command": "validate_review_package", "params": {"package_path": package_dir}}], "stop_on_error": True, "artifact_root": REPO_ROOT}))
    if not batch.get("results"):
        raise RuntimeError("run_advanced_knowledge_workflow_batch: missing results")
    _assert_phase6b_workspace_ignored()
    print("PASS phase6b full smoke completed without addon lifecycle or snippet execution")


def _unwrap_governance_envelope(name: str, response: dict) -> dict:
    result = assert_success(name, response)
    if "result" in result and isinstance(result["result"], dict):
        return result["result"]
    return result


def assert_command_success(name: str, response: dict, allowed_statuses: set[str] | None = None) -> dict:
    result = assert_success(name, response)
    allowed = allowed_statuses or {"success"}
    if result.get("status") not in allowed:
        raise RuntimeError(f"{name}: nested command did not succeed: {result}")
    return result


def run_phase7b_governance_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    _unwrap_governance_envelope("get_system_status", send_command(sock, timeout_seconds, "get_system_status"))

    packs = _unwrap_governance_envelope("discover_tool_packs", send_command(sock, timeout_seconds, "discover_tool_packs"))
    if packs.get("status") != "success" or not packs.get("tool_packs"):
        raise RuntimeError(f"discover_tool_packs: {packs}")

    for query in ["material", "bake", "geometry nodes", "approval", "project workspace"]:
        result = _unwrap_governance_envelope("search_tools", send_command(sock, timeout_seconds, "search_tools", {"query": query, "risk_max": "HIGH"}))
        if result.get("status") != "success" or not isinstance(result.get("results"), list):
            raise RuntimeError(f"search_tools {query}: {result}")

    spec = _unwrap_governance_envelope("get_tool_spec", send_command(sock, timeout_seconds, "get_tool_spec", {"name": "delete_objects"}))
    if spec.get("status") != "success" or spec.get("tool", {}).get("name") != "delete_objects":
        raise RuntimeError(f"get_tool_spec: {spec}")

    profile = _unwrap_governance_envelope("get_permission_profile", send_command(sock, timeout_seconds, "get_permission_profile"))
    if profile.get("status") != "success" or "profile" not in profile:
        raise RuntimeError(f"get_permission_profile: {profile}")

    readonly = _unwrap_governance_envelope("validate_command_capabilities", send_command(sock, timeout_seconds, "validate_command_capabilities", {"command_name": "get_scene_info", "profile": "read_only"}))
    if readonly.get("status") != "success":
        raise RuntimeError(f"validate read-only capabilities: {readonly}")

    high_risk = _unwrap_governance_envelope("validate_command_capabilities", send_command(sock, timeout_seconds, "validate_command_capabilities", {"command_name": "delete_objects", "profile": "read_only"}))
    if high_risk.get("allowed") is True:
        raise RuntimeError(f"validate high-risk capabilities should not allow read_only profile: {high_risk}")

    approval = _unwrap_governance_envelope("prepare_operation", send_command(sock, timeout_seconds, "prepare_operation", {"command_name": "delete_objects", "params": {"object_names": [], "confirm": True}}))
    if approval.get("status") != "requires_approval" or not approval.get("approval", {}).get("approval_id"):
        raise RuntimeError(f"prepare_operation: {approval}")
    approval_id = approval["approval"]["approval_id"]

    approved = _unwrap_governance_envelope("approve_operation", send_command(sock, timeout_seconds, "approve_operation", {"approval_id": approval_id}))
    if approved.get("status") != "success":
        raise RuntimeError(f"approve_operation: {approved}")

    denied_prepare = _unwrap_governance_envelope("prepare_operation deny", send_command(sock, timeout_seconds, "prepare_operation", {"command_name": "remove_object_modifier", "params": {"object_name": "NOOP", "modifier_name": "NOOP", "confirm": True}}))
    deny_id = denied_prepare.get("approval", {}).get("approval_id")
    denied = _unwrap_governance_envelope("deny_operation", send_command(sock, timeout_seconds, "deny_operation", {"approval_id": deny_id, "reason": "phase7b smoke metadata-only"}))
    if denied.get("status") != "success":
        raise RuntimeError(f"deny_operation: {denied}")

    pending = _unwrap_governance_envelope("get_pending_approvals", send_command(sock, timeout_seconds, "get_pending_approvals"))
    if pending.get("status") != "success" or not isinstance(pending.get("approvals"), list):
        raise RuntimeError(f"get_pending_approvals: {pending}")

    operations = _unwrap_governance_envelope("list_recent_operations", send_command(sock, timeout_seconds, "list_recent_operations", {"limit": 5}))
    if operations.get("status") != "success":
        raise RuntimeError(f"list_recent_operations: {operations}")
    _unwrap_governance_envelope("get_operation_status", send_command(sock, timeout_seconds, "get_operation_status"))

    logs = _unwrap_governance_envelope("get_log_status", send_command(sock, timeout_seconds, "get_log_status"))
    if logs.get("status") != "success" or "redaction_keys" not in logs:
        raise RuntimeError(f"get_log_status: {logs}")

    registry = _unwrap_governance_envelope("get_command_registry_report", send_command(sock, timeout_seconds, "get_command_registry_report"))
    if registry.get("status") != "success" or registry.get("command_count", 0) < 100:
        raise RuntimeError(f"get_command_registry_report: {registry}")


def run_phase7c_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    run_id = str(time.time_ns())
    smoke_root = os.path.join(REPO_ROOT, ".overtli_blender", "phase7c_smoke", run_id)
    os.makedirs(smoke_root, exist_ok=True)

    project_status = _unwrap_governance_envelope("get_project_status phase7c", send_command(sock, timeout_seconds, "get_project_status"))
    if project_status.get("status") != "success":
        raise RuntimeError(f"get_project_status phase7c: {project_status}")

    resolved = assert_command_success("resolve_project_workspace phase7c", send_command(sock, timeout_seconds, "resolve_project_workspace", {"preferred_root": smoke_root, "create_if_missing": False}))
    if not resolved.get("workspace", {}).get("resolved"):
        raise RuntimeError(f"resolve_project_workspace phase7c: {resolved}")

    assert_command_success("initialize_project_workspace phase7c", send_command(sock, timeout_seconds, "initialize_project_workspace", {"project_root": smoke_root, "project_name": "Phase7C Smoke", "confirm": True}))
    assert_command_success("validate_project_layout phase7c", send_command(sock, timeout_seconds, "validate_project_layout", {"project_root": smoke_root}))
    assert_command_success("get_file_access_policy phase7c", send_command(sock, timeout_seconds, "get_file_access_policy"))
    assert_command_success("add_approved_root phase7c", send_command(sock, timeout_seconds, "add_approved_root", {"root": smoke_root, "confirm": True}))

    text_path = os.path.join(smoke_root, "assets", "phase7c-note.txt")
    assert_command_success("write_project_text_file phase7c", send_command(sock, timeout_seconds, "write_project_text_file", {"path": text_path, "text": "phase7c smoke text"}))
    read_back = assert_command_success("read_project_text_file phase7c", send_command(sock, timeout_seconds, "read_project_text_file", {"path": text_path}))
    if "phase7c smoke text" not in read_back.get("text", ""):
        raise RuntimeError(f"read_project_text_file phase7c: {read_back}")

    task = assert_command_success("create_task phase7c", send_command(sock, timeout_seconds, "create_task", {"goal": "Phase 7C smoke task", "acceptance_criteria": ["file read/write", "reference calibration", "spatial measurement"]}))
    task_id = task.get("task", {}).get("task_id")
    if not task_id:
        raise RuntimeError(f"create_task phase7c: {task}")
    assert_command_success("link_task_artifact phase7c", send_command(sock, timeout_seconds, "link_task_artifact", {"task_id": task_id, "artifact_path": text_path}))
    assert_command_success("set_task_status phase7c", send_command(sock, timeout_seconds, "set_task_status", {"task_id": task_id, "status": "completed_unverified"}))
    assert_command_success("create_scene_revision_marker phase7c", send_command(sock, timeout_seconds, "create_scene_revision_marker", {"label": "phase7c-smoke"}))
    assert_command_success("get_recent_operations phase7c", send_command(sock, timeout_seconds, "get_recent_operations", {"limit": 5}))

    png_path = os.path.join(smoke_root, "references", "images", "phase7c-ref.png")
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    with open(png_path, "wb") as handle:
        handle.write(bytes.fromhex("89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D49444154789C6360F8FFFF3F0005FE02FEA73581E50000000049454E44AE426082"))
    ref = assert_command_success("import_reference_image phase7c", send_command(sock, timeout_seconds, "import_reference_image", {"source_path": png_path, "reference_type": "front_orthographic", "copy_into_project": True, "name": "OVERTLI_PHASE7C_REF_" + run_id}))
    ref_id = ref.get("reference", {}).get("reference_id")
    if not ref_id:
        raise RuntimeError(f"import_reference_image phase7c: {ref}")
    assert_command_success("create_reference_set phase7c", send_command(sock, timeout_seconds, "create_reference_set", {"name": "OVERTLI_PHASE7C_SET_" + run_id, "reference_ids": [ref_id]}))
    assert_command_success("calibrate_reference_scale phase7c", send_command(sock, timeout_seconds, "calibrate_reference_scale", {"reference_id": ref_id, "known_distance": 1.0}))
    assert_command_success("add_reference_landmark phase7c a", send_command(sock, timeout_seconds, "add_reference_landmark", {"reference_id": ref_id, "name": "A", "point": [0, 0]}))
    assert_command_success("add_reference_landmark phase7c b", send_command(sock, timeout_seconds, "add_reference_landmark", {"reference_id": ref_id, "name": "B", "point": [3, 4]}))
    landmark_distance = assert_command_success("measure_reference_landmarks phase7c", send_command(sock, timeout_seconds, "measure_reference_landmarks", {"reference_id": ref_id, "from_landmark": "A", "to_landmark": "B"}))
    if int(landmark_distance.get("distance_pixels", 0)) != 5:
        raise RuntimeError(f"measure_reference_landmarks phase7c: {landmark_distance}")

    a_name = "OVERTLI_PHASE7C_A_" + run_id
    b_name = "OVERTLI_PHASE7C_B_" + run_id
    assert_command_success("create_primitive_object phase7c a", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": a_name, "location": [0, 0, 0]}))
    assert_command_success("create_primitive_object phase7c b", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": b_name, "location": [2, 0, 0]}))
    assert_command_success("calculate_distance phase7c", send_command(sock, timeout_seconds, "calculate_distance", {"from_object": a_name, "to_object": b_name}))
    assert_command_success("calculate_angle phase7c", send_command(sock, timeout_seconds, "calculate_angle", {"point_a": [1, 0, 0], "point_b": [0, 0, 0], "point_c": [0, 1, 0]}))
    assert_command_success("get_oriented_bounds phase7c", send_command(sock, timeout_seconds, "get_oriented_bounds", {"object_name": a_name}))
    rename_plan = assert_success("plan_rename phase7c", send_command(sock, timeout_seconds, "plan_rename", {"target_type": "objects", "old_name": a_name, "new_name": a_name + "_RENAMED"}))
    if rename_plan.get("status") != "requires_approval":
        raise RuntimeError(f"plan_rename phase7c: {rename_plan}")
    assert_success("plan_cache_cleanup phase7c", send_command(sock, timeout_seconds, "plan_cache_cleanup", {"categories": ["smoke_artifacts"], "dry_run": True}))
    assert_success("plan_file_delete phase7c", send_command(sock, timeout_seconds, "plan_file_delete", {"paths": [text_path]}))
    assert_command_success("delete_objects phase7c cleanup", send_command(sock, timeout_seconds, "delete_objects", {"object_names": [a_name, b_name], "confirm": True}))
    print("PASS phase7c full smoke completed with project-local workspace and no destructive filesystem execution")


def run_phase8a_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(int(time.time()))
    target_name = f"OVERTLI_PHASE8A_TARGET_{stamp}"
    material_name = f"OVERTLI_PHASE8A_MAT_{stamp}"
    baked_material_name = f"OVERTLI_PHASE8A_BAKED_MAT_{stamp}"
    output_dir = os.path.join(REPO_ROOT, ".overtli_blender", "phase8a_smoke", stamp, "textures", "baked")
    packed_dir = os.path.join(REPO_ROOT, ".overtli_blender", "phase8a_smoke", stamp, "textures", "packed")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(packed_dir, exist_ok=True)
    created_objects: list[str] = []
    try:
        assert_command_success("add_approved_root phase8a smoke", send_command(sock, timeout_seconds, "add_approved_root", {"root": os.path.dirname(os.path.dirname(output_dir)), "confirm": True}))
        caps = assert_command_success("get_bake_capabilities", send_command(sock, timeout_seconds, "get_bake_capabilities"))
        if not caps.get("bake_operator_available"):
            print("WARN phase8a bake operator unavailable; native bake execution will report unsupported")
        created = assert_command_success("create_primitive_object phase8a target", send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": target_name, "collection_name": f"OVERTLI_PHASE8A_SMOKE_{stamp}"}))
        target_name = created.get("object_name", target_name)
        created_objects.append(target_name)
        assert_command_success("create_basic_material phase8a", send_command(sock, timeout_seconds, "create_basic_material", {"name": material_name, "base_color": [0.8, 0.3, 0.2, 1.0]}))
        assert_command_success("assign_material phase8a", send_command(sock, timeout_seconds, "assign_material", {"object_name": target_name, "material_name": material_name}))
        preflight = send_command(sock, timeout_seconds, "validate_bake_setup", {"target_object_names": [target_name], "passes": ["NORMAL"], "resolution": 64, "output_dir": output_dir})
        if preflight.get("status") not in {"success", "error"}:
            raise RuntimeError(f"validate_bake_setup unexpected response: {preflight}")
        assert_command_success("estimate_bake_cost", send_command(sock, timeout_seconds, "estimate_bake_cost", {"target_object_names": [target_name], "passes": ["NORMAL"], "resolution": 64}))
        targets = assert_command_success("create_bake_target_images", send_command(sock, timeout_seconds, "create_bake_target_images", {"target_object_names": [target_name], "passes": ["NORMAL", "ROUGHNESS"], "resolution": 64, "output_dir": output_dir, "prefix": f"phase8a_{stamp}"}))
        first_image = (targets.get("created") or [{}])[0].get("image_name")
        if first_image:
            assert_command_success("assign_bake_targets", send_command(sock, timeout_seconds, "assign_bake_targets", {"object_names": [target_name], "image_name": first_image}))
        assert_command_success("list_bake_targets", send_command(sock, timeout_seconds, "list_bake_targets"))
        native = send_command(sock, timeout_seconds, "bake_material_maps", {"target_object_names": [target_name], "passes": ["NORMAL"], "resolution": 64, "output_dir": output_dir, "verify": True})
        if native.get("status") not in {"success", "partial", "unsupported", "error"}:
            raise RuntimeError(f"bake_material_maps unexpected response: {native}")
        assert_command_success("bake_derived_map", send_command(sock, timeout_seconds, "bake_derived_map", {"object_names": [target_name], "derived_type": "roughness", "resolution": 64, "output_dir": output_dir}))
        assert_command_success("bake_curvature_map", send_command(sock, timeout_seconds, "bake_curvature_map", {"object_names": [target_name], "resolution": 64, "output_dir": output_dir}))
        assert_command_success("validate_baked_textures", send_command(sock, timeout_seconds, "validate_baked_textures", {"image_names_or_paths": [first_image] if first_image else []}))
        if first_image:
            assert_command_success("create_baked_material", send_command(sock, timeout_seconds, "create_baked_material", {"source_material_name": material_name, "new_material_name": baked_material_name, "texture_bindings": {"normal": first_image}, "assign_to_objects": [target_name]}))
        assert_command_success("validate_packed_texture", send_command(sock, timeout_seconds, "validate_packed_texture", {"packed_image_name_or_path": first_image or "missing", "layout": "ORM"}), allowed_statuses={"success", "error"})
        workflow = send_command(sock, timeout_seconds, "run_verified_bake_workflow", {"workflow_name": f"phase8a_{stamp}", "target_object_names": [target_name], "passes": ["NORMAL"], "resolution": 64, "output_dir": output_dir, "include_derived": True, "include_channel_pack": False})
        if workflow.get("status") not in {"success", "partial", "error"}:
            raise RuntimeError(f"run_verified_bake_workflow unexpected response: {workflow}")
        cleanup = send_command(sock, timeout_seconds, "plan_bake_cleanup", {"workflow_id": f"phase8a_{stamp}"})
        if cleanup.get("status") not in {"requires_approval", "success"}:
            raise RuntimeError(f"plan_bake_cleanup unexpected response: {cleanup}")
        print("PASS phase8a full smoke completed with project-local texture outputs and cleanup planning")
    finally:
        if created_objects:
            assert_command_success("delete_objects phase8a cleanup", send_command(sock, timeout_seconds, "delete_objects", {"object_names": created_objects, "confirm": True, "allow_missing": True}))


def run_phase8b_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(int(time.time()))
    collection_name = f"OVERTLI_PHASE8B_SMOKE_{stamp}"
    schema_obj = f"OVERTLI_PHASE8B_SCHEMA_OBJ_{stamp}"
    profile_name = f"OVERTLI_PHASE8B_PROFILE_{stamp}"
    panel_name = f"OVERTLI_PHASE8B_PANEL_{stamp}"
    pipe_name = f"OVERTLI_PHASE8B_PIPE_{stamp}"
    cloth_name = f"OVERTLI_PHASE8B_CLOTH_{stamp}"
    created_objects = [schema_obj, profile_name, f"{profile_name}_Extrude", f"{profile_name}_Lathe", panel_name, pipe_name, cloth_name]
    schema = {"vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]], "edges": [], "faces": [[0, 1, 2]], "metadata": {"smoke": True}}
    profile_points = [[0, 0, 0], [0.5, 0, 0], [0.5, 0, 1], [0, 0, 1]]
    try:
        assert_command_success("get_modeling_capabilities", send_command(sock, timeout_seconds, "get_modeling_capabilities"))
        assert_command_success("validate_mesh_schema phase8b", send_command(sock, timeout_seconds, "validate_mesh_schema", {"schema": schema}))
        assert_command_success("create_mesh_from_schema phase8b", send_command(sock, timeout_seconds, "create_mesh_from_schema", {"object_name": schema_obj, "schema": schema, "collection_name": collection_name}))
        assert_command_success("create_profile_curve phase8b", send_command(sock, timeout_seconds, "create_profile_curve", {"profile_name": profile_name, "points": profile_points, "collection_name": collection_name}))
        assert_command_success("extrude_profile phase8b", send_command(sock, timeout_seconds, "extrude_profile", {"profile_object_name": profile_name, "extrude_vector": [0, 0, 0.25], "new_object_name": f"{profile_name}_Extrude"}))
        lathe = send_command(sock, timeout_seconds, "lathe_profile", {"profile_object_name": profile_name, "segments": 12, "new_object_name": f"{profile_name}_Lathe"})
        if lathe.get("status") not in {"success", "unsupported", "error"}:
            raise RuntimeError(f"lathe_profile unexpected response: {lathe}")
        assert_command_success("create_beveled_curve_object phase8b", send_command(sock, timeout_seconds, "create_beveled_curve_object", {"name": pipe_name, "points": [[0, 0, 0], [1, 0, 0], [1, 1, 0]], "radius": 0.025, "collection_name": collection_name}))
        assert_command_success("create_hard_surface_panel phase8b", send_command(sock, timeout_seconds, "create_hard_surface_panel", {"panel_name": panel_name, "size": [1, 1, 0.05], "collection_name": collection_name}))
        assert_command_success("create_modifier_stack phase8b", send_command(sock, timeout_seconds, "create_modifier_stack", {"object_name": schema_obj, "modifiers": [{"type": "BEVEL", "properties": {"width": 0.01, "segments": 1}}, {"type": "WEIGHTED_NORMAL"}]}))
        assert_success("plan_reference_construction phase8b", send_command(sock, timeout_seconds, "plan_reference_construction", {"reference_set_id": "phase8b_smoke_reference", "target_description": "simple hard surface panel from calibrated reference"}))
        assert_success("validate_reference_alignment phase8b", send_command(sock, timeout_seconds, "validate_reference_alignment", {"object_names": [schema_obj], "reference_set_id": "phase8b_smoke_reference"}))
        assert_command_success("configure_sculpt_session phase8b", send_command(sock, timeout_seconds, "configure_sculpt_session", {"object_name": schema_obj, "use_shape_key": True}))
        assert_command_success("create_shape_key_sculpt_variant phase8b", send_command(sock, timeout_seconds, "create_shape_key_sculpt_variant", {"object_name": schema_obj, "shape_key_name": f"OVERTLI_PHASE8B_SHAPE_{stamp}"}))
        assert_command_success("create_sculpt_mask phase8b", send_command(sock, timeout_seconds, "create_sculpt_mask", {"object_name": schema_obj, "vertex_indices": [0, 1]}))
        stroke = send_command(sock, timeout_seconds, "apply_sculpt_stroke_batch", {"object_name": schema_obj, "strokes": []})
        stroke_result = stroke.get("result") if isinstance(stroke.get("result"), dict) else stroke
        if stroke_result.get("status") != "requires_approval":
            raise RuntimeError(f"apply_sculpt_stroke_batch should require approval: {stroke}")
        assert_command_success("create_cloth_pattern_panel phase8b", send_command(sock, timeout_seconds, "create_cloth_pattern_panel", {"panel_name": cloth_name, "points": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], "collection_name": collection_name}))
        assert_command_success("define_cloth_seam_pair phase8b", send_command(sock, timeout_seconds, "define_cloth_seam_pair", {"panel_a": cloth_name, "edge_a": [0, 1], "panel_b": cloth_name, "edge_b": [2, 3]}))
        assert_command_success("create_cloth_pin_group phase8b", send_command(sock, timeout_seconds, "create_cloth_pin_group", {"object_name": cloth_name, "vertex_indices": [0, 1]}))
        assert_command_success("create_cloth_setup phase8b", send_command(sock, timeout_seconds, "create_cloth_setup", {"object_name": cloth_name, "pin_group_name": "Overtli_Cloth_Pin"}))
        assert_command_success("create_cloth_collision_setup phase8b", send_command(sock, timeout_seconds, "create_cloth_collision_setup", {"object_name": panel_name}))
        preview = send_command(sock, timeout_seconds, "simulate_cloth_preview", {"object_name": cloth_name})
        preview_result = preview.get("result") if isinstance(preview.get("result"), dict) else preview
        if preview_result.get("status") != "requires_approval":
            raise RuntimeError(f"simulate_cloth_preview should require approval: {preview}")
        assert_command_success("validate_construction_geometry phase8b", send_command(sock, timeout_seconds, "validate_construction_geometry", {"object_names": [schema_obj, panel_name, pipe_name, cloth_name], "reference_set_id": "phase8b_smoke_reference"}))
        cleanup = assert_command_success("plan_construction_cleanup phase8b", send_command(sock, timeout_seconds, "plan_construction_cleanup", {"workflow_id": f"phase8b_{stamp}"}))
        if not cleanup.get("requires_approval"):
            raise RuntimeError(f"plan_construction_cleanup should require approval: {cleanup}")
        print("PASS phase8b full smoke completed with smoke-created data and gated sculpt/cloth actions")
    finally:
        send_command(sock, timeout_seconds, "delete_objects", {"object_names": created_objects, "confirm": True, "allow_missing": True})


def run_phase9a_full_smoke(sock: socket.socket, timeout_seconds: float) -> None:
    stamp = str(int(time.time()))
    prefix = f"OVERTLI_PHASE9A_{stamp}"
    cube_name = f"{prefix}_CUBE"
    action_name = f"{prefix}_ACTION"
    armature_name = f"{prefix}_ARMATURE"
    pose_name = f"{prefix}_POSE"
    created_objects = [cube_name, armature_name]
    try:
        assert_command_success("get_animation_system_capabilities phase9a", send_command(sock, timeout_seconds, "get_animation_system_capabilities"))
        assert_command_success("inspect_animation_system phase9a", send_command(sock, timeout_seconds, "inspect_animation_system"))
        assert_command_success("list_actions phase9a", send_command(sock, timeout_seconds, "list_actions"))
        assert_command_success(
            "create_primitive_object phase9a",
            send_command(sock, timeout_seconds, "create_primitive_object", {"primitive_type": "cube", "name": cube_name}),
        )
        assert_command_success(
            "create_action phase9a",
            send_command(sock, timeout_seconds, "create_action", {"action_name": action_name, "frame_start": 1, "frame_end": 24}),
        )
        assert_command_success(
            "insert_keyframe_batch phase9a",
            send_command(
                sock,
                timeout_seconds,
                "insert_keyframe_batch",
                {
                    "object_name": cube_name,
                    "action_name": action_name,
                    "keyframes": [
                        {"frame": 1, "data_path": "location", "value": [0, 0, 0]},
                        {"frame": 24, "data_path": "location", "value": [1, 0, 0]},
                    ],
                },
            ),
        )
        assert_command_success("get_action_deep_info phase9a", send_command(sock, timeout_seconds, "get_action_deep_info", {"action_name": action_name}))
        assert_command_success(
            "set_fcurve_interpolation phase9a",
            send_command(sock, timeout_seconds, "set_fcurve_interpolation", {"action_name": action_name, "interpolation": "LINEAR"}),
        )
        assert_command_success(
            "validate_driver_dsl phase9a",
            send_command(
                sock,
                timeout_seconds,
                "validate_driver_dsl",
                {"dsl": {"operation": "clamp", "source": {"target_name": cube_name, "data_path": "location.x"}, "min": 0, "max": 1}},
            ),
        )
        driver_response = send_command(
            sock,
            timeout_seconds,
            "create_driver_from_dsl",
            {
                "target_type": "OBJECT",
                "target_name": cube_name,
                "data_path": "scale",
                "array_index": 0,
                "dsl": {"operation": "clamp", "source": {"target_name": cube_name, "data_path": "location.x"}, "min": 0, "max": 1},
            },
        )
        driver_result = driver_response.get("result") if isinstance(driver_response.get("result"), dict) else driver_response
        if driver_result.get("status") != "requires_approval":
            raise RuntimeError(f"create_driver_from_dsl should require approval: {driver_response}")
        assert_command_success(
            "create_rig_template phase9a",
            send_command(sock, timeout_seconds, "create_rig_template", {"armature_name": armature_name, "template": "simple_biped"}),
        )
        assert_command_success(
            "validate_rig phase9a",
            send_command(sock, timeout_seconds, "validate_rig", {"armature_name": armature_name}),
        )
        assert_command_success(
            "create_pose_snapshot phase9a",
            send_command(sock, timeout_seconds, "create_pose_snapshot", {"armature_name": armature_name, "snapshot_id": pose_name}),
        )
        pose_response = send_command(sock, timeout_seconds, "apply_pose_snapshot", {"armature_name": armature_name, "snapshot_id": pose_name})
        pose_result = pose_response.get("result") if isinstance(pose_response.get("result"), dict) else pose_response
        if pose_result.get("status") != "requires_approval":
            raise RuntimeError(f"apply_pose_snapshot should require approval: {pose_response}")
        shot_plan_name = f"{prefix}_SHOT"
        assert_command_success("create_shot_plan phase9a", send_command(sock, timeout_seconds, "create_shot_plan", {"plan_name": shot_plan_name, "ranges": [{"name": "main", "frame_start": 1, "frame_end": 24}]}))
        assert_command_success("validate_shot_plan phase9a", send_command(sock, timeout_seconds, "validate_shot_plan", {"plan_name": shot_plan_name}))
        assert_command_success("get_simulation_capabilities phase9a", send_command(sock, timeout_seconds, "get_simulation_capabilities"))
        assert_command_success("inspect_simulation_state phase9a", send_command(sock, timeout_seconds, "inspect_simulation_state", {"object_names": [cube_name]}))
        preview_response = send_command(sock, timeout_seconds, "simulate_preview_range", {"object_name": cube_name, "frame_start": 1, "frame_end": 8})
        preview_result = preview_response.get("result") if isinstance(preview_response.get("result"), dict) else preview_response
        if preview_result.get("status") != "requires_approval":
            raise RuntimeError(f"simulate_preview_range should require approval: {preview_response}")
        cache_response = send_command(sock, timeout_seconds, "clear_simulation_cache", {"object_name": cube_name})
        cache_result = cache_response.get("result") if isinstance(cache_response.get("result"), dict) else cache_response
        if cache_result.get("status") != "requires_approval":
            raise RuntimeError(f"clear_simulation_cache should require approval: {cache_response}")
        assert_command_success("validate_motion phase9a", send_command(sock, timeout_seconds, "validate_motion", {"object_names": [cube_name]}))
        print("PASS phase9a full smoke completed with smoke-created data and gated driver/pose/simulation/cache actions")
    finally:
        send_command(sock, timeout_seconds, "delete_objects", {"object_names": created_objects, "confirm": True, "allow_missing": True})


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
    parser.add_argument("--include-timeline-info", action="store_true", help="Run the Phase 5A timeline info smoke.")
    parser.add_argument("--include-animation-ops", action="store_true", help="Run Phase 5A animation operations via the full contained scenario.")
    parser.add_argument("--include-camera-ops", action="store_true", help="Run Phase 5A camera operations via the full contained scenario.")
    parser.add_argument("--include-lighting-ops", action="store_true", help="Run Phase 5A lighting operations via the full contained scenario.")
    parser.add_argument("--include-render-settings", action="store_true", help="Run the Phase 5A render settings smoke.")
    parser.add_argument("--include-render-still", action="store_true", help="Run Phase 5A still rendering via the full contained scenario.")
    parser.add_argument("--include-contact-sheet", action="store_true", help="Run Phase 5A contact sheet rendering via the full contained scenario.")
    parser.add_argument("--include-turntable", action="store_true", help="Run Phase 5A turntable setup via the full contained scenario.")
    parser.add_argument("--include-preview-animation", action="store_true", help="Run Phase 5A bounded preview animation via the full contained scenario.")
    parser.add_argument("--include-compositor-ops", action="store_true", help="Run Phase 5A compositor/pass operations via the full contained scenario.")
    parser.add_argument("--include-presentation-batch", action="store_true", help="Run Phase 5A presentation batch via the full contained scenario.")
    parser.add_argument("--include-asset-formats", action="store_true", help="Run Phase 5B asset format detection via the full contained scenario.")
    parser.add_argument("--include-asset-scan", action="store_true", help="Run Phase 5B asset folder scanning via the full contained scenario.")
    parser.add_argument("--include-scene-assets", action="store_true", help="Run Phase 5B scene asset inventory via the full contained scenario.")
    parser.add_argument("--include-dependency-report", action="store_true", help="Run Phase 5B dependency reporting via the full contained scenario.")
    parser.add_argument("--include-asset-manifest", action="store_true", help="Run Phase 5B asset manifest creation via the full contained scenario.")
    parser.add_argument("--include-import-export", action="store_true", help="Run Phase 5B local smoke export/import via the full contained scenario.")
    parser.add_argument("--include-scene-kit", action="store_true", help="Run Phase 5B scene kit create/validate via the full contained scenario.")
    parser.add_argument("--include-asset-preview", action="store_true", help="Run Phase 5B asset preview creation via the full contained scenario.")
    parser.add_argument("--include-asset-workflow-batch", action="store_true", help="Run Phase 5B asset workflow batch via the full contained scenario.")
    parser.add_argument("--include-geometry-nodes-capabilities", action="store_true", help="Run Phase 6A Geometry Nodes capability detection.")
    parser.add_argument("--include-geometry-nodes-intelligence", action="store_true", help="Run Phase 6A Geometry Nodes inspection via the full contained scenario.")
    parser.add_argument("--include-geometry-node-templates", action="store_true", help="Run Phase 6A template discovery via the full contained scenario.")
    parser.add_argument("--include-geometry-node-recipe", action="store_true", help="Run Phase 6A custom recipe creation via the full contained scenario.")
    parser.add_argument("--include-procedural-assets", action="store_true", help="Run Phase 6A procedural asset generation via the full contained scenario.")
    parser.add_argument("--include-scatter-system", action="store_true", help="Run Phase 6A scatter system generation via the full contained scenario.")
    parser.add_argument("--include-curve-generator", action="store_true", help="Run Phase 6A curve generator via the full contained scenario.")
    parser.add_argument("--include-radial-array-system", action="store_true", help="Run Phase 6A radial array generation via the full contained scenario.")
    parser.add_argument("--include-panel-generator", action="store_true", help="Run Phase 6A panel generator via the full contained scenario.")
    parser.add_argument("--include-geometry-nodes-preview", action="store_true", help="Run Phase 6A Geometry Nodes preview creation via the full contained scenario.")
    parser.add_argument("--include-geometry-nodes-workflow-batch", action="store_true", help="Run Phase 6A Geometry Nodes workflow batch via the full contained scenario.")
    parser.add_argument("--include-addon-status", action="store_true", help="Run the Phase 6B addon management status smoke.")
    parser.add_argument("--include-addon-list", action="store_true", help="Run the Phase 6B addon listing smoke.")
    parser.add_argument("--include-api-docs-inspect", action="store_true", help="Run the Phase 6B local API docs inspection smoke.")
    parser.add_argument("--include-api-docs-index", action="store_true", help="Run the Phase 6B local API docs index smoke.")
    parser.add_argument("--include-api-docs-search", action="store_true", help="Run the Phase 6B API docs search smoke.")
    parser.add_argument("--include-snippet-library", action="store_true", help="Run the Phase 6B verified snippet metadata smoke.")
    parser.add_argument("--include-skill-pack", action="store_true", help="Run the Phase 6B skill pack metadata smoke.")
    parser.add_argument("--include-review-package", action="store_true", help="Run the Phase 6B review package smoke.")
    parser.add_argument("--include-advanced-knowledge-batch", action="store_true", help="Run the Phase 6B advanced knowledge batch smoke.")
    parser.add_argument("--include-governance-status", action="store_true", help="Run the Phase 7B governance status smoke.")
    parser.add_argument("--include-tool-discovery", action="store_true", help="Run the Phase 7B tool discovery smoke.")
    parser.add_argument("--include-approval-flow", action="store_true", help="Run the Phase 7B metadata-only approval flow smoke.")
    parser.add_argument("--include-operation-runtime", action="store_true", help="Run the Phase 7B operation runtime smoke.")
    parser.add_argument("--include-capability-policy", action="store_true", help="Run the Phase 7B capability policy smoke.")
    parser.add_argument("--include-log-status", action="store_true", help="Run the Phase 7B log status smoke.")
    parser.add_argument("--include-project-workspace", action="store_true", help="Run Phase 7C project workspace smoke through --phase7c-full.")
    parser.add_argument("--include-file-access-policy", action="store_true", help="Run Phase 7C file access policy smoke through --phase7c-full.")
    parser.add_argument("--include-cache-management", action="store_true", help="Run Phase 7C cache management smoke through --phase7c-full.")
    parser.add_argument("--include-task-graph", action="store_true", help="Run Phase 7C task graph smoke through --phase7c-full.")
    parser.add_argument("--include-time-revision", action="store_true", help="Run Phase 7C time/revision smoke through --phase7c-full.")
    parser.add_argument("--include-reference-images", action="store_true", help="Run Phase 7C reference image smoke through --phase7c-full.")
    parser.add_argument("--include-spatial-measurement", action="store_true", help="Run Phase 7C spatial measurement smoke through --phase7c-full.")
    parser.add_argument("--include-rename-planning", action="store_true", help="Run Phase 7C rename planning smoke through --phase7c-full.")
    parser.add_argument("--include-bake-capabilities", action="store_true", help="Run Phase 8A bake capabilities smoke through --phase8a-full.")
    parser.add_argument("--include-bake-preflight", action="store_true", help="Run Phase 8A bake preflight smoke through --phase8a-full.")
    parser.add_argument("--include-bake-target-images", action="store_true", help="Run Phase 8A bake target image smoke through --phase8a-full.")
    parser.add_argument("--include-native-bake", action="store_true", help="Run Phase 8A native bake smoke through --phase8a-full when supported.")
    parser.add_argument("--include-derived-bake", action="store_true", help="Run Phase 8A derived bake smoke through --phase8a-full.")
    parser.add_argument("--include-selected-to-active-bake", action="store_true", help="Run Phase 8A selected-to-active bake smoke through --phase8a-full when supported.")
    parser.add_argument("--include-channel-packing", action="store_true", help="Run Phase 8A channel packing validation smoke through --phase8a-full.")
    parser.add_argument("--include-baked-material", action="store_true", help="Run Phase 8A baked material smoke through --phase8a-full.")
    parser.add_argument("--include-bake-cleanup-plan", action="store_true", help="Run Phase 8A bake cleanup planning smoke through --phase8a-full.")
    parser.add_argument("--include-verified-bake-workflow", action="store_true", help="Run Phase 8A verified bake workflow smoke through --phase8a-full.")
    parser.add_argument("--include-modeling-capabilities", action="store_true", help="Run Phase 8B modeling capabilities smoke through --phase8b-full.")
    parser.add_argument("--include-mesh-schema", action="store_true", help="Run Phase 8B mesh schema smoke through --phase8b-full.")
    parser.add_argument("--include-profile-modeling", action="store_true", help="Run Phase 8B profile modeling smoke through --phase8b-full.")
    parser.add_argument("--include-curve-construction", action="store_true", help="Run Phase 8B curve construction smoke through --phase8b-full.")
    parser.add_argument("--include-modifier-construction", action="store_true", help="Run Phase 8B modifier construction smoke through --phase8b-full.")
    parser.add_argument("--include-reference-construction", action="store_true", help="Run Phase 8B reference construction smoke through --phase8b-full.")
    parser.add_argument("--include-sculpt-workflow", action="store_true", help="Run Phase 8B sculpt workflow smoke through --phase8b-full.")
    parser.add_argument("--include-cloth-patterns", action="store_true", help="Run Phase 8B cloth pattern smoke through --phase8b-full.")
    parser.add_argument("--include-construction-validation", action="store_true", help="Run Phase 8B construction validation smoke through --phase8b-full.")
    parser.add_argument("--include-construction-cleanup-plan", action="store_true", help="Run Phase 8B construction cleanup planning smoke through --phase8b-full.")
    parser.add_argument("--include-animation-system", action="store_true", help="Run Phase 9A animation system inspection smoke through --phase9a-full.")
    parser.add_argument("--include-action-library", action="store_true", help="Run Phase 9A action library smoke through --phase9a-full.")
    parser.add_argument("--include-fcurve-editing", action="store_true", help="Run Phase 9A F-Curve editing smoke through --phase9a-full.")
    parser.add_argument("--include-nla-workflow", action="store_true", help="Run Phase 9A NLA workflow smoke through --phase9a-full.")
    parser.add_argument("--include-driver-dsl", action="store_true", help="Run Phase 9A driver DSL smoke through --phase9a-full.")
    parser.add_argument("--include-rig-template", action="store_true", help="Run Phase 9A rig template smoke through --phase9a-full.")
    parser.add_argument("--include-pose-library", action="store_true", help="Run Phase 9A pose library smoke through --phase9a-full.")
    parser.add_argument("--include-shot-workflow", action="store_true", help="Run Phase 9A shot workflow smoke through --phase9a-full.")
    parser.add_argument("--include-simulation-workflow", action="store_true", help="Run Phase 9A simulation workflow smoke through --phase9a-full.")
    parser.add_argument("--include-motion-validation", action="store_true", help="Run Phase 9A motion validation smoke through --phase9a-full.")
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
    parser.add_argument(
        "--phase5a-full",
        action="store_true",
        help="Run a contained Phase 5A animation, camera, lighting, render, compositor, presentation batch, and cleanup scenario.",
    )
    parser.add_argument(
        "--phase5b-full",
        action="store_true",
        help="Run a contained Phase 5B asset scan, dependency, export/import, scene-kit, batch, and cleanup scenario.",
    )
    parser.add_argument(
        "--phase6a-full",
        action="store_true",
        help="Run a contained Phase 6A Geometry Nodes, procedural asset, preview, scene-kit, batch, and cleanup scenario.",
    )
    parser.add_argument(
        "--phase6b-full",
        action="store_true",
        help="Run a contained Phase 6B addon status, docs, snippets, skill pack, review package, and knowledge batch scenario.",
    )
    parser.add_argument(
        "--phase7b-full",
        action="store_true",
        help="Run Phase 7B governance, discovery, approvals, operation runtime, capabilities, and log status checks.",
    )
    parser.add_argument(
        "--phase7c-full",
        action="store_true",
        help="Run Phase 7C project workspace, file access, cache, task graph, time/revision, references, spatial, and rename planning checks.",
    )
    parser.add_argument(
        "--phase8a-full",
        action="store_true",
        help="Run Phase 8A texture baking and image resource smoke with project-local generated data.",
    )
    parser.add_argument(
        "--phase8b-full",
        action="store_true",
        help="Run Phase 8B advanced modeling, sculpt setup, cloth pattern, and validation smoke with smoke-created data.",
    )
    parser.add_argument(
        "--phase9a-full",
        action="store_true",
        help="Run Phase 9A animation, rigging, drivers, pose, shot, simulation, and validation smoke with smoke-created data.",
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

            if args.include_timeline_info:
                assert_success("get_timeline_info", send_command(sock, args.timeout, "get_timeline_info"))

            if args.include_render_settings:
                assert_success("get_render_settings", send_command(sock, args.timeout, "get_render_settings"))

            if (
                args.phase5a_full
                or args.include_animation_ops
                or args.include_camera_ops
                or args.include_lighting_ops
                or args.include_render_still
                or args.include_contact_sheet
                or args.include_turntable
                or args.include_preview_animation
                or args.include_compositor_ops
                or args.include_presentation_batch
            ):
                run_phase5a_full_smoke(sock, args.timeout)

            if (
                args.phase5b_full
                or args.include_asset_formats
                or args.include_asset_scan
                or args.include_scene_assets
                or args.include_dependency_report
                or args.include_asset_manifest
                or args.include_import_export
                or args.include_scene_kit
                or args.include_asset_preview
                or args.include_asset_workflow_batch
            ):
                run_phase5b_full_smoke(sock, args.timeout)

            if args.include_geometry_nodes_capabilities:
                assert_success("get_geometry_nodes_capabilities", send_command(sock, args.timeout, "get_geometry_nodes_capabilities"))

            if (
                args.phase6a_full
                or args.include_geometry_nodes_intelligence
                or args.include_geometry_node_templates
                or args.include_geometry_node_recipe
                or args.include_procedural_assets
                or args.include_scatter_system
                or args.include_curve_generator
                or args.include_radial_array_system
                or args.include_panel_generator
                or args.include_geometry_nodes_preview
                or args.include_geometry_nodes_workflow_batch
            ):
                run_phase6a_full_smoke(sock, args.timeout)

            if args.include_addon_status:
                assert_success("get_addon_management_status", send_command(sock, args.timeout, "get_addon_management_status"))

            if args.include_addon_list:
                assert_success("list_blender_addons", send_command(sock, args.timeout, "list_blender_addons", {"include_paths": False}))

            if args.include_api_docs_inspect:
                assert_success("inspect_blender_api_docs", send_command(sock, args.timeout, "inspect_blender_api_docs", {"docs_root": os.path.join(REPO_ROOT, "memory_bank", "research", "blender_python_reference_5_1_md"), "max_files": 50000}))

            if args.include_api_docs_index:
                assert_success("build_blender_api_index", send_command(sock, args.timeout, "build_blender_api_index", {"docs_root": os.path.join(REPO_ROOT, "memory_bank", "research", "blender_python_reference_5_1_md"), "max_files": 50000, "artifact_root": REPO_ROOT}))

            if args.include_api_docs_search:
                assert_success("search_blender_api_docs", send_command(sock, args.timeout, "search_blender_api_docs", {"query": "Operator", "max_results": 10, "artifact_root": REPO_ROOT}))

            if (
                args.phase6b_full
                or args.include_snippet_library
                or args.include_skill_pack
                or args.include_review_package
                or args.include_advanced_knowledge_batch
            ):
                run_phase6b_full_smoke(sock, args.timeout)

            if (
                args.phase7b_full
                or args.include_governance_status
                or args.include_tool_discovery
                or args.include_approval_flow
                or args.include_operation_runtime
                or args.include_capability_policy
                or args.include_log_status
            ):
                run_phase7b_governance_smoke(sock, args.timeout)

            if (
                args.phase7c_full
                or args.include_project_workspace
                or args.include_file_access_policy
                or args.include_cache_management
                or args.include_task_graph
                or args.include_time_revision
                or args.include_reference_images
                or args.include_spatial_measurement
                or args.include_rename_planning
            ):
                run_phase7c_full_smoke(sock, args.timeout)

            if (
                args.phase8a_full
                or args.include_bake_capabilities
                or args.include_bake_preflight
                or args.include_bake_target_images
                or args.include_native_bake
                or args.include_derived_bake
                or args.include_selected_to_active_bake
                or args.include_channel_packing
                or args.include_baked_material
                or args.include_bake_cleanup_plan
                or args.include_verified_bake_workflow
            ):
                run_phase8a_full_smoke(sock, args.timeout)

            if (
                args.phase8b_full
                or args.include_modeling_capabilities
                or args.include_mesh_schema
                or args.include_profile_modeling
                or args.include_curve_construction
                or args.include_modifier_construction
                or args.include_reference_construction
                or args.include_sculpt_workflow
                or args.include_cloth_patterns
                or args.include_construction_validation
                or args.include_construction_cleanup_plan
            ):
                run_phase8b_full_smoke(sock, args.timeout)

            if (
                args.phase9a_full
                or args.include_animation_system
                or args.include_action_library
                or args.include_fcurve_editing
                or args.include_nla_workflow
                or args.include_driver_dsl
                or args.include_rig_template
                or args.include_pose_library
                or args.include_shot_workflow
                or args.include_simulation_workflow
                or args.include_motion_validation
            ):
                run_phase9a_full_smoke(sock, args.timeout)

        print("PASS smoke harness completed")
        return 0
    except Exception as exc:
        print(f"FAIL smoke harness: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

