from __future__ import annotations

from ..core import *

class ProviderStatusService:
    def __init__(self, server):
        self.server = server

    def get_polyhaven_status(self):
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled:
            return {"enabled": True, "message": "PolyHaven integration is enabled and ready to use."}
        return {
            "enabled": False,
            "message": """PolyHaven integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Poly Haven' checkbox
                            3. Restart the connection to the MCP server"""
        }

    def get_hyper3d_status(self):
        enabled = bpy.context.scene.blendermcp_use_hyper3d
        if enabled:
            if not bpy.context.scene.blendermcp_hyper3d_api_key:
                return {
                    "enabled": False,
                    "message": """Hyper3D Rodin integration is currently enabled, but API key is not given. To enable it:
                                1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Hyper3D Rodin 3D model generation' checkbox checked
                                3. Choose the right plaform and fill in the API Key
                                4. Restart the connection to the MCP server"""
                }
            mode = bpy.context.scene.blendermcp_hyper3d_mode
            message = f"Hyper3D Rodin integration is enabled and ready to use. Mode: {mode}. " + \
                f"Key type: {'private' if bpy.context.scene.blendermcp_hyper3d_api_key != RODIN_FREE_TRIAL_KEY else 'free_trial'}"
            return {"enabled": True, "message": message}
        return {
            "enabled": False,
            "message": """Hyper3D Rodin integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use Hyper3D Rodin 3D model generation' checkbox
                            3. Restart the connection to the MCP server"""
        }

    def get_sketchfab_status(self):
        enabled = bpy.context.scene.blendermcp_use_sketchfab
        api_key = bpy.context.scene.blendermcp_sketchfab_api_key

        if api_key:
            try:
                response = requests.get(
                    "https://api.sketchfab.com/v3/me",
                    headers={"Authorization": f"Token {api_key}"},
                    timeout=30,
                )
                if response.status_code == 200:
                    user_data = response.json()
                    username = user_data.get("username", "Unknown user")
                    return {
                        "enabled": True,
                        "message": f"Sketchfab integration is enabled and ready to use. Logged in as: {username}"
                    }
                return {
                    "enabled": False,
                    "message": f"Sketchfab API key seems invalid. Status code: {response.status_code}"
                }
            except requests.exceptions.Timeout:
                return {
                    "enabled": False,
                    "message": "Timeout connecting to Sketchfab API. Check your internet connection."
                }
            except Exception as e:
                return {
                    "enabled": False,
                    "message": f"Error testing Sketchfab API key: {str(e)}"
                }

        if enabled and api_key:
            return {"enabled": True, "message": "Sketchfab integration is enabled and ready to use."}
        if enabled and not api_key:
            return {
                "enabled": False,
                "message": """Sketchfab integration is currently enabled, but API key is not given. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Keep the 'Use Sketchfab' checkbox checked
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to the MCP server"""
            }
        return {
            "enabled": False,
            "message": """Sketchfab integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Sketchfab' checkbox
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to the MCP server"""
        }

