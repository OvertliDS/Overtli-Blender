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
REQUIRED_BROWSER_TOOLS = {
    "discover_tool_packs",
    "search_tools",
    "get_tool_spec",
    "get_runtime_dashboard",
    "get_approval_queue_summary",
    "get_recent_operation_summary",
    "prepare_operation",
    "get_pending_approvals",
    "approve_operation",
    "deny_operation",
    "execute_approved_operation",
    "approve_and_execute_operation",
    "validate_command_capabilities",
    "get_scene_info",
    "get_scene_index",
    "get_scene_health",
    "get_selection_info",
    "get_object_deep_info",
    "list_materials_deep",
    "get_material_deep_info",
    "get_project_status",
    "get_loaded_project_folder",
    "resolve_project_workspace",
    "initialize_project_workspace",
    "validate_project_layout",
    "repair_project_layout",
    "resave_project_folder",
    "plan_project_folder_move",
    "move_project_folder",
    "get_file_access_policy",
    "list_approved_roots",
    "detect_drive_roots",
    "approve_drive_roots",
    "get_tool_profiles",
    "get_active_tool_profile",
    "get_enabled_tool_packs",
    "get_bundled_skill_pack",
    "search_bundled_skill_packs",
    "explain_error",
    "get_remediation_steps",
    "create_primitive_object",
    "transform_object",
    "duplicate_object",
    "create_collection",
    "move_objects_to_collection",
    "set_object_visibility",
    "create_basic_material",
    "assign_material",
    "update_material_properties",
    "create_material_from_template",
    "create_custom_material",
    "apply_material_to_objects",
    "create_camera",
    "frame_camera_to_objects",
    "set_active_camera",
    "create_light",
    "create_lighting_setup",
    "update_light",
    "set_world_lighting",
    "create_verification_snapshot",
    "run_verified_edit_batch",
    "run_presentation_workflow_batch",
}
DANGEROUS_BROWSER_TOOLS = {
    "execute_code",
    "execute_blender_code",
    "download_polyhaven_asset",
    "download_sketchfab_model",
    "create_rodin_job",
    "delete_objects",
    "execute_approved_file_delete",
    "execute_cache_cleanup",
    "run_verified_snippet_smoke",
    "execute_approved_addon_operator",
    "install_local_addon",
    "enable_blender_addon",
    "disable_blender_addon",
    "remove_blender_addon",
}


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
            server._parse_args(["--transport", "http", "--profile", "browser_full_standard", "--remote-safety", "browser_standard"])
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
            checks.append(_result("connector_metadata_profile", metadata.get("default_tool_profile") in {"browser_full_standard", "chatgpt_browser_default"}, metadata.get("default_tool_profile")))
    else:
        checks.append(_result("connector_metadata_exists", False))

    browser_doc = _text("docs/chatgpt_browser_connector.md") if (ROOT / "docs/chatgpt_browser_connector.md").is_file() else ""
    checks.append(_result("browser_doc_mentions_mcp", "/mcp" in browser_doc))
    checks.append(_result("browser_doc_mentions_developer_mode", "Developer mode" in browser_doc))
    checks.append(_result("browser_doc_mentions_mcp_inspector", "MCP Inspector" in browser_doc))
    checks.append(_result("browser_doc_mentions_tunnel_warning", "local/tunnel development" in browser_doc))
    checks.append(_result("browser_doc_mentions_openai_tunnel_client", "tunnel-client" in browser_doc and "Start_OpenAI_MCP_Tunnel.bat" in browser_doc))
    checks.append(_result("browser_doc_mentions_combined_launcher", "Start_ChatGPT_Connector.bat" in browser_doc))
    checks.append(_result("browser_doc_mentions_server_url_launcher", "Start_ChatGPT_Server_URL.bat" in browser_doc and "Server URL" in browser_doc))

    mcp_setup = _text("docs/mcp_setup.md") if (ROOT / "docs/mcp_setup.md").is_file() else ""
    checks.append(_result("mcp_setup_links_browser_connector", "chatgpt_browser_connector.md" in mcp_setup))
    checks.append(_result("mcp_setup_mentions_tunnel_launcher", "Start_OpenAI_MCP_Tunnel.bat" in mcp_setup))
    checks.append(_result("mcp_setup_mentions_combined_launcher", "Start_ChatGPT_Connector.bat" in mcp_setup))

    combined_bat = ROOT / "Start_ChatGPT_Connector.bat"
    combined_ps1 = ROOT / "scripts" / "start_chatgpt_connector.ps1"
    server_url_bat = ROOT / "Start_ChatGPT_Server_URL.bat"
    server_url_ps1 = ROOT / "scripts" / "start_chatgpt_server_url.ps1"
    bridge_bat = ROOT / "Start_ChatGPT_MCP_Server.bat"
    tunnel_bat = ROOT / "Start_OpenAI_MCP_Tunnel.bat"
    reset_bat = ROOT / "Reset_ChatGPT_Connector_Credentials.bat"
    checks.append(_result("chatgpt_combined_bat_exists", combined_bat.is_file()))
    checks.append(_result("chatgpt_combined_ps1_exists", combined_ps1.is_file()))
    checks.append(_result("chatgpt_server_url_bat_exists", server_url_bat.is_file()))
    checks.append(_result("chatgpt_server_url_ps1_exists", server_url_ps1.is_file()))
    checks.append(_result("chatgpt_bridge_bat_exists", bridge_bat.is_file()))
    checks.append(_result("openai_tunnel_bat_exists", tunnel_bat.is_file()))
    checks.append(_result("chatgpt_reset_credentials_bat_exists", reset_bat.is_file()))
    if combined_ps1.is_file():
        combined_text = combined_ps1.read_text(encoding="utf-8")
        checks.append(_result("chatgpt_combined_launcher_starts_bridge", "overtli_blender.server" in combined_text and "Start-Process" in combined_text))
        checks.append(_result("chatgpt_combined_launcher_stops_owned_bridge", "Stop-Process" in combined_text and "$StartedServer" in combined_text))
        checks.append(_result("chatgpt_combined_launcher_uses_tunnel_client", "tunnel-client.exe" in combined_text and "& $TunnelExe run" in combined_text))
        checks.append(_result("chatgpt_combined_launcher_uses_no_auth_tunnel_sample", "--sample sample_mcp_remote_no_auth" in combined_text and "--force" in combined_text))
        checks.append(_result("chatgpt_combined_launcher_prompts_for_missing_credentials", "Read-Host" in combined_text and "-AsSecureString" in combined_text))
        checks.append(_result("chatgpt_combined_launcher_validates_tunnel_id", "^tunnel_[a-z0-9]{32}$" in combined_text))
        checks.append(_result("chatgpt_combined_launcher_stores_runtime_key_dpapi", "ConvertFrom-SecureString" in combined_text and "control_plane_api_key.dpapi" in combined_text))
        checks.append(_result("chatgpt_combined_launcher_stores_tunnel_config", "tunnel.json" in combined_text and "Save-StoredTunnelId" in combined_text))
    if server_url_ps1.is_file():
        server_url_text = server_url_ps1.read_text(encoding="utf-8")
        checks.append(_result("chatgpt_server_url_launcher_starts_bridge", "overtli_blender.server" in server_url_text and "Start-Process" in server_url_text))
        checks.append(_result("chatgpt_server_url_launcher_uses_cloudflared", "cloudflared.exe" in server_url_text and "cloudflared-windows-amd64.exe" in server_url_text))
        checks.append(_result("chatgpt_server_url_launcher_prints_mcp_url", "trycloudflare.com" in server_url_text and "/mcp" in server_url_text and "Server URL" in server_url_text))
        checks.append(_result("chatgpt_server_url_launcher_allows_public_tunnel_hosts", "--allow-public-tunnel-hosts" in server_url_text))
        checks.append(_result("chatgpt_server_url_launcher_stops_owned_processes", "Stop-Process" in server_url_text and "$TunnelProcess" in server_url_text))
    if tunnel_bat.is_file():
        tunnel_text = tunnel_bat.read_text(encoding="utf-8")
        checks.append(_result("openai_tunnel_bat_uses_tunnel_client", '"%TUNNEL_CLIENT_EXE%" init' in tunnel_text and '"%TUNNEL_CLIENT_EXE%" run' in tunnel_text))
        checks.append(_result("openai_tunnel_bat_uses_no_auth_tunnel_sample", "--sample sample_mcp_remote_no_auth" in tunnel_text and "--force" in tunnel_text))
        checks.append(_result("openai_tunnel_bat_requires_tunnel_id", "OVERTLI_TUNNEL_ID" in tunnel_text and "CONTROL_PLANE_API_KEY" in tunnel_text))
        checks.append(_result("openai_tunnel_bat_prefers_local_exe", "tools\\tunnel-client.exe" in tunnel_text))
        checks.append(_result("openai_tunnel_bat_validates_tunnel_id", "^tunnel_[a-z0-9]{32}$" in tunnel_text))

    if (ROOT / "src" / "overtli_blender" / "runtime" / "tool_profiles.py").is_file():
        from overtli_blender.runtime.tool_profiles import get_profile

        profile = get_profile("browser_full_standard")
        legacy = get_profile("chatgpt_browser_default")
        checks.append(_result("tool_profile_exists", profile is not None))
        checks.append(_result("tool_profile_legacy_alias", legacy is not None and legacy.to_dict() == profile.to_dict() if profile is not None else False))
        if profile is not None:
            checks.append(_result("tool_profile_bounded", profile.max_visible_tools <= 160, {"max_visible_tools": profile.max_visible_tools}))
            checks.append(_result("tool_profile_remote_safe", profile.permission_profile == "browser_standard", profile.permission_profile))
            hidden = set(profile.hidden_risky_tools)
            checks.append(_result("tool_profile_hides_raw_python", "execute_code" in hidden and "execute_blender_code" in hidden))
            checks.append(_result("tool_profile_hides_provider_downloads", {"download_polyhaven_asset", "download_sketchfab_model", "create_rodin_job"} <= hidden))

    from overtli_blender.runtime.capabilities import PROFILE_CAPABILITIES

    remote_caps = PROFILE_CAPABILITIES.get("browser_standard", set())
    legacy_caps = PROFILE_CAPABILITIES.get("remote_browser_safe", set())
    checks.append(_result("remote_safety_profile_exists", bool(remote_caps)))
    checks.append(_result("remote_safety_legacy_alias", legacy_caps == remote_caps))
    checks.append(_result("remote_safety_allows_scene_write", "scene.write" in remote_caps))
    checks.append(_result("remote_safety_disables_raw_python", "raw_python" not in remote_caps))
    checks.append(_result("remote_safety_disables_external_write", "filesystem.external.write" not in remote_caps))
    checks.append(_result("remote_safety_disables_file_delete", "filesystem.delete" not in remote_caps))

    return checks


