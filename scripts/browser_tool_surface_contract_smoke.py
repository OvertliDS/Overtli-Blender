from __future__ import annotations

import argparse
import json
from typing import Any

from overtli_blender.server import create_mcp_server


REQUIRED_CALLABLE_TOOLS = {
    "clear_scene": "clear scene",
    "delete_objects": "delete objects",
    "delete_collection": "delete collection",
    "measure_object": "measure object dimension",
}

FULL_BROWSER_REQUIRED_TOOLS = {
    "execute_code",
    "execute_blender_code",
    "execute_approved_addon_operator",
    "register_context_script",
    "execute_context_script",
    "install_local_addon",
    "enable_blender_addon",
    "disable_blender_addon",
    "remove_blender_addon",
    "run_skill_pack",
    "run_verified_snippet_smoke",
}


def _load_search_result(server: Any, query: str) -> dict[str, Any]:
    search_tool = server._tool_manager._tools["search_tools"]  # type: ignore[attr-defined]
    return json.loads(search_tool.fn(query))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify browser discovery and MCP callable surface agree.")
    parser.add_argument("--profile", default="browser_full_standard")
    parser.add_argument("--remote-safety", default="browser_standard")
    args = parser.parse_args()

    server = create_mcp_server(profile=args.profile, remote_safety=args.remote_safety)
    tools = set(server._tool_manager._tools)  # type: ignore[attr-defined]
    missing = sorted(name for name in REQUIRED_CALLABLE_TOOLS if name not in tools)
    if missing:
        raise SystemExit(f"Missing required browser-callable tools: {missing}")

    high_risk_missing = sorted(FULL_BROWSER_REQUIRED_TOOLS - tools)
    if high_risk_missing:
        raise SystemExit(f"Full browser profile is missing required high-risk tools: {high_risk_missing}")

    mismatches: list[dict[str, Any]] = []
    required_discovery: dict[str, list[str]] = {}
    for required_tool, query in REQUIRED_CALLABLE_TOOLS.items():
        result = _load_search_result(server, query)
        discovered = [tool.get("name") for tool in result.get("results", [])]
        required_discovery[required_tool] = discovered
        if required_tool not in discovered:
            mismatches.append({"query": query, "required_tool": required_tool, "discovered": discovered})
        unknown = sorted(name for name in discovered if name not in tools)
        if unknown:
            mismatches.append({"query": query, "unknown_after_discovery": unknown})

    if mismatches:
        raise SystemExit(json.dumps({"status": "failed", "mismatches": mismatches}, indent=2))

    print(
        json.dumps(
            {
                "status": "passed",
                "profile": args.profile,
                "remote_safety": args.remote_safety,
                "visible_count": len(tools),
                "required_callable_tools": sorted(REQUIRED_CALLABLE_TOOLS),
                "full_browser_required_tools": sorted(FULL_BROWSER_REQUIRED_TOOLS),
                "required_discovery": required_discovery,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
