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
        with tempfile.NamedTemporaryFile(prefix="blender_mcp_smoke_", suffix=".png", delete=False) as temp_file:
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
    parser = argparse.ArgumentParser(description="Smoke-test the Blender MCP addon socket directly.")
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
        "--include-geometry-nodes-status",
        action="store_true",
        help="Run the optional Geometry Nodes status smoke.",
    )
    parser.add_argument(
        "--include-code-execution",
        action="store_true",
        help="Run the optional harmless code execution smoke.",
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

            if args.include_geometry_nodes_status:
                run_optional_geometry_nodes_status_smoke(sock, args.timeout)

            if args.include_code_execution:
                run_optional_code_execution_smoke(sock, args.timeout)

        print("PASS smoke harness completed")
        return 0
    except Exception as exc:
        print(f"FAIL smoke harness: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
