"""MCP tool registration for PolyHaven tools."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from typing import Any


logger = logging.getLogger("BlenderMCPServer")


def _is_polyhaven_enabled() -> bool:
    try:
        server_module = importlib.import_module("blender_mcp.server")
        return bool(getattr(server_module, "_polyhaven_enabled", False))
    except Exception:
        return False


def register_polyhaven_tools(mcp: Any, get_blender_connection: Callable[[], Any]) -> None:
    """Register PolyHaven MCP tools on the provided FastMCP app."""

    @mcp.tool()
    def get_polyhaven_categories(ctx: Any, asset_type: str = "hdris") -> str:
        """
        Get a list of categories for a specific asset type on Polyhaven.

        Parameters:
        - asset_type: The type of asset to get categories for (hdris, textures, models, all)
        """
        try:
            blender = get_blender_connection()
            if not _is_polyhaven_enabled():
                return "PolyHaven integration is disabled. Select it in the sidebar in BlenderMCP, then run it again."
            result = blender.send_command("get_polyhaven_categories", {"asset_type": asset_type})

            if "error" in result:
                return f"Error: {result['error']}"

            # Format the categories in a more readable way
            categories = result["categories"]
            formatted_output = f"Categories for {asset_type}:\n\n"

            # Sort categories by count (descending)
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)

            for category, count in sorted_categories:
                formatted_output += f"- {category}: {count} assets\n"

            return formatted_output
        except Exception as e:
            logger.error(f"Error getting Polyhaven categories: {str(e)}")
            return f"Error getting Polyhaven categories: {str(e)}"

    @mcp.tool()
    def search_polyhaven_assets(
        ctx: Any,
        asset_type: str = "all",
        categories: str = None,
    ) -> str:
        """
        Search for assets on Polyhaven with optional filtering.

        Parameters:
        - asset_type: Type of assets to search for (hdris, textures, models, all)
        - categories: Optional comma-separated list of categories to filter by

        Returns a list of matching assets with basic information.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("search_polyhaven_assets", {
                "asset_type": asset_type,
                "categories": categories,
            })

            if "error" in result:
                return f"Error: {result['error']}"

            # Format the assets in a more readable way
            assets = result["assets"]
            total_count = result["total_count"]
            returned_count = result["returned_count"]

            formatted_output = f"Found {total_count} assets"
            if categories:
                formatted_output += f" in categories: {categories}"
            formatted_output += f"\nShowing {returned_count} assets:\n\n"

            # Sort assets by download count (popularity)
            sorted_assets = sorted(assets.items(), key=lambda x: x[1].get("download_count", 0), reverse=True)

            for asset_id, asset_data in sorted_assets:
                formatted_output += f"- {asset_data.get('name', asset_id)} (ID: {asset_id})\n"
                formatted_output += f"  Type: {['HDRI', 'Texture', 'Model'][asset_data.get('type', 0)]}\n"
                formatted_output += f"  Categories: {', '.join(asset_data.get('categories', []))}\n"
                formatted_output += f"  Downloads: {asset_data.get('download_count', 'Unknown')}\n\n"

            return formatted_output
        except Exception as e:
            logger.error(f"Error searching Polyhaven assets: {str(e)}")
            return f"Error searching Polyhaven assets: {str(e)}"

    @mcp.tool()
    def download_polyhaven_asset(
        ctx: Any,
        asset_id: str,
        asset_type: str,
        resolution: str = "1k",
        file_format: str = None,
    ) -> str:
        """
        Download and import a Polyhaven asset into Blender.

        Parameters:
        - asset_id: The ID of the asset to download
        - asset_type: The type of asset (hdris, textures, models)
        - resolution: The resolution to download (e.g., 1k, 2k, 4k)
        - file_format: Optional file format (e.g., hdr, exr for HDRIs; jpg, png for textures; gltf, fbx for models)

        Returns a message indicating success or failure.
        """
        try:
            blender = get_blender_connection()
            result = blender.send_command("download_polyhaven_asset", {
                "asset_id": asset_id,
                "asset_type": asset_type,
                "resolution": resolution,
                "file_format": file_format,
            })

            if "error" in result:
                return f"Error: {result['error']}"

            if result.get("success"):
                message = result.get("message", "Asset downloaded and imported successfully")

                # Add additional information based on asset type
                if asset_type == "hdris":
                    return f"{message}. The HDRI has been set as the world environment."
                elif asset_type == "textures":
                    material_name = result.get("material", "")
                    material_handle = result.get("material_handle", "")
                    maps = ", ".join(result.get("maps", []))
                    output = f"{message}. Created material '{material_name}' with maps: {maps}."
                    if material_handle:
                        output += f"\nMaterial handle '{material_handle}' created for easy reference in scripts: get_material('{material_handle}')"
                    return output
                elif asset_type == "models":
                    output = f"{message}. The model has been imported into the current scene."
                    object_handles = result.get("object_handles", {})
                    if object_handles:
                        handles_list = [f"'{handle}' -> {obj_name}" for handle, obj_name in object_handles.items()]
                        output += f"\nObject handles created: {', '.join(handles_list)}"
                        output += f"\nUse in scripts: get_object('handle_name')"
                    return output
                else:
                    return message
            else:
                return f"Failed to download asset: {result.get('message', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Error downloading Polyhaven asset: {str(e)}")
            return f"Error downloading Polyhaven asset: {str(e)}"

    @mcp.tool()
    def set_texture(
        ctx: Any,
        object_name: str,
        texture_id: str,
    ) -> str:
        """
        Apply a previously downloaded Polyhaven texture to an object.

        Parameters:
        - object_name: Name of the object to apply the texture to
        - texture_id: ID of the Polyhaven texture to apply (must be downloaded first)

        Returns a message indicating success or failure.
        """
        try:
            # Get the global connection
            blender = get_blender_connection()
            result = blender.send_command("set_texture", {
                "object_name": object_name,
                "texture_id": texture_id,
            })

            if "error" in result:
                return f"Error: {result['error']}"

            if result.get("success"):
                material_name = result.get("material", "")
                maps = ", ".join(result.get("maps", []))

                # Add detailed material info
                material_info = result.get("material_info", {})
                node_count = material_info.get("node_count", 0)
                has_nodes = material_info.get("has_nodes", False)
                texture_nodes = material_info.get("texture_nodes", [])

                output = f"Successfully applied texture '{texture_id}' to {object_name}.\n"
                output += f"Using material '{material_name}' with maps: {maps}.\n\n"
                output += f"Material has nodes: {has_nodes}\n"
                output += f"Total node count: {node_count}\n\n"

                if texture_nodes:
                    output += "Texture nodes:\n"
                    for node in texture_nodes:
                        output += f"- {node['name']} using image: {node['image']}\n"
                        if node["connections"]:
                            output += "  Connections:\n"
                            for conn in node["connections"]:
                                output += f"    {conn}\n"
                else:
                    output += "No texture nodes found in the material.\n"

                return output
            else:
                return f"Failed to apply texture: {result.get('message', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Error applying texture: {str(e)}")
            return f"Error applying texture: {str(e)}"