class PolyHavenService:
    def __init__(self, server):
        self.server = server

    def get_polyhaven_categories(self, asset_type):
        try:
            if asset_type not in ["hdris", "textures", "models", "all"]:
                return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}

            response = requests.get(f"https://api.polyhaven.com/categories/{asset_type}", headers=REQ_HEADERS)
            if response.status_code == 200:
                return {"categories": response.json()}
            return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def search_polyhaven_assets(self, asset_type=None, categories=None):
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}
            if asset_type and asset_type != "all":
                if asset_type not in ["hdris", "textures", "models"]:
                    return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}
                params["type"] = asset_type
            if categories:
                params["categories"] = categories
            response = requests.get(url, params=params, headers=REQ_HEADERS)
            if response.status_code == 200:
                assets = response.json()
                limited_assets = {}
                for i, (key, value) in enumerate(assets.items()):
                    if i >= 20:
                        break
                    limited_assets[key] = value
                return {"assets": limited_assets, "total_count": len(assets), "returned_count": len(limited_assets)}
            return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def download_polyhaven_asset(self, asset_id, asset_type, resolution="1k", file_format=None):
        try:
            files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}", headers=REQ_HEADERS)
            if files_response.status_code != 200:
                return {"error": f"Failed to get asset files: {files_response.status_code}"}

            files_data = files_response.json()

            if asset_type == "hdris":
                if not file_format:
                    file_format = "hdr"
                if "hdri" in files_data and resolution in files_data["hdri"] and file_format in files_data["hdri"][resolution]:
                    file_info = files_data["hdri"][resolution][file_format]
                    file_url = file_info["url"]
                    with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                        response = requests.get(file_url, headers=REQ_HEADERS)
                        if response.status_code != 200:
                            return {"error": f"Failed to download HDRI: {response.status_code}"}
                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name

                    try:
                        if not bpy.data.worlds:
                            bpy.data.worlds.new("World")
                        world = bpy.data.worlds[0]
                        world.use_nodes = True
                        node_tree = world.node_tree
                        for node in node_tree.nodes:
                            node_tree.nodes.remove(node)

                        tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
                        tex_coord.location = (-800, 0)
                        mapping = node_tree.nodes.new(type='ShaderNodeMapping')
                        mapping.location = (-600, 0)
                        env_tex = node_tree.nodes.new(type='ShaderNodeTexEnvironment')
                        env_tex.location = (-400, 0)
                        env_tex.image = bpy.data.images.load(tmp_path)
                        if file_format.lower() == 'exr':
                            try:
                                env_tex.image.colorspace_settings.name = 'Linear'
                            except:
                                env_tex.image.colorspace_settings.name = 'Non-Color'
                        else:
                            for color_space in ['Linear', 'Linear Rec.709', 'Non-Color']:
                                try:
                                    env_tex.image.colorspace_settings.name = color_space
                                    break
                                except:
                                    continue
                        background = node_tree.nodes.new(type='ShaderNodeBackground')
                        background.location = (-200, 0)
                        output = node_tree.nodes.new(type='ShaderNodeOutputWorld')
                        output.location = (0, 0)
                        node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
                        node_tree.links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
                        node_tree.links.new(env_tex.outputs['Color'], background.inputs['Color'])
                        node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
                        bpy.context.scene.world = world
                        try:
                            tempfile._cleanup()
                        except:
                            pass
                        return {"success": True, "message": f"HDRI {asset_id} imported successfully", "image_name": env_tex.image.name}
                    except Exception as e:
                        return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
                return {"error": f"Requested resolution or format not available for this HDRI"}

            if asset_type == "textures":
                if not file_format:
                    file_format = "jpg"
                downloaded_maps = {}
                try:
                    for map_type in files_data:
                        if map_type not in ["blend", "gltf"]:
                            if resolution in files_data[map_type] and file_format in files_data[map_type][resolution]:
                                file_info = files_data[map_type][resolution][file_format]
                                file_url = file_info["url"]
                                with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                                    response = requests.get(file_url, headers=REQ_HEADERS)
                                    if response.status_code == 200:
                                        tmp_file.write(response.content)
                                        tmp_path = tmp_file.name
                                        image = bpy.data.images.load(tmp_path)
                                        image.name = f"{asset_id}_{map_type}.{file_format}"
                                        image.pack()
                                        if map_type in ['color', 'diffuse', 'albedo']:
                                            try:
                                                image.colorspace_settings.name = 'sRGB'
                                            except:
                                                pass
                                        else:
                                            try:
                                                image.colorspace_settings.name = 'Non-Color'
                                            except:
                                                pass
                                        downloaded_maps[map_type] = image
                                        try:
                                            os.unlink(tmp_path)
                                        except:
                                            pass
                    if not downloaded_maps:
                        return {"error": "No texture maps found for the requested resolution and format"}
                    mat = bpy.data.materials.new(name=asset_id)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    for node in nodes:
                        nodes.remove(node)
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    output.location = (300, 0)
                    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
                    principled.location = (0, 0)
                    links.new(principled.outputs[0], output.inputs[0])
                    tex_coord = nodes.new(type='ShaderNodeTexCoord')
                    tex_coord.location = (-800, 0)
                    mapping = nodes.new(type='ShaderNodeMapping')
                    mapping.location = (-600, 0)
                    mapping.vector_type = 'TEXTURE'
                    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
                    x_pos = -400
                    y_pos = 300
                    for map_type, image in downloaded_maps.items():
                        tex_node = nodes.new(type='ShaderNodeTexImage')
                        tex_node.location = (x_pos, y_pos)
                        tex_node.image = image
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            try:
                                tex_node.image.colorspace_settings.name = 'sRGB'
                            except:
                                pass
                        else:
                            try:
                                tex_node.image.colorspace_settings.name = 'Non-Color'
                            except:
                                pass
                        links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                        elif map_type.lower() in ['roughness', 'rough']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                        elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                        elif map_type.lower() in ['normal', 'nor']:
                            normal_map = nodes.new(type='ShaderNodeNormalMap')
                            normal_map.location = (x_pos + 200, y_pos)
                            links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                            links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                        elif map_type in ['displacement', 'disp', 'height']:
                            disp_node = nodes.new(type='ShaderNodeDisplacement')
                            disp_node.location = (x_pos + 200, y_pos - 200)
                            links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                            links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                        y_pos -= 250

                    texture_nodes = {}
                    for node in nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            for map_type, image in downloaded_maps.items():
                                if node.image == image:
                                    texture_nodes[map_type] = node
                                    break
                    for map_name in ['color', 'diffuse', 'albedo']:
                        if map_name in texture_nodes:
                            links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                            break
                    for map_name in ['roughness', 'rough']:
                        if map_name in texture_nodes:
                            links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                            break
                    for map_name in ['metallic', 'metalness', 'metal']:
                        if map_name in texture_nodes:
                            links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                            break
                    for map_name in ['gl', 'dx', 'nor']:
                        if map_name in texture_nodes:
                            normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                            normal_map_node.location = (100, 100)
                            links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                            links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                            break
                    for map_name in ['displacement', 'disp', 'height']:
                        if map_name in texture_nodes:
                            disp_node = nodes.new(type='ShaderNodeDisplacement')
                            disp_node.location = (300, -200)
                            disp_node.inputs['Scale'].default_value = 0.1
                            links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                            links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                            break
                    if 'arm' in texture_nodes:
                        separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
                        separate_rgb.location = (-200, -100)
                        links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Image'])
                        if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                            links.new(separate_rgb.outputs['G'], principled.inputs['Roughness'])
                        if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                            links.new(separate_rgb.outputs['B'], principled.inputs['Metallic'])
                        base_color_node = None
                        for map_name in ['color', 'diffuse', 'albedo']:
                            if map_name in texture_nodes:
                                base_color_node = texture_nodes[map_name]
                                break
                        if base_color_node:
                            mix_node = nodes.new(type='ShaderNodeMixRGB')
                            mix_node.location = (100, 200)
                            mix_node.blend_type = 'MULTIPLY'
                            mix_node.inputs['Fac'].default_value = 0.8
                            for link in base_color_node.outputs['Color'].links:
                                if link.to_socket == principled.inputs['Base Color']:
                                    links.remove(link)
                            links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                            links.new(separate_rgb.outputs['R'], mix_node.inputs[2])
                            links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    if 'ao' in texture_nodes:
                        base_color_node = None
                        for map_name in ['color', 'diffuse', 'albedo']:
                            if map_name in texture_nodes:
                                base_color_node = texture_nodes[map_name]
                                break
                        if base_color_node:
                            mix_node = nodes.new(type='ShaderNodeMixRGB')
                            mix_node.location = (100, 200)
                            mix_node.blend_type = 'MULTIPLY'
                            mix_node.inputs['Fac'].default_value = 0.8
                            for link in base_color_node.outputs['Color'].links:
                                if link.to_socket == principled.inputs['Base Color']:
                                    links.remove(link)
                            links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                            links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                            links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    material_handle = f"material_{asset_id}"
                    self.server.shared_context['materials'][material_handle] = mat
                    self.server._add_to_history("download_polyhaven_asset", f"texture {asset_id}", f"Created material {mat.name}")
                    return {
                        "success": True,
                        "message": f"Texture {asset_id} imported as material",
                        "material": mat.name,
                        "material_handle": material_handle,
                        "maps": list(downloaded_maps.keys())
                    }
                except Exception as e:
                    return {"error": f"Failed to process textures: {str(e)}"}

            if asset_type == "models":
                if not file_format:
                    file_format = "gltf"
                if file_format in files_data and resolution in files_data[file_format]:
                    file_info = files_data[file_format][resolution][file_format]
                    file_url = file_info["url"]
                    temp_dir = tempfile.mkdtemp()
                    main_file_path = ""
                    try:
                        main_file_name = file_url.split("/")[-1]
                        main_file_path = os.path.join(temp_dir, main_file_name)
                        response = requests.get(file_url, headers=REQ_HEADERS)
                        if response.status_code != 200:
                            return {"error": f"Failed to download model: {response.status_code}"}
                        with open(main_file_path, "wb") as f:
                            f.write(response.content)
                        if "include" in file_info and file_info["include"]:
                            for include_path, include_info in file_info["include"].items():
                                include_url = include_info["url"]
                                include_file_path = os.path.join(temp_dir, include_path)
                                os.makedirs(os.path.dirname(include_file_path), exist_ok=True)
                                include_response = requests.get(include_url, headers=REQ_HEADERS)
                                if include_response.status_code == 200:
                                    with open(include_file_path, "wb") as f:
                                        f.write(include_response.content)
                        if file_format in ("gltf", "glb"):
                            bpy.ops.import_scene.gltf(filepath=main_file_path)
                        elif file_format == "fbx":
                            bpy.ops.import_scene.fbx(filepath=main_file_path)
                        elif file_format == "obj":
                            bpy.ops.import_scene.obj(filepath=main_file_path)
                        elif file_format == "blend":
                            with bpy.data.libraries.load(main_file_path, link=False) as (data_from, data_to):
                                data_to.objects = data_from.objects
                            for obj in data_to.objects:
                                if obj is not None:
                                    bpy.context.collection.objects.link(obj)
                        else:
                            return {"error": f"Unsupported model format: {file_format}"}
                        imported_objects = [obj.name for obj in bpy.context.selected_objects]
                        object_handles = {}
                        for i, obj_name in enumerate(imported_objects):
                            handle = f"imported_{asset_id}_{i}"
                            self.server.shared_context['objects'][handle] = bpy.data.objects[obj_name]
                            object_handles[handle] = obj_name
                        self.server._add_to_history("download_polyhaven_asset", f"model {asset_id}", f"Imported {len(imported_objects)} objects")
                        return {
                            "success": True,
                            "message": f"Model {asset_id} imported successfully",
                            "imported_objects": imported_objects,
                            "object_handles": object_handles
                        }
                    except Exception as e:
                        return {"error": f"Failed to import model: {str(e)}"}
                    finally:
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                return {"error": "Requested format or resolution not available for this model"}

            return {"error": f"Unsupported asset type: {asset_type}"}
        except Exception as e:
            return {"error": f"Failed to download asset: {str(e)}"}

    def set_texture(self, object_name, texture_id):
        try:
            obj = bpy.data.objects.get(object_name)
            if not obj:
                return {"error": f"Object not found: {object_name}"}
            if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
                return {"error": f"Object {object_name} cannot accept materials"}

            texture_images = {}
            for img in bpy.data.images:
                if img.name.startswith(texture_id + "_"):
                    map_type = img.name.split('_')[-1].split('.')[0]
                    img.reload()
                    if map_type.lower() in ['color', 'diffuse', 'albedo']:
                        try:
                            img.colorspace_settings.name = 'sRGB'
                        except:
                            pass
                    else:
                        try:
                            img.colorspace_settings.name = 'Non-Color'
                        except:
                            pass
                    if not img.packed_file:
                        img.pack()
                    texture_images[map_type] = img

            if not texture_images:
                return {"error": f"No texture images found for: {texture_id}. Please download the texture first."}

            new_mat_name = f"{texture_id}_material_{object_name}"
            existing_mat = bpy.data.materials.get(new_mat_name)
            if existing_mat:
                bpy.data.materials.remove(existing_mat)
            new_mat = bpy.data.materials.new(name=new_mat_name)
            new_mat.use_nodes = True
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links
            nodes.clear()
            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (600, 0)
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            principled.location = (300, 0)
            links.new(principled.outputs[0], output.inputs[0])
            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            tex_coord.location = (-800, 0)
            mapping = nodes.new(type='ShaderNodeMapping')
            mapping.location = (-600, 0)
            mapping.vector_type = 'TEXTURE'
            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
            x_pos = -400
            y_pos = 300
            for map_type, image in texture_images.items():
                tex_node = nodes.new(type='ShaderNodeTexImage')
                tex_node.location = (x_pos, y_pos)
                tex_node.image = image
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    try:
                        tex_node.image.colorspace_settings.name = 'sRGB'
                    except:
                        pass
                else:
                    try:
                        tex_node.image.colorspace_settings.name = 'Non-Color'
                    except:
                        pass
                links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                elif map_type.lower() in ['roughness', 'rough']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                elif map_type.lower() in ['normal', 'nor', 'dx', 'gl']:
                    normal_map = nodes.new(type='ShaderNodeNormalMap')
                    normal_map.location = (x_pos + 200, y_pos)
                    links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                elif map_type.lower() in ['displacement', 'disp', 'height']:
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (x_pos + 200, y_pos - 200)
                    disp_node.inputs['Scale'].default_value = 0.1
                    links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                y_pos -= 250

            texture_nodes = {}
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    for map_type, image in texture_images.items():
                        if node.image == image:
                            texture_nodes[map_type] = node
                            break
            for map_name in ['color', 'diffuse', 'albedo']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                    break
            for map_name in ['roughness', 'rough']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                    break
            for map_name in ['metallic', 'metalness', 'metal']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                    break
            for map_name in ['normal', 'nor', 'dx', 'gl']:
                if map_name in texture_nodes:
                    normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                    normal_map_node.location = (100, 100)
                    links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                    links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                    break
            for map_name in ['displacement', 'disp', 'height']:
                if map_name in texture_nodes:
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (300, -200)
                    disp_node.inputs['Scale'].default_value = 0.1
                    links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                    break

            if 'arm' in texture_nodes:
                separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
                separate_rgb.location = (-200, -100)
                links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Image'])
                if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                    links.new(separate_rgb.outputs['G'], principled.inputs['Roughness'])
                if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                    links.new(separate_rgb.outputs['B'], principled.inputs['Metallic'])
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break
                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(separate_rgb.outputs['R'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])

            if 'ao' in texture_nodes:
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break
                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])

            while len(obj.data.materials) > 0:
                obj.data.materials.pop(index=0)
            obj.data.materials.append(new_mat)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.context.view_layer.update()
            material_handle = f"material_{texture_id}"
            self.server.shared_context['materials'][material_handle] = new_mat
            self.server._add_to_history("set_texture", f"texture {texture_id}", f"Created material {new_mat.name}")

            material_info = {
                "name": new_mat.name,
                "has_nodes": new_mat.use_nodes,
                "node_count": len(new_mat.node_tree.nodes),
                "texture_nodes": []
            }
            for node in new_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    connections = []
                    for output in node.outputs:
                        for link in output.links:
                            connections.append(f"{output.name} → {link.to_node.name}.{link.to_socket.name}")
                    material_info["texture_nodes"].append({
                        "name": node.name,
                        "image": node.image.name,
                        "colorspace": node.image.colorspace_settings.name,
                        "connections": connections
                    })

            return {
                "success": True,
                "message": f"Created new material and applied texture {texture_id} to {object_name}",
                "material": new_mat.name,
                "maps": list(texture_images.keys()),
                "material_info": material_info
            }
        except Exception as e:
            print(f"Error in set_texture: {str(e)}")
            traceback.print_exc()
            return {"error": f"Failed to apply texture: {str(e)}"}


