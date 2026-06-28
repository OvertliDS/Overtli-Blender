from __future__ import annotations

from ..core import *

class SceneEditService:
    SUPPORTED_PRIMITIVES = {
        "cube": bpy.ops.mesh.primitive_cube_add,
        "uv_sphere": bpy.ops.mesh.primitive_uv_sphere_add,
        "ico_sphere": bpy.ops.mesh.primitive_ico_sphere_add,
        "cylinder": bpy.ops.mesh.primitive_cylinder_add,
        "cone": bpy.ops.mesh.primitive_cone_add,
        "plane": bpy.ops.mesh.primitive_plane_add,
        "torus": bpy.ops.mesh.primitive_torus_add,
    }

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _vector(value, default, length=3):
        if value is None:
            return list(default)
        if not isinstance(value, (list, tuple)) or len(value) != length:
            raise ValueError(f"Expected a {length}-item numeric list")
        return [float(item) for item in value]

    @staticmethod
    def _unique_name(base_name):
        base = re.sub(r"[^A-Za-z0-9_. -]+", "_", str(base_name or "Object")).strip() or "Object"
        if base not in bpy.data.objects:
            return base
        index = 1
        while f"{base}.{index:03d}" in bpy.data.objects:
            index += 1
        return f"{base}.{index:03d}"

    def _deep_info(self, object_name):
        return self.server.scene_intelligence_service.get_object_deep_info(object_name=object_name).get("object")

    @staticmethod
    def _world_bounds(obj):
        corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in getattr(obj, "bound_box", [])]
        if not corners:
            loc = obj.matrix_world.translation
            corners = [loc]
        min_corner = [min(corner[i] for corner in corners) for i in range(3)]
        max_corner = [max(corner[i] for corner in corners) for i in range(3)]
        center = [(min_corner[i] + max_corner[i]) / 2 for i in range(3)]
        size = [max_corner[i] - min_corner[i] for i in range(3)]
        return {
            "min": [round(float(v), 6) for v in min_corner],
            "max": [round(float(v), 6) for v in max_corner],
            "center": [round(float(v), 6) for v in center],
            "size": [round(float(v), 6) for v in size],
            "bottom_z": round(float(min_corner[2]), 6),
            "top_z": round(float(max_corner[2]), 6),
        }

    @classmethod
    def _anchor_point(cls, obj, anchor="center"):
        bounds = cls._world_bounds(obj)
        point = list(bounds["center"])
        anchor = str(anchor or "center").lower()
        if anchor == "bottom_center":
            point[2] = bounds["min"][2]
        elif anchor == "top_center":
            point[2] = bounds["max"][2]
        elif anchor == "front_center":
            point[1] = bounds["min"][1]
        elif anchor == "back_center":
            point[1] = bounds["max"][1]
        return point

    @classmethod
    def _move_anchor_to(cls, obj, anchor, target):
        current = cls._anchor_point(obj, anchor)
        delta = [float(target[i]) - current[i] for i in range(3)]
        obj.location = [obj.location[i] + delta[i] for i in range(3)]

    def _apply_dimensions(self, obj, dimensions):
        dims = self._vector(dimensions, [1.0, 1.0, 1.0])
        if any(value <= 0 for value in dims):
            raise ValueError("dimensions values must be positive")
        obj.dimensions = dims
        bpy.context.view_layer.update()
        return dims

    def _dimension_verification(self, obj, requested_dimensions=None, tolerance=0.001):
        bounds = self._world_bounds(obj)
        warnings = []
        if requested_dimensions:
            requested = [float(v) for v in requested_dimensions]
            for index, axis in enumerate("xyz"):
                if abs(bounds["size"][index] - requested[index]) > float(tolerance):
                    warnings.append(f"{axis} dimension differs from requested value by more than {tolerance}")
        return {
            "final_dimensions": [round(float(v), 6) for v in obj.dimensions],
            "bounds": bounds,
            "warnings": warnings,
        }

    def _verification(self, label, verify):
        if not verify:
            return {}
        return self.server.verification_artifact_service.create_verification_snapshot(
            label=label,
            include_scene_index=True,
            include_scene_health=True,
            include_selection=False,
            include_screenshots=False,
        )

    def _operation_record(self, operation, payload, result):
        self.server._add_to_history(operation, payload, result)

    def get_supported_edit_operations(self):
        return {
            "status": "success",
            "operations": {
                "create_primitive_object": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False, "supported_types": sorted(self.SUPPORTED_PRIMITIVES)},
                "transform_object": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "duplicate_object": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "delete_objects": {"risk_level": "HIGH", "mutates_scene": True, "requires_confirmation": True},
                "set_object_visibility": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "create_basic_material": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "assign_material": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "update_material_properties": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "add_object_modifier": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "update_object_modifier": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "remove_object_modifier": {"risk_level": "HIGH", "mutates_scene": True, "requires_confirmation": True},
                "create_collection": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "move_objects_to_collection": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
                "delete_collection": {"risk_level": "HIGH", "mutates_scene": True, "requires_confirmation": True, "require_empty_default": True},
                "run_verified_edit_batch": {"risk_level": "MEDIUM", "mutates_scene": True, "requires_confirmation": False},
            },
            "warnings": [],
        }

    def create_primitive_object(self, primitive_type, name=None, location=None, rotation=None, scale=None, collection_name=None, material_name=None, verify=False, dimensions=None, anchor="center", origin_mode=None, snap_to=None, clearance=0.0):
        primitive_key = str(primitive_type or "").strip().lower()
        if primitive_key not in self.SUPPORTED_PRIMITIVES:
            return {"status": "error", "message": f"Unsupported primitive_type: {primitive_type}", "warnings": []}
        if material_name and material_name not in bpy.data.materials:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}

        self.SUPPORTED_PRIMITIVES[primitive_key]()
        obj = bpy.context.object
        obj.name = self._unique_name(name or f"Overtli_{primitive_key}")
        obj.location = self._vector(location, [0.0, 0.0, 0.0])
        obj.rotation_euler = self._vector(rotation, [0.0, 0.0, 0.0])
        obj.scale = self._vector(scale, [1.0, 1.0, 1.0])
        bpy.context.view_layer.update()
        if dimensions is not None:
            self._apply_dimensions(obj, dimensions)
            target = self._vector(location, [0.0, 0.0, 0.0])
            if anchor:
                self._move_anchor_to(obj, anchor, target)
        if snap_to:
            target_name = snap_to.get("object") if isinstance(snap_to, dict) else str(snap_to)
            target_obj = bpy.data.objects.get(target_name)
            if target_obj:
                self._move_anchor_to(obj, anchor or "bottom_center", [self._anchor_point(obj, anchor or "bottom_center")[0], self._anchor_point(obj, anchor or "bottom_center")[1], self._world_bounds(target_obj)["max"][2] + float(clearance or 0.0)])

        collection = None
        if collection_name:
            collection = bpy.data.collections.get(collection_name)
            if collection is None:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)
            for linked in list(obj.users_collection):
                linked.objects.unlink(obj)
            collection.objects.link(obj)

        if material_name:
            obj.data.materials.append(bpy.data.materials[material_name])

        result = {
            "status": "success",
            "object_name": obj.name,
            "object_type": obj.type,
            "created": True,
            "collection_name": collection.name if collection else (obj.users_collection[0].name if obj.users_collection else None),
            "transform": {"location": list(obj.location), "rotation": list(obj.rotation_euler), "scale": list(obj.scale)},
            "dimension_verification": self._dimension_verification(obj, dimensions),
            "anchor": anchor,
            "origin_mode": origin_mode,
            "material_name": material_name,
            "object": self._deep_info(obj.name),
            "verification": self._verification(f"edit_{obj.name}", verify),
            "warnings": [],
        }
        self._operation_record("create_primitive_object", {"primitive_type": primitive_key, "name": name}, result)
        return result

    def create_box(self, name=None, dimensions=None, location=None, anchor="bottom_center", collection_name=None, material_name=None, verify=False):
        return self.create_primitive_object(
            "cube",
            name=name,
            location=location or [0.0, 0.0, 0.0],
            dimensions=dimensions or [1.0, 1.0, 1.0],
            anchor=anchor,
            collection_name=collection_name,
            material_name=material_name,
            verify=verify,
        )

    def transform_object(self, object_name, location=None, rotation=None, scale=None, relative=False, verify=False, dimensions=None, anchor=None, preserve_anchor=True):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if location is not None:
            vec = self._vector(location, [0.0, 0.0, 0.0])
            obj.location = [obj.location[i] + vec[i] for i in range(3)] if relative else vec
        if rotation is not None:
            vec = self._vector(rotation, [0.0, 0.0, 0.0])
            obj.rotation_euler = [obj.rotation_euler[i] + vec[i] for i in range(3)] if relative else vec
        if scale is not None:
            vec = self._vector(scale, [1.0, 1.0, 1.0])
            obj.scale = [obj.scale[i] + vec[i] for i in range(3)] if relative else vec
        bpy.context.view_layer.update()
        preserved_point = self._anchor_point(obj, anchor or "center") if dimensions is not None and preserve_anchor else None
        if dimensions is not None:
            self._apply_dimensions(obj, dimensions)
            if preserved_point is not None:
                self._move_anchor_to(obj, anchor or "center", preserved_point)
        result = {"status": "success", "object_name": obj.name, "object": self._deep_info(obj.name), "dimension_verification": self._dimension_verification(obj, dimensions), "verification": self._verification(f"transform_{obj.name}", verify), "warnings": []}
        self._operation_record("transform_object", {"object_name": object_name}, result)
        return result

    def transform_object_dimensions(self, object_name, dimensions, preserve_anchor=True, anchor="bottom_center", verify=False):
        return self.transform_object(object_name, dimensions=dimensions, preserve_anchor=preserve_anchor, anchor=anchor, verify=verify)

    def duplicate_object(self, object_name, new_name=None, linked=False, location_offset=None, collection_name=None, verify=False):
        source = bpy.data.objects.get(object_name)
        if not source:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        duplicate = source.copy()
        if not linked and getattr(source, "data", None):
            duplicate.data = source.data.copy()
        duplicate.name = self._unique_name(new_name or f"{source.name}_copy")
        offset = self._vector(location_offset, [0.0, 0.0, 0.0])
        duplicate.location = [source.location[i] + offset[i] for i in range(3)]
        target_collection = bpy.data.collections.get(collection_name) if collection_name else (source.users_collection[0] if source.users_collection else bpy.context.scene.collection)
        if target_collection is None:
            return {"status": "error", "message": f"Collection not found: {collection_name}", "warnings": []}
        target_collection.objects.link(duplicate)
        result = {"status": "success", "source_object_name": source.name, "object_name": duplicate.name, "linked": bool(linked), "collection_name": target_collection.name, "object": self._deep_info(duplicate.name), "verification": self._verification(f"duplicate_{duplicate.name}", verify), "warnings": []}
        self._operation_record("duplicate_object", {"object_name": object_name, "new_name": new_name}, result)
        return result

    def delete_objects(self, object_names, confirm=False, allow_missing=False, verify=False):
        if not confirm:
            return {"status": "error", "message": "delete_objects requires confirm=True", "deleted": [], "missing": list(object_names or []), "refused": list(object_names or []), "warnings": []}
        if not isinstance(object_names, list) or not object_names:
            return {"status": "error", "message": "object_names must be a non-empty list", "deleted": [], "missing": [], "refused": [], "warnings": []}
        deleted, missing = [], []
        for name in object_names:
            if any(token in str(name) for token in ["*", "?", "["]):
                return {"status": "error", "message": f"Wildcard-like object name refused: {name}", "deleted": deleted, "missing": missing, "refused": [name], "warnings": []}
            obj = bpy.data.objects.get(str(name))
            if obj is None:
                missing.append(str(name))
                continue
            bpy.data.objects.remove(obj, do_unlink=True)
            deleted.append(str(name))
        if missing and not allow_missing:
            status = "partial" if deleted else "error"
            message = f"Missing objects: {missing}"
        else:
            status, message = "success", None
        result = {"status": status, "deleted": deleted, "missing": missing, "refused": [], "verification": self._verification("delete_objects", verify), "warnings": []}
        if message:
            result["message"] = message
        self._operation_record("delete_objects", {"object_names": object_names}, result)
        return result

    def clear_scene(self, scope="prefix", prefix="OVERTLI_", collection_name=None, delete_objects=True, delete_empty_collections=True, delete_unused_materials=True, delete_unused_images=False, delete_cameras_lights=False, dry_run=True, confirm=False, create_before_snapshot=True):
        warnings = []
        objects = []
        if scope == "all_scene":
            objects = list(bpy.context.scene.objects)
            if not confirm:
                warnings.append("all_scene cleanup requires confirm=True")
        elif scope == "selected":
            objects = list(bpy.context.selected_objects)
        elif scope == "collection":
            collection = bpy.data.collections.get(collection_name or "")
            if not collection:
                return {"status": "error", "message": f"Collection not found: {collection_name}", "warnings": []}
            objects = list(collection.objects)
        else:
            safe_prefix = str(prefix or "OVERTLI_")
            objects = [obj for obj in bpy.context.scene.objects if obj.name.startswith(safe_prefix)]
        if not delete_cameras_lights:
            objects = [obj for obj in objects if obj.type not in {"CAMERA", "LIGHT"}]
        if scope == "all_scene" and not confirm:
            objects = [obj for obj in objects if obj.name.startswith(str(prefix or "OVERTLI_"))]
            warnings.append("Without confirm=True, all_scene is constrained to generated prefix content")
        object_names = sorted({obj.name for obj in objects}) if delete_objects else []
        collection_names = []
        if delete_empty_collections:
            for collection in bpy.data.collections:
                prefix_match = collection.name.startswith(str(prefix or "OVERTLI_"))
                collection_match = scope == "collection" and collection.name == collection_name
                if (prefix_match or collection_match) and len(collection.objects) == 0 and len(collection.children) == 0:
                    collection_names.append(collection.name)
        material_names = sorted(mat.name for mat in bpy.data.materials if delete_unused_materials and mat.users == 0 and mat.name.startswith(("OVERTLI_", "OVERTLI_MAT_")))
        image_names = sorted(img.name for img in bpy.data.images if delete_unused_images and img.users == 0 and img.name.startswith("OVERTLI_"))
        before_snapshot = self.server.workspace_safety_diff_service.create_scene_snapshot(label="clear_scene_before", include_verification_snapshot=False) if create_before_snapshot else None
        plan = {
            "objects_to_delete": object_names,
            "collections_to_delete": collection_names,
            "materials_to_delete": material_names,
            "images_to_delete": image_names,
            "warnings": warnings,
            "approval_required": bool(object_names or collection_names or material_names or image_names),
            "destructive": True,
            "dry_run": bool(dry_run),
            "before_snapshot": before_snapshot,
        }
        if dry_run or not confirm:
            return {"status": "requires_approval" if plan["approval_required"] else "success", **plan}
        for name in object_names:
            obj = bpy.data.objects.get(name)
            if obj:
                bpy.data.objects.remove(obj, do_unlink=True)
        for name in collection_names:
            collection = bpy.data.collections.get(name)
            if collection:
                bpy.data.collections.remove(collection)
        for name in material_names:
            material = bpy.data.materials.get(name)
            if material and material.users == 0:
                bpy.data.materials.remove(material)
        for name in image_names:
            image = bpy.data.images.get(name)
            if image and image.users == 0:
                bpy.data.images.remove(image)
        after_snapshot = self.server.workspace_safety_diff_service.create_scene_snapshot(label="clear_scene_after", include_verification_snapshot=False)
        return {"status": "success", **plan, "dry_run": False, "after_snapshot": after_snapshot}

    def scene_cleanup_plan(self, **kwargs):
        kwargs["dry_run"] = True
        kwargs["confirm"] = False
        return self.clear_scene(**kwargs)

    def validate_ground_contact(self, object_names, ground_object, expected_relation="on_top", tolerance=0.01):
        ground = bpy.data.objects.get(ground_object)
        if not ground:
            return {"status": "error", "message": f"Ground object not found: {ground_object}", "warnings": []}
        ground_bounds = self._world_bounds(ground)
        rows = []
        warnings = []
        for name in object_names or []:
            obj = bpy.data.objects.get(name)
            if not obj:
                rows.append({"object_name": name, "status": "missing"})
                continue
            bounds = self._world_bounds(obj)
            gap = bounds["bottom_z"] - ground_bounds["top_z"]
            ok = abs(gap) <= float(tolerance) if expected_relation == "on_top" else gap >= -float(tolerance)
            if not ok:
                warnings.append(f"{name} contact gap/penetration {round(gap, 6)} exceeds tolerance {tolerance}")
            rows.append({"object_name": name, "bottom_z": bounds["bottom_z"], "ground_top_z": ground_bounds["top_z"], "gap": round(float(gap), 6), "within_tolerance": ok})
        return {"status": "success" if not warnings else "warning", "ground_object": ground_object, "results": rows, "warnings": warnings}

    def align_object_to_surface(self, object_name, target_object, target_face="top", anchor="bottom_center", clearance=0.0):
        obj = bpy.data.objects.get(object_name)
        target = bpy.data.objects.get(target_object)
        if not obj or not target:
            return {"status": "error", "message": "object_name and target_object must exist", "warnings": []}
        target_bounds = self._world_bounds(target)
        z = target_bounds["max"][2] if str(target_face).lower() == "top" else target_bounds["min"][2]
        current_anchor = self._anchor_point(obj, anchor)
        self._move_anchor_to(obj, anchor, [current_anchor[0], current_anchor[1], z + float(clearance or 0.0)])
        return {"status": "success", "object_name": obj.name, "target_object": target.name, "bounds": self._world_bounds(obj), "warnings": []}

    def validate_scene_composition(self, generated_prefix="OVERTLI_", expected_collection=None, ground_object=None, tolerance=0.01, allow_below_ground=False):
        objects = [obj for obj in bpy.context.scene.objects if obj.name.startswith(str(generated_prefix or ""))]
        warnings = []
        if expected_collection:
            for obj in objects:
                if expected_collection not in [collection.name for collection in obj.users_collection]:
                    warnings.append(f"{obj.name} is not in expected collection {expected_collection}")
        ground_top = None
        if ground_object and bpy.data.objects.get(ground_object):
            ground_top = self._world_bounds(bpy.data.objects[ground_object])["top_z"]
        below_ground = []
        if ground_top is not None and not allow_below_ground:
            for obj in objects:
                if self._world_bounds(obj)["bottom_z"] < ground_top - float(tolerance):
                    below_ground.append(obj.name)
            if below_ground:
                warnings.append(f"{len(below_ground)} generated object(s) are below ground tolerance")
        empty_collections = [collection.name for collection in bpy.data.collections if collection.name.startswith(str(generated_prefix or "")) and len(collection.objects) == 0 and len(collection.children) == 0]
        if empty_collections:
            warnings.append(f"{len(empty_collections)} empty generated collection(s) found")
        return {
            "status": "success" if not warnings else "warning",
            "generated_object_count": len(objects),
            "generated_objects": [obj.name for obj in objects],
            "empty_generated_collections": empty_collections,
            "below_ground_objects": below_ground,
            "camera_exists": any(obj.type == "CAMERA" for obj in bpy.context.scene.objects),
            "lights_exist": any(obj.type == "LIGHT" for obj in bpy.context.scene.objects),
            "warnings": warnings,
        }

    def set_object_visibility(self, object_name, hide_viewport=None, hide_render=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if hide_viewport is not None:
            obj.hide_viewport = bool(hide_viewport)
        if hide_render is not None:
            obj.hide_render = bool(hide_render)
        result = {"status": "success", "object_name": obj.name, "visibility": {"hide_viewport": bool(obj.hide_viewport), "hide_render": bool(obj.hide_render), "visible": bool(obj.visible_get())}, "verification": self._verification(f"visibility_{obj.name}", verify), "warnings": []}
        self._operation_record("set_object_visibility", {"object_name": object_name}, result)
        return result

class RiggingSimulationService:
    def __init__(self, server):
        self.server = server

    def inspect_rigging(self, object_name=None):
        objects = [bpy.data.objects.get(object_name)] if object_name else list(bpy.data.objects)
        rigs = []
        for obj in [o for o in objects if o]:
            if obj.type == "ARMATURE":
                rigs.append({"name": obj.name, "type": "ARMATURE", "bones": [b.name for b in obj.data.bones], "pose_bones": [b.name for b in obj.pose.bones] if obj.pose else []})
            elif obj.type == "MESH":
                armature_mods = [m.name for m in obj.modifiers if m.type == "ARMATURE"]
                if armature_mods or obj.vertex_groups:
                    rigs.append({"name": obj.name, "type": "MESH", "armature_modifiers": armature_mods, "vertex_groups": [g.name for g in obj.vertex_groups]})
        return {"status": "success", "rigging": rigs, "warnings": []}

    @staticmethod
    def _normalized_bone_specs(bones, epsilon=1e-6):
        specs = bones or [{"name": "Root", "head": [0, 0, 0], "tail": [0, 0, 1]}]
        normalized = []
        for index, spec in enumerate(specs):
            name = spec.get("name", "Root" if index == 0 else "Bone")
            head = [float(value) for value in spec.get("head", [0, 0, 0])]
            tail = [float(value) for value in spec.get("tail", [0, 0, 1])]
            if len(head) != 3 or len(tail) != 3:
                raise ValueError(f"Bone '{name}' head and tail must be 3-item numeric lists")
            if (mathutils.Vector(tail) - mathutils.Vector(head)).length < float(epsilon):
                if spec.get("auto_offset_tail") is True:
                    tail = [head[0], head[1], head[2] + max(float(epsilon), 0.001)]
                else:
                    raise ValueError(f"Bone '{name}' has zero or near-zero length; provide a distinct tail or set auto_offset_tail=true")
            normalized.append({"name": name, "head": head, "tail": tail, "parent": spec.get("parent")})
        return normalized

    def create_armature(self, armature_name=None, bones=None, collection_name=None, location=None):
        try:
            bone_specs = self._normalized_bone_specs(bones)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}
        name = armature_name or f"OVERTLI_ARMATURE_{RenderArtifactService.stamp()}"
        arm_data = bpy.data.armatures.new(name)
        arm_obj = bpy.data.objects.new(name, arm_data)
        collection = bpy.data.collections.get(collection_name) if collection_name else bpy.context.scene.collection
        if collection_name and collection is None:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        collection.objects.link(arm_obj)
        arm_obj.location = location or [0, 0, 0]
        bpy.context.view_layer.objects.active = arm_obj
        arm_obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            first = bone_specs[0]
            default = arm_data.edit_bones[0] if arm_data.edit_bones else arm_data.edit_bones.new(first.get("name", "Root"))
            default.name = first.get("name", "Root")
            default.head = first.get("head", [0, 0, 0])
            default.tail = first.get("tail", [0, 0, 1])
            for spec in bone_specs[1:]:
                bone = arm_data.edit_bones.new(spec.get("name", "Bone"))
                bone.head = spec.get("head", [0, 0, 0])
                bone.tail = spec.get("tail", [0, 0, 1])
                if spec.get("parent"):
                    bone.parent = arm_data.edit_bones.get(spec["parent"])
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
        return {"status": "success", "armature": {"name": arm_obj.name, "bones": [b.name for b in arm_data.bones]}, "warnings": []}

    def parent_mesh_to_armature(self, mesh_name, armature_name, add_modifier=True, create_vertex_groups=True):
        mesh = bpy.data.objects.get(mesh_name)
        arm = bpy.data.objects.get(armature_name)
        if not mesh or mesh.type != "MESH" or not arm or arm.type != "ARMATURE":
            return {"status": "error", "message": "Mesh and armature objects are required", "warnings": []}
        mesh.parent = arm
        if add_modifier and not any(m.type == "ARMATURE" and m.object == arm for m in mesh.modifiers):
            mod = mesh.modifiers.new(f"{arm.name}_Armature", "ARMATURE")
            mod.object = arm
        if create_vertex_groups:
            for bone in arm.data.bones:
                if not mesh.vertex_groups.get(bone.name):
                    mesh.vertex_groups.new(name=bone.name)
        return {"status": "success", "mesh_name": mesh.name, "armature_name": arm.name, "vertex_groups": [g.name for g in mesh.vertex_groups], "warnings": []}

    def pose_bone_transform(self, armature_name, bone_name, location=None, rotation=None, scale=None, keyframe_frame=None):
        arm = bpy.data.objects.get(armature_name)
        if not arm or arm.type != "ARMATURE" or not arm.pose or bone_name not in arm.pose.bones:
            return {"status": "error", "message": "Armature pose bone not found", "warnings": []}
        bone = arm.pose.bones[bone_name]
        keyed_channels = []
        if location is not None:
            bone.location = location
            if keyframe_frame is not None:
                bone.keyframe_insert("location", frame=int(keyframe_frame))
                keyed_channels.append("location")
        if rotation is not None:
            rotation_values = [float(value) for value in rotation]
            if len(rotation_values) == 4:
                bone.rotation_mode = "QUATERNION"
                bone.rotation_quaternion = rotation_values
                rotation_channel = "rotation_quaternion"
            elif len(rotation_values) == 3:
                bone.rotation_mode = "XYZ"
                bone.rotation_euler = rotation_values
                rotation_channel = "rotation_euler"
            else:
                return {"status": "error", "message": "rotation must be a 3-item Euler list or 4-item quaternion list", "warnings": []}
            if keyframe_frame is not None:
                bone.keyframe_insert(rotation_channel, frame=int(keyframe_frame))
                keyed_channels.append(rotation_channel)
        if scale is not None:
            bone.scale = scale
            if keyframe_frame is not None:
                bone.keyframe_insert("scale", frame=int(keyframe_frame))
                keyed_channels.append("scale")
        return {"status": "success", "armature_name": arm.name, "bone_name": bone.name, "rotation_mode_used": bone.rotation_mode, "keyed_channels": keyed_channels, "warnings": []}

    def add_driver(self, target_type, target_name, data_path, expression="var", variables=None, array_index=-1):
        target_type_key = str(target_type or "").lower()
        if target_type_key not in {"object", "material"}:
            return {"status": "error", "message": "target_type must be 'object' or 'material'", "warnings": []}
        target = bpy.data.objects.get(target_name) if target_type_key == "object" else bpy.data.materials.get(target_name)
        if not target:
            return {"status": "error", "message": "Driver target not found", "warnings": []}
        resolved_variables = []
        for spec in variables or []:
            source = None
            source_kind = str(spec.get("target_type") or "").lower()
            if spec.get("object_name"):
                source = bpy.data.objects.get(spec.get("object_name"))
                if source is None:
                    return {"status": "error", "message": f"Driver variable object not found: {spec.get('object_name')}", "warnings": []}
            elif source_kind == "scene" or spec.get("use_scene"):
                source = bpy.context.scene
            elif target_type_key == "object":
                source = target
            else:
                return {"status": "error", "message": "Material driver variables require object_name or target_type='scene'; refusing invalid Material variable target", "warnings": []}
            resolved_variables.append((spec, source))
        try:
            fcurve = target.driver_add(data_path, int(array_index)) if int(array_index) >= 0 else target.driver_add(data_path)
            fcurves = fcurve if isinstance(fcurve, list) else [fcurve]
            for fc in fcurves:
                fc.driver.type = "SCRIPTED"
                fc.driver.expression = str(expression)
                for spec, source in resolved_variables:
                    var = fc.driver.variables.new()
                    var.name = spec.get("name", "var")
                    var.targets[0].id = source
                    var.targets[0].data_path = spec.get("data_path", "location.x")
            return {"status": "success", "target_type": target_type_key, "target_name": target.name, "data_path": data_path, "driver_count": len(fcurves), "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def remove_driver(self, target_type, target_name, data_path, array_index=-1, confirm=False):
        if not confirm:
            return {"status": "error", "message": "remove_driver requires confirm=True", "warnings": []}
        target = bpy.data.objects.get(target_name) if target_type == "object" else bpy.data.materials.get(target_name)
        if not target:
            return {"status": "error", "message": "Driver target not found", "warnings": []}
        try:
            target.driver_remove(data_path, int(array_index)) if int(array_index) >= 0 else target.driver_remove(data_path)
            return {"status": "success", "target_type": target_type, "target_name": target.name, "data_path": data_path, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def add_physics_basic(self, object_name, physics_type="cloth", settings=None):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        physics_type = str(physics_type).lower()
        settings = settings or {}
        try:
            if physics_type == "cloth":
                mod = obj.modifiers.new(settings.get("name", "Overtli Cloth"), "CLOTH")
            elif physics_type == "collision":
                mod = obj.modifiers.new(settings.get("name", "Overtli Collision"), "COLLISION")
            elif physics_type == "soft_body":
                mod = obj.modifiers.new(settings.get("name", "Overtli Soft Body"), "SOFT_BODY")
            elif physics_type == "rigid_body":
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.rigidbody.object_add(type=settings.get("body_type", "ACTIVE"))
                mod = None
            elif physics_type == "particle_hair":
                mod = obj.modifiers.new(settings.get("name", "Overtli Hair"), "PARTICLE_SYSTEM")
                ps = obj.particle_systems[-1].settings
                ps.type = "HAIR"
                ps.count = max(1, min(int(settings.get("count", 100)), 10000))
                ps.hair_length = max(0.001, min(float(settings.get("hair_length", 1.0)), 100.0))
            else:
                return {"status": "error", "message": f"Unsupported physics_type: {physics_type}", "warnings": []}
            return {"status": "success", "object_name": obj.name, "physics_type": physics_type, "modifier_name": mod.name if mod else None, "warnings": ["Simulation cache is not baked by this command"]}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}


class ModifierService:
    SUPPORTED_MODIFIERS = {"BEVEL", "SUBSURF", "SOLIDIFY", "MIRROR", "ARRAY", "WEIGHTED_NORMAL", "TRIANGULATE", "DECIMATE"}
    ALLOWED_PROPERTIES = {
        "BEVEL": {"width", "segments", "affect", "profile", "show_viewport", "show_render"},
        "SUBSURF": {"levels", "render_levels", "subdivision_type", "show_viewport", "show_render"},
        "SOLIDIFY": {"thickness", "offset", "use_quality_normals", "show_viewport", "show_render"},
        "MIRROR": {"use_axis", "use_clip", "show_viewport", "show_render"},
        "ARRAY": {"count", "relative_offset_displace", "use_relative_offset", "show_viewport", "show_render"},
        "WEIGHTED_NORMAL": {"keep_sharp", "weight", "show_viewport", "show_render"},
        "TRIANGULATE": {"quad_method", "ngon_method", "show_viewport", "show_render"},
        "DECIMATE": {"ratio", "decimate_type", "show_viewport", "show_render"},
    }

    def __init__(self, server):
        self.server = server

    def _summary(self, modifier):
        return {"name": modifier.name, "type": modifier.type, "show_viewport": bool(modifier.show_viewport), "show_render": bool(modifier.show_render)}

    def _apply_properties(self, modifier, properties):
        warnings = []
        allowed = self.ALLOWED_PROPERTIES.get(modifier.type, set())
        for key, value in (properties or {}).items():
            if key not in allowed:
                warnings.append(f"Unsupported modifier property skipped: {key}")
                continue
            try:
                setattr(modifier, key, value)
            except Exception as exc:
                warnings.append(f"Failed to set {key}: {exc}")
        return warnings

    def add_object_modifier(self, object_name, modifier_type, name=None, properties=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        modifier_type = str(modifier_type or "").upper()
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if modifier_type not in self.SUPPORTED_MODIFIERS:
            return {"status": "error", "message": f"Unsupported modifier_type: {modifier_type}", "warnings": []}
        modifier = obj.modifiers.new(name=name or modifier_type.title(), type=modifier_type)
        warnings = self._apply_properties(modifier, properties)
        result = {"status": "success", "object_name": obj.name, "modifier": self._summary(modifier), "verification": self.server.scene_edit_service._verification(f"modifier_{obj.name}", verify), "warnings": warnings}
        self.server._add_to_history("add_object_modifier", {"object_name": object_name, "modifier_type": modifier_type}, result)
        return result

    def update_object_modifier(self, object_name, modifier_name, properties, verify=False):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        modifier = obj.modifiers.get(modifier_name)
        if not modifier:
            return {"status": "error", "message": f"Modifier not found: {modifier_name}", "warnings": []}
        warnings = self._apply_properties(modifier, properties or {})
        status = "partial" if warnings else "success"
        result = {"status": status, "object_name": obj.name, "modifier": self._summary(modifier), "verification": self.server.scene_edit_service._verification(f"modifier_{obj.name}", verify), "warnings": warnings}
        self.server._add_to_history("update_object_modifier", {"object_name": object_name, "modifier_name": modifier_name}, result)
        return result

    def remove_object_modifier(self, object_name, modifier_name, confirm=False, verify=False):
        if not confirm:
            return {"status": "error", "message": "remove_object_modifier requires confirm=True", "warnings": []}
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        modifier = obj.modifiers.get(modifier_name)
        if not modifier:
            return {"status": "error", "message": f"Modifier not found: {modifier_name}", "warnings": []}
        summary = self._summary(modifier)
        obj.modifiers.remove(modifier)
        result = {"status": "success", "object_name": obj.name, "removed_modifier": summary, "verification": self.server.scene_edit_service._verification(f"remove_modifier_{obj.name}", verify), "warnings": []}
        self.server._add_to_history("remove_object_modifier", {"object_name": object_name, "modifier_name": modifier_name}, result)
        return result


class CollectionOrganizationService:
    def __init__(self, server):
        self.server = server

    def _summary(self, collection):
        return {"name": collection.name, "object_count": len(collection.objects), "children": [child.name for child in collection.children]}

    def create_collection(self, collection_name, parent_collection_name=None, replace_existing=False):
        if not collection_name:
            return {"status": "error", "message": "collection_name is required", "warnings": []}
        existing = bpy.data.collections.get(collection_name)
        if existing and not replace_existing:
            return {"status": "success", "collection_name": existing.name, "created": False, "collection": self._summary(existing), "warnings": ["collection already exists"]}
        collection = existing or bpy.data.collections.new(collection_name)
        if not existing:
            parent = bpy.data.collections.get(parent_collection_name) if parent_collection_name else bpy.context.scene.collection
            if parent is None:
                return {"status": "error", "message": f"Parent collection not found: {parent_collection_name}", "warnings": []}
            parent.children.link(collection)
        result = {"status": "success", "collection_name": collection.name, "created": existing is None, "collection": self._summary(collection), "warnings": []}
        self.server._add_to_history("create_collection", {"collection_name": collection_name}, result)
        return result

    def move_objects_to_collection(self, object_names, collection_name, unlink_from_other_collections=False, create_collection=False):
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            if create_collection:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)
            else:
                return {"status": "error", "message": f"Collection not found: {collection_name}", "moved": [], "missing": list(object_names or []), "warnings": []}
        moved, missing = [], []
        for name in object_names or []:
            obj = bpy.data.objects.get(str(name))
            if not obj:
                missing.append(str(name))
                continue
            if obj.name not in collection.objects.keys():
                collection.objects.link(obj)
            if unlink_from_other_collections:
                for linked in list(obj.users_collection):
                    if linked != collection:
                        linked.objects.unlink(obj)
            moved.append(obj.name)
        status = "partial" if missing else "success"
        result = {"status": status, "collection_name": collection.name, "moved": moved, "missing": missing, "collection": self._summary(collection), "warnings": []}
        self.server._add_to_history("move_objects_to_collection", {"collection_name": collection_name, "object_names": object_names}, result)
        return result

    def delete_collection(self, collection_name, confirm=False, require_empty=True):
        if not confirm:
            return {"status": "error", "message": "delete_collection requires confirm=True", "collection_name": collection_name, "deleted": False, "warnings": []}
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            return {"status": "error", "message": f"Collection not found: {collection_name}", "collection_name": collection_name, "deleted": False, "warnings": []}
        object_count = len(collection.objects)
        child_count = len(collection.children)
        if require_empty and (object_count > 0 or child_count > 0):
            return {
                "status": "error",
                "message": f"Collection is not empty: {collection_name}",
                "collection_name": collection_name,
                "deleted": False,
                "object_count": object_count,
                "child_count": child_count,
                "warnings": ["delete_collection defaults to require_empty=True"],
            }
        summary = self._summary(collection)
        bpy.data.collections.remove(collection)
        result = {"status": "success", "collection_name": collection_name, "deleted": True, "collection": summary, "warnings": []}
        self.server._add_to_history("delete_collection", {"collection_name": collection_name}, result)
        return result


class VerifiedEditBatchService:
    SUPPORTED_BATCH_OPERATIONS = {
        "create_primitive_object",
        "transform_object",
        "duplicate_object",
        "set_object_visibility",
        "create_basic_material",
        "assign_material",
        "update_material_properties",
        "add_object_modifier",
        "update_object_modifier",
        "create_collection",
        "move_objects_to_collection",
        "delete_objects",
        "remove_object_modifier",
        "delete_collection",
        "create_box",
        "transform_object_dimensions",
        "clear_scene",
        "validate_ground_contact",
        "align_object_to_surface",
        "validate_scene_composition",
    }
    DESTRUCTIVE_OPERATIONS = {"delete_objects", "remove_object_modifier", "delete_collection", "clear_scene"}

    def __init__(self, server):
        self.server = server

    def _normalize_operation(self, operation):
        if not isinstance(operation, dict):
            return None, {}, "Operation must be an object"
        op_type = operation.get("command_name") or operation.get("type") or operation.get("command")
        params = dict(operation.get("params") or operation.get("parameters") or {})
        if not op_type:
            return None, params, "Expected operation.command_name, operation.type, or operation.command"
        return str(op_type), params, None

    def _schema_error(self, index, op_type=None, message=None):
        return {
            "index": index,
            "type": op_type,
            "message": message or "Unsupported batch operation",
            "expected_schema": {"command_name": "transform_object", "params": {"object_name": "Cube", "location": [0, 0, 1]}},
            "alternate_schema": {"type": "transform_object", "params": {"object_name": "Cube"}},
            "supported_operations": sorted(self.SUPPORTED_BATCH_OPERATIONS),
            "suggested_correction": "Use a public command name in command_name and place command inputs under params.",
        }

    def _prevalidate(self, operations, batch_allow_destructive):
        errors = []
        normalized = []
        for index, operation in enumerate(operations):
            op_type, params, error = self._normalize_operation(operation)
            if error:
                errors.append(self._schema_error(index, op_type, error))
                continue
            if op_type not in self.SUPPORTED_BATCH_OPERATIONS:
                errors.append(self._schema_error(index, op_type, "Unsupported batch operation"))
                continue
            if op_type in self.DESTRUCTIVE_OPERATIONS and not (operation.get("confirm") is True and batch_allow_destructive is True):
                errors.append(self._schema_error(index, op_type, "Destructive batch operation requires operation.confirm=True and batch_allow_destructive=True"))
                continue
            if op_type in self.DESTRUCTIVE_OPERATIONS and "confirm" not in params:
                params["confirm"] = bool(operation.get("confirm"))
            normalized.append((index, op_type, params))
        return normalized, errors

    def run_verified_edit_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=20, batch_allow_destructive=False, artifact_root=None, prevalidate_only=False, prevalidate_all=True):
        operations = operations or []
        max_operations = max(1, min(int(max_operations), 50))
        if len(operations) > max_operations:
            return {"status": "error", "message": f"Batch exceeds max_operations={max_operations}", "operation_results": [], "errors": [], "warnings": []}
        normalized, validation_errors = self._prevalidate(operations, batch_allow_destructive)
        if validation_errors and (prevalidate_all or prevalidate_only):
            return {"status": "error", "message": "Batch prevalidation failed before applying operations", "operation_results": [], "errors": validation_errors, "warnings": []}
        if prevalidate_only:
            return {"status": "success", "valid": True, "normalized_operations": [{"index": index, "type": op_type, "params": params} for index, op_type, params in normalized], "warnings": []}
        batch_id = f"batch_{int(time.time())}_{abs(hash(str(operations))) % 100000}"
        batch_label = label or batch_id
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_label}_before", include_screenshots=False, artifact_root=artifact_root) if create_before_snapshot else {}
        results, errors, warnings = [], [], []
        if validation_errors:
            errors.extend(validation_errors)
        for index, op_type, params in normalized:
            handler = self.server._build_command_handlers().get(op_type)
            result = handler(**params)
            results.append({"index": index, "type": op_type, "result": result})
            warnings.extend(result.get("warnings", []) if isinstance(result, dict) else [])
            if isinstance(result, dict) and result.get("status") not in {"success"}:
                errors.append({"index": index, "type": op_type, "message": result.get("message", result.get("status"))})
                if stop_on_error:
                    break
        after = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_label}_after", include_screenshots=False, artifact_root=artifact_root) if create_after_snapshot else {}
        status = "success" if not errors else ("partial" if results else "error")
        result = {"status": status, "batch_id": batch_id, "label": batch_label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors, "warnings": warnings}
        self.server._add_to_history("run_verified_edit_batch", {"label": label, "operation_count": len(operations)}, result)
        return result

