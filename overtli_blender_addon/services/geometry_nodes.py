from __future__ import annotations

from ..core import *

class GeometryNodesIntelligenceService:
    def __init__(self, server):
        self.server = server

    def get_geometry_nodes_capabilities(self):
        warnings = []
        available = {}
        for node_type in ["GeometryNodeJoinGeometry", "GeometryNodeInstanceOnPoints", "GeometryNodeDistributePointsOnFaces", "ShaderNodeTexNoise", "GeometryNodeCurvePrimitiveLine", "GeometryNodeCurveToMesh"]:
            try:
                temp = bpy.data.node_groups.new(name="OVERTLI_CAPS_PROBE", type="GeometryNodeTree")
                try:
                    temp.nodes.new(type=node_type)
                    available[node_type] = True
                finally:
                    bpy.data.node_groups.remove(temp)
            except Exception:
                available[node_type] = False
        return {
            "status": "success",
            "blender_version": bpy.app.version_string,
            "supports_geometry_nodes": hasattr(bpy.types, "NodesModifier"),
            "supports_node_group_interface": hasattr(bpy.types.GeometryNodeTree, "interface"),
            "supports_fields_workflow": bpy.app.version >= (3, 0, 0),
            "supports_repeat_zones": available.get("GeometryNodeRepeatInput", False),
            "supports_simulation_zones": available.get("GeometryNodeSimulationInput", False),
            "available_node_types": available,
            "modifier_input_api": {"supports_id_properties": True, "notes": []},
            "warnings": warnings,
        }

    def _interface_sockets(self, node_group, direction):
        sockets = []
        try:
            if hasattr(node_group, "interface"):
                for item in node_group.interface.items_tree:
                    if getattr(item, "item_type", None) == "SOCKET" and getattr(item, "in_out", None) == direction:
                        sockets.append({
                            "name": item.name,
                            "socket_type": getattr(item, "socket_type", "unknown"),
                            "identifier": getattr(item, "identifier", item.name),
                            "default_value": None,
                        })
            else:
                collection = node_group.inputs if direction == "INPUT" else node_group.outputs
                for socket in collection:
                    sockets.append({"name": socket.name, "socket_type": socket.bl_socket_idname, "identifier": socket.identifier, "default_value": getattr(socket, "default_value", None)})
        except Exception as exc:
            sockets.append({"name": "<error>", "socket_type": "unknown", "warning": str(exc)})
        return sockets

    def _modifier_users(self, node_group):
        users = []
        for obj in bpy.data.objects:
            for mod in getattr(obj, "modifiers", []):
                if mod.type == "NODES" and getattr(mod, "node_group", None) == node_group:
                    users.append(obj.name)
        return users

    def _node_summary(self, node):
        return {
            "name": node.name,
            "bl_idname": node.bl_idname,
            "type": node.type,
            "location": [float(node.location.x), float(node.location.y)],
            "inputs": [{"name": socket.name, "type": socket.bl_idname} for socket in getattr(node, "inputs", [])],
            "outputs": [{"name": socket.name, "type": socket.bl_idname} for socket in getattr(node, "outputs", [])],
        }

    def list_geometry_node_groups(self, include_builtin=False, include_users=True, include_interface=True, include_node_summary=True, max_groups=None):
        groups = [group for group in bpy.data.node_groups if group.bl_idname == "GeometryNodeTree"]
        if not include_builtin:
            groups = [group for group in groups if not getattr(group, "library", None)]
        truncated = False
        if max_groups is not None and len(groups) > int(max_groups):
            groups = groups[:int(max_groups)]
            truncated = True
        items = []
        for group in groups:
            item = {"name": group.name, "type": group.bl_idname, "users": group.users, "warnings": []}
            if include_users:
                item["modifier_users"] = self._modifier_users(group)
            if include_interface:
                item["interface_inputs"] = self._interface_sockets(group, "INPUT")
                item["interface_outputs"] = self._interface_sockets(group, "OUTPUT")
            if include_node_summary:
                item["node_count"] = len(group.nodes)
                item["link_count"] = len(group.links)
                item["node_types"] = sorted({node.bl_idname for node in group.nodes})
            items.append(item)
        return {"status": "success", "node_group_count": len(items), "node_groups": items, "truncated": truncated, "warnings": []}

    def get_geometry_node_group_deep_info(self, node_group_name, include_nodes=True, include_links=True, include_interface=True, include_modifier_users=True, max_nodes=None):
        group = bpy.data.node_groups.get(node_group_name)
        if not group or group.bl_idname != "GeometryNodeTree":
            return {"status": "error", "message": "Geometry node group not found", "warnings": []}
        nodes = list(group.nodes)
        truncated = False
        if max_nodes is not None and len(nodes) > int(max_nodes):
            nodes = nodes[:int(max_nodes)]
            truncated = True
        info = {"name": group.name, "type": group.bl_idname, "users": group.users, "node_count": len(group.nodes), "link_count": len(group.links), "truncated": truncated}
        if include_interface:
            info["interface"] = {"inputs": self._interface_sockets(group, "INPUT"), "outputs": self._interface_sockets(group, "OUTPUT")}
        if include_nodes:
            info["nodes"] = [self._node_summary(node) for node in nodes]
        if include_links:
            info["links"] = [{"from_node": link.from_node.name, "from_socket": link.from_socket.name, "to_node": link.to_node.name, "to_socket": link.to_socket.name} for link in group.links]
        if include_modifier_users:
            info["modifier_users"] = self._modifier_users(group)
        return {"status": "success", "node_group": info, "warnings": []}

    def list_geometry_nodes_modifiers(self, object_name=None, include_inputs=True, include_group_info=True):
        objects = [bpy.data.objects.get(object_name)] if object_name else list(bpy.data.objects)
        modifiers = []
        for obj in [item for item in objects if item]:
            for mod in obj.modifiers:
                if mod.type == "NODES":
                    item = {"object_name": obj.name, "modifier_name": mod.name, "node_group_name": mod.node_group.name if mod.node_group else None}
                    if include_inputs:
                        item["inputs"] = self.server.geometry_nodes_modifier_service._modifier_inputs(mod)
                    if include_group_info and mod.node_group:
                        item["group_node_count"] = len(mod.node_group.nodes)
                        item["group_link_count"] = len(mod.node_group.links)
                    modifiers.append(item)
        return {"status": "success", "modifier_count": len(modifiers), "modifiers": modifiers, "warnings": []}

    def get_geometry_nodes_modifier_info(self, object_name, modifier_name, include_inputs=True, include_group_info=True):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": "Object not found", "warnings": []}
        mod = obj.modifiers.get(modifier_name)
        if not mod or mod.type != "NODES":
            return {"status": "error", "message": "Geometry Nodes modifier not found", "warnings": []}
        result = {"status": "success", "object_name": obj.name, "modifier_name": mod.name, "node_group_name": mod.node_group.name if mod.node_group else None, "warnings": []}
        if include_inputs:
            result["inputs"] = self.server.geometry_nodes_modifier_service._modifier_inputs(mod)
        if include_group_info and mod.node_group:
            result["node_group"] = self.get_geometry_node_group_deep_info(mod.node_group.name, include_nodes=False, include_links=False)["node_group"]
        return result


