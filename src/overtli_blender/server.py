"""Overtli-Blender MCP server entrypoint."""

from __future__ import annotations

import argparse
import json
import socket

from mcp.server.fastmcp import FastMCP, Image
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

from overtli_blender.connection import BlenderConnection
from overtli_blender.runtime.capabilities import DEFAULT_CAPABILITY_POLICY, PROFILE_CAPABILITIES
from overtli_blender.runtime.command_registry import list_command_specs
from overtli_blender.runtime.tool_profiles import get_profile
from overtli_blender.server_config import get_default_config
from overtli_blender.tools.registry import register_all_tools

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OvertliBlenderServer")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    # We don't need to create a connection here since we're using the global connection
    # for resources and tools
    
    try:
        # Just log that we're starting up
        logger.info("Overtli-Blender server starting up")
        
        # Try to connect to Blender on startup to verify it's available
        try:
            # This will initialize the global connection if needed
            blender = get_blender_connection()
            logger.info("Successfully connected to Blender on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Blender on startup: {str(e)}")
            logger.warning("Make sure the Blender addon is running before using Blender resources or tools")
        
        # Return an empty context - we're using the global connection
        yield {}
    finally:
        # Clean up the global connection on shutdown
        global _blender_connection
        if _blender_connection:
            logger.info("Disconnecting from Blender on shutdown")
            _blender_connection.disconnect()
            _blender_connection = None
        logger.info("Overtli-Blender server shut down")

HTTP_TRANSPORT_ALIASES = {
    "http": "streamable-http",
    "streamable-http": "streamable-http",
    "sse": "sse",
    "stdio": "stdio",
}
DEFAULT_HTTP_HOST = "127.0.0.1"
DEFAULT_HTTP_PORT = 2091
DEFAULT_HTTP_PATH = "/mcp"
DEFAULT_CHATGPT_PROFILE = "chatgpt_browser_default"
DEFAULT_REMOTE_SAFETY = "remote_browser_safe"

# Resource endpoints

# Global connection for resources (since resources can't access context)
_blender_connection = None
_polyhaven_enabled = False

def get_blender_connection():
    """Get or create a persistent Blender connection"""
    global _blender_connection, _polyhaven_enabled
    
    # If we have an existing connection, check if it's still valid
    if _blender_connection is not None:
        try:
            # First check if PolyHaven is enabled by sending a ping command
            result = _blender_connection.send_command("get_polyhaven_status")
            # Store the PolyHaven status globally
            _polyhaven_enabled = result.get("enabled", False)
            return _blender_connection
        except Exception as e:
            # Connection is dead, close it and create a new one
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _blender_connection.disconnect()
            except:
                pass
            _blender_connection = None
    
    # Create a new connection if needed
    if _blender_connection is None:
        config = get_default_config()
        _blender_connection = BlenderConnection(
            host=config.host,
            port=config.port,
            timeout_seconds=config.timeout_seconds,
        )
        if not _blender_connection.connect():
            logger.error("Failed to connect to Blender")
            _blender_connection = None
            raise Exception("Could not connect to Blender. Make sure the Blender addon is running.")
        logger.info("Created new persistent connection to Blender")

    return _blender_connection


def _blender_socket_status() -> dict[str, Any]:
    config = get_default_config()
    status: dict[str, Any] = {
        "host": config.host,
        "port": config.port,
        "connected": False,
    }
    try:
        with socket.create_connection((config.host, config.port), timeout=1.0):
            status["connected"] = True
    except OSError as exc:
        status["error"] = str(exc)
    return status


def _visible_tool_names_for_profile(profile_name: str | None) -> set[str] | None:
    if not profile_name:
        return None
    profile = get_profile(profile_name)
    if profile is None:
        raise ValueError(f"Unknown tool profile: {profile_name}")

    hidden = set(profile.hidden_risky_tools)
    allowed_packs = set(profile.enabled_tool_packs)
    specs = [
        spec
        for spec in list_command_specs()
        if spec.tool_pack in allowed_packs
        and spec.name not in hidden
        and spec.risk_level != "HIGH"
        and not spec.destructive
        and "raw_python" not in spec.allowed_capabilities
        and "network.providers" not in spec.allowed_capabilities
        and "addon.execute" not in spec.allowed_capabilities
        and "filesystem.delete" not in spec.allowed_capabilities
    ]
    specs.sort(key=lambda spec: (not spec.read_only, spec.risk_level, spec.tool_pack, spec.name))
    visible = {spec.name for spec in specs[: profile.max_visible_tools]}
    visible.update(
        {
            "discover_tool_packs",
            "get_tool_pack",
            "search_tools",
            "get_tool_spec",
            "get_recommended_tools_for_task",
            "get_permission_profile",
            "get_capability_policy",
            "validate_command_capabilities",
        }
    )
    visible.difference_update(hidden)
    return visible


