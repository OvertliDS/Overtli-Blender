from __future__ import annotations

from ..core import *

class SceneObservationService:
    def __init__(self, server):
        self.server = server

    def get_scene_info(self):
        try:
            print("Getting scene info...")
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
            }

            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 10:
                    break
                scene_info["objects"].append({
                    "name": obj.name,
                    "type": obj.type,
                    "location": [
                        round(float(obj.location.x), 2),
                        round(float(obj.location.y), 2),
                        round(float(obj.location.z), 2),
                    ],
                })

            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    def get_object_info(self, name):
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "materials": [],
        }

        if obj.type == "MESH":
            obj_info["world_bounding_box"] = self.server._get_aabb(obj)

        for slot in obj.material_slots:
            if slot.material:
                obj_info["materials"].append(slot.material.name)

        if obj.type == "MESH" and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }

        return obj_info


class ViewportScreenshotService:
    def __init__(self, server):
        self.server = server

    def get_viewport_screenshot(self, max_size=800, filepath=None, format="png"):
        try:
            if not filepath:
                return {"error": "No filepath provided"}

            area = None
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    area = a
                    break

            if not area:
                return {"error": "No 3D viewport found"}

            with bpy.context.temp_override(area=area):
                bpy.ops.screen.screenshot_area(filepath=filepath)

            img = bpy.data.images.load(filepath)
            width, height = img.size

            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img.scale(new_width, new_height)
                img.file_format = format.upper()
                img.save()
                width, height = new_width, new_height

            bpy.data.images.remove(img)

            return {
                "success": True,
                "width": width,
                "height": height,
                "filepath": filepath
            }
        except Exception as e:
            return {"error": str(e)}