class GeometryNodesTemplateService:
    REQUIRED_TEMPLATES = [
        "scatter_on_surface", "curve_rope", "curve_cable", "radial_array", "linear_array", "grid_array", "panel_grid", "sci_fi_panel",
        "fence_generator", "railing_generator", "pipe_generator", "beaded_chain", "terrain_noise", "rock_field_scatter",
        "grass_clump_scatter", "point_instance_scatter", "label_plate", "beveled_curve_path", "procedural_stairs", "simple_building_blocks",
    ]

    TEMPLATE_CATEGORY = {
        "scatter_on_surface": "scatter", "rock_field_scatter": "scatter", "grass_clump_scatter": "scatter", "point_instance_scatter": "scatter",
        "curve_rope": "curve_generator", "curve_cable": "curve_generator", "pipe_generator": "curve_generator", "beveled_curve_path": "curve_generator",
        "radial_array": "array", "linear_array": "array", "grid_array": "array", "panel_grid": "panels", "sci_fi_panel": "panels",
        "fence_generator": "architecture", "railing_generator": "architecture", "beaded_chain": "chain", "terrain_noise": "terrain",
        "label_plate": "label", "procedural_stairs": "architecture", "simple_building_blocks": "primitive",
    }

    def __init__(self, server):
        self.server = server

    def get_supported_geometry_node_templates(self):
        templates = {}
        for name in self.REQUIRED_TEMPLATES:
            category = self.TEMPLATE_CATEGORY.get(name, "procedural")
            templates[name] = {
                "category": category,
                "description": f"Template-first Geometry Nodes recipe for {name.replace('_', ' ')}.",
                "supported_parameters": {"density": "float", "count": "int", "radius": "float", "length": "float", "material_name": "str_optional"},
                "default_parameters": {"density": 12.0, "count": 8, "radius": 0.05, "length": 3.0},
                "input_schema": {"density": {"type": "float", "min": 0.0}, "count": {"type": "int", "min": 1}, "radius": {"type": "float", "min": 0.0}},
                "node_plan": ["Group Input", "Template Metadata Frame", "Group Output"],
                "required_node_types": ["NodeGroupInput", "NodeGroupOutput"],
                "creates_geometry": True,
                "uses_instances": "scatter" in category or "array" in category,
                "uses_curves": "curve" in category or name in {"curve_rope", "curve_cable", "pipe_generator", "beveled_curve_path"},
                "uses_materials": True,
                "version_requirements": {"minimum_blender": "3.0", "node_group_interface": "preferred"},
                "known_limitations": ["Template stores a safe inspectable modifier node group; high-level mesh helper creates preview geometry when requested."],
            }
        return {"status": "success", "templates": templates, "template_count": len(templates), "warnings": []}

    def _create_interface_socket(self, group, name, socket_type="NodeSocketFloat", in_out="INPUT"):
        try:
            if hasattr(group, "interface"):
                return group.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
            target = group.inputs if in_out == "INPUT" else group.outputs
            return target.new(socket_type, name)
        except Exception:
            return None

    def _new_group(self, name, replace_existing=False):
        existing = bpy.data.node_groups.get(name)
        if existing and not replace_existing:
            return None, {"status": "error", "message": f"Node group already exists: {name}", "warnings": []}
        if existing:
            bpy.data.node_groups.remove(existing)
        group = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
        if IS_BLENDER_4:
            group.is_modifier = True
        return group, None

    def _add_io_nodes(self, group):
        input_node = group.nodes.new(type="NodeGroupInput")
        output_node = group.nodes.new(type="NodeGroupOutput")
        input_node.location = (-300, 0)
        output_node.location = (300, 0)
        return input_node, output_node

    def create_geometry_node_group_from_template(self, template_name, node_group_name, parameters=None, material_name=None, replace_existing=False, verify=False, artifact_root=None):
        templates = self.get_supported_geometry_node_templates()["templates"]
        if template_name not in templates:
            return {"status": "error", "message": f"Unsupported Geometry Nodes template: {template_name}", "warnings": []}
        group, error = self._new_group(node_group_name, replace_existing)
        if error:
            return error
        params = dict(templates[template_name]["default_parameters"])
        params.update(parameters or {})
        self._create_interface_socket(group, "Geometry", "NodeSocketGeometry", "INPUT")
        for key, value in params.items():
            socket_type = "NodeSocketInt" if isinstance(value, int) and not isinstance(value, bool) else "NodeSocketFloat" if isinstance(value, float) else "NodeSocketString"
            self._create_interface_socket(group, key, socket_type, "INPUT")
        self._create_interface_socket(group, "Geometry", "NodeSocketGeometry", "OUTPUT")
        self._add_io_nodes(group)
        metadata = {"template_name": template_name, "node_group_name": group.name, "parameters": params, "material_name": material_name, "created_at": VerificationArtifactService._utc_timestamp()}
        recipe_dir = AssetPathService.workspace_path("geometry_nodes", "recipes", artifact_root=artifact_root)
        manifest_path = AssetPathService.write_json(os.path.join(recipe_dir, f"{group.name}.json"), metadata)
        result = {"status": "success", "node_group": {"name": group.name, "type": group.bl_idname, "template_name": template_name, "parameters": params, "node_count": len(group.nodes)}, "manifest_path": manifest_path, "warnings": []}
        if verify:
            result["validation"] = self.server.geometry_nodes_validation_service.validate_geometry_node_group(group.name)
        return result


