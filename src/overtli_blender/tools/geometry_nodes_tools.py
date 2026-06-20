"""MCP tool registration for geometry nodes tools."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Dict, List


logger = logging.getLogger("BlenderMCPServer")


def register_geometry_nodes_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register geometry nodes MCP tools on the provided FastMCP app."""

    @mcp.tool()
    def complete_geometry_node(
        ctx: Any,
        object_name: str,
        nodes: List[Dict[str, Any]],
        links: List[Dict[str, Any]],
        input_sockets: List[Dict[str, str]] = None,
    ) -> str:
        """
        Create a complete geometry node network for procedural modeling.

        This tool enables AI-driven procedural modeling by creating sophisticated geometry node networks.
        Perfect for creating parametric objects like tables, chairs, organic shapes, and complex procedural geometry.

        Parameters:
        - object_name: Name of the object to apply geometry nodes to (will be created if doesn't exist)
        - nodes: List of node definitions, each containing:
          - type: Node type (e.g., "GeometryNodeMeshCube", "GeometryNodeSubdivisionSurface")
          - location: [x, y] position in node editor (optional)
          - label: Custom label for the node (optional)
          - inputs: Dict of input values {input_name: value} (optional)
          - properties: Dict of node properties {property_name: value} (optional)
        - links: List of connections between nodes:
          - from_node: Source node index (int) or name (str)
          - from_socket: Source socket name (str) or index (int)
          - to_node: Target node index (int) or name (str)
          - to_socket: Target socket name (str) or index (int)
        - input_sockets: Interface inputs for the node group (optional):
          - name: Input name
          - type: Socket type (e.g., "VALUE", "VECTOR", "GEOMETRY")
          - value: Default value (optional)

        Example for a simple procedural table:
        nodes = [
            {"type": "NodeGroupInput", "location": [0, 0]},
            {"type": "GeometryNodeMeshCube", "location": [200, 200], "inputs": {"Size": [2, 0.1, 1]}},
            {"type": "GeometryNodeMeshCube", "location": [200, 0], "inputs": {"Size": [0.1, 1.8, 0.1]}},
            {"type": "GeometryNodeJoinGeometry", "location": [400, 100]},
            {"type": "NodeGroupOutput", "location": [600, 100]}
        ]
        links = [
            {"from_node": 1, "from_socket": "Mesh", "to_node": 3, "to_socket": 0},
            {"from_node": 2, "from_socket": "Mesh", "to_node": 3, "to_socket": 0},
            {"from_node": 3, "from_socket": "Geometry", "to_node": 4, "to_socket": "Geometry"}
        ]

        Returns success message with details about the created node network.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("complete_geometry_node", {
                "object_name": object_name,
                "nodes": nodes,
                "links": links,
                "input_sockets": input_sockets,
            })

            if "error" in result:
                return f"Error: {result['error']}"

            if result.get("success"):
                message = result.get("message", "Geometry node network created")
                node_group = result.get("node_group", "")
                nodes_created = result.get("nodes_created", 0)
                links_created = result.get("links_created", 0)
                object_handle = result.get("object_handle", "")

                output = f"{message}\n"
                output += f"Node group: {node_group}\n"
                output += f"Created {nodes_created} nodes and {links_created} links\n"
                output += f"Object '{object_name}' now has procedural geometry nodes applied"

                if object_handle:
                    output += f"\nObject handle '{object_handle}' created for easy reference in scripts: get_object('{object_handle}')"

                return output
            else:
                return f"Failed to create geometry node network: {result.get('message', 'Unknown error')}"

        except Exception as e:
            logger.error(f"Error creating geometry node network: {str(e)}")
            return f"Error creating geometry node network: {str(e)}"

    @mcp.tool()
    def get_geometry_nodes_status(ctx: Any) -> str:
        """
        Check the status of Geometry Nodes support in Blender.

        Returns information about Blender version and geometry nodes capabilities.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("get_geometry_nodes_status")

            enabled = result.get("enabled", False)
            blender_version = result.get("blender_version", "Unknown")
            is_blender_4 = result.get("is_blender_4", False)
            message = result.get("message", "")

            if enabled:
                output = f"{message}\n"
                output += f"Blender version: {blender_version}\n"
                output += f"Blender 4.x features: {'Available' if is_blender_4 else 'Not available'}\n"
                output += f"\nGeometry Nodes enables procedural modeling with AI assistance.\n"
                output += f"You can create complex parametric objects, organic shapes, and procedural geometry."
                return output
            else:
                return f"Geometry Nodes not available: {message}"

        except Exception as e:
            logger.error(f"Error checking Geometry Nodes status: {str(e)}")
            return f"Error checking Geometry Nodes status: {str(e)}"