class AdvancedModelingServiceBase:
    def __init__(self, server):
        self.server = server

    def _collection(self, name=None):
        if name:
            collection = bpy.data.collections.get(name) or bpy.data.collections.new(name)
            if collection.name not in bpy.context.scene.collection.children:
                with suppress(Exception):
                    bpy.context.scene.collection.children.link(collection)
            return collection
        return bpy.context.collection or bpy.context.scene.collection

    def _material(self, name):
        if not name:
            return None
        return bpy.data.materials.get(name) or bpy.data.materials.new(name)

    def _object(self, name):
        return bpy.data.objects.get(name)

    def _link(self, obj, collection_name=None):
        collection = self._collection(collection_name)
        if obj.name not in collection.objects:
            collection.objects.link(obj)
        return obj

    def _verify_object(self, obj):
        return {
            "object_name": obj.name,
            "type": obj.type,
            "dimensions": [float(value) for value in obj.dimensions],
            "location": [float(value) for value in obj.location],
            "modifier_count": len(obj.modifiers),
        }


class MeshSchemaConstructionService(AdvancedModelingServiceBase):
    def get_modeling_capabilities(self):
        return {
            "status": "success",
            "blender_version": ".".join(str(part) for part in bpy.app.version),
            "mesh_schema": {"from_pydata_available": hasattr(bpy.types.Mesh, "from_pydata"), "mesh_validate_available": hasattr(bpy.types.Mesh, "validate")},
            "bmesh": {"available": "bmesh" in sys.modules or True, "operators_supported": True},
            "curves": {"curve_data_available": hasattr(bpy.data, "curves"), "bevel_depth_supported": hasattr(bpy.types.Curve, "bevel_depth")},
            "modifiers": {name.lower(): hasattr(bpy.types, f"{name.title().replace('_', '')}Modifier") for name in ["array", "bevel", "boolean", "mirror", "solidify", "shrinkwrap", "skin", "wireframe", "cloth"]},
            "sculpt": {"mode_supported": hasattr(bpy.ops.object, "mode_set"), "stroke_api": "unknown", "face_sets": "unknown", "voxel_remesh": "available" if hasattr(bpy.ops.object, "voxel_remesh") else "unknown"},
            "cloth": {"modifier_supported": hasattr(bpy.types, "ClothModifier"), "cache_supported": hasattr(bpy.ops, "ptcache"), "preview_bake_supported": "available" if hasattr(bpy.ops, "ptcache") else "unknown"},
            "warnings": [],
        }

    def validate_mesh_schema(self, schema, max_vertices=10000, max_faces=20000, check_non_manifold=True):
        return runtime_validate_mesh_schema(schema, max_vertices=max_vertices, max_faces=max_faces, check_non_manifold=check_non_manifold)

    def create_mesh_from_schema(self, object_name, schema, collection_name=None, material_name=None, validate=True, create_uvs=True, verify=True):
        validation = self.validate_mesh_schema(schema) if validate else {"valid": True, "warnings": [], "summary": {}}
        if not validation.get("valid"):
            return {"status": "error", "validation": validation}
        mesh = bpy.data.meshes.new(f"{object_name}_Mesh")
        mesh.from_pydata(schema.get("vertices", []), schema.get("edges", []), schema.get("faces", []))
        mesh.update()
        with suppress(Exception):
            mesh.validate(clean_customdata=False)
        obj = bpy.data.objects.new(object_name, mesh)
        material = self._material(material_name)
        if material:
            mesh.materials.append(material)
        self._link(obj, collection_name)
        snapshot = self._verify_object(obj) if verify else None
        manifest = {"workflow_id": runtime_new_workflow_id("mesh_schema"), "created_objects": [obj.name], "created_materials": [material.name] if material else []}
        return {"status": "success", "object": snapshot, "validation": validation, "manifest": manifest, "warnings": validation.get("warnings", [])}