def _browser_write_profile_checks(url: str | None = None) -> list[dict]:
    checks: list[dict] = []
    from overtli_blender.runtime.capabilities import PROFILE_CAPABILITIES
    from overtli_blender.runtime.preferences_schema import APPROVAL_MODES, default_preferences
    from overtli_blender.runtime.tool_profiles import get_profile
    from overtli_blender.server import create_mcp_server

    profile = get_profile("browser_full_standard")
    legacy = get_profile("chatgpt_browser_default")
    checks.append(_result("browser_full_standard_exists", profile is not None))
    checks.append(_result("chatgpt_browser_default_aliases_browser_full_standard", profile is not None and legacy is not None and legacy.to_dict() == profile.to_dict()))
    browser_caps = PROFILE_CAPABILITIES.get("browser_standard", set())
    legacy_caps = PROFILE_CAPABILITIES.get("remote_browser_safe", set())
    checks.append(_result("browser_standard_exists", bool(browser_caps)))
    checks.append(_result("remote_browser_safe_aliases_browser_standard", browser_caps == legacy_caps))
    checks.append(_result("browser_standard_allows_safe_scene_write", {"scene.read", "scene.write", "filesystem.project.write"} <= browser_caps, sorted(browser_caps)))
    checks.append(_result("browser_standard_blocks_danger_caps", not {"raw_python", "network.providers", "filesystem.delete", "addon.manage", "addon.execute", "external_process"}.intersection(browser_caps)))
    prefs = default_preferences()
    security = prefs.get("security", {})
    checks.append(_result("approval_modes_exist", {"always_ask", "ask_for_medium_high", "ask_for_high_destructive", "ask_for_destructive_only", "full_access_developer", "read_only"} <= APPROVAL_MODES))
    checks.append(_result("browser_approval_default", security.get("default_browser_approval_mode") == "ask_for_destructive_only", security))
    checks.append(_result("local_approval_default", security.get("default_local_approval_mode") == "ask_for_high_destructive", security))
    checks.append(_result("approval_timeout_default", security.get("approval_timeout_seconds") == 900, security.get("approval_timeout_seconds")))

    server = create_mcp_server(profile="browser_full_standard", remote_safety="browser_standard")
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    missing = sorted(REQUIRED_BROWSER_TOOLS - tools)
    dangerous_visible = sorted(DANGEROUS_BROWSER_TOOLS.intersection(tools))
    checks.append(_result("browser_required_tools_visible", not missing, {"missing": missing, "visible_count": len(tools)}))
    checks.append(_result("browser_danger_tools_hidden", not dangerous_visible, {"visible": dangerous_visible}))
    checks.append(_result("browser_execute_approved_visible", "execute_approved_operation" in tools))
    checks.append(_result("browser_approve_and_execute_visible", "approve_and_execute_operation" in tools))
    if url:
        checks.extend(_live_http_checks(url))
    return checks