class SketchfabService:
    def __init__(self, server):
        self.server = server

    def get_sketchfab_status(self):
        return ProviderStatusService(self.server).get_sketchfab_status()

    def search_sketchfab_models(self, query, categories=None, count=20, downloadable=True):
        try:
            api_key = bpy.context.scene.blendermcp_sketchfab_api_key
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}
            params = {
                "type": "models",
                "q": query,
                "count": count,
                "downloadable": downloadable,
                "archives_flavours": False
            }
            if categories:
                params["categories"] = categories
            headers = {"Authorization": f"Token {api_key}"}
            response = requests.get("https://api.sketchfab.com/v3/search", headers=headers, params=params, timeout=30)
            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}
            if response.status_code != 200:
                return {"error": f"API request failed with status code {response.status_code}"}
            response_data = response.json()
            if response_data is None:
                return {"error": "Received empty response from Sketchfab API"}
            results = response_data.get("results", [])
            if not isinstance(results, list):
                return {"error": f"Unexpected response format from Sketchfab API: {response_data}"}
            return response_data
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def download_sketchfab_model(self, uid):
        try:
            api_key = bpy.context.scene.blendermcp_sketchfab_api_key
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}
            headers = {"Authorization": f"Token {api_key}"}
            download_endpoint = f"https://api.sketchfab.com/v3/models/{uid}/download"
            response = requests.get(download_endpoint, headers=headers, timeout=30)
            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}
            if response.status_code != 200:
                return {"error": f"Download request failed with status code {response.status_code}"}
            data = response.json()
            if data is None:
                return {"error": "Received empty response from Sketchfab API for download request"}
            gltf_data = data.get("gltf")
            if not gltf_data:
                return {"error": "No gltf download URL available for this model. Response: " + str(data)}
            download_url = gltf_data.get("url")
            if not download_url:
                return {"error": "No download URL available for this model. Make sure the model is downloadable and you have access."}
            model_response = requests.get(download_url, timeout=60)
            if model_response.status_code != 200:
                return {"error": f"Model download failed with status code {model_response.status_code}"}
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, f"{uid}.zip")
            with open(zip_file_path, "wb") as f:
                f.write(model_response.content)
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    file_path = file_info.filename
                    target_path = os.path.join(temp_dir, os.path.normpath(file_path))
                    abs_temp_dir = os.path.abspath(temp_dir)
                    abs_target_path = os.path.abspath(target_path)
                    if not abs_target_path.startswith(abs_temp_dir):
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with path traversal attempt"}
                    if ".." in file_path:
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with directory traversal sequence"}
                zip_ref.extractall(temp_dir)
            gltf_files = [f for f in os.listdir(temp_dir) if f.endswith('.gltf') or f.endswith('.glb')]
            if not gltf_files:
                with suppress(Exception):
                    shutil.rmtree(temp_dir)
                return {"error": "No glTF file found in the downloaded model"}
            main_file = os.path.join(temp_dir, gltf_files[0])
            bpy.ops.import_scene.gltf(filepath=main_file)
            imported_objects = [obj.name for obj in bpy.context.selected_objects]
            with suppress(Exception):
                shutil.rmtree(temp_dir)
            return {
                "success": True,
                "message": "Model imported successfully",
                "imported_objects": imported_objects
            }
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection and try again with a simpler model."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Failed to download model: {str(e)}"}