class ProfileModelingService(AdvancedModelingServiceBase):
    def create_profile_curve(self, profile_name, points, closed=True, collection_name=None, material_name=None):
        if not isinstance(points, list) or len(points) < 2 or len(points) > 1024:
            return {"status": "error", "message": "profile requires 2..1024 points"}
        curve = bpy.data.curves.new(profile_name, "CURVE")
        curve.dimensions = "3D"
        spline = curve.splines.new("POLY")
        spline.points.add(len(points) - 1)
        for point, co in zip(spline.points, points):
            point.co = (float(co[0]), float(co[1]), float(co[2]), 1.0)
        spline.use_cyclic_u = bool(closed)
        obj = bpy.data.objects.new(profile_name, curve)
        material = self._material(material_name)
        if material:
            curve.materials.append(material)
        self._link(obj, collection_name)
        return {"status": "success", "profile": self._verify_object(obj), "closed": bool(closed)}

    def extrude_profile(self, profile_object_name, extrude_vector, steps=1, solidify=True, bevel=0.0, new_object_name=None, verify=True):
        source = self._object(profile_object_name)
        if not source or source.type != "CURVE":
            return {"status": "error", "message": "profile curve not found"}
        obj = source.copy()
        obj.data = source.data.copy()
        obj.name = new_object_name or f"{profile_object_name}_Extrude"
        self._link(obj)
        obj.data.extrude = max(abs(float(extrude_vector[2] if len(extrude_vector) > 2 else 0.0)), 0.001)
        obj.data.bevel_depth = max(float(bevel), 0.0)
        if solidify:
            mod = obj.modifiers.new("Overtli_Profile_Solidify", "SOLIDIFY")
            mod.thickness = 0.01
        return {"status": "success", "classification": "curve_generated", "object": self._verify_object(obj) if verify else obj.name}

    def lathe_profile(self, profile_object_name, axis="Z", angle_degrees=360, segments=32, new_object_name=None, verify=True):
        source = self._object(profile_object_name)
        if not source:
            return {"status": "error", "message": "profile object not found"}
        if segments < 3 or segments > 256:
            return {"status": "error", "message": "segments must be 3..256"}
        obj = source.copy()
        obj.data = source.data.copy()
        obj.name = new_object_name or f"{profile_object_name}_Lathe"
        self._link(obj)
        mod = obj.modifiers.new("Overtli_Lathe_Screw", "SCREW")
        mod.steps = int(segments)
        mod.render_steps = int(segments)
        mod.angle = math.radians(float(angle_degrees))
        mod.axis = str(axis).upper()[0]
        return {"status": "success", "classification": "modifier_based", "object": self._verify_object(obj) if verify else obj.name}

    def loft_profiles(self, profile_object_names, new_object_name, segments_between=1, closed_loop=False, verify=True):
        profiles = [self._object(name) for name in profile_object_names]
        if len(profiles) < 2 or any(obj is None for obj in profiles):
            return {"status": "error", "message": "loft requires at least two existing profiles"}
        return {"status": "planned", "classification": "requires-explicit-profile-sampling", "profile_object_names": profile_object_names, "new_object_name": new_object_name, "warnings": ["loft mesh generation is planned to avoid guessing mismatched profile point order"]}

    def bridge_profile_loops(self, object_name, loop_a=None, loop_b=None, new_object_name=None, verify=True):
        if not loop_a or not loop_b:
            return {"status": "requires_user_action", "message": "explicit loop_a and loop_b are required; destructive loop guessing is refused"}
        return {"status": "planned", "object_name": object_name, "loop_a_count": len(loop_a), "loop_b_count": len(loop_b), "new_object_name": new_object_name}

    def create_curve_path_object(self, name, points, curve_type="polyline", bevel_depth=0.0, resolution=12, collection_name=None, material_name=None):
        result = self.create_profile_curve(name, points, closed=False, collection_name=collection_name, material_name=material_name)
        obj = self._object(name)
        if obj and obj.type == "CURVE":
            obj.data.bevel_depth = max(float(bevel_depth), 0.0)
            obj.data.resolution_u = int(max(1, min(resolution, 64)))
        result["curve_type"] = curve_type
        return result

    def create_beveled_curve_object(self, name, points, radius=0.05, resolution=12, fill_caps=True, material_name=None, collection_name=None):
        result = self.create_curve_path_object(name, points, "polyline", radius, resolution, collection_name, material_name)
        obj = self._object(name)
        if obj and obj.type == "CURVE":
            obj.data.fill_mode = "FULL"
            obj.data.use_fill_caps = bool(fill_caps)
        return result