def _apply_tool_profile(server: FastMCP, profile_name: str | None) -> None:
    visible = _visible_tool_names_for_profile(profile_name)
    if visible is None:
        return
    tool_manager = getattr(server, "_tool_manager", None)
    tools = getattr(tool_manager, "_tools", {})
    for tool_name in list(tools):
        if tool_name not in visible:
            server.remove_tool(tool_name)


def _apply_remote_safety(remote_safety: str | None) -> None:
    if not remote_safety:
        return
    if remote_safety not in PROFILE_CAPABILITIES:
        raise ValueError(f"Unknown remote safety profile: {remote_safety}")
    DEFAULT_CAPABILITY_POLICY.profile = remote_safety


async def _health(_request):
    from starlette.responses import JSONResponse

    socket_status = _blender_socket_status()
    status = "ok" if socket_status["connected"] else "degraded"
    return JSONResponse(
        {
            "status": status,
            "service": "overtli-blender-http-mcp",
            "mcp_endpoint": DEFAULT_HTTP_PATH,
            "blender_socket": socket_status,
            "message": "Blender addon socket is reachable." if socket_status["connected"] else "Start Blender, enable Overtli-Blender, and start the socket server on localhost:9876.",
        }
    )


async def _metadata(request):
    from starlette.responses import JSONResponse

    server = request.app.state.overtli_mcp_server
    tools = await server.list_tools()
    return JSONResponse(
        {
            "name": "Overtli-Blender",
            "description": "Inspect, organize, and safely control a local Blender scene through the Overtli-Blender MCP bridge.",
            "mcp_endpoint": DEFAULT_HTTP_PATH,
            "tool_count": len(tools),
            "default_tool_profile": getattr(request.app.state, "overtli_tool_profile", None),
            "remote_safety": getattr(request.app.state, "overtli_remote_safety", None),
            "recommended_permission": "Always ask",
        }
    )


def _add_http_routes(server: FastMCP, profile_name: str | None, remote_safety: str | None) -> None:
    from starlette.routing import Route

    async def metadata_with_state(request):
        request.app.state.overtli_mcp_server = server
        request.app.state.overtli_tool_profile = profile_name
        request.app.state.overtli_remote_safety = remote_safety
        return await _metadata(request)

    server._custom_starlette_routes.extend(  # type: ignore[attr-defined]
        [
            Route("/health", endpoint=_health, methods=["GET"]),
            Route("/metadata", endpoint=metadata_with_state, methods=["GET"]),
            Route("/status", endpoint=metadata_with_state, methods=["GET"]),
        ]
    )


def create_mcp_server(
    *,
    host: str = DEFAULT_HTTP_HOST,
    port: int = DEFAULT_HTTP_PORT,
    profile: str | None = None,
    remote_safety: str | None = None,
) -> FastMCP:
    server = FastMCP(
        "Overtli-Blender",
        instructions=(
            "Use Overtli-Blender to inspect local Blender scene state, plan safe workflows, "
            "request approval before mutations, and avoid raw Python or destructive actions unless explicitly approved."
        ),
        host=host,
        port=port,
        streamable_http_path=DEFAULT_HTTP_PATH,
        lifespan=server_lifespan,
    )
    _apply_remote_safety(remote_safety)
    register_all_tools(server, get_blender_connection, image_type=Image)
    _apply_tool_profile(server, profile)
    _add_http_routes(server, profile, remote_safety)
    return server


# Default stdio server object retained for MCP clients and existing imports.
mcp = create_mcp_server()