class Hyper3DService:
    def __init__(self, server):
        self.server = server

    def get_hyper3d_status(self):
        return ProviderStatusService(self.server).get_hyper3d_status()

    def create_rodin_job(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.create_rodin_job_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.create_rodin_job_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def create_rodin_job_main_site(self, text_prompt: str = None, images: list[tuple[str, str]] = None, bbox_condition=None):
        try:
            if images is None:
                images = []
            files = [
                *[("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)],
                ("tier", (None, "Sketch")),
                ("mesh_mode", (None, "Raw")),
            ]
            if text_prompt:
                files.append(("prompt", (None, text_prompt)))
            if bbox_condition:
                files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post(
                "https://hyperhuman.deemos.com/api/v2/rodin",
                headers={"Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}"},
                files=files
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def create_rodin_job_fal_ai(self, text_prompt: str = None, images: list[tuple[str, str]] = None, bbox_condition=None):
        try:
            req_data = {"tier": "Sketch"}
            if images:
                req_data["input_image_urls"] = images
            if text_prompt:
                req_data["prompt"] = text_prompt
            if bbox_condition:
                req_data["bbox_condition"] = bbox_condition
            response = requests.post(
                "https://queue.fal.run/fal-ai/hyper3d/rodin",
                headers={
                    "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
                    "Content-Type": "application/json",
                },
                json=req_data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.poll_rodin_job_status_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.poll_rodin_job_status_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def poll_rodin_job_status_main_site(self, subscription_key: str):
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/status",
            headers={"Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}"},
            json={"subscription_key": subscription_key},
        )
        data = response.json()
        return {"status_list": [i["status"] for i in data["jobs"]]}

    def poll_rodin_job_status_fal_ai(self, request_id: str):
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
            headers={"Authorization": f"KEY {bpy.context.scene.blendermcp_hyper3d_api_key}"},
        )
        return response.json()

    def import_generated_asset(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.import_generated_asset_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.import_generated_asset_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def import_generated_asset_main_site(self, task_uuid: str, name: str):
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/download",
            headers={"Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}"},
            json={'task_uuid': task_uuid}
        )
        data_ = response.json()
        temp_file = None
        for i in data_["list"]:
            if i["name"].endswith(".glb"):
                temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=task_uuid, suffix=".glb")
                try:
                    response = requests.get(i["url"], stream=True)
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    temp_file.close()
                except Exception as e:
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return {"succeed": False, "error": str(e)}
                break
        else:
            return {"succeed": False, "error": "Generation failed. Please first make sure that all jobs of the task are done and then try again later."}

        try:
            obj = self.server._clean_imported_glb(filepath=temp_file.name, mesh_name=name)
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }
            if obj.type == "MESH":
                result["world_bounding_box"] = self.server._get_aabb(obj)
            return {"succeed": True, **result}
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_generated_asset_fal_ai(self, request_id: str, name: str):
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={"Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}"},
        )
        data_ = response.json()
        temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=request_id, suffix=".glb")
        try:
            response = requests.get(data_["model_mesh"]["url"], stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file.close()
        except Exception as e:
            temp_file.close()
            os.unlink(temp_file.name)
            return {"succeed": False, "error": str(e)}

        try:
            obj = self.server._clean_imported_glb(filepath=temp_file.name, mesh_name=name)
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }
            if obj.type == "MESH":
                result["world_bounding_box"] = self.server._get_aabb(obj)
            return {"succeed": True, **result}
        except Exception as e:
            return {"succeed": False, "error": str(e)}

class AssetPathService:
    MODEL_EXTENSIONS = {".glb", ".gltf", ".obj", ".fbx", ".stl", ".ply", ".usd", ".usda", ".usdc", ".abc", ".dae"}
    TEXTURE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".hdr", ".webp"}
    MEDIA_EXTENSIONS = {".mp4", ".mov", ".avi"}

    @staticmethod
    def artifact_root(artifact_root=None):
        return RenderArtifactService.artifact_root(artifact_root)

    @staticmethod
    def workspace_path(*parts, artifact_root=None):
        path = os.path.join(AssetPathService.artifact_root(artifact_root), ".overtli_blender", *parts)
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def local_path(path, must_exist=True):
        if not path:
            raise ValueError("A local filesystem path is required")
        value = os.path.abspath(os.path.expanduser(str(path)))
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", str(path)):
            raise ValueError("Only local filesystem paths are supported")
        if must_exist and not os.path.exists(value):
            raise ValueError(f"Path does not exist: {value}")
        return value

    @staticmethod
    def classify(path):
        ext = os.path.splitext(str(path))[1].lower()
        if ext == ".blend":
            return "blend"
        if ext in AssetPathService.MODEL_EXTENSIONS:
            return "model"
        if ext in AssetPathService.TEXTURE_EXTENSIONS:
            return "texture"
        if ext in AssetPathService.MEDIA_EXTENSIONS:
            return "media"
        return "unknown"

    @staticmethod
    def write_json(path, data):
        RenderArtifactService.write_json(path, data)
        return path