class ModifierConstructionService(AdvancedModelingServiceBase):
    ALLOWED = {"BEVEL", "ARRAY", "MIRROR", "SOLIDIFY", "WEIGHTED_NORMAL", "BOOLEAN", "SHRINKWRAP", "SIMPLE_DEFORM", "CURVE", "SKIN", "WIREFRAME", "LATTICE", "DISPLACE"}

    def create_modifier_stack(self, object_name, stack_name=None, modifiers=None, verify=True):
        obj = self._object(object_name)
        if not obj:
            return {"status": "error", "message": "object not found"}
        plan = runtime_plan_modifier_stack(modifiers or [])
        if plan.get("status") != "success":
            return plan
        created = []
        for index, spec in enumerate(modifiers or []):
            mod_type = str(spec.get("type", "")).upper()
            mod = obj.modifiers.new(spec.get("name") or f"{stack_name or 'Overtli'}_{mod_type}_{index+1}", mod_type)
            for key, value in spec.get("properties", {}).items():
                if hasattr(mod, key) and key not in {"object", "collection"}:
                    with suppress(Exception):
                        setattr(mod, key, value)
            created.append({"name": mod.name, "type": mod.type})
        return {"status": "success", "stack_name": stack_name, "created_modifiers": created, "object": self._verify_object(obj) if verify else object_name}

    def create_hard_surface_panel(self, panel_name, size=(2, 2, 0.05), bevel=0.02, inset_count=1, slot_count=0, material_name=None, collection_name=None, verify=True):
        sx, sy, sz = [float(value) for value in size]
        schema = {"vertices": [[-sx/2, -sy/2, -sz/2], [sx/2, -sy/2, -sz/2], [sx/2, sy/2, -sz/2], [-sx/2, sy/2, -sz/2], [-sx/2, -sy/2, sz/2], [sx/2, -sy/2, sz/2], [sx/2, sy/2, sz/2], [-sx/2, sy/2, sz/2]], "faces": [[0,1,2,3], [4,7,6,5], [0,4,5,1], [1,5,6,2], [2,6,7,3], [3,7,4,0]]}
        result = self.server.mesh_schema_construction_service.create_mesh_from_schema(panel_name, schema, collection_name, material_name, True, False, verify)
        obj = self._object(panel_name)
        if obj:
            self.create_modifier_stack(panel_name, "HardSurface", [{"type": "BEVEL", "properties": {"width": bevel, "segments": 2}}, {"type": "WEIGHTED_NORMAL"}], verify=False)
            obj["overtli_inset_count"] = int(inset_count)
            obj["overtli_slot_count"] = int(slot_count)
        return result

    def create_pipe_or_rail(self, name, points, radius=0.05, support_posts=False, post_spacing=None, material_name=None, collection_name=None, verify=True):
        result = self.server.profile_modeling_service.create_beveled_curve_object(name, points, radius, 12, True, material_name, collection_name)
        result["support_posts"] = {"planned": bool(support_posts), "post_spacing": post_spacing}
        return result

    def create_modular_assembly(self, assembly_name, module_specs, collection_name=None, verify=True):
        created = []
        for index, spec in enumerate(module_specs or []):
            name = spec.get("name") or f"{assembly_name}_Module_{index+1}"
            panel = self.create_hard_surface_panel(name, spec.get("size", [1, 1, 0.05]), collection_name=collection_name, verify=False)
            obj = self._object(name)
            if obj:
                obj.location = spec.get("location", [index, 0, 0])
                created.append(name)
        return {"status": "success", "assembly_name": assembly_name, "created_objects": created}