def _live_http_checks(url: str) -> list[dict]:
    health_url = url.replace("/mcp", "/health")
    protected_resource_url = url.replace("/mcp", "/.well-known/oauth-protected-resource/mcp")
    authorization_server_url = url.replace("/mcp", "/.well-known/oauth-authorization-server")
    checks: list[dict] = []
    try:
        with urllib.request.urlopen(health_url, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        checks.append(_result("health_endpoint_responds", False, str(exc)))
    else:
        checks.append(_result("health_endpoint_responds", True, payload))
        checks.append(_result("health_endpoint_mentions_mcp", payload.get("mcp_endpoint") == "/mcp", payload))
    try:
        with urllib.request.urlopen(protected_resource_url, timeout=3) as response:
            protected_resource = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        checks.append(_result("oauth_protected_resource_metadata_responds", False, str(exc)))
    else:
        checks.append(_result("oauth_protected_resource_metadata_responds", True, protected_resource))
        checks.append(_result("oauth_protected_resource_metadata_mentions_mcp", protected_resource.get("resource", "").endswith("/mcp"), protected_resource))
        checks.append(_result("oauth_protected_resource_metadata_has_authorization_server", bool(protected_resource.get("authorization_servers")), protected_resource))
    try:
        with urllib.request.urlopen(authorization_server_url, timeout=3) as response:
            authorization_server = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        checks.append(_result("oauth_authorization_server_metadata_responds", False, str(exc)))
    else:
        checks.append(_result("oauth_authorization_server_metadata_responds", True, authorization_server))
        checks.append(_result("oauth_authorization_server_metadata_has_endpoints", bool(authorization_server.get("authorization_endpoint")) and bool(authorization_server.get("token_endpoint")), authorization_server))
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
    parser.add_argument("--browser-write-profile", action="store_true", help="Run Phase 10D browser write profile checks.")
    parser.add_argument("--browser-mutation-smoke", action="store_true", help="Run Phase 10D browser mutation readiness checks against HTTP metadata and static profile.")
    parser.add_argument("--url", default=DEFAULT_MCP_URL, help="HTTP MCP URL for --live-http.")
    parser.add_argument("--live-blender", action="store_true", help="Check the Blender addon socket.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9876)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if not args.static and not args.live_http and not args.live_blender and not args.browser_write_profile and not args.browser_mutation_smoke:
        args.static = True

    checks: list[dict] = []
    if args.static:
        checks.extend(_static_checks())
    if args.live_http:
        checks.extend(_live_http_checks(args.url))
    if args.live_blender:
        checks.extend(_live_blender_checks(args.host, args.port))
    if args.browser_write_profile:
        checks.extend(_browser_write_profile_checks(args.url if args.url != DEFAULT_MCP_URL else None))
    if args.browser_mutation_smoke:
        checks.extend(_browser_write_profile_checks(args.url))

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