class AssetLibraryIntelligenceService:
    IMPORT_OPERATORS = {
        "glb": [("bpy.ops.import_scene.gltf", lambda filepath: bpy.ops.import_scene.gltf(filepath=filepath))],
        "gltf": [("bpy.ops.import_scene.gltf", lambda filepath: bpy.ops.import_scene.gltf(filepath=filepath))],
        "obj": [("bpy.ops.wm.obj_import", lambda filepath: bpy.ops.wm.obj_import(filepath=filepath)), ("bpy.ops.import_scene.obj", lambda filepath: bpy.ops.import_scene.obj(filepath=filepath))],
        "fbx": [("bpy.ops.import_scene.fbx", lambda filepath: bpy.ops.import_scene.fbx(filepath=filepath))],
        "stl": [("bpy.ops.wm.stl_import", lambda filepath: bpy.ops.wm.stl_import(filepath=filepath)), ("bpy.ops.import_mesh.stl", lambda filepath: bpy.ops.import_mesh.stl(filepath=filepath))],
        "ply": [("bpy.ops.wm.ply_import", lambda filepath: bpy.ops.wm.ply_import(filepath=filepath)), ("bpy.ops.import_mesh.ply", lambda filepath: bpy.ops.import_mesh.ply(filepath=filepath))],
        "usd": [("bpy.ops.wm.usd_import", lambda filepath: bpy.ops.wm.usd_import(filepath=filepath))],
        "usda": [("bpy.ops.wm.usd_import", lambda filepath: bpy.ops.wm.usd_import(filepath=filepath))],
        "usdc": [("bpy.ops.wm.usd_import", lambda filepath: bpy.ops.wm.usd_import(filepath=filepath))],
        "abc": [("bpy.ops.wm.alembic_import", lambda filepath: bpy.ops.wm.alembic_import(filepath=filepath))],
        "dae": [("bpy.ops.wm.collada_import", lambda filepath: bpy.ops.wm.collada_import(filepath=filepath))],
    }
    EXPORT_OPERATORS = {
        "glb": [("bpy.ops.export_scene.gltf", lambda filepath, selected: bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLB", use_selection=selected))],
        "gltf": [("bpy.ops.export_scene.gltf", lambda filepath, selected: bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLTF_SEPARATE", use_selection=selected))],
        "obj": [("bpy.ops.wm.obj_export", lambda filepath, selected: bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=selected)), ("bpy.ops.export_scene.obj", lambda filepath, selected: bpy.ops.export_scene.obj(filepath=filepath, use_selection=selected))],
        "fbx": [("bpy.ops.export_scene.fbx", lambda filepath, selected: bpy.ops.export_scene.fbx(filepath=filepath, use_selection=selected))],
        "stl": [("bpy.ops.wm.stl_export", lambda filepath, selected: bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=selected)), ("bpy.ops.export_mesh.stl", lambda filepath, selected: bpy.ops.export_mesh.stl(filepath=filepath, use_selection=selected))],
        "ply": [("bpy.ops.wm.ply_export", lambda filepath, selected: bpy.ops.wm.ply_export(filepath=filepath, export_selected_objects=selected)), ("bpy.ops.export_mesh.ply", lambda filepath, selected: bpy.ops.export_mesh.ply(filepath=filepath, use_selection=selected))],
        "usd": [("bpy.ops.wm.usd_export", lambda filepath, selected: bpy.ops.wm.usd_export(filepath=filepath, selected_objects_only=selected))],
        "usda": [("bpy.ops.wm.usd_export", lambda filepath, selected: bpy.ops.wm.usd_export(filepath=filepath, selected_objects_only=selected))],
        "usdc": [("bpy.ops.wm.usd_export", lambda filepath, selected: bpy.ops.wm.usd_export(filepath=filepath, selected_objects_only=selected))],
        "abc": [("bpy.ops.wm.alembic_export", lambda filepath, selected: bpy.ops.wm.alembic_export(filepath=filepath, selected=selected))],
        "dae": [("bpy.ops.wm.collada_export", lambda filepath, selected: bpy.ops.wm.collada_export(filepath=filepath, selected=selected))],
    }

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _operator_exists(path):
        target = bpy.ops
        for part in path.replace("bpy.ops.", "").split("."):
            if not hasattr(target, part):
                return False
            target = getattr(target, part)
        return True

    def _format_status(self, mapping):
        result = {}
        for fmt, options in mapping.items():
            found = next((name for name, _runner in options if self._operator_exists(name)), None)
            result[fmt] = {"supported": bool(found), "operator": found}
        return result

    def get_supported_asset_formats(self):
        return {
            "status": "success",
            "import_formats": self._format_status(self.IMPORT_OPERATORS),
            "export_formats": self._format_status(self.EXPORT_OPERATORS),
            "blend_library": {"append_supported": True, "link_supported": True},
            "warnings": [],
        }

    def choose_importer(self, fmt):
        for name, runner in self.IMPORT_OPERATORS.get(str(fmt).lower(), []):
            if self._operator_exists(name):
                return name, runner
        return None, None

    def choose_exporter(self, fmt):
        for name, runner in self.EXPORT_OPERATORS.get(str(fmt).lower(), []):
            if self._operator_exists(name):
                return name, runner
        return None, None

    def scan_asset_folder(self, folder_path, recursive=True, include_textures=True, include_blend_files=True, include_model_files=True, max_files=1000, write_manifest=True, artifact_root=None):
        try:
            folder = AssetPathService.local_path(folder_path)
            if not os.path.isdir(folder):
                return {"status": "error", "message": "folder_path must be a directory", "warnings": []}
            max_files = max(1, min(int(max_files), 5000))
            formats = self.get_supported_asset_formats()
            assets = []
            by_type = {"model": 0, "texture": 0, "blend": 0, "media": 0, "unknown": 0}
            walker = os.walk(folder) if recursive else [(folder, [], os.listdir(folder))]
            truncated = False
            for root, dirs, files in walker:
                dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".venv", "Library", "Temp", "Logs", "Obj"}]
                for filename in files:
                    path = os.path.join(root, filename)
                    kind = AssetPathService.classify(path)
                    if kind == "texture" and not include_textures:
                        continue
                    if kind == "blend" and not include_blend_files:
                        continue
                    if kind == "model" and not include_model_files:
                        continue
                    stat = os.stat(path)
                    ext = os.path.splitext(filename)[1].lower().lstrip(".")
                    assets.append({"path": path, "name": filename, "extension": "." + ext if ext else "", "kind": kind, "size_bytes": stat.st_size, "modified_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)), "import_supported": bool(formats["import_formats"].get(ext, {}).get("supported")) if kind == "model" else kind == "blend", "warnings": []})
                    by_type[kind] = by_type.get(kind, 0) + 1
                    if len(assets) >= max_files:
                        truncated = True
                        break
                if truncated:
                    break
            manifest_path = None
            result = {"status": "success", "folder_path": folder, "recursive": bool(recursive), "file_count": len(assets), "by_type": by_type, "assets": assets, "manifest_path": None, "truncated": truncated, "warnings": []}
            if write_manifest:
                out = os.path.join(AssetPathService.workspace_path("assets", "scans", artifact_root=artifact_root), f"asset_scan_{RenderArtifactService.stamp()}.json")
                manifest_path = AssetPathService.write_json(out, result)
                result["manifest_path"] = manifest_path
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def list_asset_libraries(self, artifact_root=None):
        base = AssetPathService.workspace_path("assets", artifact_root=artifact_root)
        libraries = [{"name": "Repo Local Assets", "path": base, "source": "repo_workspace", "exists": os.path.isdir(base)}]
        prefs = getattr(bpy.context, "preferences", None)
        filepaths = getattr(prefs, "filepaths", None)
        for item in getattr(filepaths, "asset_libraries", []) or []:
            path = os.path.abspath(bpy.path.abspath(item.path))
            libraries.append({"name": item.name, "path": path, "source": "blender_preferences", "exists": os.path.isdir(path)})
        kit_root = AssetPathService.workspace_path("scene_kits", artifact_root=artifact_root)
        libraries.append({"name": "Scene Kits", "path": kit_root, "source": "scene_kits", "exists": os.path.isdir(kit_root)})
        return {"status": "success", "libraries": libraries, "warnings": []}

    def get_asset_file_info(self, file_path, inspect_blend_contents=True):
        try:
            path = AssetPathService.local_path(file_path)
            stat = os.stat(path)
            ext = os.path.splitext(path)[1].lower()
            kind = AssetPathService.classify(path)
            result = {"status": "success", "file_path": path, "name": os.path.basename(path), "extension": ext, "kind": kind, "size_bytes": stat.st_size, "modified_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)), "warnings": []}
            if kind == "model":
                fmt = ext.lstrip(".")
                supported = self.get_supported_asset_formats()["import_formats"].get(fmt, {"supported": False, "operator": None})
                result["import_support"] = supported
            if kind == "blend" and inspect_blend_contents:
                contents = {}
                with bpy.data.libraries.load(path, link=False) as (data_from, _data_to):
                    for attr in ["objects", "collections", "materials", "node_groups", "worlds", "actions"]:
                        contents[attr] = list(getattr(data_from, attr, []) or [])
                result["blend_contents"] = contents
            if kind == "texture":
                image = None
                try:
                    image = bpy.data.images.load(path, check_existing=False)
                    result["image"] = {"size": list(image.size), "source": image.source}
                finally:
                    if image:
                        bpy.data.images.remove(image)
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def list_scene_assets(self, include_objects=True, include_meshes=True, include_materials=True, include_images=True, include_libraries=True, include_actions=True, include_collections=True):
        result = {"status": "success", "counts": {}, "warnings": []}
        if include_objects:
            result["objects"] = [{"name": o.name, "type": o.type, "library": o.library.filepath if o.library else None, "material_slots": [s.material.name for s in o.material_slots if s.material]} for o in bpy.data.objects]
            result["counts"]["objects"] = len(result["objects"])
        if include_meshes:
            result["meshes"] = [{"name": m.name, "users": m.users, "library": m.library.filepath if m.library else None} for m in bpy.data.meshes]
            result["counts"]["meshes"] = len(result["meshes"])
        if include_materials:
            result["materials"] = [{"name": m.name, "users": m.users, "library": m.library.filepath if m.library else None} for m in bpy.data.materials]
            result["counts"]["materials"] = len(result["materials"])
        if include_images:
            images = []
            for image in bpy.data.images:
                path = bpy.path.abspath(image.filepath) if image.filepath else ""
                images.append({"name": image.name, "filepath": path, "packed_file": bool(image.packed_file), "source": image.source, "users": image.users, "missing": bool(path and not os.path.exists(path))})
            result["images"] = images
            result["counts"]["images"] = len(images)
        if include_libraries:
            result["libraries"] = [{"filepath": lib.filepath, "name": lib.name} for lib in bpy.data.libraries]
            result["counts"]["libraries"] = len(result["libraries"])
        if include_actions:
            result["actions"] = [{"name": a.name, "users": a.users, "frame_range": list(a.frame_range)} for a in bpy.data.actions]
            result["counts"]["actions"] = len(result["actions"])
        if include_collections:
            result["collections"] = [{"name": c.name, "object_count": len(c.objects), "child_count": len(c.children), "library": c.library.filepath if c.library else None} for c in bpy.data.collections]
            result["counts"]["collections"] = len(result["collections"])
        return result


class AssetDependencyService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _path_record(datablock, filepath):
        path = bpy.path.abspath(filepath) if filepath else ""
        packed = bool(getattr(datablock, "packed_file", None))
        return {"name": datablock.name, "filepath": path, "raw_filepath": filepath, "packed": packed, "missing": bool(path and not os.path.exists(path) and not packed), "absolute": bool(path and os.path.isabs(path)), "relative": str(filepath).startswith("//") if filepath else False, "users": getattr(datablock, "users", 0)}

    def get_asset_dependency_report(self, include_images=True, include_libraries=True, include_fonts=True, include_movie_clips=True, include_sounds=True, write_manifest=True, artifact_root=None):
        deps = {"images": [], "libraries": [], "fonts": [], "movie_clips": [], "sounds": []}
        if include_images:
            deps["images"] = [self._path_record(image, image.filepath) for image in bpy.data.images if image.filepath or image.packed_file]
        if include_libraries:
            deps["libraries"] = [{"name": lib.name, "filepath": bpy.path.abspath(lib.filepath), "raw_filepath": lib.filepath, "missing": bool(lib.filepath and not os.path.exists(bpy.path.abspath(lib.filepath))), "absolute": os.path.isabs(bpy.path.abspath(lib.filepath)) if lib.filepath else False, "relative": str(lib.filepath).startswith("//")} for lib in bpy.data.libraries]
        if include_fonts:
            deps["fonts"] = [self._path_record(font, font.filepath) for font in bpy.data.fonts if getattr(font, "filepath", "")]
        if include_movie_clips:
            deps["movie_clips"] = [self._path_record(clip, clip.filepath) for clip in bpy.data.movieclips if getattr(clip, "filepath", "")]
        if include_sounds:
            deps["sounds"] = [self._path_record(sound, sound.filepath) for sound in bpy.data.sounds if getattr(sound, "filepath", "")]
        flat = [item for values in deps.values() for item in values]
        summary = {"external_count": len(flat), "missing_count": sum(1 for item in flat if item.get("missing")), "absolute_path_count": sum(1 for item in flat if item.get("absolute")), "relative_path_count": sum(1 for item in flat if item.get("relative")), "packed_count": sum(1 for item in flat if item.get("packed"))}
        result = {"status": "success", "dependencies": deps, "summary": summary, "manifest_path": None, "warnings": []}
        if write_manifest:
            result["manifest_path"] = AssetPathService.write_json(os.path.join(AssetPathService.workspace_path("dependency_reports", artifact_root=artifact_root), f"dependency_report_{RenderArtifactService.stamp()}.json"), result)
        return result

    def create_asset_manifest(self, label=None, include_scene_index=True, include_scene_assets=True, include_dependencies=True, include_materials=True, include_animation=True, include_render_settings=True, include_previews=False, artifact_root=None):
        manifest = {"status": "success", "label": label or "asset_manifest", "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "warnings": []}
        if include_scene_index:
            manifest["scene_index"] = self.server.scene_intelligence_service.get_scene_index(max_objects=1000)
        if include_scene_assets:
            manifest["scene_assets"] = self.server.asset_library_intelligence_service.list_scene_assets(include_materials=include_materials, include_actions=include_animation)
        if include_dependencies:
            manifest["dependencies"] = self.get_asset_dependency_report(write_manifest=False)
        if include_render_settings:
            manifest["render_settings"] = self.server.render_settings_service.get_render_settings()
        if include_previews:
            manifest["preview"] = self.server.asset_preview_service.create_asset_preview(label=label or "asset_manifest_preview", artifact_root=artifact_root)
        safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(label or "manifest")).strip("._-") or "manifest"
        path = os.path.join(AssetPathService.workspace_path("assets", "manifests", artifact_root=artifact_root), f"{safe_label}_{RenderArtifactService.stamp()}.json")
        manifest["manifest_path"] = AssetPathService.write_json(path, manifest)
        return manifest

    def collect_external_dependencies(self, target_dir=None, overwrite=False, include_packed=False, artifact_root=None):
        target = target_dir or AssetPathService.workspace_path("assets", "dependencies", artifact_root=artifact_root)
        target = AssetPathService.local_path(target, must_exist=False)
        os.makedirs(target, exist_ok=True)
        report = self.get_asset_dependency_report(write_manifest=False)
        copied = []
        warnings = []
        for item in report["dependencies"].get("images", []):
            src = item.get("filepath")
            if not src or item.get("packed") and not include_packed or not os.path.exists(src):
                continue
            dst = os.path.join(target, os.path.basename(src))
            if os.path.exists(dst) and not overwrite:
                warnings.append(f"Skipped existing dependency: {dst}")
                continue
            shutil.copy2(src, dst)
            copied.append({"source": src, "target": dst})
        manifest_path = AssetPathService.write_json(os.path.join(target, "dependency_collection_manifest.json"), {"copied": copied, "warnings": warnings})
        return {"status": "success", "target_dir": target, "copied": copied, "manifest_path": manifest_path, "warnings": warnings}

    def validate_external_dependencies(self):
        report = self.get_asset_dependency_report(write_manifest=False)
        return {"status": "success", "portable": report["summary"]["missing_count"] == 0 and report["summary"]["absolute_path_count"] == 0, "dependency_report": report, "warnings": []}

    def pack_external_data(self, confirm=False):
        if not confirm:
            return {"status": "error", "message": "pack_external_data requires confirm=True", "warnings": []}
        try:
            bpy.ops.file.pack_all()
            return {"status": "success", "dependency_report": self.get_asset_dependency_report(write_manifest=False), "warnings": ["Packed external data into the current Blender session; save is not automatic"]}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def make_paths_relative(self, confirm=False):
        if not confirm:
            return {"status": "error", "message": "make_paths_relative requires confirm=True", "warnings": []}
        try:
            bpy.ops.file.make_paths_relative()
            return {"status": "success", "dependency_report": self.get_asset_dependency_report(write_manifest=False), "warnings": ["Converted paths in the current Blender session; save is not automatic"]}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}


class AssetImportService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _names():
        return {"objects": {o.name for o in bpy.data.objects}, "materials": {m.name for m in bpy.data.materials}, "images": {i.name for i in bpy.data.images}, "actions": {a.name for a in bpy.data.actions}}

    @staticmethod
    def _created(before):
        return {"created_objects": [o.name for o in bpy.data.objects if o.name not in before["objects"]], "created_materials": [m.name for m in bpy.data.materials if m.name not in before["materials"]], "created_images": [i.name for i in bpy.data.images if i.name not in before["images"]], "created_actions": [a.name for a in bpy.data.actions if a.name not in before["actions"]]}

    def import_model_file(self, file_path, format_hint=None, collection_name=None, rename_prefix=None, import_materials=True, import_animations=True, import_cameras_lights=True, verify=True):
        try:
            path = AssetPathService.local_path(file_path)
            fmt = str(format_hint or os.path.splitext(path)[1].lstrip(".")).lower()
            _op_name, runner = self.server.asset_library_intelligence_service.choose_importer(fmt)
            if not runner:
                return {"status": "error", "message": f"Unsupported import format: {fmt}", "warnings": []}
            collection = None
            if collection_name:
                collection = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
                if collection.name not in bpy.context.scene.collection.children:
                    bpy.context.scene.collection.children.link(collection)
            before = self._names()
            runner(path)
            created = self._created(before)
            for name in list(created["created_objects"]):
                obj = bpy.data.objects.get(name)
                if obj and rename_prefix:
                    obj.name = f"{rename_prefix}{obj.name}"
                if obj and collection:
                    for col in list(obj.users_collection):
                        col.objects.unlink(obj)
                    collection.objects.link(obj)
            if rename_prefix:
                created = self._created(before)
            verification = self.server.scene_intelligence_service.get_scene_index(max_objects=1000) if verify else None
            manifest = {"status": "success", "file_path": path, "format": fmt, "collection_name": collection.name if collection else None, **created, "verification": verification, "warnings": []}
            out = os.path.join(AssetPathService.workspace_path("imports", "phase5b"), f"import_manifest_{RenderArtifactService.stamp()}.json")
            manifest["manifest_path"] = AssetPathService.write_json(out, manifest)
            return manifest
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}


class AssetExportService:
    def __init__(self, server):
        self.server = server

    def _export(self, fmt, path, selected, overwrite):
        if os.path.exists(path) and not overwrite:
            return {"status": "error", "message": f"Output exists and overwrite=False: {path}", "warnings": []}
        op_name, runner = self.server.asset_library_intelligence_service.choose_exporter(fmt)
        if not runner:
            return {"status": "error", "message": f"Unsupported export format: {fmt}", "warnings": []}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        runner(path, selected)
        return {"status": "success", "format": fmt, "operator": op_name, "output_path": path, "exists": os.path.exists(path), "bytes": os.path.getsize(path) if os.path.exists(path) else 0, "warnings": []}

    def export_selected_objects(self, output_path=None, format_hint="glb", object_names=None, overwrite=False, artifact_root=None):
        fmt = str(format_hint or "glb").lower()
        ext = "glb" if fmt == "glb" else fmt
        path = output_path or os.path.join(AssetPathService.workspace_path("exports", "selected", artifact_root=artifact_root), f"selected_{RenderArtifactService.stamp()}.{ext}")
        path = AssetPathService.local_path(path, must_exist=False)
        previous = list(bpy.context.selected_objects)
        try:
            if object_names:
                bpy.ops.object.select_all(action="DESELECT")
                for name in object_names:
                    obj = bpy.data.objects.get(name)
                    if obj:
                        obj.select_set(True)
            return self._export(fmt, path, True, overwrite)
        finally:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in previous:
                if obj.name in bpy.data.objects:
                    obj.select_set(True)

    def export_scene(self, output_path=None, format_hint="glb", overwrite=False, artifact_root=None):
        fmt = str(format_hint or "glb").lower()
        path = output_path or os.path.join(AssetPathService.workspace_path("exports", "scenes", artifact_root=artifact_root), f"scene_{RenderArtifactService.stamp()}.{fmt}")
        path = AssetPathService.local_path(path, must_exist=False)
        return self._export(fmt, path, False, overwrite)


class BlendLibraryService:
    def __init__(self, server):
        self.server = server

    def append_blend_asset(self, blend_file_path, datablock_type, datablock_names, collection_name=None, link=False, rename_prefix=None, verify=True):
        try:
            path = AssetPathService.local_path(blend_file_path)
            if not path.lower().endswith(".blend"):
                return {"status": "error", "message": "append_blend_asset requires a .blend file", "warnings": []}
            attr_map = {"Object": "objects", "Collection": "collections", "Material": "materials", "NodeTree": "node_groups", "World": "worlds", "Action": "actions"}
            attr = attr_map.get(str(datablock_type))
            if not attr:
                return {"status": "error", "message": f"Unsupported datablock_type: {datablock_type}", "warnings": []}
            requested = list(datablock_names or [])
            with bpy.data.libraries.load(path, link=bool(link)) as (data_from, data_to):
                available = set(getattr(data_from, attr) or [])
                missing = [name for name in requested if name not in available]
                if missing:
                    return {"status": "error", "message": f"Datablocks not found: {missing}", "warnings": []}
                setattr(data_to, attr, requested)
            loaded = [block for block in getattr(data_to, attr) if block]
            collection = None
            if collection_name:
                collection = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
                if collection.name not in bpy.context.scene.collection.children:
                    bpy.context.scene.collection.children.link(collection)
            created = []
            for block in loaded:
                if rename_prefix:
                    block.name = f"{rename_prefix}{block.name}"
                created.append(block.name)
                if collection and str(datablock_type) == "Object" and block.name not in collection.objects:
                    collection.objects.link(block)
            return {"status": "success", "blend_file_path": path, "datablock_type": datablock_type, "datablocks": created, "linked": bool(link), "collection_name": collection.name if collection else None, "dependency_report": self.server.asset_dependency_service.get_asset_dependency_report(write_manifest=False) if verify else None, "warnings": ["Linked blend assets create external dependencies"] if link else []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}


class AssetPreviewService:
    def __init__(self, server):
        self.server = server

    def create_asset_preview(self, object_names=None, label=None, artifact_root=None, camera_name=None, clamp_for_smoke=True):
        filename = f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', str(label or 'asset_preview'))}_{RenderArtifactService.stamp()}.png"
        result = self.server.render_artifact_service.render_still(artifact_root=artifact_root, filename=filename, camera_name=camera_name, clamp_for_smoke=clamp_for_smoke)
        result["object_names"] = object_names or []
        return result

    def create_asset_contact_sheet(self, object_names=None, label=None, artifact_root=None, views=None, camera_name=None, clamp_for_smoke=True):
        filename = f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', str(label or 'asset_contact'))}_{RenderArtifactService.stamp()}.json"
        return self.server.render_artifact_service.render_contact_sheet(object_names=object_names, camera_name=camera_name, views=views, artifact_root=artifact_root, filename=filename, clamp_for_smoke=clamp_for_smoke)


class SceneKitService:
    def __init__(self, server):
        self.server = server

    def _kit_dir(self, kit_id, artifact_root=None):
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(kit_id)).strip("._-") or f"kit_{RenderArtifactService.stamp()}"
        return os.path.join(AssetPathService.workspace_path("scene_kits", artifact_root=artifact_root), safe)

    def create_scene_kit(self, kit_id=None, label=None, collection_name=None, object_names=None, export_format="glb", include_preview=True, include_scene_export=True, overwrite=False, artifact_root=None):
        kit_id = kit_id or f"scene_kit_{RenderArtifactService.stamp()}"
        kit_dir = self._kit_dir(kit_id, artifact_root)
        if os.path.exists(os.path.join(kit_dir, "manifest.json")) and not overwrite:
            return {"status": "error", "message": f"Scene kit exists and overwrite=False: {kit_dir}", "warnings": []}
        os.makedirs(os.path.join(kit_dir, "previews"), exist_ok=True)
        os.makedirs(os.path.join(kit_dir, "exports"), exist_ok=True)
        manifest = {"status": "success", "kit_id": os.path.basename(kit_dir), "label": label, "collection_name": collection_name, "object_names": object_names or [], "warnings": []}
        manifest["scene_index_path"] = AssetPathService.write_json(os.path.join(kit_dir, "scene_index.json"), self.server.scene_intelligence_service.get_scene_index(max_objects=1000))
        manifest["scene_health_path"] = AssetPathService.write_json(os.path.join(kit_dir, "scene_health.json"), self.server.scene_intelligence_service.get_scene_health())
        manifest["dependencies_path"] = AssetPathService.write_json(os.path.join(kit_dir, "dependencies.json"), self.server.asset_dependency_service.get_asset_dependency_report(write_manifest=False))
        if include_preview:
            manifest["preview"] = self.server.asset_preview_service.create_asset_preview(object_names=object_names, label=kit_id, artifact_root=artifact_root)
        if include_scene_export:
            export_path = os.path.join(kit_dir, "exports", f"{os.path.basename(kit_dir)}.{export_format}")
            if object_names:
                manifest["export"] = self.server.asset_export_service.export_selected_objects(export_path, export_format, object_names, overwrite=True)
            else:
                manifest["export"] = self.server.asset_export_service.export_scene(export_path, export_format, overwrite=True)
        manifest["manifest_path"] = AssetPathService.write_json(os.path.join(kit_dir, "manifest.json"), manifest)
        return manifest

    def validate_scene_kit(self, kit_path):
        try:
            path = AssetPathService.local_path(kit_path)
            manifest = os.path.join(path, "manifest.json") if os.path.isdir(path) else path
            if not os.path.exists(manifest):
                return {"status": "error", "message": "Scene kit manifest not found", "warnings": []}
            with open(manifest, "r", encoding="utf-8") as file:
                data = json.load(file)
            required = ["scene_index_path", "scene_health_path", "dependencies_path"]
            missing = [key for key in required if not data.get(key) or not os.path.exists(data.get(key))]
            return {"status": "success", "kit_path": os.path.dirname(manifest), "valid": not missing, "missing": missing, "manifest": data, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def list_scene_kits(self, artifact_root=None):
        root = AssetPathService.workspace_path("scene_kits", artifact_root=artifact_root)
        kits = []
        for name in sorted(os.listdir(root)):
            manifest = os.path.join(root, name, "manifest.json")
            if os.path.exists(manifest):
                kits.append({"kit_id": name, "path": os.path.join(root, name), "manifest_path": manifest})
        return {"status": "success", "kits": kits, "warnings": []}

    def import_scene_kit(self, kit_path, collection_name=None, rename_prefix=None):
        validation = self.validate_scene_kit(kit_path)
        if validation.get("status") != "success" or not validation.get("valid"):
            return validation
        export = validation["manifest"].get("export") or {}
        output_path = export.get("output_path")
        if not output_path:
            return {"status": "error", "message": "Scene kit has no importable export artifact", "warnings": []}
        return self.server.asset_import_service.import_model_file(output_path, collection_name=collection_name, rename_prefix=rename_prefix)


class AssetWorkflowBatchService:
    ALLOWED_COMMANDS = {"get_supported_asset_formats", "scan_asset_folder", "list_scene_assets", "get_asset_file_info", "get_asset_dependency_report", "create_asset_manifest", "import_model_file", "export_selected_objects", "export_scene", "create_asset_preview", "create_asset_contact_sheet", "collect_external_dependencies", "validate_external_dependencies", "create_scene_kit", "validate_scene_kit", "list_scene_kits"}
    DESTRUCTIVE_COMMANDS = {"pack_external_data", "make_paths_relative", "cleanup_asset_artifacts"}

    def __init__(self, server):
        self.server = server

    def cleanup_asset_artifacts(self, prefix, confirm=False, cleanup_scene_data=True, cleanup_files=False, artifact_root=None):
        if not confirm:
            return {"status": "error", "message": "cleanup_asset_artifacts requires confirm=True", "warnings": []}
        prefix = str(prefix or "")
        if len(prefix) < 8:
            return {"status": "error", "message": "A longer cleanup prefix is required", "warnings": []}
        deleted = {"objects": [], "collections": [], "materials": [], "images": [], "actions": [], "files": []}
        if cleanup_scene_data:
            for obj in list(bpy.data.objects):
                if obj.name.startswith(prefix):
                    deleted["objects"].append(obj.name)
                    bpy.data.objects.remove(obj, do_unlink=True)
            for col in list(bpy.data.collections):
                if col.name.startswith(prefix) and len(col.objects) == 0 and len(col.children) == 0:
                    deleted["collections"].append(col.name)
                    bpy.data.collections.remove(col)
            for mat in list(bpy.data.materials):
                if mat.name.startswith(prefix):
                    deleted["materials"].append(mat.name)
                    bpy.data.materials.remove(mat)
            for image in list(bpy.data.images):
                if image.name.startswith(prefix):
                    deleted["images"].append(image.name)
                    bpy.data.images.remove(image)
            for action in list(bpy.data.actions):
                if action.name.startswith(prefix):
                    deleted["actions"].append(action.name)
                    bpy.data.actions.remove(action)
        if cleanup_files:
            root = os.path.join(AssetPathService.artifact_root(artifact_root), ".overtli_blender")
            for current_root, _dirs, files in os.walk(root):
                for filename in files:
                    if filename.startswith(prefix):
                        path = os.path.join(current_root, filename)
                        os.remove(path)
                        deleted["files"].append(path)
        return {"status": "success", "prefix": prefix, "deleted": deleted, "warnings": []}

    def run_asset_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=40, batch_allow_file_writes=True, batch_allow_destructive=False, artifact_root=None):
        operations = operations or []
        if len(operations) > max(1, min(int(max_operations), 80)):
            return {"status": "error", "message": "Too many batch operations", "warnings": []}
        batch_id = f"asset_batch_{RenderArtifactService.stamp()}"
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_before", include_screenshots=False, artifact_root=artifact_root) if create_before_snapshot else None
        results = []
        errors = []
        handlers = self.server._build_command_handlers()
        for op in operations:
            command = op.get("command")
            params = dict(op.get("params") or {})
            if command not in self.ALLOWED_COMMANDS and command not in self.DESTRUCTIVE_COMMANDS:
                errors.append({"command": command, "message": "Command is not allowed in asset workflow batches"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_COMMANDS and not (batch_allow_destructive and params.get("confirm") is True):
                errors.append({"command": command, "message": "Destructive batch operation requires batch_allow_destructive=True and operation confirm=True"})
                if stop_on_error:
                    break
                continue
            if command not in self.DESTRUCTIVE_COMMANDS and not batch_allow_file_writes and command not in {"get_supported_asset_formats", "list_scene_assets", "get_asset_file_info", "get_asset_dependency_report", "validate_external_dependencies", "validate_scene_kit", "list_scene_kits"}:
                errors.append({"command": command, "message": "File-writing/import/export command blocked by batch_allow_file_writes=False"})
                if stop_on_error:
                    break
                continue
            params.setdefault("artifact_root", artifact_root)
            try:
                result = handlers[command](**params)
            except Exception as exc:
                result = {"status": "error", "message": str(exc), "warnings": []}
            results.append({"command": command, "params": params, "result": result})
            if result.get("status") == "error":
                errors.append({"command": command, "message": result.get("message")})
                if stop_on_error:
                    break
        after = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_after", include_screenshots=False, artifact_root=artifact_root) if create_after_snapshot else None
        batch_dir = AssetPathService.workspace_path("assets", "batches", batch_id, artifact_root=artifact_root)
        manifest_path = AssetPathService.write_json(os.path.join(batch_dir, "manifest.json"), {"batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors})
        return {"status": "partial" if errors else "success", "batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "artifacts": [manifest_path], "errors": errors, "warnings": []}