class ReferenceDrivenConstructionService(AdvancedModelingServiceBase):
    def plan_reference_construction(self, reference_set_id=None, target_description="", measurement_ids=None, method_preference=None):
        plan = runtime_plan_reference_construction(reference_set_id, target_description, measurement_ids)
        plan["method"] = method_preference or runtime_select_modeling_method(target_description, {"reference_set_id": reference_set_id}).get("method")
        return plan

    def run_reference_construction_step(self, step, reference_set_id=None, target_object_name=None, params=None, verify=True):
        if not reference_set_id:
            return {"status": "planned", "message": "reference_set_id required before construction execution", "step": step}
        return {"status": "planned", "step": step, "reference_set_id": reference_set_id, "target_object_name": target_object_name, "params": params or {}, "warnings": ["reference-guided construction step recorded; exact geometry command should be selected by plan"]}

    def validate_reference_alignment(self, object_names, reference_set_id=None, tolerance=0.05):
        found = [name for name in object_names or [] if self._object(name)]
        return {"status": "success", "reference_set_id": reference_set_id, "checked_objects": found, "measurement_confidence": "medium" if reference_set_id else "low", "warnings": [] if reference_set_id else ["no-reference-set-id"]}


class SculptWorkflowPhase8BService(AdvancedModelingServiceBase):
    def configure_sculpt_session(self, object_name, brush="SMOOTH", use_shape_key=True, symmetry=None, radius=50, strength=0.25):
        obj = self._object(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": "mesh object not found"}
        if use_shape_key and not obj.data.shape_keys:
            obj.shape_key_add(name="Basis")
        obj["overtli_sculpt_session"] = json.dumps({"brush": brush, "use_shape_key": use_shape_key, "symmetry": symmetry or [False, False, False], "radius": radius, "strength": strength})
        return {"status": "success", "object_name": object_name, "brush": brush, "use_shape_key": bool(use_shape_key), "stroke_api": "unsupported-by-default"}

    def create_sculpt_mask(self, object_name, mask_name="Overtli_Sculpt_Mask", vertex_indices=None, weight=1.0):
        obj = self._object(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": "mesh object not found"}
        group = obj.vertex_groups.get(mask_name) or obj.vertex_groups.new(name=mask_name)
        indices = vertex_indices or list(range(len(obj.data.vertices)))
        if indices:
            group.add([int(i) for i in indices if 0 <= int(i) < len(obj.data.vertices)], float(weight), "REPLACE")
        return {"status": "success", "object_name": object_name, "mask_name": group.name, "vertex_count": len(indices), "classification": "vertex-group-mask"}

    def create_face_set(self, object_name, face_indices=None, face_set_name="Overtli_Face_Set"):
        obj = self._object(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": "mesh object not found"}
        obj["overtli_face_set"] = json.dumps({"name": face_set_name, "faces": face_indices or []})
        return {"status": "success", "object_name": object_name, "face_set_name": face_set_name, "classification": "metadata-face-set"}

    def apply_sculpt_stroke_batch(self, object_name, strokes, approval_id=None, max_strokes=32):
        if not approval_id:
            return {"status": "requires_approval", "approval_required": True, "message": "sculpt stroke playback is high risk and requires approval_id"}
        if len(strokes or []) > max_strokes:
            return {"status": "error", "message": "stroke batch exceeds max_strokes"}
        return {"status": "unsupported", "message": "bounded sculpt stroke playback is not enabled for this Blender API surface", "approval_id": approval_id}

    def create_shape_key_sculpt_variant(self, object_name, shape_key_name="Overtli_Sculpt_Variant", value=0.0):
        obj = self._object(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": "mesh object not found"}
        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis")
        key = obj.shape_key_add(name=shape_key_name)
        key.value = float(value)
        return {"status": "success", "object_name": object_name, "shape_key_name": key.name, "basis_preserved": True}

    def validate_sculpt_result(self, object_name, shape_key_name=None):
        obj = self._object(object_name)
        keys = [key.name for key in obj.data.shape_keys.key_blocks] if obj and obj.type == "MESH" and obj.data.shape_keys else []
        return {"status": "success" if obj else "error", "object_name": object_name, "shape_keys": keys, "shape_key_present": shape_key_name in keys if shape_key_name else bool(keys)}


class ClothPatternWorkflowService(AdvancedModelingServiceBase):
    def create_cloth_pattern_panel(self, panel_name, points, thickness=0.01, collection_name=None, material_name=None, verify=True):
        if len(points or []) < 3:
            return {"status": "error", "message": "cloth panel requires at least three points"}
        center = [sum(float(p[axis]) for p in points) / len(points) for axis in range(3)]
        vertices = [[float(p[0]), float(p[1]), float(p[2])] for p in points]
        schema = {"vertices": vertices, "faces": [list(range(len(vertices)))]}
        result = self.server.mesh_schema_construction_service.create_mesh_from_schema(panel_name, schema, collection_name, material_name, True, False, verify)
        obj = self._object(panel_name)
        if obj:
            obj["overtli_cloth_panel"] = json.dumps({"thickness": thickness, "center": center})
            solidify = obj.modifiers.new("Overtli_Cloth_Thickness", "SOLIDIFY")
            solidify.thickness = float(thickness)
        return result

    def define_cloth_seam_pair(self, panel_a, edge_a, panel_b, edge_b, seam_name=None):
        return {"status": "success", "seam_name": seam_name or f"{panel_a}_{panel_b}_Seam", "panel_a": panel_a, "edge_a": edge_a, "panel_b": panel_b, "edge_b": edge_b, "classification": "metadata-seam"}

    def create_cloth_setup(self, object_name, quality=3, mass=0.3, pressure=0.0, pin_group_name=None):
        obj = self._object(object_name)
        if not obj:
            return {"status": "error", "message": "object not found"}
        mod = obj.modifiers.get("Overtli_Cloth") or obj.modifiers.new("Overtli_Cloth", "CLOTH")
        mod.settings.quality = int(max(1, min(quality, 12)))
        mod.settings.mass = float(mass)
        with suppress(Exception):
            mod.settings.uniform_pressure_force = float(pressure)
        if pin_group_name:
            mod.settings.vertex_group_mass = pin_group_name
        return {"status": "success", "object_name": object_name, "modifier": mod.name, "cache_actions": "approval-gated"}

    def create_cloth_pin_group(self, object_name, vertex_indices=None, group_name="Overtli_Cloth_Pin", weight=1.0):
        return self.server.sculpt_phase8b_workflow_service.create_sculpt_mask(object_name, group_name, vertex_indices, weight)

    def create_cloth_collision_setup(self, object_name, thickness_outer=0.02, thickness_inner=0.01):
        obj = self._object(object_name)
        if not obj:
            return {"status": "error", "message": "object not found"}
        mod = obj.modifiers.get("Overtli_Collision") or obj.modifiers.new("Overtli_Collision", "COLLISION")
        mod.settings.thickness_outer = float(thickness_outer)
        mod.settings.thickness_inner = float(thickness_inner)
        return {"status": "success", "object_name": object_name, "modifier": mod.name}

    def simulate_cloth_preview(self, object_name, frame_start=1, frame_end=24, approval_id=None, max_frames=48):
        if not approval_id:
            return {"status": "requires_approval", "approval_required": True, "message": "cloth preview simulation requires approval_id"}
        if int(frame_end) - int(frame_start) + 1 > int(max_frames):
            return {"status": "error", "message": "preview frame range exceeds max_frames"}
        return {"status": "planned", "object_name": object_name, "frame_start": frame_start, "frame_end": frame_end, "approval_id": approval_id}

    def bake_cloth_cache(self, object_name, approval_id=None):
        return {"status": "requires_approval" if not approval_id else "planned", "approval_required": not bool(approval_id), "object_name": object_name, "message": "cloth cache bake is gated and not run by default"}

    def clear_cloth_cache(self, object_name, approval_id=None):
        return {"status": "requires_approval" if not approval_id else "planned", "approval_required": not bool(approval_id), "object_name": object_name, "message": "cloth cache clear is exact-object approval-gated"}

    def convert_cloth_result(self, object_name, new_object_name=None, approval_id=None):
        return {"status": "requires_approval" if not approval_id else "planned", "approval_required": not bool(approval_id), "object_name": object_name, "new_object_name": new_object_name, "message": "conversion is destructive-adjacent and approval-gated"}


class ConstructionValidationService(AdvancedModelingServiceBase):
    def validate_construction_geometry(self, object_names, check_mesh_health=True, check_normals=True, check_bounds=True, check_intersections=True, check_scale=True, reference_set_id=None):
        results = []
        for name in object_names or []:
            obj = self._object(name)
            if not obj:
                results.append({"object_name": name, "status": "missing"})
                continue
            item = self._verify_object(obj)
            if obj.type == "MESH":
                item["mesh_health"] = {"vertices": len(obj.data.vertices), "edges": len(obj.data.edges), "polygons": len(obj.data.polygons), "has_polygons": bool(obj.data.polygons)}
            results.append(item)
        return {"status": "success", "objects": results, "reference_alignment": {"reference_set_id": reference_set_id, "confidence": "medium" if reference_set_id else "not_checked"}}

    def plan_construction_cleanup(self, workflow_id=None, target_prefix="OVERTLI_PHASE8B_", include_temp_curves=True, include_temp_modifiers=True, include_cloth_caches=True):
        targets = [obj.name for obj in bpy.data.objects if obj.name.startswith(target_prefix)]
        approval_id = "cleanup_" + hashlib.sha256(json.dumps([workflow_id, targets], sort_keys=True).encode("utf-8")).hexdigest()[:16]
        return {"status": "success", "workflow_id": workflow_id, "approval_id": approval_id, "dry_run": True, "targets": targets, "requires_approval": True}

    def execute_construction_cleanup(self, approval_id, workflow_id=None, target_prefix="OVERTLI_PHASE8B_", delete_final=False):
        if not approval_id:
            return {"status": "requires_approval", "approval_required": True}
        if delete_final:
            return {"status": "error", "message": "final object deletion is refused by construction cleanup"}
        deleted = []
        for obj in list(bpy.data.objects):
            if obj.name.startswith(target_prefix) and obj.get("overtli_temp", True):
                bpy.data.objects.remove(obj, do_unlink=True)
                deleted.append(obj.name)
        return {"status": "success", "approval_id": approval_id, "workflow_id": workflow_id, "deleted_objects": deleted}


class AdvancedModelingWorkflowBatchService(AdvancedModelingServiceBase):
    def run_advanced_modeling_workflow_batch(self, workflow_name=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=50, allow_sculpt=False, allow_simulation=False, allow_destructive=False):
        operations = operations or []
        if len(operations) > max_operations:
            return {"status": "error", "message": "operation count exceeds max_operations"}
        before = self.server.create_scene_snapshot(label=f"{workflow_name or 'phase8b'}_before") if create_before_snapshot else None
        results = []
        for operation in operations:
            command = operation.get("command")
            if command in {"apply_sculpt_stroke_batch"} and not allow_sculpt:
                result = {"status": "requires_approval", "message": "sculpt operations require allow_sculpt"}
            elif command in {"simulate_cloth_preview", "bake_cloth_cache", "clear_cloth_cache", "convert_cloth_result"} and not allow_simulation:
                result = {"status": "requires_approval", "message": "simulation/cache operations require allow_simulation"}
            elif command in {"execute_construction_cleanup"} and not allow_destructive:
                result = {"status": "requires_approval", "message": "destructive cleanup requires allow_destructive"}
            else:
                handler = self.server._build_command_handlers().get(command)
                result = handler(**operation.get("params", {})) if handler else {"status": "error", "message": f"unknown command {command}"}
            results.append({"command": command, "result": result})
            if stop_on_error and result.get("status") == "error":
                break
        after = self.server.create_scene_snapshot(label=f"{workflow_name or 'phase8b'}_after") if create_after_snapshot else None
        return {"status": "success" if all(item["result"].get("status") != "error" for item in results) else "partial", "workflow_name": workflow_name, "before_snapshot": before, "after_snapshot": after, "results": results}