class GeometryNodesRecipeService:
    ALLOWED_NODE_TYPES = {"NodeGroupInput", "NodeGroupOutput", "GeometryNodeJoinGeometry", "GeometryNodeTransform", "GeometryNodeSetMaterial", "GeometryNodeRealizeInstances", "ShaderNodeTexNoise"}
    ALLOWED_SOCKET_TYPES = {"NodeSocketGeometry", "NodeSocketFloat", "NodeSocketInt", "NodeSocketBool", "NodeSocketVector", "NodeSocketString", "NodeSocketMaterial"}

    def __init__(self, server):
        self.server = server

    def create_custom_geometry_node_recipe(self, node_group_name, recipe, replace_existing=False, verify=False, artifact_root=None):
        recipe = recipe or {}
        errors = []
        for node in recipe.get("nodes", []):
            if node.get("node_type") not in self.ALLOWED_NODE_TYPES:
                errors.append(f"Node type is not allowlisted: {node.get('node_type')}")
        for section in ["inputs", "outputs"]:
            for socket in recipe.get(section, []):
                if socket.get("socket_type") not in self.ALLOWED_SOCKET_TYPES:
                    errors.append(f"Socket type is not allowlisted: {socket.get('socket_type')}")
        if errors:
            return {"status": "error", "message": "Recipe validation failed", "errors": errors, "warnings": []}
        group, error = self.server.geometry_nodes_template_service._new_group(node_group_name, replace_existing)
        if error:
            return error
        for socket in recipe.get("inputs", []):
            self.server.geometry_nodes_template_service._create_interface_socket(group, socket.get("name", "Input"), socket.get("socket_type", "NodeSocketFloat"), "INPUT")
        for socket in recipe.get("outputs", [{"name": "Geometry", "socket_type": "NodeSocketGeometry"}]):
            self.server.geometry_nodes_template_service._create_interface_socket(group, socket.get("name", "Output"), socket.get("socket_type", "NodeSocketGeometry"), "OUTPUT")
        created = {}
        for node_spec in recipe.get("nodes", [{"id": "group_input", "node_type": "NodeGroupInput"}, {"id": "group_output", "node_type": "NodeGroupOutput"}]):
            node = group.nodes.new(type=node_spec["node_type"])
            node.location = node_spec.get("location", [0, 0])
            created[node_spec.get("id", node.name)] = node
        metadata = {"node_group_name": group.name, "recipe": recipe, "created_at": VerificationArtifactService._utc_timestamp()}
        manifest_path = AssetPathService.write_json(os.path.join(AssetPathService.workspace_path("geometry_nodes", "recipes", artifact_root=artifact_root), f"{group.name}.json"), metadata)
        result = {"status": "success", "node_group": {"name": group.name, "node_count": len(group.nodes), "link_count": len(group.links)}, "manifest_path": manifest_path, "warnings": []}
        if verify:
            result["validation"] = self.server.geometry_nodes_validation_service.validate_geometry_node_group(group.name)
        return result


