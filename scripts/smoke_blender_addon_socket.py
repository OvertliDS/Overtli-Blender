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
    parser.add_argument(
        "--phase2-full",
        action="store_true",
        help="Run default smoke plus safe Phase 2 inspection, screenshot-pack, and verification snapshot checks.",
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

        print("PASS smoke harness completed")
        return 0
    except Exception as exc:
        print(f"FAIL smoke harness: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

