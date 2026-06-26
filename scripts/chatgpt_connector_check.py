from __future__ import annotations

import argparse
import importlib
import json
import socket
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MCP_URL = "http://127.0.0.1:2091/mcp"


def _result(name: str, passed: bool, details: str | dict | None = None) -> dict:
    return {"name": name, "status": "passed" if passed else "failed", "details": details}


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _static_checks() -> list[dict]:
    checks: list[dict] = []
    try:
        server = importlib.import_module("overtli_blender.server")
        checks.append(_result("mcp_server_import", True))
    except Exception as exc:
        checks.append(_result("mcp_server_import", False, str(exc)))
        server = None

    if server is not None:
        status = server.build_server_status(
            server._parse_args(["--transport", "http", "--profile", "chatgpt_browser_default", "--remote-safety", "remote_browser_safe"])
        )
        checks.append(_result("http_mode_command_exists", status.get("transport") == "streamable-http", status))
        checks.append(_result("mcp_url_is_documented_path", status.get("mcp_url", "").endswith("/mcp"), status.get("mcp_url")))

    docs = [
        "docs/chatgpt_browser_connector.md",
        "docs/chatgpt_connector_prompts.md",
        "docs/mcp_setup.md",
    ]
    for rel in docs:
        checks.append(_result(f"{rel}_exists", (ROOT / rel).is_file()))

    metadata_path = ROOT / "config" / "chatgpt_connector_metadata.json"
    if metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            checks.append(_result("connector_metadata_valid_json", False, str(exc)))
        else:
            checks.append(_result("connector_metadata_valid_json", True, metadata))
            checks.append(_result("connector_metadata_mcp_url", metadata.get("local_http_url") == DEFAULT_MCP_URL, metadata.get("local_http_url")))
            checks.append(_result("connector_metadata_profile", metadata.get("default_tool_profile") == "chatgpt_browser_default", metadata.get("default_tool_profile")))
    else:
        checks.append(_result("connector_metadata_exists", False))

    browser_doc = _text("docs/chatgpt_browser_connector.md") if (ROOT / "docs/chatgpt_browser_connector.md").is_file() else ""
    checks.append(_result("browser_doc_mentions_mcp", "/mcp" in browser_doc))
    checks.append(_result("browser_doc_mentions_developer_mode", "Developer mode" in browser_doc))
    checks.append(_result("browser_doc_mentions_mcp_inspector", "MCP Inspector" in browser_doc))
    checks.append(_result("browser_doc_mentions_tunnel_warning", "local/tunnel development" in browser_doc))

    mcp_setup = _text("docs/mcp_setup.md") if (ROOT / "docs/mcp_setup.md").is_file() else ""
    checks.append(_result("mcp_setup_links_browser_connector", "chatgpt_browser_connector.md" in mcp_setup))

    if (ROOT / "src" / "overtli_blender" / "runtime" / "tool_profiles.py").is_file():
        from overtli_blender.runtime.tool_profiles import get_profile

        profile = get_profile("chatgpt_browser_default")
        checks.append(_result("tool_profile_exists", profile is not None))
        if profile is not None:
            checks.append(_result("tool_profile_bounded", profile.max_visible_tools <= 100, {"max_visible_tools": profile.max_visible_tools}))
            checks.append(_result("tool_profile_remote_safe", profile.permission_profile == "remote_browser_safe", profile.permission_profile))
            hidden = set(profile.hidden_risky_tools)
            checks.append(_result("tool_profile_hides_raw_python", "execute_code" in hidden and "execute_blender_code" in hidden))
            checks.append(_result("tool_profile_hides_provider_downloads", {"download_polyhaven_asset", "download_sketchfab_model", "create_rodin_job"} <= hidden))

    from overtli_blender.runtime.capabilities import PROFILE_CAPABILITIES

    remote_caps = PROFILE_CAPABILITIES.get("remote_browser_safe", set())
    checks.append(_result("remote_safety_profile_exists", bool(remote_caps)))
    checks.append(_result("remote_safety_disables_raw_python", "raw_python" not in remote_caps))
    checks.append(_result("remote_safety_disables_external_write", "filesystem.external.write" not in remote_caps))
    checks.append(_result("remote_safety_disables_file_delete", "filesystem.delete" not in remote_caps))

    return checks


def _live_http_checks(url: str) -> list[dict]:
    health_url = url.replace("/mcp", "/health")
    checks: list[dict] = []
    try:
        with urllib.request.urlopen(health_url, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        checks.append(_result("health_endpoint_responds", False, str(exc)))
    else:
        checks.append(_result("health_endpoint_responds", True, payload))
        checks.append(_result("health_endpoint_mentions_mcp", payload.get("mcp_endpoint") == "/mcp", payload))
    return checks


def _live_blender_checks(host: str, port: int) -> list[dict]:
    try:
        with socket.create_connection((host, port), timeout=3):
            return [_result("blender_socket_reachable", True, {"host": host, "port": port})]
    except OSError as exc:
        return [_result("blender_socket_reachable", False, str(exc))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ChatGPT browser connector readiness.")
    parser.add_argument("--static", action="store_true", help="Run static readiness checks.")
    parser.add_argument("--live-http", action="store_true", help="Check /health for a running HTTP bridge.")
    parser.add_argument("--url", default=DEFAULT_MCP_URL, help="HTTP MCP URL for --live-http.")
    parser.add_argument("--live-blender", action="store_true", help="Check the Blender addon socket.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9876)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if not args.static and not args.live_http and not args.live_blender:
        args.static = True

    checks: list[dict] = []
    if args.static:
        checks.extend(_static_checks())
    if args.live_http:
        checks.extend(_live_http_checks(args.url))
    if args.live_blender:
        checks.extend(_live_blender_checks(args.host, args.port))

    failed = [check for check in checks if check["status"] != "passed"]
    report = {
        "status": "failed" if failed else "passed",
        "checks": checks,
        "failed": failed,
    }
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        for check in checks:
            print(f"{check['status'].upper()} {check['name']}")
        print(f"status: {report['status']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
