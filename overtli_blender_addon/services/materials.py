from __future__ import annotations

from ..core import *

class MaterialAuthoringService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _clamp(value, minimum=0.0, maximum=1.0):
        return max(minimum, min(maximum, float(value)))

    def _material_summary(self, material):
        props = {"base_color": list(material.diffuse_color), "metallic": 0.0, "roughness": 0.5, "alpha": float(material.diffuse_color[3])}
        if material.use_nodes:
            node = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
            if node:
                for key, socket_name in [("base_color", "Base Color"), ("metallic", "Metallic"), ("roughness", "Roughness"), ("alpha", "Alpha")]:
                    socket = node.inputs.get(socket_name)
                    if socket:
                        value = socket.default_value
                        props[key] = list(value) if hasattr(value, "__len__") and not isinstance(value, str) else float(value)
        return {"name": material.name, "use_nodes": bool(material.use_nodes), "users": int(material.users), "properties": props}

    def _set_properties(self, material, base_color=None, metallic=None, roughness=None, alpha=None):
        if base_color is not None:
            if not isinstance(base_color, (list, tuple)) or len(base_color) not in {3, 4}:
                raise ValueError("base_color must be a 3- or 4-item numeric list")
            color = [self._clamp(component) for component in base_color]
            if len(color) == 3:
                color.append(self._clamp(alpha if alpha is not None else material.diffuse_color[3]))
            material.diffuse_color = color
        elif alpha is not None:
            color = list(material.diffuse_color)
            color[3] = self._clamp(alpha)
            material.diffuse_color = color

        if material.use_nodes and material.node_tree:
            node = material.node_tree.nodes.get("Principled BSDF")
            if node:
                if base_color is not None and node.inputs.get("Base Color"):
                    node.inputs["Base Color"].default_value = material.diffuse_color
                if metallic is not None and node.inputs.get("Metallic"):
                    node.inputs["Metallic"].default_value = self._clamp(metallic)
                if roughness is not None and node.inputs.get("Roughness"):
                    node.inputs["Roughness"].default_value = self._clamp(roughness)
                if alpha is not None and node.inputs.get("Alpha"):
                    node.inputs["Alpha"].default_value = self._clamp(alpha)

    def create_basic_material(self, name, base_color=None, metallic=None, roughness=None, alpha=None, use_nodes=True, replace_existing=False):
        if not name:
            return {"status": "error", "message": "name is required", "warnings": []}
        material = bpy.data.materials.get(name)
        created = False
        if material and not replace_existing:
            return {"status": "success", "material_name": material.name, "created": False, "properties": self._material_summary(material)["properties"], "warnings": ["material already exists"]}
        if material is None:
            material = bpy.data.materials.new(name)
            created = True
        material.use_nodes = bool(use_nodes)
        self._set_properties(material, base_color, metallic, roughness, alpha)
        result = {"status": "success", "material_name": material.name, "created": created, "properties": self._material_summary(material)["properties"], "warnings": []}
        self.server._add_to_history("create_basic_material", {"name": name}, result)
        return result

    def assign_material(self, object_name, material_name, slot_index=None, replace=True, verify=False):
        obj = bpy.data.objects.get(object_name)
        material = bpy.data.materials.get(material_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        if slot_index is None:
            if replace and len(obj.data.materials) > 0:
                obj.data.materials[0] = material
                slot_index = 0
            else:
                obj.data.materials.append(material)
                slot_index = len(obj.data.materials) - 1
        else:
            slot_index = int(slot_index)
            while len(obj.data.materials) <= slot_index:
                obj.data.materials.append(None)
            obj.data.materials[slot_index] = material
        result = {"status": "success", "object_name": obj.name, "material_name": material.name, "slot_index": slot_index, "materials": [slot.material.name if slot.material else None for slot in obj.material_slots], "verification": self.server.scene_edit_service._verification(f"assign_material_{obj.name}", verify), "warnings": []}
        self.server._add_to_history("assign_material", {"object_name": object_name, "material_name": material_name}, result)
        return result

    def update_material_properties(self, material_name, base_color=None, metallic=None, roughness=None, alpha=None, verify=False):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        self._set_properties(material, base_color, metallic, roughness, alpha)
        result = {"status": "success", "material_name": material.name, "properties": self._material_summary(material)["properties"], "verification": self.server.scene_edit_service._verification(f"material_{material.name}", verify), "warnings": []}
        self.server._add_to_history("update_material_properties", {"material_name": material_name}, result)
        return result


MATERIAL_CHANNEL_SCHEMA = {
    "base_color": {"type": "rgba", "color_space": "sRGB", "principled_targets": ["Base Color"]},
    "albedo": {"type": "rgba", "color_space": "sRGB", "principled_targets": ["Base Color"]},
    "metallic": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Metallic"]},
    "roughness": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Roughness"]},
    "specular": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Specular IOR Level", "Specular"]},
    "ior": {"type": "float", "range": [1, 3], "color_space": "Non-Color", "principled_targets": ["IOR"]},
    "alpha": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Alpha"]},
    "opacity": {"type": "float_or_map", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Alpha"]},
    "normal": {"type": "normal_map", "color_space": "Non-Color", "node_path": ["Image Texture", "Normal Map", "Principled Normal"]},
    "bump": {"type": "height_or_bump_map", "color_space": "Non-Color", "node_path": ["Image Texture or procedural", "Bump", "Principled Normal"]},
    "height": {"type": "height_or_bump_map", "color_space": "Non-Color", "node_path": ["Image Texture or procedural", "Bump", "Principled Normal"]},
    "displacement": {"type": "displacement_map", "color_space": "Non-Color", "node_path": ["Image Texture or procedural", "Displacement", "Material Output Displacement"]},
    "ambient_occlusion": {"type": "map_metadata", "color_space": "Non-Color", "principled_targets": []},
    "emission_color": {"type": "rgba_or_map", "color_space": "sRGB", "principled_targets": ["Emission Color", "Emission"]},
    "emission_strength": {"type": "float", "range": [0, 100], "color_space": "Non-Color", "principled_targets": ["Emission Strength"]},
    "subsurface": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Subsurface Weight", "Subsurface"]},
    "coat_weight": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Coat Weight", "Clearcoat"]},
    "coat_roughness": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Coat Roughness", "Clearcoat Roughness"]},
    "anisotropy": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Anisotropic IOR Level", "Anisotropic"]},
    "transmission": {"type": "float", "range": [0, 1], "color_space": "Non-Color", "principled_targets": ["Transmission Weight", "Transmission"]},
    "volume_absorption": {"type": "volume", "color_space": "sRGB", "principled_targets": []},
}

MATERIAL_MAP_KINDS = {
    "base_color_map": {"channel": "base_color", "color_space": "sRGB"},
    "albedo_map": {"channel": "albedo", "color_space": "sRGB"},
    "metallic_map": {"channel": "metallic", "color_space": "Non-Color"},
    "roughness_map": {"channel": "roughness", "color_space": "Non-Color"},
    "metallic_roughness_map": {"channel": "metallic_roughness", "color_space": "Non-Color", "packed": "glTF_metallic_roughness"},
    "normal_map": {"channel": "normal", "color_space": "Non-Color"},
    "bump_map": {"channel": "bump", "color_space": "Non-Color"},
    "height_map": {"channel": "height", "color_space": "Non-Color"},
    "displacement_map": {"channel": "displacement", "color_space": "Non-Color"},
    "ambient_occlusion_map": {"channel": "ambient_occlusion", "color_space": "Non-Color"},
    "emission_map": {"channel": "emission_color", "color_space": "sRGB"},
    "alpha_map": {"channel": "alpha", "color_space": "Non-Color"},
    "opacity_map": {"channel": "opacity", "color_space": "Non-Color"},
    "orm_map": {"channel": "packed", "color_space": "Non-Color", "packed": "ORM"},
    "rma_map": {"channel": "packed", "color_space": "Non-Color", "packed": "RMA"},
    "mra_map": {"channel": "packed", "color_space": "Non-Color", "packed": "MRA"},
    "mask_map": {"channel": "mask", "color_space": "Non-Color"},
    "color_ramp_map": {"channel": "procedural", "color_space": "sRGB"},
    "procedural_channel": {"channel": "procedural", "color_space": "Non-Color"},
}

PACKED_MAP_CONVENTIONS = {
    "ORM": "R=occlusion, G=roughness, B=metallic",
    "RMA": "R=roughness, G=metallic, B=ambient occlusion",
    "MRA": "R=metallic, G=roughness, B=ambient occlusion",
    "glTF_metallic_roughness": "G=roughness, B=metallic",
}

PHASE4A_TEMPLATE_NAMES = [
    "pbr_metal_gold", "pbr_metal_brushed", "pbr_plastic", "pbr_rubber", "pbr_ceramic", "pbr_clay",
    "glass_clear", "glass_frosted", "water_basic", "emission_neon", "toon_flat", "toon_rim",
    "fabric_woven", "leather_grain", "skin_basic", "stone_rough", "concrete_rough",
    "wood_procedural", "marble_procedural", "brick_procedural", "sci_fi_panel", "painted_metal",
    "car_paint_basic",
]


class MaterialIntelligenceService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _json_value(value):
        if hasattr(value, "__len__") and not isinstance(value, str):
            return [float(v) if isinstance(v, (int, float)) else v for v in value]
        if isinstance(value, (int, float, bool)):
            return value
        return str(value)

    @staticmethod
    def _principled_node(material):
        if not material or not material.use_nodes or not material.node_tree:
            return None
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeBsdfPrincipled" or node.name == "Principled BSDF":
                return node
        return None

    @staticmethod
    def _material_objects(material):
        names = []
        for obj in bpy.data.objects:
            data = getattr(obj, "data", None)
            if data and hasattr(data, "materials"):
                for slot_material in data.materials:
                    if slot_material == material:
                        names.append(obj.name)
                        break
        return names

    def get_material_channel_schema(self):
        return {
            "status": "success",
            "channels": MATERIAL_CHANNEL_SCHEMA,
            "map_kinds": MATERIAL_MAP_KINDS,
            "packed_map_conventions": PACKED_MAP_CONVENTIONS,
            "warnings": [],
        }

    def _channel_summary(self, material):
        principled = self._principled_node(material)
        channels = {}
        if not principled:
            return {"base_color": {"source": "material_diffuse", "value": list(material.diffuse_color)}, "warnings": ["no Principled BSDF node found"]}
        mapping = {
            "base_color": "Base Color", "metallic": "Metallic", "roughness": "Roughness", "alpha": "Alpha",
            "emission_color": "Emission Color", "emission_strength": "Emission Strength", "ior": "IOR",
            "coat_weight": "Coat Weight", "coat_roughness": "Coat Roughness", "transmission": "Transmission Weight",
        }
        for channel, socket_name in mapping.items():
            socket = principled.inputs.get(socket_name)
            if not socket and socket_name == "Emission Color":
                socket = principled.inputs.get("Emission")
            if socket:
                source = "linked" if socket.is_linked else "constant"
                channels[channel] = {"source": source, "value": self._json_value(socket.default_value)}
        normal = principled.inputs.get("Normal")
        channels["normal"] = {"source": "linked" if normal and normal.is_linked else "none"}
        return channels

    def _texture_slots(self, material):
        slots = {key: None for key in MATERIAL_MAP_KINDS}
        packed_maps = []
        if not material.use_nodes or not material.node_tree:
            return slots, packed_maps
        for node in material.node_tree.nodes:
            if node.bl_idname != "ShaderNodeTexImage":
                continue
            map_kind = node.get("overtli_map_kind") or "image_texture"
            entry = {
                "node": node.name,
                "map_kind": map_kind,
                "image_name": node.image.name if getattr(node, "image", None) else None,
                "filepath": bpy.path.abspath(node.image.filepath) if getattr(node, "image", None) and node.image.filepath else None,
                "color_space_intent": MATERIAL_MAP_KINDS.get(map_kind, {}).get("color_space", "unknown"),
                "packed_convention": node.get("overtli_packed_convention"),
            }
            if map_kind in slots:
                slots[map_kind] = entry
            if entry["packed_convention"]:
                packed_maps.append(entry)
        return slots, packed_maps

    def _material_record(self, material, include_node_summary=True, include_users=True, include_objects=True, include_texture_slots=True, include_channel_summary=True):
        objects = self._material_objects(material) if include_objects or include_users else []
        slots, packed = self._texture_slots(material) if include_texture_slots else ({}, [])
        node_count = len(material.node_tree.nodes) if material.use_nodes and material.node_tree else 0
        link_count = len(material.node_tree.links) if material.use_nodes and material.node_tree else 0
        image_count = 0
        procedural_count = 0
        if material.use_nodes and material.node_tree:
            for node in material.node_tree.nodes:
                if node.bl_idname == "ShaderNodeTexImage":
                    image_count += 1
                if node.bl_idname in {"ShaderNodeTexNoise", "ShaderNodeTexVoronoi", "ShaderNodeValToRGB", "ShaderNodeBump", "ShaderNodeNormalMap"}:
                    procedural_count += 1
        record = {
            "name": material.name,
            "use_nodes": bool(material.use_nodes),
            "users": int(material.users),
            "surface_node": self._principled_node(material).name if self._principled_node(material) else None,
            "node_count": node_count,
            "link_count": link_count,
            "image_texture_count": image_count,
            "procedural_node_count": procedural_count,
            "warnings": [],
        }
        if include_objects:
            record["object_names"] = objects
        if include_channel_summary:
            record["channel_summary"] = self._channel_summary(material)
        if include_texture_slots:
            record["texture_slots"] = slots
            record["packed_maps"] = packed
        if include_node_summary:
            record["node_summary"] = {"node_count": node_count, "link_count": link_count, "image_texture_count": image_count, "procedural_node_count": procedural_count}
        return record

    def list_materials_deep(self, include_node_summary=True, include_users=True, include_objects=True, include_texture_slots=True, include_channel_summary=True, max_materials=None):
        materials = list(bpy.data.materials)
        truncated = False
        if max_materials is not None and len(materials) > int(max_materials):
            materials = materials[:int(max_materials)]
            truncated = True
        return {
            "status": "success",
            "material_count": len(bpy.data.materials),
            "materials": [self._material_record(m, include_node_summary, include_users, include_objects, include_texture_slots, include_channel_summary) for m in materials],
            "truncated": truncated,
            "warnings": [],
        }

    def get_material_deep_info(self, material_name, include_node_graph=True, include_texture_slots=True, include_channel_summary=True, include_users=True, include_preview_hints=True):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        record = self._material_record(material, True, include_users, include_users, include_texture_slots, include_channel_summary)
        principled = self._principled_node(material)
        record["principled"] = {}
        if principled:
            for channel, socket_name in [("base_color", "Base Color"), ("metallic", "Metallic"), ("roughness", "Roughness"), ("alpha", "Alpha")]:
                socket = principled.inputs.get(socket_name)
                if socket:
                    record["principled"][channel] = self._json_value(socket.default_value)
        if include_node_graph:
            graph = self.server.shader_graph_service.get_shader_graph(material.name, max_nodes=80)
            record["graph"] = {"nodes": graph.get("nodes", []), "links": graph.get("links", []), "warnings": graph.get("warnings", [])}
        if include_preview_hints:
            record["preview_hints"] = {"preview_shape": material.get("overtli_preview_shape", "sphere"), "recommended_views": ["material_preview", "front", "isometric"]}
        return {"status": "success", "material": record, "warnings": []}


class MaterialTemplateService:
    DEFAULTS = {
        "pbr_metal_gold": ([1.0, 0.72, 0.22, 1.0], 1.0, 0.22, "pbr", "sphere"),
        "pbr_metal_brushed": ([0.78, 0.76, 0.70, 1.0], 1.0, 0.32, "pbr", "sphere"),
        "pbr_plastic": ([0.12, 0.22, 0.9, 1.0], 0.0, 0.38, "pbr", "cube"),
        "pbr_rubber": ([0.02, 0.02, 0.018, 1.0], 0.0, 0.78, "pbr", "sphere"),
        "pbr_ceramic": ([0.86, 0.82, 0.74, 1.0], 0.0, 0.24, "pbr", "sphere"),
        "pbr_clay": ([0.62, 0.38, 0.24, 1.0], 0.0, 0.74, "pbr", "sphere"),
        "glass_clear": ([0.85, 0.95, 1.0, 0.28], 0.0, 0.02, "transparent", "sphere"),
        "glass_frosted": ([0.82, 0.93, 1.0, 0.42], 0.0, 0.55, "transparent", "sphere"),
        "water_basic": ([0.18, 0.45, 0.75, 0.55], 0.0, 0.03, "transparent", "plane"),
        "emission_neon": ([0.1, 1.0, 0.75, 1.0], 0.0, 0.18, "emission", "sphere"),
        "toon_flat": ([0.95, 0.62, 0.25, 1.0], 0.0, 0.5, "stylized", "sphere"),
        "toon_rim": ([0.32, 0.42, 1.0, 1.0], 0.0, 0.45, "stylized", "sphere"),
        "fabric_woven": ([0.26, 0.22, 0.18, 1.0], 0.0, 0.86, "procedural", "sphere"),
        "leather_grain": ([0.21, 0.09, 0.035, 1.0], 0.0, 0.48, "procedural", "sphere"),
        "skin_basic": ([0.86, 0.56, 0.42, 1.0], 0.0, 0.42, "organic", "sphere"),
        "stone_rough": ([0.36, 0.35, 0.32, 1.0], 0.0, 0.82, "procedural", "cube"),
        "concrete_rough": ([0.48, 0.47, 0.43, 1.0], 0.0, 0.88, "procedural", "cube"),
        "wood_procedural": ([0.55, 0.28, 0.11, 1.0], 0.0, 0.46, "procedural", "cube"),
        "marble_procedural": ([0.86, 0.84, 0.78, 1.0], 0.0, 0.28, "procedural", "sphere"),
        "brick_procedural": ([0.56, 0.16, 0.08, 1.0], 0.0, 0.72, "procedural", "cube"),
        "sci_fi_panel": ([0.08, 0.10, 0.13, 1.0], 0.6, 0.34, "hard_surface", "cube"),
        "painted_metal": ([0.8, 0.08, 0.04, 1.0], 0.65, 0.42, "pbr", "sphere"),
        "car_paint_basic": ([0.02, 0.08, 0.74, 1.0], 0.25, 0.18, "pbr", "sphere"),
    }

    def __init__(self, server):
        self.server = server

    def _recipe(self, name):
        color, metallic, roughness, category, preview = self.DEFAULTS[name]
        procedural = name.endswith("_procedural") or name in {"fabric_woven", "leather_grain", "stone_rough", "concrete_rough", "brick_procedural", "sci_fi_panel"}
        return {
            "category": category,
            "description": f"{name.replace('_', ' ').title()} material recipe with PBR channels, map slots, and verification metadata.",
            "supported_parameters": {
                "base_color": "rgba", "metallic": "float", "roughness": "float", "alpha": "float",
                "emission_strength": "float", "noise_scale": "float", "bump_strength": "float",
                "normal_map_path": "path_optional", "roughness_map_path": "path_optional", "orm_map_path": "path_optional",
            },
            "default_parameters": {"base_color": color, "metallic": metallic, "roughness": roughness, "alpha": color[3], "noise_scale": 18.0, "bump_strength": 0.04},
            "channel_plan": {"base_color": "constant_or_map", "metallic": "constant_or_map", "roughness": "constant_map_or_noise", "normal": "optional_normal_or_bump", "ambient_occlusion": "metadata_or_packed_map"},
            "node_plan": ["Principled BSDF", "Image Texture optional", "Normal Map optional", "Bump optional"] + (["Noise Texture", "ColorRamp"] if procedural else []),
            "map_slots": ["base_color_map", "roughness_map", "metallic_map", "normal_map", "ambient_occlusion_map", "orm_map", "rma_map", "mra_map", "metallic_roughness_map"],
            "procedural_slots": ["roughness_noise", "bump_noise", "color_ramp"] if procedural else ["optional_noise_variation"],
            "preview_shape": preview,
            "risk_level": "MEDIUM",
            "known_limitations": ["No texture baking or external downloads in Phase 4A."],
        }

    def get_supported_material_templates(self):
        return {"status": "success", "templates": {name: self._recipe(name) for name in PHASE4A_TEMPLATE_NAMES}, "warnings": []}

    def create_material_from_template(self, template_name, material_name, parameters=None, map_slots=None, assign_to_object=None, replace_existing=False, verify=True):
        if template_name not in PHASE4A_TEMPLATE_NAMES:
            return {"status": "error", "message": f"Unsupported template_name: {template_name}", "supported_templates": PHASE4A_TEMPLATE_NAMES, "warnings": []}
        recipe = self._recipe(template_name)
        params = dict(recipe["default_parameters"])
        params.update(parameters or {})
        material_result = self.server.advanced_material_authoring_service.create_custom_material(
            material_name=material_name,
            recipe={"channels": params, "procedural": {"enabled": bool(recipe["procedural_slots"] and "optional" not in str(recipe["procedural_slots"]))}, "preview_shape": recipe["preview_shape"]},
            replace_existing=replace_existing,
            verify=False,
        )
        if material_result.get("status") != "success":
            return material_result
        warnings = material_result.get("warnings", [])
        for kind, path in (map_slots or {}).items():
            bind = self.server.material_texture_slot_service.bind_material_texture_map(material_name, kind, path, strict_file_exists=False, verify=False)
            warnings.extend(bind.get("warnings", []))
            if bind.get("status") == "error":
                warnings.append(bind.get("message"))
        assignment = None
        if assign_to_object:
            assignment = self.server.material_authoring_service.assign_material(assign_to_object, material_name, verify=False)
        deep = self.server.material_intelligence_service.get_material_deep_info(material_name, include_node_graph=True) if verify else None
        return {"status": "success", "template_name": template_name, "material_name": material_name, "material": material_result.get("material"), "assignment": assignment, "verification": deep, "warnings": warnings}


class AdvancedMaterialAuthoringService:
    def __init__(self, server):
        self.server = server

    def _ensure_material(self, material_name, replace_existing=False):
        if not material_name:
            raise ValueError("material_name is required")
        material = bpy.data.materials.get(material_name)
        created = False
        if material and not replace_existing:
            return material, created, ["material already exists"]
        if material is None:
            material = bpy.data.materials.new(material_name)
            created = True
        material.use_nodes = True
        if not material.node_tree:
            material.use_nodes = True
        return material, created, []

    @staticmethod
    def _set_input(node, names, value):
        for name in names:
            socket = node.inputs.get(name)
            if socket:
                socket.default_value = value
                return True
        return False

    def _apply_channels(self, material, channels):
        warnings = []
        principled = MaterialIntelligenceService._principled_node(material)
        if not principled:
            return ["No Principled BSDF node found"]
        scalar_map = {
            "metallic": ["Metallic"], "roughness": ["Roughness"], "alpha": ["Alpha"], "opacity": ["Alpha"],
            "ior": ["IOR"], "emission_strength": ["Emission Strength"], "subsurface": ["Subsurface Weight", "Subsurface"],
            "coat_weight": ["Coat Weight", "Clearcoat"], "coat_roughness": ["Coat Roughness", "Clearcoat Roughness"],
            "anisotropy": ["Anisotropic IOR Level", "Anisotropic"], "transmission": ["Transmission Weight", "Transmission"],
        }
        for channel, value in (channels or {}).items():
            try:
                if channel in {"base_color", "albedo"}:
                    color = list(value)
                    if len(color) == 3:
                        color.append(1.0)
                    material.diffuse_color = color
                    if not self._set_input(principled, ["Base Color"], color):
                        warnings.append("Base Color socket not available")
                elif channel == "emission_color":
                    self._set_input(principled, ["Emission Color", "Emission"], list(value))
                elif channel in scalar_map:
                    self._set_input(principled, scalar_map[channel], float(value))
                elif channel not in {"noise_scale", "bump_strength"}:
                    warnings.append(f"Channel recorded as metadata only: {channel}")
                material[f"overtli_channel_{channel}"] = json.dumps(value)
            except Exception as exc:
                warnings.append(f"Failed to set channel {channel}: {exc}")
        return warnings

    def _add_noise_bump(self, material, strength=0.04, scale=18.0):
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        principled = MaterialIntelligenceService._principled_node(material)
        if not principled:
            return ["No Principled BSDF node found for procedural bump"]
        noise = nodes.new(type="ShaderNodeTexNoise")
        noise.name = "OVERTLI Procedural Noise"
        if noise.inputs.get("Scale"):
            noise.inputs["Scale"].default_value = float(scale)
        bump = nodes.new(type="ShaderNodeBump")
        bump.name = "OVERTLI Procedural Bump"
        if bump.inputs.get("Strength"):
            bump.inputs["Strength"].default_value = float(strength)
        if noise.outputs.get("Fac") and bump.inputs.get("Height"):
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
        normal = principled.inputs.get("Normal")
        if bump.outputs.get("Normal") and normal:
            links.new(bump.outputs["Normal"], normal)
        return []

    def create_custom_material(self, material_name, recipe=None, replace_existing=False, verify=True):
        try:
            material, created, warnings = self._ensure_material(material_name, replace_existing)
        except ValueError as exc:
            return {"status": "error", "message": str(exc), "warnings": []}
        recipe = recipe or {}
        channels = recipe.get("channels", recipe)
        warnings.extend(self._apply_channels(material, channels))
        procedural = recipe.get("procedural") or {}
        if procedural.get("enabled"):
            warnings.extend(self._add_noise_bump(material, procedural.get("bump_strength", channels.get("bump_strength", 0.04)), procedural.get("noise_scale", channels.get("noise_scale", 18.0))))
        material["overtli_recipe"] = json.dumps(recipe, sort_keys=True)
        material["overtli_preview_shape"] = recipe.get("preview_shape", "sphere")
        deep = self.server.material_intelligence_service.get_material_deep_info(material.name, include_node_graph=True) if verify else None
        result = {"status": "success", "material_name": material.name, "created": created, "material": self.server.material_intelligence_service._material_record(material), "verification": deep, "warnings": warnings}
        self.server._add_to_history("create_custom_material", {"material_name": material_name}, result)
        return result

    def create_material_variant(self, source_material_name, variant_name, overrides=None, replace_existing=False, verify=True):
        source = bpy.data.materials.get(source_material_name)
        if not source:
            return {"status": "error", "message": f"Material not found: {source_material_name}", "warnings": []}
        existing = bpy.data.materials.get(variant_name)
        if existing and not replace_existing:
            return {"status": "error", "message": f"Material already exists: {variant_name}", "warnings": []}
        if existing:
            bpy.data.materials.remove(existing)
        material = source.copy()
        material.name = variant_name
        warnings = self._apply_channels(material, overrides or {})
        deep = self.server.material_intelligence_service.get_material_deep_info(material.name, include_node_graph=True) if verify else None
        return {"status": "success", "source_material_name": source_material_name, "material_name": material.name, "verification": deep, "warnings": warnings}

    def apply_material_to_objects(self, material_name, object_names, slot_index=None, replace=True, verify=True):
        results = []
        for object_name in object_names or []:
            results.append(self.server.material_authoring_service.assign_material(object_name, material_name, slot_index, replace, verify=False))
        status = "success" if all(item.get("status") == "success" for item in results) else "partial"
        verification = self.server.material_intelligence_service.get_material_deep_info(material_name, include_node_graph=False) if verify else None
        return {"status": status, "material_name": material_name, "object_names": object_names or [], "operation_results": results, "verification": verification, "warnings": []}

    def delete_materials(self, material_names, confirm=False, allow_missing=False, only_if_unused=False):
        if not confirm:
            return {"status": "error", "message": "delete_materials requires confirm=True", "deleted": [], "missing": list(material_names or []), "warnings": []}
        deleted, missing, refused, warnings = [], [], [], []
        for name in material_names or []:
            if any(token in str(name) for token in ["*", "?", "["]):
                refused.append(str(name))
                continue
            material = bpy.data.materials.get(str(name))
            if not material:
                missing.append(str(name))
                continue
            if only_if_unused and material.users > 0:
                refused.append(material.name)
                warnings.append(f"Material still has users: {material.name}")
                continue
            bpy.data.materials.remove(material)
            deleted.append(str(name))
        status = "success" if not refused and (allow_missing or not missing) else "partial" if deleted else "error"
        return {"status": status, "deleted": deleted, "missing": missing, "refused": refused, "warnings": warnings}


class ShaderGraphService:
    ALLOWED_NODE_TYPES = {
        "ShaderNodeTexNoise", "ShaderNodeTexVoronoi", "ShaderNodeValToRGB", "ShaderNodeBump",
        "ShaderNodeNormalMap", "ShaderNodeTexCoord", "ShaderNodeMapping", "ShaderNodeSeparateColor",
        "ShaderNodeMix", "ShaderNodeMath",
    }
    ALLOWED_INPUTS = {"Base Color", "Metallic", "Roughness", "Alpha", "Emission Color", "Emission Strength", "Scale", "Strength", "Distance", "Fac", "Color", "Normal", "Height"}

    def __init__(self, server):
        self.server = server

    def get_shader_graph(self, material_name, include_links=True, include_node_inputs=True, include_node_outputs=True, include_texture_metadata=True, max_nodes=None):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        if not material.use_nodes or not material.node_tree:
            return {"status": "success", "material_name": material.name, "nodes": [], "links": [], "warnings": ["material does not use nodes"]}
        nodes = list(material.node_tree.nodes)
        truncated = False
        if max_nodes is not None and len(nodes) > int(max_nodes):
            nodes = nodes[:int(max_nodes)]
            truncated = True
        node_names = {node.name for node in nodes}
        graph_nodes = []
        for node in nodes:
            item = {"name": node.name, "label": node.label, "type": node.type, "bl_idname": node.bl_idname, "location": [float(node.location.x), float(node.location.y)]}
            if include_node_inputs:
                item["inputs"] = [{"name": socket.name, "type": socket.type, "default_value": MaterialIntelligenceService._json_value(getattr(socket, "default_value", "")) if hasattr(socket, "default_value") else None, "is_linked": bool(socket.is_linked), "channel_guess": self._channel_guess(socket.name)} for socket in node.inputs]
            if include_node_outputs:
                item["outputs"] = [{"name": socket.name, "type": socket.type, "is_linked": bool(socket.is_linked)} for socket in node.outputs]
            if include_texture_metadata and node.bl_idname == "ShaderNodeTexImage":
                item["texture_metadata"] = {"map_kind": node.get("overtli_map_kind"), "color_space_intent": node.get("overtli_color_space_intent"), "packed_convention": node.get("overtli_packed_convention")}
            graph_nodes.append(item)
        links = []
        if include_links:
            for link in material.node_tree.links:
                if link.from_node.name in node_names and link.to_node.name in node_names:
                    links.append({"from_node": link.from_node.name, "from_socket": link.from_socket.name, "to_node": link.to_node.name, "to_socket": link.to_socket.name})
        return {"status": "success", "material_name": material.name, "nodes": graph_nodes, "links": links, "truncated": truncated, "warnings": []}

    @staticmethod
    def _channel_guess(socket_name):
        normalized = socket_name.lower().replace(" ", "_")
        return {"base_color": "base_color", "roughness": "roughness", "metallic": "metallic", "alpha": "alpha", "normal": "normal", "height": "height"}.get(normalized)

    def add_material_node(self, material_name, node_type, name=None, location=None):
        if node_type not in self.ALLOWED_NODE_TYPES:
            return {"status": "error", "message": f"Node type not allowlisted: {node_type}", "allowed_node_types": sorted(self.ALLOWED_NODE_TYPES), "warnings": []}
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        material.use_nodes = True
        node = material.node_tree.nodes.new(type=node_type)
        if name:
            node.name = str(name)
            node.label = str(name)
        if location and len(location) == 2:
            node.location = (float(location[0]), float(location[1]))
        return {"status": "success", "material_name": material.name, "node": {"name": node.name, "type": node.type, "bl_idname": node.bl_idname}, "warnings": []}

    def set_material_node_input(self, material_name, node_name, input_name, value):
        if input_name not in self.ALLOWED_INPUTS:
            return {"status": "error", "message": f"Node input not allowlisted: {input_name}", "warnings": []}
        material = bpy.data.materials.get(material_name)
        if not material or not material.node_tree:
            return {"status": "error", "message": f"Material not found or has no node tree: {material_name}", "warnings": []}
        node = material.node_tree.nodes.get(node_name)
        if not node:
            return {"status": "error", "message": f"Node not found: {node_name}", "warnings": []}
        socket = node.inputs.get(input_name)
        if not socket or not hasattr(socket, "default_value"):
            return {"status": "error", "message": f"Input not settable: {input_name}", "warnings": []}
        socket.default_value = value
        return {"status": "success", "material_name": material.name, "node_name": node.name, "input_name": input_name, "value": MaterialIntelligenceService._json_value(socket.default_value), "warnings": []}

    def connect_material_nodes(self, material_name, from_node, from_socket, to_node, to_socket):
        material = bpy.data.materials.get(material_name)
        if not material or not material.node_tree:
            return {"status": "error", "message": f"Material not found or has no node tree: {material_name}", "warnings": []}
        source = material.node_tree.nodes.get(from_node)
        target = material.node_tree.nodes.get(to_node)
        if not source or not target:
            return {"status": "error", "message": "Source or target node not found", "warnings": []}
        output = source.outputs.get(from_socket)
        input_socket = target.inputs.get(to_socket)
        if not output or not input_socket:
            return {"status": "error", "message": "Source or target socket not found", "warnings": []}
        material.node_tree.links.new(output, input_socket)
        return {"status": "success", "material_name": material.name, "link": {"from_node": source.name, "from_socket": output.name, "to_node": target.name, "to_socket": input_socket.name}, "warnings": []}

    def remove_material_node(self, material_name, node_name, confirm=False):
        if not confirm:
            return {"status": "error", "message": "remove_material_node requires confirm=True", "warnings": []}
        material = bpy.data.materials.get(material_name)
        if not material or not material.node_tree:
            return {"status": "error", "message": f"Material not found or has no node tree: {material_name}", "warnings": []}
        node = material.node_tree.nodes.get(node_name)
        if not node:
            return {"status": "error", "message": f"Node not found: {node_name}", "warnings": []}
        if node.bl_idname not in self.ALLOWED_NODE_TYPES or not node.name.startswith("OVERTLI"):
            return {"status": "error", "message": "Refusing to remove non-Overtli or non-allowlisted material node", "warnings": []}
        material.node_tree.nodes.remove(node)
        return {"status": "success", "material_name": material.name, "removed_node": node_name, "warnings": []}


class MaterialTextureSlotService:
    def __init__(self, server):
        self.server = server

    def bind_material_texture_map(self, material_name, map_kind, texture_path, strict_file_exists=True, connect=True, packed_convention=None, verify=True):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        if map_kind not in MATERIAL_MAP_KINDS:
            return {"status": "error", "message": f"Unsupported map_kind: {map_kind}", "supported_map_kinds": sorted(MATERIAL_MAP_KINDS), "warnings": []}
        warnings = []
        abs_path = bpy.path.abspath(texture_path) if texture_path else ""
        if strict_file_exists and (not abs_path or not os.path.exists(abs_path)):
            return {"status": "error", "message": f"Texture file not found: {texture_path}", "color_space_intent": MATERIAL_MAP_KINDS[map_kind]["color_space"], "warnings": []}
        material.use_nodes = True
        node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
        node.name = f"OVERTLI {map_kind}"
        node["overtli_map_kind"] = map_kind
        node["overtli_color_space_intent"] = MATERIAL_MAP_KINDS[map_kind]["color_space"]
        convention = packed_convention or MATERIAL_MAP_KINDS[map_kind].get("packed")
        if convention:
            node["overtli_packed_convention"] = convention
            warnings.append(f"Packed map convention recorded: {convention}; channel splitting is metadata-first in Phase 4A.")
        if abs_path and os.path.exists(abs_path):
            try:
                image = bpy.data.images.load(abs_path, check_existing=True)
                node.image = image
                if hasattr(image, "colorspace_settings"):
                    image.colorspace_settings.name = "Non-Color" if MATERIAL_MAP_KINDS[map_kind]["color_space"] == "Non-Color" else "sRGB"
            except Exception as exc:
                warnings.append(f"Texture node created but image load failed: {exc}")
        elif texture_path:
            warnings.append(f"Texture path recorded but not loaded because file is missing: {texture_path}")
        if connect:
            warnings.extend(self._connect_texture_node(material, node, map_kind))
        verification = self.server.material_intelligence_service.get_material_deep_info(material.name, include_node_graph=True) if verify else None
        return {"status": "success", "material_name": material.name, "map_kind": map_kind, "texture_path": texture_path, "color_space_intent": MATERIAL_MAP_KINDS[map_kind]["color_space"], "packed_convention": convention, "verification": verification, "warnings": warnings}

    def _connect_texture_node(self, material, image_node, map_kind):
        warnings = []
        principled = MaterialIntelligenceService._principled_node(material)
        if not principled:
            return ["No Principled BSDF node found for texture connection"]
        links = material.node_tree.links
        color_output = image_node.outputs.get("Color")
        alpha_output = image_node.outputs.get("Alpha")
        def link_to(output, socket_name):
            socket = principled.inputs.get(socket_name)
            if output and socket:
                links.new(output, socket)
                return True
            return False
        if map_kind in {"base_color_map", "albedo_map"}:
            if not link_to(color_output, "Base Color"):
                warnings.append("Base Color socket not available")
        elif map_kind in {"roughness_map", "metallic_map", "alpha_map", "opacity_map"}:
            socket_name = {"roughness_map": "Roughness", "metallic_map": "Metallic", "alpha_map": "Alpha", "opacity_map": "Alpha"}[map_kind]
            if not link_to(alpha_output or color_output, socket_name):
                warnings.append(f"{socket_name} socket not available")
        elif map_kind == "normal_map":
            normal = material.node_tree.nodes.new(type="ShaderNodeNormalMap")
            normal.name = "OVERTLI Normal Map"
            if color_output and normal.inputs.get("Color"):
                links.new(color_output, normal.inputs["Color"])
            if normal.outputs.get("Normal") and principled.inputs.get("Normal"):
                links.new(normal.outputs["Normal"], principled.inputs["Normal"])
        elif map_kind in {"bump_map", "height_map"}:
            bump = material.node_tree.nodes.new(type="ShaderNodeBump")
            bump.name = "OVERTLI Bump From Map"
            if color_output and bump.inputs.get("Height"):
                links.new(color_output, bump.inputs["Height"])
            if bump.outputs.get("Normal") and principled.inputs.get("Normal"):
                links.new(bump.outputs["Normal"], principled.inputs["Normal"])
        elif map_kind == "emission_map":
            link_to(color_output, "Emission Color") or link_to(color_output, "Emission")
        elif map_kind in {"ambient_occlusion_map", "orm_map", "rma_map", "mra_map", "metallic_roughness_map"}:
            warnings.append("Map recorded for agent-aware workflow; automatic packed/AO channel mixing is not blindly connected.")
        return warnings


class ProceduralTextureService:
    def __init__(self, server):
        self.server = server

    def create_procedural_material(self, material_name, procedural_type="noise", base_color=None, secondary_color=None, parameters=None, assign_to_object=None, replace_existing=False, verify=True):
        recipe = {
            "channels": {"base_color": base_color or [0.45, 0.45, 0.45, 1.0], "roughness": (parameters or {}).get("roughness", 0.68), "metallic": (parameters or {}).get("metallic", 0.0)},
            "procedural": {"enabled": True, "type": procedural_type, "noise_scale": (parameters or {}).get("noise_scale", 22.0), "bump_strength": (parameters or {}).get("bump_strength", 0.04), "secondary_color": secondary_color},
            "preview_shape": (parameters or {}).get("preview_shape", "sphere"),
        }
        result = self.server.advanced_material_authoring_service.create_custom_material(material_name, recipe, replace_existing, verify)
        if result.get("status") == "success" and assign_to_object:
            result["assignment"] = self.server.material_authoring_service.assign_material(assign_to_object, material_name, verify=False)
        return result


class MaterialPreviewService:
    def __init__(self, server):
        self.server = server

    def create_material_preview(self, material_name, preview_shape="sphere", artifact_root=None, include_snapshot=True):
        material = bpy.data.materials.get(material_name)
        if not material:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        root = artifact_root or ADDON_ROOT
        preview_dir = os.path.join(root, ".overtli_blender", "material_previews")
        os.makedirs(preview_dir, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", material.name)
        manifest_path = os.path.join(preview_dir, f"{safe_name}_{int(time.time())}.json")
        payload = {
            "material_name": material.name,
            "preview_shape": preview_shape,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "deep_info": self.server.material_intelligence_service.get_material_deep_info(material.name, include_node_graph=False).get("material"),
            "note": "Phase 4A preview manifest; no external assets downloaded.",
        }
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        snapshot = None
        if include_snapshot:
            snapshot = self.server.verification_artifact_service.create_verification_snapshot(label=f"material_preview_{safe_name}", include_screenshots=False, artifact_root=root)
        return {"status": "success", "material_name": material.name, "preview_artifact": manifest_path, "snapshot": snapshot, "warnings": []}


class MaterialWorkflowBatchService:
    def __init__(self, server):
        self.server = server

    def run_material_workflow_batch(self, operations, label=None, artifact_root=None, verify=True):
        batch_id = f"material_batch_{int(time.time())}"
        before = self.server.workspace_safety_diff_service.create_scene_snapshot(label=f"{batch_id}_before", artifact_root=artifact_root or ADDON_ROOT) if verify else None
        results, errors, warnings = [], [], []
        for op in operations or []:
            command = op.get("command")
            params = op.get("params", {})
            if command not in {
                "create_material_from_template", "create_custom_material", "create_procedural_material",
                "create_material_variant", "apply_material_to_objects", "bind_material_texture_map",
                "set_material_node_input", "add_material_node", "connect_material_nodes", "create_material_preview",
            }:
                errors.append({"command": command, "message": "Command not allowed in material workflow batch"})
                continue
            result = getattr(self.server, command)(**params)
            results.append({"command": command, "result": result})
            warnings.extend(result.get("warnings", []))
            if result.get("status") == "error":
                errors.append({"command": command, "message": result.get("message")})
        after = self.server.workspace_safety_diff_service.create_scene_snapshot(label=f"{batch_id}_after", artifact_root=artifact_root or ADDON_ROOT) if verify else None
        status = "success" if not errors else "partial" if results else "error"
        return {"status": status, "batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors, "warnings": warnings}