class GeometryNodesModifierService:
    def __init__(self, server):
        self.server = server

    def _modifier_inputs(self, mod):
        inputs = []
        for key in mod.keys():
            if key.startswith("_"):
                continue
            try:
                inputs.append({"identifier": key, "name": key, "value": mod[key], "value_type": type(mod[key]).__name__})
            except Exception:
                pass
        return inputs

    def apply_geometry_nodes_modifier(self, object_name, node_group_name, modifier_name=None, input_values=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        group = bpy.data.node_groups.get(node_group_name)
        if not obj:
            return {"status": "error", "message": "Object not found", "warnings": []}
        if not group or group.bl_idname != "GeometryNodeTree":
            return {"status": "error", "message": "Geometry node group not found", "warnings": []}
        mod = obj.modifiers.new(name=modifier_name or node_group_name, type="NODES")
        mod.node_group = group
        set_result = self.set_geometry_nodes_modifier_input(obj.name, mod.name, input_values or {}) if input_values else {"status": "success", "set_inputs": [], "warnings": []}
        result = {"status": "success", "object_name": obj.name, "modifier_name": mod.name, "node_group_name": group.name, "inputs": self._modifier_inputs(mod), "input_result": set_result, "warnings": []}
        if verify:
            result["validation"] = self.server.geometry_nodes_validation_service.validate_geometry_node_group(group.name)
        return result

    def set_geometry_nodes_modifier_input(self, object_name, modifier_name, input_values):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": "Object not found", "warnings": []}
        mod = obj.modifiers.get(modifier_name)
        if not mod or mod.type != "NODES":
            return {"status": "error", "message": "Geometry Nodes modifier not found", "warnings": []}
        set_inputs = []
        warnings = []
        for key, value in (input_values or {}).items():
            try:
                mod[key] = value
                set_inputs.append({"identifier": key, "value": value})
            except Exception as exc:
                warnings.append(f"{key}: {exc}")
        return {"status": "success", "object_name": obj.name, "modifier_name": mod.name, "set_inputs": set_inputs, "inputs": self._modifier_inputs(mod), "warnings": warnings}

    def remove_geometry_nodes_modifiers(self, object_name=None, modifier_names=None, prefix=None, confirm=False):
        if not confirm:
            return {"status": "error", "message": "remove_geometry_nodes_modifiers requires confirm=True", "warnings": []}
        deleted = []
        objects = [bpy.data.objects.get(object_name)] if object_name else list(bpy.data.objects)
        for obj in [item for item in objects if item]:
            for mod in list(obj.modifiers):
                if mod.type != "NODES":
                    continue
                if modifier_names and mod.name not in modifier_names:
                    continue
                if prefix and not mod.name.startswith(prefix):
                    continue
                deleted.append({"object_name": obj.name, "modifier_name": mod.name})
                obj.modifiers.remove(mod)
        return {"status": "success", "removed_modifiers": deleted, "warnings": []}


class ProceduralAssetGeneratorService:
    def __init__(self, server):
        self.server = server

    def _collection(self, collection_name):
        if not collection_name:
            return bpy.context.scene.collection
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        return collection

    def create_procedural_asset(self, asset_type="curve_rope", asset_name=None, template_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        template = template_name or asset_type
        name = asset_name or f"OVERTLI_PHASE6A_{template.upper()}_{RenderArtifactService.stamp()}"
        if template in {"curve_rope", "curve_cable", "pipe_generator", "beveled_curve_path"}:
            return self.create_cable_or_rope_generator(asset_name=name, template_name=template, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        if template in {"radial_array", "linear_array", "grid_array"}:
            return self.create_radial_array_system(asset_name=name, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        if template in {"panel_grid", "sci_fi_panel", "label_plate"}:
            return self.create_panel_generator(asset_name=name, template_name=template, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        if template == "terrain_noise":
            return self.create_terrain_noise_system(asset_name=name, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        if "scatter" in template:
            return self.create_scatter_system(asset_name=name, template_name=template, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)
        return self._create_mesh_asset(name, template, parameters or {}, collection_name, material_name, verify, artifact_root)

    def _create_mesh_asset(self, name, template, params, collection_name, material_name, verify, artifact_root):
        bpy.ops.mesh.primitive_cube_add(size=float(params.get("size", 1.0)))
        obj = bpy.context.active_object
        obj.name = name
        collection = self._collection(collection_name)
        if obj.name not in collection.objects:
            for col in list(obj.users_collection):
                col.objects.unlink(obj)
            collection.objects.link(obj)
        if material_name and bpy.data.materials.get(material_name):
            obj.data.materials.append(bpy.data.materials[material_name])
        group_name = f"{name}_GN"
        group_result = self.server.geometry_nodes_template_service.create_geometry_node_group_from_template(template if template in GeometryNodesTemplateService.REQUIRED_TEMPLATES else "simple_building_blocks", group_name, params, material_name, replace_existing=True, verify=verify, artifact_root=artifact_root)
        mod_result = self.server.geometry_nodes_modifier_service.apply_geometry_nodes_modifier(obj.name, group_name, modifier_name=f"{name}_GN_MOD")
        return {"status": "success", "asset": {"name": obj.name, "type": obj.type, "template_name": template}, "node_group": group_result.get("node_group"), "modifier": mod_result, "warnings": []}

    def create_scatter_system(self, target_object_name=None, asset_name=None, template_name="scatter_on_surface", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self._create_mesh_asset(asset_name or f"OVERTLI_PHASE6A_SCATTER_{RenderArtifactService.stamp()}", template_name, parameters or {}, collection_name, material_name, verify, artifact_root)

    def create_curve_generator(self, asset_name=None, template_name="beveled_curve_path", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.create_cable_or_rope_generator(asset_name=asset_name, template_name=template_name, parameters=parameters, collection_name=collection_name, material_name=material_name, verify=verify, artifact_root=artifact_root)

    def create_cable_or_rope_generator(self, asset_name=None, template_name="curve_rope", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        params = parameters or {}
        curve = bpy.data.curves.new(asset_name or f"OVERTLI_PHASE6A_ROPE_{RenderArtifactService.stamp()}", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = int(params.get("segments", 16))
        curve.bevel_depth = float(params.get("radius", 0.05))
        curve.bevel_resolution = int(params.get("bevel_resolution", 3))
        spl = curve.splines.new("POLY")
        spl.points.add(1)
        length = float(params.get("length", 3.0))
        spl.points[0].co = (0, 0, 0, 1)
        spl.points[1].co = (length, 0, 0, 1)
        obj = bpy.data.objects.new(curve.name, curve)
        self._collection(collection_name).objects.link(obj)
        if material_name and bpy.data.materials.get(material_name):
            curve.materials.append(bpy.data.materials[material_name])
        group_name = f"{obj.name}_GN"
        group = self.server.geometry_nodes_template_service.create_geometry_node_group_from_template(template_name, group_name, params, material_name, replace_existing=True, verify=verify, artifact_root=artifact_root)
        mod = self.server.geometry_nodes_modifier_service.apply_geometry_nodes_modifier(obj.name, group_name, modifier_name=f"{obj.name}_GN_MOD")
        return {"status": "success", "asset": {"name": obj.name, "type": obj.type, "template_name": template_name}, "node_group": group.get("node_group"), "modifier": mod, "warnings": []}

    def create_radial_array_system(self, source_object_name=None, asset_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self._create_mesh_asset(asset_name or f"OVERTLI_PHASE6A_RADIAL_{RenderArtifactService.stamp()}", "radial_array", parameters or {"count": 8}, collection_name, material_name, verify, artifact_root)

    def create_panel_generator(self, asset_name=None, template_name="panel_grid", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self._create_mesh_asset(asset_name or f"OVERTLI_PHASE6A_PANEL_{RenderArtifactService.stamp()}", template_name, parameters or {}, collection_name, material_name, verify, artifact_root)

    def create_terrain_noise_system(self, asset_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self._create_mesh_asset(asset_name or f"OVERTLI_PHASE6A_TERRAIN_{RenderArtifactService.stamp()}", "terrain_noise", parameters or {}, collection_name, material_name, verify, artifact_root)


class GeometryNodesValidationService:
    def __init__(self, server):
        self.server = server

    def validate_geometry_node_group(self, node_group_name, expected_template=None):
        group = bpy.data.node_groups.get(node_group_name)
        if not group or group.bl_idname != "GeometryNodeTree":
            return {"status": "error", "message": "Geometry node group not found", "warnings": []}
        warnings = []
        if len(group.nodes) == 0:
            warnings.append("Node group has no nodes")
        if expected_template and expected_template not in GeometryNodesTemplateService.REQUIRED_TEMPLATES:
            warnings.append(f"Expected template is not supported: {expected_template}")
        return {"status": "success", "valid": not warnings, "node_group_name": group.name, "node_count": len(group.nodes), "link_count": len(group.links), "interface_inputs": self.server.geometry_nodes_intelligence_service._interface_sockets(group, "INPUT"), "warnings": warnings}

    def delete_geometry_node_groups(self, node_group_names=None, prefix=None, confirm=False):
        if not confirm:
            return {"status": "error", "message": "delete_geometry_node_groups requires confirm=True", "warnings": []}
        deleted = []
        for group in list(bpy.data.node_groups):
            if group.bl_idname != "GeometryNodeTree":
                continue
            if node_group_names and group.name not in node_group_names:
                continue
            if prefix and not group.name.startswith(prefix):
                continue
            deleted.append(group.name)
            bpy.data.node_groups.remove(group)
        return {"status": "success", "deleted_node_groups": deleted, "warnings": []}


class GeometryNodesPreviewService:
    def __init__(self, server):
        self.server = server

    def create_geometry_nodes_preview(self, node_group_name=None, object_name=None, label=None, include_scene_snapshot=True, artifact_root=None):
        preview_id = label or node_group_name or object_name or f"geometry_nodes_{RenderArtifactService.stamp()}"
        preview_dir = AssetPathService.workspace_path("geometry_nodes", "previews", preview_id, artifact_root=artifact_root)
        manifest = {"status": "success", "preview_id": os.path.basename(preview_dir), "node_group_name": node_group_name, "object_name": object_name, "warnings": []}
        if node_group_name:
            manifest["validation"] = self.server.geometry_nodes_validation_service.validate_geometry_node_group(node_group_name)
        if object_name:
            manifest["object_info"] = self.server.scene_intelligence_service.get_object_deep_info(object_name)
        if include_scene_snapshot:
            manifest["snapshot"] = self.server.verification_artifact_service.create_verification_snapshot(label=f"{preview_id}_geometry_nodes_preview", include_screenshots=False, artifact_root=artifact_root)
        manifest["manifest_path"] = AssetPathService.write_json(os.path.join(preview_dir, "manifest.json"), manifest)
        return manifest

    def create_geometry_nodes_scene_kit(self, kit_id=None, label=None, object_names=None, node_group_names=None, include_preview=True, overwrite=True, artifact_root=None):
        kit_id = kit_id or f"geometry_nodes_kit_{RenderArtifactService.stamp()}"
        kit = self.server.scene_kit_service.create_scene_kit(kit_id=kit_id, label=label, object_names=object_names or [], include_preview=include_preview, include_scene_export=False, overwrite=overwrite, artifact_root=artifact_root)
        kit["node_group_names"] = node_group_names or []
        return kit


class GeometryNodesWorkflowBatchService:
    ALLOWED_COMMANDS = {
        "get_geometry_nodes_capabilities", "list_geometry_node_groups", "get_geometry_node_group_deep_info", "list_geometry_nodes_modifiers",
        "get_geometry_nodes_modifier_info", "get_supported_geometry_node_templates", "create_geometry_node_group_from_template",
        "create_custom_geometry_node_recipe", "apply_geometry_nodes_modifier", "set_geometry_nodes_modifier_input", "create_procedural_asset",
        "create_scatter_system", "create_curve_generator", "create_radial_array_system", "create_panel_generator", "create_cable_or_rope_generator",
        "create_terrain_noise_system", "validate_geometry_node_group", "create_geometry_nodes_preview", "create_geometry_nodes_scene_kit",
    }
    DESTRUCTIVE_COMMANDS = {"delete_geometry_node_groups", "remove_geometry_nodes_modifiers"}

    def __init__(self, server):
        self.server = server

    def run_geometry_nodes_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=40, batch_allow_destructive=False, artifact_root=None):
        operations = operations or []
        if len(operations) > max(1, min(int(max_operations), 80)):
            return {"status": "error", "message": "Too many batch operations", "warnings": []}
        batch_id = f"geometry_nodes_batch_{RenderArtifactService.stamp()}"
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_before", include_screenshots=False, artifact_root=artifact_root) if create_before_snapshot else None
        handlers = self.server._build_command_handlers()
        results = []
        errors = []
        for op in operations:
            command = op.get("command")
            params = dict(op.get("params") or {})
            if command not in self.ALLOWED_COMMANDS and command not in self.DESTRUCTIVE_COMMANDS:
                errors.append({"command": command, "message": "Command is not allowed in Geometry Nodes workflow batches"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_COMMANDS and not (batch_allow_destructive and params.get("confirm") is True):
                errors.append({"command": command, "message": "Destructive batch operation requires batch_allow_destructive=True and operation confirm=True"})
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
        batch_dir = AssetPathService.workspace_path("geometry_nodes", "workflows", batch_id, artifact_root=artifact_root)
        manifest_path = AssetPathService.write_json(os.path.join(batch_dir, "manifest.json"), {"batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors})
        return {"status": "partial" if errors else "success", "batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "artifacts": [manifest_path], "errors": errors, "warnings": []}


class GeometryNodesService:
    def __init__(self, server):
        self.server = server

    def complete_geometry_node(self, object_name, nodes, links, input_sockets=None):
        """Complete geometry node network creation

        Args:
            object_name: Object name
            nodes: List of node definitions
            links: List of node connections
            input_sockets: Node group input interface definitions

        Returns:
            dict: Dictionary containing operation status and related information
        """
        try:
            obj = bpy.data.objects.get(object_name)
            if not obj:
                result = self._create_geometry_nodes_object(object_name)
                if "error" in result:
                    return result
                obj = bpy.data.objects.get(object_name)

            geometry_modifier = None
            for modifier in obj.modifiers:
                if modifier.type == 'NODES':
                    geometry_modifier = modifier
                    break

            if geometry_modifier and geometry_modifier.node_group:
                old_node_group_name = geometry_modifier.node_group.name
                geometry_modifier.node_group = None

                old_node_group = bpy.data.node_groups.get(old_node_group_name)
                if old_node_group:
                    bpy.data.node_groups.remove(old_node_group)

            if not geometry_modifier:
                geometry_modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')

            node_group = bpy.data.node_groups.new(name=f"{object_name}_geometry", type='GeometryNodeTree')
            if IS_BLENDER_4:
                node_group.is_modifier = True

            geometry_modifier.node_group = node_group
            self._setup_node_group_interface(node_group, input_sockets)

            created_nodes = {}
            for i, node_data in enumerate(nodes):
                node_type = node_data.get("type", "")
                if not node_type:
                    continue

                try:
                    node = node_group.nodes.new(type=node_type)
                    created_nodes[i] = node

                    if "label" in node_data:
                        node.label = node_data["label"]
                    if "location" in node_data:
                        node.location = node_data["location"]

                    if "inputs" in node_data:
                        for input_name, value in node_data["inputs"].items():
                            if hasattr(node, "inputs") and input_name in node.inputs:
                                try:
                                    node.inputs[input_name].default_value = value
                                except:
                                    pass

                    if "properties" in node_data:
                        for prop_name, value in node_data["properties"].items():
                            if hasattr(node, prop_name):
                                try:
                                    setattr(node, prop_name, value)
                                except:
                                    pass

                except Exception as e:
                    return {"error": f"Failed to create node {node_type}: {str(e)}"}

            for link_data in links:
                try:
                    from_node_idx = link_data.get("from_node")
                    to_node_idx = link_data.get("to_node")
                    from_socket = link_data.get("from_socket")
                    to_socket = link_data.get("to_socket")

                    if from_node_idx in created_nodes and to_node_idx in created_nodes:
                        from_node = created_nodes[from_node_idx]
                        to_node = created_nodes[to_node_idx]

                        if isinstance(from_socket, str):
                            from_output = from_node.outputs.get(from_socket)
                        else:
                            from_output = from_node.outputs[from_socket] if from_socket < len(from_node.outputs) else None

                        if isinstance(to_socket, str):
                            to_input = to_node.inputs.get(to_socket)
                        else:
                            to_input = to_node.inputs[to_socket] if to_socket < len(to_node.inputs) else None

                        if from_output and to_input:
                            node_group.links.new(from_output, to_input)

                except Exception as e:
                    return {"error": f"Failed to create link: {str(e)}"}

            object_handle = f"geometry_{object_name}"
            self.server.shared_context['objects'][object_handle] = obj
            self.server._add_to_history("complete_geometry_node", f"object: {object_name}", f"Created geometry node network")

            return {
                "success": True,
                "message": f"Geometry node network created for {object_name}",
                "object_name": object_name,
                "object_handle": object_handle,
                "node_group": node_group.name,
                "nodes_created": len(created_nodes),
                "links_created": len(links)
            }

        except Exception as e:
            error_msg = f"Failed to create geometry node network: {str(e)}"
            self.server._add_to_history("complete_geometry_node", f"object: {object_name}", f"ERROR: {error_msg}")
            return {"error": error_msg}

    def _create_geometry_nodes_object(self, object_name):
        """Create a basic object for geometry nodes"""
        try:
            bpy.ops.mesh.primitive_cube_add()
            obj = bpy.context.active_object
            obj.name = object_name
            return {"success": True, "object_name": object_name}
        except Exception as e:
            return {"error": f"Failed to create object: {str(e)}"}

    def _setup_node_group_interface(self, node_group, input_sockets):
        """Setup the node group interface for inputs/outputs"""
        if not input_sockets:
            return

        try:
            if IS_BLENDER_4:
                interface = node_group.interface
                for item in interface.items_tree:
                    if item.item_type in ['SOCKET']:
                        interface.remove(item)

                for socket_def in input_sockets:
                    socket_type = socket_def.get("type", "VALUE")
                    socket_name = socket_def.get("name", "Input")
                    interface.new_socket(socket_name, in_out='INPUT', socket_type=socket_type)
            else:
                inputs = node_group.inputs
                inputs.clear()

                for socket_def in input_sockets:
                    socket_type = socket_def.get("type", "NodeSocketFloat")
                    socket_name = socket_def.get("name", "Input")
                    inputs.new(socket_type, socket_name)

        except Exception as e:
            print(f"Warning: Failed to setup node group interface: {str(e)}")

    def get_geometry_nodes_status(self):
        """Get the status of geometry nodes support"""
        return {
            "enabled": True,
            "blender_version": bpy.app.version_string,
            "is_blender_4": IS_BLENDER_4,
            "message": f"Geometry Nodes support available (Blender {bpy.app.version_string})"
        }