@mcp.prompt()
def asset_creation_strategy() -> str:
    """Defines the preferred strategy for creating assets in Blender"""
    return """When creating 3D content in Blender, always start by checking if integrations are available:

    0. Before anything, always check the scene from get_scene_info()
    1. First use the following tools to verify if the following integrations are enabled:
        1. PolyHaven
            Use get_polyhaven_status() to verify its status
            If PolyHaven is enabled:
            - For objects/models: Use download_polyhaven_asset() with asset_type="models"
            - For materials/textures: Use download_polyhaven_asset() with asset_type="textures"
            - For environment lighting: Use download_polyhaven_asset() with asset_type="hdris"
        2. Sketchfab
            Sketchfab is good at Realistic models, and has a wider variety of models than PolyHaven.
            Use get_sketchfab_status() to verify its status
            If Sketchfab is enabled:
            - For objects/models: First search using search_sketchfab_models() with your query
            - Then download specific models using download_sketchfab_model() with the UID
            - Note that only downloadable models can be accessed, and API key must be properly configured
            - Sketchfab has a wider variety of models than PolyHaven, especially for specific subjects
        3. Hyper3D(Rodin)
            Hyper3D Rodin is good at generating 3D models for single item.
            So don't try to:
            1. Generate the whole scene with one shot
            2. Generate ground using Hyper3D
            3. Generate parts of the items separately and put them together afterwards

            Use get_hyper3d_status() to verify its status
            If Hyper3D is enabled:
            - For objects/models, do the following steps:
                1. Create the model generation task
                    - Use generate_hyper3d_model_via_images() if image(s) is/are given
                    - Use generate_hyper3d_model_via_text() if generating 3D asset using text prompt
                    If key type is free_trial and insufficient balance error returned, tell the user that the free trial key can only generated limited models everyday, they can choose to:
                    - Wait for another day and try again
                    - Go to hyper3d.ai to find out how to get their own API key
                    - Go to fal.ai to get their own private API key
                2. Poll the status
                    - Use poll_rodin_job_status() to check if the generation task has completed or failed
                3. Import the asset
                    - Use import_generated_asset() to import the generated GLB model the asset
                4. After importing the asset, ALWAYS check the world_bounding_box of the imported mesh, and adjust the mesh's location and size
                    Adjust the imported mesh's location, scale, rotation, so that the mesh is on the right spot.

                You can reuse assets previous generated by running python code to duplicate the object, without creating another generation task.

    3. Always check the world_bounding_box for each item so that:
        - Ensure that all objects that should not be clipping are not clipping.
        - Items have right spatial relationship.
    
    4. Recommended asset source priority:
        - For specific existing objects: First try Sketchfab, then PolyHaven
        - For generic objects/furniture: First try PolyHaven, then Sketchfab
        - For custom or unique items not available in libraries: Use Hyper3D Rodin
        - For environment lighting: Use PolyHaven HDRIs
        - For materials/textures: Use PolyHaven textures

    Only fall back to scripting when:
    - PolyHaven, Sketchfab, and Hyper3D are all disabled
    - A simple primitive is explicitly requested
    - No suitable asset exists in any of the libraries
    - Hyper3D Rodin failed to generate the desired asset
    - The task specifically requires a basic material/color
    """

# Main execution

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Overtli-Blender MCP server.")
    parser.add_argument("--transport", choices=sorted(HTTP_TRANSPORT_ALIASES), default="stdio")
    parser.add_argument("--http", action="store_true", help="Alias for --transport http.")
    parser.add_argument("--host", default=DEFAULT_HTTP_HOST, help="HTTP/SSE bind host.")
    parser.add_argument("--port", type=int, default=DEFAULT_HTTP_PORT, help="HTTP/SSE bind port.")
    parser.add_argument("--profile", help="Optional MCP visible tool profile, for example chatgpt_browser_default.")
    parser.add_argument("--remote-safety", help="Optional remote safety permission profile, for example remote_browser_safe.")
    parser.add_argument("--status-json", action="store_true", help="Print server mode metadata and exit.")
    return parser.parse_args(argv)


def build_server_status(args: argparse.Namespace) -> dict[str, Any]:
    transport = "http" if args.http else args.transport
    normalized = HTTP_TRANSPORT_ALIASES[transport]
    profile = args.profile or (DEFAULT_CHATGPT_PROFILE if normalized in {"streamable-http", "sse"} else None)
    remote_safety = args.remote_safety or (DEFAULT_REMOTE_SAFETY if normalized in {"streamable-http", "sse"} else None)
    profile_obj = get_profile(profile) if profile else None
    return {
        "status": "success",
        "transport": normalized,
        "host": args.host,
        "port": args.port,
        "mcp_url": f"http://{args.host}:{args.port}{DEFAULT_HTTP_PATH}" if normalized != "stdio" else None,
        "health_url": f"http://{args.host}:{args.port}/health" if normalized != "stdio" else None,
        "profile": profile,
        "remote_safety": remote_safety,
        "visible_tool_budget": profile_obj.max_visible_tools if profile_obj else None,
    }


def main(argv: list[str] | None = None):
    """Run the MCP server."""
    args = _parse_args(argv)
    status = build_server_status(args)
    if args.status_json:
        print(json.dumps(status, indent=2))
        return

    if status["transport"] == "stdio":
        mcp.run("stdio")
        return

    server = create_mcp_server(
        host=args.host,
        port=args.port,
        profile=status["profile"],
        remote_safety=status["remote_safety"],
    )
    logger.info("Starting Overtli-Blender HTTP MCP bridge at %s", status["mcp_url"])
    logger.info("Health endpoint: %s", status["health_url"])
    logger.info("Tool profile: %s; remote safety: %s", status["profile"], status["remote_safety"])
    server.run(status["transport"])

if __name__ == "__main__":
    main()