class SceneIntelligenceService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _vector(value, digits=4):
        return [round(float(component), digits) for component in value]

    @staticmethod
    def _matrix(value, digits=4):
        return [[round(float(component), digits) for component in row] for row in value]

    @staticmethod
    def _collection_names(obj):
        return [collection.name for collection in getattr(obj, "users_collection", [])]

    @staticmethod
    def _material_names(obj):
        names = []
        for slot in getattr(obj, "material_slots", []):
            if slot.material:
                names.append(slot.material.name)
        return names

    @staticmethod
    def _modifier_names(obj):
        return [modifier.name for modifier in getattr(obj, "modifiers", [])]

    @staticmethod
    def _constraint_names(obj):
        return [constraint.name for constraint in getattr(obj, "constraints", [])]

    def _world_bounds(self, obj):
        if not hasattr(obj, "bound_box") or not obj.bound_box:
            return None

        corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        if not corners:
            return None

        min_corner = [min(corner[index] for corner in corners) for index in range(3)]
        max_corner = [max(corner[index] for corner in corners) for index in range(3)]
        center = [(min_corner[index] + max_corner[index]) / 2 for index in range(3)]
        size = [max_corner[index] - min_corner[index] for index in range(3)]
        return {
            "min": self._vector(min_corner),
            "max": self._vector(max_corner),
            "center": self._vector(center),
            "size": self._vector(size),
        }

    def _object_summary(self, obj, include_materials=True, include_modifiers=True, include_constraints=True):
        active = bpy.context.view_layer.objects.active
        summary = {
            "name": obj.name,
            "type": obj.type,
            "visible": bool(obj.visible_get()),
            "hidden_viewport": bool(obj.hide_viewport),
            "selected": bool(obj.select_get()),
            "active": active == obj,
            "collection_names": self._collection_names(obj),
            "parent": obj.parent.name if obj.parent else None,
            "children": [child.name for child in obj.children],
            "location": self._vector(obj.location),
            "rotation_euler": self._vector(obj.rotation_euler),
            "scale": self._vector(obj.scale),
            "dimensions": self._vector(obj.dimensions),
            "bound_box_world": self._world_bounds(obj),
        }
        if include_materials:
            summary["material_names"] = self._material_names(obj)
        if include_modifiers:
            summary["modifier_names"] = self._modifier_names(obj)
        if include_constraints:
            summary["constraint_names"] = self._constraint_names(obj)
        return summary

    def _collection_summary(self, collection):
        return {
            "name": collection.name,
            "object_count": len(collection.objects),
            "children": [child.name for child in collection.children],
            "hide_viewport": bool(collection.hide_viewport),
        }

    def _material_summary(self, material):
        return {
            "name": material.name,
            "use_nodes": bool(material.use_nodes),
            "users": int(material.users),
        }

    def get_scene_index(
        self,
        include_hidden=True,
        include_materials=True,
        include_modifiers=True,
        include_constraints=True,
        include_collections=True,
        max_objects=None,
    ):
        warnings = []
        scene = bpy.context.scene
        objects = list(scene.objects)
        if not include_hidden:
            objects = [obj for obj in objects if obj.visible_get()]

        truncated = False
        if max_objects is not None:
            try:
                max_count = max(0, int(max_objects))
                if len(objects) > max_count:
                    objects = objects[:max_count]
                    truncated = True
                    warnings.append(f"Scene index truncated to {max_count} objects")
            except (TypeError, ValueError):
                warnings.append(f"Ignoring invalid max_objects value: {max_objects!r}")

        scene_data = {
            "name": scene.name,
            "frame_current": int(scene.frame_current),
            "frame_start": int(scene.frame_start),
            "frame_end": int(scene.frame_end),
            "unit_system": scene.unit_settings.system,
            "render_engine": scene.render.engine,
            "object_count": len(scene.objects),
            "collection_count": len(bpy.data.collections),
            "material_count": len(bpy.data.materials),
            "camera_count": sum(1 for obj in scene.objects if obj.type == "CAMERA"),
            "light_count": sum(1 for obj in scene.objects if obj.type == "LIGHT"),
        }

        return {
            "status": "success",
            "scene": scene_data,
            "objects": [
                self._object_summary(obj, include_materials, include_modifiers, include_constraints)
                for obj in objects
            ],
            "collections": [self._collection_summary(collection) for collection in bpy.data.collections] if include_collections else [],
            "materials": [self._material_summary(material) for material in bpy.data.materials] if include_materials else [],
            "warnings": warnings,
            "truncated": truncated,
        }

    def _mesh_stats(self, obj):
        mesh = obj.data
        return {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "triangles_estimate": sum(max(1, len(poly.vertices) - 2) for poly in mesh.polygons),
        }

    def _modifier_details(self, obj):
        return [
            {
                "name": modifier.name,
                "type": modifier.type,
                "show_viewport": bool(modifier.show_viewport),
                "show_render": bool(modifier.show_render),
            }
            for modifier in getattr(obj, "modifiers", [])
        ]

    def _constraint_details(self, obj):
        return [
            {
                "name": constraint.name,
                "type": constraint.type,
                "mute": bool(constraint.mute),
                "influence": round(float(constraint.influence), 4),
            }
            for constraint in getattr(obj, "constraints", [])
        ]

    def _material_slots(self, obj):
        materials = []
        for index, slot in enumerate(getattr(obj, "material_slots", [])):
            material = slot.material
            materials.append({
                "slot_index": index,
                "slot_name": slot.name,
                "material_name": material.name if material else None,
                "use_nodes": bool(material.use_nodes) if material else False,
            })
        return materials

    def _animation_summary(self, obj):
        animation_data = obj.animation_data
        if not animation_data:
            return {"has_animation_data": False}
        action = animation_data.action
        return {
            "has_animation_data": True,
            "action": action.name if action else None,
            "fcurve_count": len(phase9a_action_fcurves(action)) if action else 0,
            "nla_track_count": len(animation_data.nla_tracks),
        }

    def _custom_properties(self, obj):
        properties = {}
        for key in obj.keys():
            if key == "_RNA_UI":
                continue
            value = obj.get(key)
            if isinstance(value, (str, int, float, bool)) or value is None:
                properties[key] = value
            else:
                properties[key] = str(value)
        return properties

    def _type_specific_info(self, obj):
        data = getattr(obj, "data", None)
        if obj.type == "CAMERA" and data:
            return {
                "lens": round(float(data.lens), 4),
                "sensor_width": round(float(data.sensor_width), 4),
                "clip_start": round(float(data.clip_start), 4),
                "clip_end": round(float(data.clip_end), 4),
                "dof_enabled": bool(data.dof.use_dof),
            }
        if obj.type == "LIGHT" and data:
            return {
                "light_type": data.type,
                "energy": round(float(data.energy), 4),
                "color": self._vector(data.color),
                "use_shadow": bool(getattr(data, "use_shadow", False)),
            }
        if obj.type == "CURVE" and data:
            return {"spline_count": len(data.splines), "dimensions": data.dimensions}
        if obj.type == "ARMATURE" and data:
            return {"bone_count": len(data.bones)}
        if obj.type == "EMPTY":
            return {"empty_display_type": obj.empty_display_type}
        return {}

    def get_object_deep_info(
        self,
        object_name=None,
        name=None,
        include_mesh_stats=True,
        include_material_slots=True,
        include_modifiers=True,
        include_constraints=True,
        include_animation=True,
        include_custom_properties=True,
    ):
        target_name = object_name or name
        if not target_name:
            return {"status": "error", "message": "object_name is required"}

        obj = bpy.data.objects.get(target_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {target_name}"}

        info = {
            "name": obj.name,
            "type": obj.type,
            "data_name": obj.data.name if getattr(obj, "data", None) else None,
            "parent": obj.parent.name if obj.parent else None,
            "children": [child.name for child in obj.children],
            "collection_names": self._collection_names(obj),
            "visible": bool(obj.visible_get()),
            "selected": bool(obj.select_get()),
            "active": bpy.context.view_layer.objects.active == obj,
            "transform": {
                "location": self._vector(obj.location),
                "rotation_euler": self._vector(obj.rotation_euler),
                "scale": self._vector(obj.scale),
                "matrix_world": self._matrix(obj.matrix_world),
            },
            "dimensions": self._vector(obj.dimensions),
            "bounding_box": self._world_bounds(obj),
            "type_specific": self._type_specific_info(obj),
        }
        if include_mesh_stats and obj.type == "MESH" and obj.data:
            info["mesh_stats"] = self._mesh_stats(obj)
        if include_material_slots:
            info["materials"] = self._material_slots(obj)
        if include_modifiers:
            info["modifiers"] = self._modifier_details(obj)
        if include_constraints:
            info["constraints"] = self._constraint_details(obj)
        if include_animation:
            info["animation"] = self._animation_summary(obj)
        if include_custom_properties:
            info["custom_properties"] = self._custom_properties(obj)

        return {"status": "success", "object": info, "warnings": []}

    def get_selection_info(self):
        selected = list(bpy.context.selected_objects)
        active = bpy.context.view_layer.objects.active
        bounds = None
        warnings = []

        if selected:
            object_bounds = [self._world_bounds(obj) for obj in selected]
            object_bounds = [bound for bound in object_bounds if bound]
            if object_bounds:
                min_corner = [min(bound["min"][index] for bound in object_bounds) for index in range(3)]
                max_corner = [max(bound["max"][index] for bound in object_bounds) for index in range(3)]
                center = [(min_corner[index] + max_corner[index]) / 2 for index in range(3)]
                size = [max_corner[index] - min_corner[index] for index in range(3)]
                bounds = {
                    "min": self._vector(min_corner),
                    "max": self._vector(max_corner),
                    "center": self._vector(center),
                    "size": self._vector(size),
                }

        mode = getattr(bpy.context, "mode", "UNKNOWN")
        if mode != "OBJECT":
            warnings.append("Edit-mode component selection details are not implemented; object selection was reported without changing mode")

        return {
            "status": "success",
            "active_object": active.name if active else None,
            "selected_objects": [obj.name for obj in selected],
            "selected_count": len(selected),
            "mode": mode,
            "selection_bounds": bounds,
            "objects": [
                {
                    "name": obj.name,
                    "type": obj.type,
                    "visible": bool(obj.visible_get()),
                    "dimensions": self._vector(obj.dimensions),
                }
                for obj in selected
            ],
            "warnings": warnings,
        }

    def get_scene_health(self):
        scene = bpy.context.scene
        objects = list(scene.objects)
        mesh_objects = [obj for obj in objects if obj.type == "MESH"]
        hidden = [obj for obj in objects if obj.hide_viewport or not obj.visible_get()]
        no_material = [obj for obj in mesh_objects if not self._material_names(obj)]
        negative_scale = [obj for obj in objects if any(float(axis) < 0 for axis in obj.scale)]
        unapplied_scale = [obj for obj in objects if any(abs(float(axis) - 1.0) > 0.001 for axis in obj.scale)]
        missing_mesh_data = [obj for obj in mesh_objects if obj.data is None]
        far_from_origin = [obj for obj in objects if obj.location.length > 10000]
        empty_collections = [collection for collection in bpy.data.collections if len(collection.objects) == 0 and len(collection.children) == 0]
        issues = []

        def add_issue(severity, code, message, issue_objects=None):
            issues.append({
                "severity": severity,
                "code": code,
                "message": message,
                "objects": [obj.name for obj in issue_objects or []],
            })

        if not any(obj.type == "CAMERA" for obj in objects):
            add_issue("warning", "NO_CAMERA", "Scene has no camera")
        if not any(obj.type == "LIGHT" for obj in objects):
            add_issue("info", "NO_LIGHTS", "Scene has no lights")
        if no_material:
            add_issue("info", "MISSING_MATERIALS", f"{len(no_material)} mesh object(s) have no material slots", no_material[:20])
        if hidden:
            add_issue("info", "HIDDEN_OBJECTS", f"{len(hidden)} object(s) are hidden or not visible in viewport", hidden[:20])
        if len(objects) > 1000:
            add_issue("warning", "LARGE_OBJECT_COUNT", f"Scene has {len(objects)} objects")
        if negative_scale:
            add_issue("warning", "NEGATIVE_SCALE", f"{len(negative_scale)} object(s) have negative scale", negative_scale[:20])
        if unapplied_scale:
            add_issue("info", "UNAPPLIED_SCALE", f"{len(unapplied_scale)} object(s) have scale different from 1.0", unapplied_scale[:20])
        if missing_mesh_data:
            add_issue("error", "MISSING_MESH_DATA", f"{len(missing_mesh_data)} mesh object(s) have missing mesh data", missing_mesh_data[:20])
        if empty_collections:
            issues.append({
                "severity": "info",
                "code": "EMPTY_COLLECTIONS",
                "message": f"{len(empty_collections)} empty collection(s)",
                "objects": [],
                "collections": [collection.name for collection in empty_collections[:20]],
            })
        if far_from_origin:
            add_issue("warning", "FAR_FROM_ORIGIN", f"{len(far_from_origin)} object(s) are very far from origin", far_from_origin[:20])

        summary = {
            "object_count": len(objects),
            "hidden_count": len(hidden),
            "mesh_count": len(mesh_objects),
            "material_count": len(bpy.data.materials),
            "missing_material_objects": len(no_material),
            "camera_count": sum(1 for obj in objects if obj.type == "CAMERA"),
            "light_count": sum(1 for obj in objects if obj.type == "LIGHT"),
            "objects_with_negative_scale": len(negative_scale),
            "objects_with_unapplied_scale": len(unapplied_scale),
            "objects_with_modifiers": sum(1 for obj in objects if len(getattr(obj, "modifiers", [])) > 0),
        }
        return {"status": "success", "summary": summary, "issues": issues, "warnings": []}
