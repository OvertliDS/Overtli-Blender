from __future__ import annotations

from ..core import *

class SelectionIntelligenceService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _vec(value):
        return [float(value[0]), float(value[1]), float(value[2])]

    @staticmethod
    def _bounds_from_points(points):
        if not points:
            return {"min": [], "max": [], "center": [], "size": []}
        mins = [min(point[i] for point in points) for i in range(3)]
        maxs = [max(point[i] for point in points) for i in range(3)]
        center = [(mins[i] + maxs[i]) / 2.0 for i in range(3)]
        size = [maxs[i] - mins[i] for i in range(3)]
        return {"min": mins, "max": maxs, "center": center, "size": size}

    def _object_bounds(self, objects):
        points = []
        for obj in objects:
            if getattr(obj, "bound_box", None):
                points.extend([obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box])
        return self._bounds_from_points(points)

    def _component_selection(self, obj, max_components):
        if not obj or obj.type != "MESH":
            return {"available": False, "warnings": ["active object is not a mesh"]}
        if bpy.context.mode != "EDIT_MESH":
            return {"available": False, "object_name": obj.name, "mode": bpy.context.mode, "warnings": ["component selection requires EDIT_MESH mode"]}
        try:
            import bmesh
            bm = bmesh.from_edit_mesh(obj.data)
            selected_vertices = [vert.index for vert in bm.verts if vert.select]
            selected_edges = [edge.index for edge in bm.edges if edge.select]
            selected_faces = [face.index for face in bm.faces if face.select]
            truncated = any(len(items) > max_components for items in [selected_vertices, selected_edges, selected_faces])
            return {
                "available": True,
                "object_name": obj.name,
                "mode": bpy.context.mode,
                "selected_vertices": {"count": len(selected_vertices), "indices": selected_vertices[:max_components]},
                "selected_edges": {"count": len(selected_edges), "indices": selected_edges[:max_components]},
                "selected_faces": {"count": len(selected_faces), "indices": selected_faces[:max_components]},
                "truncated": truncated,
                "warnings": [],
            }
        except Exception as exc:
            return {"available": False, "object_name": obj.name, "mode": bpy.context.mode, "warnings": [f"component selection unavailable: {exc}"]}

    def get_selection_deep_info(self, include_components=True, include_bounds=True, include_material_slots=True, include_vertex_groups=True, max_components=500):
        selected = list(bpy.context.selected_objects or [])
        active = bpy.context.view_layer.objects.active
        max_components = max(1, min(int(max_components or 500), 5000))
        result = {
            "status": "success",
            "mode": bpy.context.mode,
            "active_object": active.name if active else None,
            "selected_objects": [obj.name for obj in selected],
            "selected_count": len(selected),
            "object_selection_bounds": self._object_bounds(selected) if include_bounds else {},
            "component_selection": {"available": False, "warnings": ["component inspection disabled"]},
            "material_slots": [],
            "vertex_groups": [],
            "warnings": [],
        }
        if include_components:
            result["component_selection"] = self._component_selection(active, max_components)
            result["warnings"].extend(result["component_selection"].get("warnings", []))
        if active and active.type == "MESH" and include_material_slots:
            result["material_slots"] = [{"index": idx, "name": slot.material.name if slot.material else None} for idx, slot in enumerate(active.material_slots)]
        if active and active.type == "MESH" and include_vertex_groups:
            result["vertex_groups"] = [{"index": group.index, "name": group.name} for group in active.vertex_groups]
        return result

    def get_mesh_component_summary(self, object_name, include_bounds=True, include_material_faces=True, include_vertex_group_stats=True, include_shape_key_stats=True):
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        mesh = obj.data
        result = {
            "status": "success",
            "object_name": obj.name,
            "mesh_stats": {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "faces": len(mesh.polygons),
                "triangles_estimate": sum(max(1, len(poly.vertices) - 2) for poly in mesh.polygons),
            },
            "bounds": self._object_bounds([obj]) if include_bounds else {},
            "material_face_counts": {},
            "vertex_group_count": len(obj.vertex_groups) if include_vertex_group_stats else 0,
            "shape_key_count": len(mesh.shape_keys.key_blocks) if include_shape_key_stats and mesh.shape_keys else 0,
            "warnings": [],
        }
        if include_material_faces:
            counts = {}
            for poly in mesh.polygons:
                key = str(poly.material_index)
                counts[key] = counts.get(key, 0) + 1
            result["material_face_counts"] = counts
        return result


class VertexGroupService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _clamp(value, minimum=0.0, maximum=1.0):
        return max(minimum, min(maximum, float(value)))

    def _mesh_object(self, object_name):
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return None
        return obj

    def _indices_from_rule(self, obj, selection_mode, indices=None, rule=None):
        mesh = obj.data
        rule = rule or {}
        mode = str(selection_mode or "all").lower()
        if mode == "all":
            return list(range(len(mesh.vertices)))
        if mode == "indices":
            selected = [int(index) for index in (indices or [])]
            bad = [index for index in selected if index < 0 or index >= len(mesh.vertices)]
            if bad:
                raise ValueError(f"Vertex indices out of range: {bad[:10]}")
            return sorted(set(selected))
        if mode == "selected_vertices":
            if bpy.context.mode != "EDIT_MESH" or bpy.context.view_layer.objects.active != obj:
                raise ValueError("selected_vertices requires target object to be active in EDIT_MESH mode")
            import bmesh
            bm = bmesh.from_edit_mesh(mesh)
            return [vert.index for vert in bm.verts if vert.select]
        if mode == "by_axis":
            axis = str(rule.get("axis", "z")).lower()
            axis_index = {"x": 0, "y": 1, "z": 2}.get(axis)
            if axis_index is None:
                raise ValueError("by_axis requires axis x, y, or z")
            op = str(rule.get("operator", ">="))
            threshold = rule.get("threshold")
            coords = [vert.co[axis_index] for vert in mesh.vertices]
            if threshold is None:
                threshold = (min(coords) + max(coords)) / 2.0 if coords else 0.0
            threshold = float(threshold)
            return [vert.index for vert in mesh.vertices if (vert.co[axis_index] >= threshold if op in {">=", "above", "max"} else vert.co[axis_index] <= threshold)]
        if mode == "by_bounds":
            mins = rule.get("min")
            maxs = rule.get("max")
            if not isinstance(mins, (list, tuple)) or not isinstance(maxs, (list, tuple)) or len(mins) != 3 or len(maxs) != 3:
                raise ValueError("by_bounds requires rule.min and rule.max 3-item lists")
            return [vert.index for vert in mesh.vertices if all(float(mins[i]) <= vert.co[i] <= float(maxs[i]) for i in range(3))]
        if mode == "by_material_slot":
            slot_index = int(rule.get("slot_index", 0))
            found = set()
            for poly in mesh.polygons:
                if poly.material_index == slot_index:
                    found.update(poly.vertices)
            return sorted(found)
        if mode == "by_proximity_to_object":
            other = bpy.data.objects.get(rule.get("object_name"))
            radius = float(rule.get("radius", 1.0))
            if not other:
                raise ValueError("by_proximity_to_object requires rule.object_name")
            center = other.matrix_world.translation
            return [vert.index for vert in mesh.vertices if (obj.matrix_world @ vert.co - center).length <= radius]
        raise ValueError(f"Unsupported selection_mode: {selection_mode}")

    def _group_weight_stats(self, obj, group, max_vertices_sample=25):
        weights = []
        sample = []
        for vert in obj.data.vertices:
            for membership in vert.groups:
                if membership.group == group.index and membership.weight > 0:
                    weights.append(float(membership.weight))
                    if len(sample) < max_vertices_sample:
                        sample.append(vert.index)
        return {
            "name": group.name,
            "index": group.index,
            "nonzero_vertex_count": len(weights),
            "weight_min": min(weights) if weights else 0.0,
            "weight_max": max(weights) if weights else 0.0,
            "sample_indices": sample,
        }

    def create_vertex_group(self, object_name, group_name, selection_mode="all", indices=None, weight=1.0, replace_existing=False, rule=None):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        if not group_name:
            return {"status": "error", "message": "group_name is required", "warnings": []}
        existing = obj.vertex_groups.get(group_name)
        if existing and not replace_existing:
            return {"status": "error", "message": f"Vertex group already exists: {group_name}", "warnings": []}
        if existing:
            obj.vertex_groups.remove(existing)
        try:
            selected = self._indices_from_rule(obj, selection_mode, indices, rule)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}
        group = obj.vertex_groups.new(name=group_name)
        if selected:
            group.add(selected, self._clamp(weight), "REPLACE")
        result = {"status": "success", "object_name": obj.name, "group_name": group.name, "vertex_count": len(selected), "weight": self._clamp(weight), "selection_mode": selection_mode, "warnings": []}
        self.server._add_to_history("create_vertex_group", {"object_name": object_name, "group_name": group_name}, result)
        return result

    def update_vertex_group_weights(self, object_name, group_name, indices=None, weight=1.0, mode="replace", rule=None):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        group = obj.vertex_groups.get(group_name)
        if not group:
            return {"status": "error", "message": f"Vertex group not found: {group_name}", "warnings": []}
        try:
            selected = self._indices_from_rule(obj, "indices" if indices is not None else (rule or {}).get("selection_mode", "all"), indices, rule)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}
        op = {"replace": "REPLACE", "add": "ADD", "subtract": "SUBTRACT"}.get(str(mode).lower())
        if not op:
            return {"status": "error", "message": f"Unsupported weight update mode: {mode}", "warnings": []}
        if selected:
            group.add(selected, self._clamp(weight), op)
        result = {"status": "success", "object_name": obj.name, "group_name": group.name, "changed_count": len(selected), "mode": mode, "weight": self._clamp(weight), "warnings": []}
        self.server._add_to_history("update_vertex_group_weights", {"object_name": object_name, "group_name": group_name}, result)
        return result

    def list_vertex_groups(self, object_name, include_weights_summary=True, max_vertices_sample=25):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        groups = []
        for group in obj.vertex_groups:
            groups.append(self._group_weight_stats(obj, group, int(max_vertices_sample)) if include_weights_summary else {"name": group.name, "index": group.index})
        return {"status": "success", "object_name": obj.name, "vertex_groups": groups, "warnings": []}

    def delete_vertex_groups(self, object_name, group_names, confirm=False):
        if not confirm:
            return {"status": "error", "message": "delete_vertex_groups requires confirm=True", "deleted": [], "missing": list(group_names or []), "refused": list(group_names or []), "warnings": []}
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "deleted": [], "missing": [], "refused": list(group_names or []), "warnings": []}
        deleted, missing, refused = [], [], []
        for name in group_names or []:
            if any(token in str(name) for token in ["*", "?", "["]):
                refused.append(str(name))
                continue
            group = obj.vertex_groups.get(str(name))
            if not group:
                missing.append(str(name))
                continue
            obj.vertex_groups.remove(group)
            deleted.append(str(name))
        return {"status": "success" if not refused else "partial", "object_name": obj.name, "deleted": deleted, "missing": missing, "refused": refused, "warnings": []}


class ShapeKeyService:
    def __init__(self, server):
        self.server = server

    def _mesh_object(self, object_name):
        obj = bpy.data.objects.get(object_name)
        return obj if obj and obj.type == "MESH" else None

    def _shape_key(self, obj, name):
        return obj.data.shape_keys.key_blocks.get(name) if obj.data.shape_keys else None

    @staticmethod
    def _shape_summary(key):
        return {"name": key.name, "value": float(getattr(key, "value", 0.0)), "relative_key": key.relative_key.name if getattr(key, "relative_key", None) else None, "mute": bool(getattr(key, "mute", False))}

    def create_shape_key(self, object_name, shape_key_name, from_mix=False, replace_existing=False, value=0.0):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        if not shape_key_name:
            return {"status": "error", "message": "shape_key_name is required", "warnings": []}
        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis", from_mix=False)
        existing = self._shape_key(obj, shape_key_name)
        if existing and not replace_existing:
            return {"status": "error", "message": f"Shape key already exists: {shape_key_name}", "warnings": []}
        if existing:
            obj.active_shape_key_index = list(obj.data.shape_keys.key_blocks).index(existing)
            bpy.ops.object.shape_key_remove()
        key = obj.shape_key_add(name=shape_key_name, from_mix=bool(from_mix))
        key.value = max(-10.0, min(10.0, float(value)))
        result = {"status": "success", "object_name": obj.name, "shape_key": self._shape_summary(key), "warnings": []}
        self.server._add_to_history("create_shape_key", {"object_name": object_name, "shape_key_name": shape_key_name}, result)
        return result

    def update_shape_key_value(self, object_name, shape_key_name, value):
        obj = self._mesh_object(object_name)
        key = self._shape_key(obj, shape_key_name) if obj else None
        if not key:
            return {"status": "error", "message": f"Shape key not found: {shape_key_name}", "warnings": []}
        before = float(key.value)
        key.value = max(-10.0, min(10.0, float(value)))
        return {"status": "success", "object_name": obj.name, "shape_key_name": key.name, "before_value": before, "after_value": float(key.value), "warnings": []}

    def _target_indices(self, obj, offsets=None, vertex_group_name=None, deformation=None):
        if offsets:
            indices = [int(item["index"]) for item in offsets if "index" in item]
            bad = [index for index in indices if index < 0 or index >= len(obj.data.vertices)]
            if bad:
                raise ValueError(f"Vertex indices out of range: {bad[:10]}")
            return sorted(set(indices))
        if vertex_group_name:
            group = obj.vertex_groups.get(vertex_group_name)
            if not group:
                raise ValueError(f"Vertex group not found: {vertex_group_name}")
            return [vert.index for vert in obj.data.vertices if any(m.group == group.index and m.weight > 0 for m in vert.groups)]
        rule = (deformation or {}).get("region") or {}
        if rule:
            return self.server.vertex_group_service._indices_from_rule(obj, rule.get("selection_mode", "by_bounds"), None, rule)
        raise ValueError("edit_shape_key_offsets requires offsets, vertex_group_name, or deformation.region")

    def edit_shape_key_offsets(self, object_name, shape_key_name, offsets=None, vertex_group_name=None, deformation=None, confirm=False, verify=False):
        if not confirm:
            return {"status": "error", "message": "edit_shape_key_offsets requires confirm=True", "warnings": []}
        obj = self._mesh_object(object_name)
        key = self._shape_key(obj, shape_key_name) if obj else None
        if not key:
            return {"status": "error", "message": f"Shape key not found: {shape_key_name}", "warnings": []}
        if key.name == "Basis":
            return {"status": "error", "message": "Refusing to edit Basis shape key", "warnings": []}
        try:
            target_indices = self._target_indices(obj, offsets, vertex_group_name, deformation)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}
        offset_map = {int(item["index"]): mathutils.Vector(item.get("offset", [0, 0, 0])) for item in (offsets or []) if "index" in item}
        mode = str((deformation or {}).get("mode", "translate"))
        amount = float((deformation or {}).get("amount", 0.0))
        vector = mathutils.Vector((deformation or {}).get("vector", [0.0, 0.0, amount]))
        center = mathutils.Vector((deformation or {}).get("center", [0.0, 0.0, 0.0]))
        for index in target_indices:
            base = obj.data.vertices[index].co.copy()
            if index in offset_map:
                delta = offset_map[index]
            elif mode == "translate":
                delta = vector
            elif mode == "scale_from_center":
                delta = (base - center) * amount
            elif mode == "inflate_along_normals":
                delta = obj.data.vertices[index].normal * amount
            elif mode == "taper_axis":
                delta = mathutils.Vector((base.x * amount * base.z, base.y * amount * base.z, 0.0))
            elif mode == "bend_approx":
                delta = mathutils.Vector((amount * base.z * base.z, 0.0, 0.0))
            else:
                return {"status": "error", "message": f"Unsupported deformation mode: {mode}", "warnings": []}
            key.data[index].co = base + delta
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"shape_key_{shape_key_name}", include_screenshots=False) if verify else {}
        result = {"status": "success", "object_name": obj.name, "shape_key_name": key.name, "changed_vertex_count": len(target_indices), "object_summary": self.server.selection_intelligence_service.get_mesh_component_summary(obj.name), "verification": verification, "warnings": []}
        self.server._add_to_history("edit_shape_key_offsets", {"object_name": object_name, "shape_key_name": shape_key_name}, result)
        return result

    def list_shape_keys(self, object_name, include_stats=True):
        obj = self._mesh_object(object_name)
        if not obj:
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        keys = [self._shape_summary(key) for key in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else []
        return {"status": "success", "object_name": obj.name, "shape_keys": keys, "warnings": []}

    def delete_shape_keys(self, object_name, shape_key_names, confirm=False, allow_basis=False):
        if not confirm:
            return {"status": "error", "message": "delete_shape_keys requires confirm=True", "deleted": [], "missing": list(shape_key_names or []), "refused": list(shape_key_names or []), "warnings": []}
        obj = self._mesh_object(object_name)
        if not obj or not obj.data.shape_keys:
            return {"status": "error", "message": f"Mesh object or shape keys not found: {object_name}", "deleted": [], "missing": list(shape_key_names or []), "refused": [], "warnings": []}
        deleted, missing, refused = [], [], []
        for name in shape_key_names or []:
            key = self._shape_key(obj, str(name))
            if not key:
                missing.append(str(name))
                continue
            if key.name == "Basis" and not allow_basis:
                refused.append(key.name)
                continue
            obj.active_shape_key_index = list(obj.data.shape_keys.key_blocks).index(key)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.shape_key_remove()
            deleted.append(str(name))
        return {"status": "success" if not refused else "partial", "object_name": obj.name, "deleted": deleted, "missing": missing, "refused": refused, "warnings": []}


class LatticeDeformationService:
    def __init__(self, server):
        self.server = server

    def create_lattice_deformer(self, target_object_name, lattice_name=None, resolution=None, padding=0.25, collection_name=None, add_modifier=True, verify=False):
        target = bpy.data.objects.get(target_object_name)
        if not target:
            return {"status": "error", "message": f"Target object not found: {target_object_name}", "warnings": []}
        lattice_data = bpy.data.lattices.new(lattice_name or f"{target.name}_Lattice")
        resolution = resolution or [2, 2, 2]
        lattice_data.points_u, lattice_data.points_v, lattice_data.points_w = [max(2, min(12, int(v))) for v in resolution[:3]]
        lattice_obj = bpy.data.objects.new(lattice_name or lattice_data.name, lattice_data)
        bounds = self.server.selection_intelligence_service._object_bounds([target])
        center = bounds.get("center") or list(target.location)
        size = [max(0.01, v + float(padding) * 2.0) for v in (bounds.get("size") or list(target.dimensions))]
        lattice_obj.location = center
        lattice_obj.scale = size
        collection = bpy.data.collections.get(collection_name) if collection_name else (target.users_collection[0] if target.users_collection else bpy.context.scene.collection)
        if collection is None:
            collection = bpy.context.scene.collection
        collection.objects.link(lattice_obj)
        modifier_name = None
        if add_modifier:
            modifier = target.modifiers.new(name=f"{lattice_obj.name}_Lattice", type="LATTICE")
            modifier.object = lattice_obj
            modifier_name = modifier.name
        verification = self.server.scene_edit_service._verification(f"lattice_{lattice_obj.name}", verify)
        return {"status": "success", "target_object_name": target.name, "lattice_name": lattice_obj.name, "modifier_name": modifier_name, "bounds": bounds, "resolution": [lattice_data.points_u, lattice_data.points_v, lattice_data.points_w], "verification": verification, "warnings": []}

    def update_lattice_deformer(self, lattice_name, control_point_offsets=None, deformation=None, confirm=False, verify=False):
        if not confirm:
            return {"status": "error", "message": "update_lattice_deformer requires confirm=True", "warnings": []}
        lattice_obj = bpy.data.objects.get(lattice_name)
        if not lattice_obj or lattice_obj.type != "LATTICE":
            return {"status": "error", "message": f"Lattice object not found: {lattice_name}", "warnings": []}
        points = lattice_obj.data.points
        changed = 0
        if control_point_offsets:
            for item in control_point_offsets:
                index = int(item.get("index", -1))
                if 0 <= index < len(points):
                    points[index].co_deform += mathutils.Vector(item.get("offset", [0, 0, 0]))
                    changed += 1
        else:
            deformation = deformation or {}
            mode = str(deformation.get("mode", "move_top"))
            amount = float(deformation.get("amount", 0.05))
            coords = [point.co_deform.z for point in points]
            top = max(coords) if coords else 0.0
            bottom = min(coords) if coords else 0.0
            for point in points:
                if mode == "move_top" and point.co_deform.z >= top:
                    point.co_deform.z += amount
                    changed += 1
                elif mode == "move_bottom" and point.co_deform.z <= bottom:
                    point.co_deform.z += amount
                    changed += 1
                elif mode == "scale_axis":
                    axis = str(deformation.get("axis", "x"))
                    setattr(point.co_deform, axis, getattr(point.co_deform, axis) * (1.0 + amount))
                    changed += 1
                elif mode in {"twist_approx", "taper_axis", "bend_approx"}:
                    point.co_deform.x += amount * point.co_deform.z
                    changed += 1
        verification = self.server.scene_edit_service._verification(f"lattice_update_{lattice_obj.name}", verify)
        return {"status": "success", "lattice_name": lattice_obj.name, "changed_point_count": changed, "verification": verification, "warnings": []}

    def apply_lattice_to_object(self, target_object_name, lattice_name, modifier_name=None, create_if_missing=True):
        target = bpy.data.objects.get(target_object_name)
        lattice_obj = bpy.data.objects.get(lattice_name)
        if not target or not lattice_obj or lattice_obj.type != "LATTICE":
            return {"status": "error", "message": "Target object or lattice not found", "warnings": []}
        modifier = target.modifiers.get(modifier_name) if modifier_name else None
        if modifier is None:
            for candidate in target.modifiers:
                if candidate.type == "LATTICE" and getattr(candidate, "object", None) == lattice_obj:
                    modifier = candidate
                    break
        if modifier is None and create_if_missing:
            modifier = target.modifiers.new(name=modifier_name or f"{lattice_obj.name}_Lattice", type="LATTICE")
        if modifier is None:
            return {"status": "error", "message": "Lattice modifier not found and create_if_missing=False", "warnings": []}
        modifier.object = lattice_obj
        return {"status": "success", "object_name": target.name, "lattice_name": lattice_obj.name, "modifier": {"name": modifier.name, "type": modifier.type}, "warnings": []}

    def remove_lattice_deformer(self, lattice_name, target_object_name=None, remove_modifier=True, delete_lattice_object=True, confirm=False):
        if not confirm:
            return {"status": "error", "message": "remove_lattice_deformer requires confirm=True", "warnings": []}
        lattice_obj = bpy.data.objects.get(lattice_name)
        removed_modifiers = []
        if remove_modifier:
            targets = [bpy.data.objects.get(target_object_name)] if target_object_name else list(bpy.data.objects)
            for obj in [item for item in targets if item]:
                for modifier in list(obj.modifiers):
                    if modifier.type == "LATTICE" and getattr(modifier, "object", None) == lattice_obj:
                        removed_modifiers.append({"object_name": obj.name, "modifier_name": modifier.name})
                        obj.modifiers.remove(modifier)
        deleted = False
        if delete_lattice_object and lattice_obj:
            bpy.data.objects.remove(lattice_obj, do_unlink=True)
            deleted = True
        return {"status": "success", "lattice_name": lattice_name, "removed_modifiers": removed_modifiers, "deleted_lattice_object": deleted, "warnings": []}


class DeformationModifierService:
    SUPPORTED_MODIFIERS = {"SIMPLE_DEFORM", "DISPLACE", "SHRINKWRAP", "SMOOTH", "CORRECTIVE_SMOOTH", "LAPLACIANSMOOTH", "WARP"}
    ALLOWED_PROPERTIES = {
        "SIMPLE_DEFORM": {"deform_method", "deform_axis", "angle", "factor", "limits", "show_viewport", "show_render"},
        "DISPLACE": {"strength", "direction", "mid_level", "show_viewport", "show_render"},
        "SHRINKWRAP": {"target", "wrap_method", "offset", "show_viewport", "show_render"},
        "SMOOTH": {"factor", "iterations", "show_viewport", "show_render"},
        "CORRECTIVE_SMOOTH": {"factor", "iterations", "smooth_type", "show_viewport", "show_render"},
        "LAPLACIANSMOOTH": {"lambda_factor", "lambda_border", "iterations", "show_viewport", "show_render"},
        "WARP": {"strength", "falloff_type", "show_viewport", "show_render"},
    }

    def __init__(self, server):
        self.server = server

    def _summary(self, modifier):
        return {"name": modifier.name, "type": modifier.type, "vertex_group": getattr(modifier, "vertex_group", ""), "show_viewport": bool(modifier.show_viewport), "show_render": bool(modifier.show_render)}

    def _apply_properties(self, modifier, properties):
        warnings = []
        allowed = self.ALLOWED_PROPERTIES.get(modifier.type, set())
        for key, value in (properties or {}).items():
            if key not in allowed:
                warnings.append(f"Unsupported deformation modifier property skipped: {key}")
                continue
            if key == "target" and isinstance(value, str):
                value = bpy.data.objects.get(value)
                if value is None:
                    warnings.append(f"Target object not found for property target")
                    continue
            try:
                setattr(modifier, key, value)
            except Exception as exc:
                warnings.append(f"Failed to set {key}: {exc}")
        return warnings

    def add_deformation_modifier(self, object_name, modifier_type, name=None, properties=None, vertex_group_name=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        modifier_type = str(modifier_type or "").upper()
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        if modifier_type not in self.SUPPORTED_MODIFIERS:
            return {"status": "error", "message": f"Unsupported deformation modifier_type: {modifier_type}", "warnings": []}
        if vertex_group_name and not obj.vertex_groups.get(vertex_group_name):
            return {"status": "error", "message": f"Vertex group not found: {vertex_group_name}", "warnings": []}
        modifier = obj.modifiers.new(name=name or modifier_type.title(), type=modifier_type)
        if vertex_group_name and hasattr(modifier, "vertex_group"):
            modifier.vertex_group = vertex_group_name
        warnings = self._apply_properties(modifier, properties)
        return {"status": "success", "object_name": obj.name, "modifier": self._summary(modifier), "verification": self.server.scene_edit_service._verification(f"deform_modifier_{obj.name}", verify), "warnings": warnings}

    def update_deformation_modifier(self, object_name, modifier_name, properties, vertex_group_name=None, verify=False):
        obj = bpy.data.objects.get(object_name)
        modifier = obj.modifiers.get(modifier_name) if obj else None
        if not modifier:
            return {"status": "error", "message": f"Modifier not found: {modifier_name}", "warnings": []}
        if modifier.type not in self.SUPPORTED_MODIFIERS:
            return {"status": "error", "message": f"Modifier is not a Phase 4B deformation modifier: {modifier.type}", "warnings": []}
        before = self._summary(modifier)
        warnings = self._apply_properties(modifier, properties)
        if vertex_group_name is not None and hasattr(modifier, "vertex_group"):
            if vertex_group_name and not obj.vertex_groups.get(vertex_group_name):
                return {"status": "error", "message": f"Vertex group not found: {vertex_group_name}", "warnings": warnings}
            modifier.vertex_group = vertex_group_name
        return {"status": "success" if not warnings else "partial", "object_name": obj.name, "before": before, "modifier": self._summary(modifier), "verification": self.server.scene_edit_service._verification(f"deform_modifier_{obj.name}", verify), "warnings": warnings}


class DirectMeshEditService:
    def __init__(self, server):
        self.server = server


class DeformationWorkflowBatchService:
    SUPPORTED_BATCH_OPERATIONS = {
        "get_selection_deep_info", "get_mesh_component_summary", "create_vertex_group", "update_vertex_group_weights",
        "create_shape_key", "update_shape_key_value", "edit_shape_key_offsets", "create_lattice_deformer",
        "update_lattice_deformer", "apply_lattice_to_object", "add_deformation_modifier", "update_deformation_modifier",
        "create_region_deformation", "delete_vertex_groups", "delete_shape_keys", "remove_lattice_deformer",
    }
    DESTRUCTIVE_OPERATIONS = {"delete_vertex_groups", "delete_shape_keys", "remove_lattice_deformer"}

    def __init__(self, server):
        self.server = server

    def create_region_deformation(self, object_name, region, method="shape_key", deformation=None, name=None, verify=True, confirm=False):
        if not confirm:
            return {"status": "error", "message": "create_region_deformation requires confirm=True", "warnings": []}
        method = str(method or "shape_key")
        region = region or {}
        deformation = deformation or {"mode": "translate", "vector": [0, 0, 0.05]}
        group_name = region.get("vertex_group")
        created = {}
        if not group_name:
            group_name = name or f"{object_name}_Region"
            mode_map = {"axis_range": "by_axis", "bounds": "by_bounds", "material_slot": "by_material_slot", "all": "all", "selected_vertices": "selected_vertices"}
            selector = region.get("selector") or region.get("type") or "all"
            group_result = self.server.vertex_group_service.create_vertex_group(object_name, group_name, mode_map.get(selector, selector), rule=region, replace_existing=True)
            if group_result.get("status") != "success":
                return group_result
            created["vertex_group"] = group_result
        if method == "shape_key":
            shape_name = name or f"{group_name}_Shape"
            shape = self.server.shape_key_service.create_shape_key(object_name, shape_name, replace_existing=True, value=1.0)
            if shape.get("status") != "success":
                return shape
            edit = self.server.shape_key_service.edit_shape_key_offsets(object_name, shape_name, vertex_group_name=group_name, deformation=deformation, confirm=True, verify=verify)
            created.update({"shape_key_name": shape_name, "shape_key_edit": edit})
        elif method == "lattice":
            lattice_name = name or f"{object_name}_RegionLattice"
            created["lattice"] = self.server.lattice_deformation_service.create_lattice_deformer(object_name, lattice_name=lattice_name, verify=verify)
        elif method == "deformation_modifier":
            modifier_name = name or f"{object_name}_RegionDeform"
            created["modifier"] = self.server.deformation_modifier_service.add_deformation_modifier(object_name, deformation.get("modifier_type", "SIMPLE_DEFORM"), name=modifier_name, properties=deformation.get("properties", {"deform_method": "TAPER", "factor": 0.05}), vertex_group_name=group_name, verify=verify)
        else:
            return {"status": "error", "message": f"Unsupported deformation method: {method}", "warnings": []}
        return {"status": "success", "object_name": object_name, "method": method, "region": region, "created": created, "warnings": []}

    def run_deformation_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=30, batch_allow_destructive=False):
        operations = operations or []
        max_operations = max(1, min(int(max_operations), 60))
        if len(operations) > max_operations:
            return {"status": "error", "message": f"Batch exceeds max_operations={max_operations}", "operation_results": [], "errors": [], "warnings": []}
        batch_id = f"deform_batch_{int(time.time())}_{abs(hash(str(operations))) % 100000}"
        batch_label = label or batch_id
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_label}_before", include_screenshots=False) if create_before_snapshot else {}
        results, errors, warnings = [], [], []
        handlers = self.server._build_command_handlers()
        for index, operation in enumerate(operations):
            command = operation.get("type") or operation.get("command")
            params = dict(operation.get("params") or {})
            if command not in self.SUPPORTED_BATCH_OPERATIONS:
                errors.append({"index": index, "command": command, "message": "Unsupported deformation workflow operation"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_OPERATIONS and not (batch_allow_destructive and operation.get("confirm") is True):
                errors.append({"index": index, "command": command, "message": "Destructive operation requires batch_allow_destructive=True and operation.confirm=True"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_OPERATIONS:
                params.setdefault("confirm", True)
            result = handlers[command](**params)
            results.append({"index": index, "command": command, "result": result})
            warnings.extend(result.get("warnings", []) if isinstance(result, dict) else [])
            if isinstance(result, dict) and result.get("status") not in {"success"}:
                errors.append({"index": index, "command": command, "message": result.get("message", result.get("status"))})
                if stop_on_error:
                    break
        after = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_label}_after", include_screenshots=False) if create_after_snapshot else {}
        return {"status": "success" if not errors else ("partial" if results else "error"), "batch_id": batch_id, "label": batch_label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors, "warnings": warnings}


class MethodIntelligenceService:
    PLAYBOOKS = {
        "make_region_larger": ["inspect selection", "create or reuse vertex group", "prefer shape key or lattice", "verify before/after"],
        "arrange_repeated_objects": ["inspect count and spacing", "prefer array or geometry nodes", "avoid many unique duplicates", "verify scene health"],
        "create_pbr_material": ["inspect material slots", "choose template", "bind color-space-aware maps", "preview material"],
        "sculpt_region_safely": ["inspect mesh and masks", "prefer shape-key sculpt workflow", "use small brush settings", "capture verification snapshot"],
    }
    ANTI_PATTERNS = [
        "Do not run raw Python mesh edits when a structured vertex group, shape key, lattice, modifier, or playbook can solve the task.",
        "Do not apply modifiers destructively by default.",
        "Do not deform a vague region without selection, bounds, material slot, UV island, or vertex group evidence.",
        "Do not download assets or overwrite texture files as part of local smoke workflows.",
        "Do not claim visual success without snapshot or scene-health evidence when verification is requested.",
    ]
    MODIFIER_RECIPES = {
        "body_proportion_lattice": {"modifiers": ["LATTICE"], "requires": ["target_object", "lattice_cage"], "risk": "medium"},
        "localized_taper": {"modifiers": ["SIMPLE_DEFORM"], "requires": ["vertex_group"], "risk": "medium"},
        "soft_surface_relax": {"modifiers": ["SMOOTH", "CORRECTIVE_SMOOTH"], "requires": ["optional_vertex_group"], "risk": "medium"},
        "surface_fit": {"modifiers": ["SHRINKWRAP"], "requires": ["target_object"], "risk": "medium"},
    }

    def __init__(self, server):
        self.server = server

    def get_method_plan(self, intent, object_name=None, region=None, constraints=None, verify=True):
        constraints = constraints or []
        region = region or {}
        intent_text = str(intent or "").lower()
        if any(word in intent_text for word in ["sculpt", "brush", "grab", "smooth"]):
            method = "shape_key_sculpt_workflow"
            sequence = self.PLAYBOOKS["sculpt_region_safely"]
        elif any(word in intent_text for word in ["larger", "smaller", "wider", "deform", "proportion"]):
            method = "shape_key_or_lattice"
            sequence = self.PLAYBOOKS["make_region_larger"]
        elif any(word in intent_text for word in ["material", "shader", "pbr", "texture"]):
            method = "material_template_or_pbr_builder"
            sequence = self.PLAYBOOKS["create_pbr_material"]
        else:
            method = "inspect_then_choose_structured_tool"
            sequence = ["inspect scene", "choose non-destructive structured tool", "execute bounded operation", "verify result"]
        confidence = self.score_selection_confidence(object_name=object_name, region=region).get("confidence", 0.0) if object_name else 0.5
        return {"status": "success", "intent": intent, "object_name": object_name, "recommended_method": method, "sequence": sequence, "constraints": constraints, "confidence": confidence, "verification_required": bool(verify), "anti_patterns": self.ANTI_PATTERNS, "warnings": []}

    def list_operation_playbooks(self, category=None):
        playbooks = self.PLAYBOOKS
        if category:
            playbooks = {key: value for key, value in playbooks.items() if category in key}
        return {"status": "success", "playbooks": playbooks, "warnings": []}

    def get_tricks_knowledge_base(self, category=None):
        entries = {
            "deformation": ["Use vertex groups as reusable masks.", "Use shape keys for reversible local edits.", "Use lattices for broad proportion changes."],
            "materials": ["Keep non-color maps as Non-Color.", "Use templates before custom node graphs."],
            "sculpt": ["Prefer shape-key sculpt workflow for recoverability.", "Use masks/vertex groups before brush changes."],
        }
        return {"status": "success", "category": category, "entries": entries.get(category, entries), "warnings": []}

    def get_anti_pattern_rules(self):
        return {"status": "success", "anti_patterns": self.ANTI_PATTERNS, "warnings": []}

    def get_modifier_recipes(self, recipe_name=None):
        recipes = self.MODIFIER_RECIPES
        if recipe_name:
            recipes = {recipe_name: recipes.get(recipe_name)} if recipe_name in recipes else {}
        return {"status": "success", "recipes": recipes, "warnings": []}

    def score_selection_confidence(self, object_name=None, region=None):
        score = 0.0
        reasons = []
        obj = bpy.data.objects.get(object_name) if object_name else bpy.context.view_layer.objects.active
        if obj:
            score += 0.25
            reasons.append("target object exists")
        region = region or {}
        if region.get("vertex_group") and obj and obj.vertex_groups.get(region.get("vertex_group")):
            score += 0.45
            reasons.append("vertex group region exists")
        if region.get("min") and region.get("max"):
            score += 0.25
            reasons.append("bounded region supplied")
        if region.get("material_slot") is not None or region.get("slot_index") is not None:
            score += 0.2
            reasons.append("material slot region supplied")
        if bpy.context.mode == "EDIT_MESH":
            score += 0.2
            reasons.append("user edit-mode selection is available")
        return {"status": "success", "confidence": min(1.0, score), "reasons": reasons, "warnings": [] if score >= 0.5 else ["low-confidence-region"]}


class AssetMaterialWorkflowService:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".bmp", ".tga"}

    def __init__(self, server):
        self.server = server

    def scan_blender_asset_libraries(self, include_current_file=True, max_items=200):
        assets = []
        if include_current_file:
            for collection_name, data_blocks in [("materials", bpy.data.materials), ("objects", bpy.data.objects), ("images", bpy.data.images)]:
                for item in list(data_blocks)[:max_items]:
                    assets.append({"library": "current_file", "type": collection_name[:-1], "name": item.name, "users": int(getattr(item, "users", 0))})
                    if len(assets) >= max_items:
                        break
        return {"status": "success", "asset_count": len(assets), "assets": assets, "warnings": []}

    def preview_asset(self, asset_name, asset_type="material", artifact_root=None, include_snapshot=True):
        if asset_type == "material":
            return self.server.material_preview_service.create_material_preview(asset_name, artifact_root=artifact_root, include_snapshot=include_snapshot)
        datablocks = {"object": bpy.data.objects, "image": bpy.data.images, "collection": bpy.data.collections}.get(asset_type)
        if datablocks is None or asset_name not in datablocks:
            return {"status": "error", "message": f"Asset not found: {asset_type}:{asset_name}", "warnings": []}
        snapshot = self.server.verification_artifact_service.create_verification_snapshot(label=f"asset_preview_{asset_type}_{asset_name}", include_screenshots=False, artifact_root=artifact_root) if include_snapshot else {}
        return {"status": "success", "asset_name": asset_name, "asset_type": asset_type, "snapshot": snapshot, "warnings": []}

    def import_texture_folder(self, folder_path, material_name=None, assign_to_object=None, strict_file_exists=True, verify=True):
        folder = os.path.abspath(os.path.expanduser(str(folder_path or "")))
        if strict_file_exists and not os.path.isdir(folder):
            return {"status": "error", "message": f"Texture folder not found: {folder}", "warnings": []}
        files = []
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                if os.path.splitext(name)[1].lower() in self.IMAGE_EXTENSIONS:
                    files.append(os.path.join(folder, name))
        material_name = material_name or f"OVERTLI_TEXTURE_SET_{int(time.time())}"
        material_result = self.server.advanced_material_authoring_service.create_custom_material(material_name, replace_existing=True, verify=False)
        bindings = []
        kind_map = [("base_color", ["base", "albedo", "diffuse"]), ("roughness_map", ["rough"]), ("metallic_map", ["metal"]), ("normal_map", ["normal"]), ("height_map", ["height", "disp"]), ("ao_map", ["ao", "ambient"])]
        for path in files:
            lower = os.path.basename(path).lower()
            kind = next((candidate for candidate, tokens in kind_map if any(token in lower for token in tokens)), None)
            if kind:
                bindings.append(self.server.material_texture_slot_service.bind_material_texture_map(material_name, kind, path, strict_file_exists=False, verify=False))
        assignment = self.server.material_authoring_service.assign_material(assign_to_object, material_name, verify=False) if assign_to_object else None
        verification = self.server.material_intelligence_service.get_material_deep_info(material_name, include_node_graph=False) if verify else {}
        return {"status": "success", "folder_path": folder, "material_name": material_name, "texture_files": files, "bindings": bindings, "assignment": assignment, "verification": verification, "warnings": []}

    def create_style_material(self, style_name, material_name, parameters=None, assign_to_object=None, verify=True):
        style = str(style_name or "stylized").lower()
        templates = {"realistic": "pbr_metal_gold", "glass": "glass_clear", "fabric": "fabric_woven", "wood": "wood_procedural", "sci_fi": "sci_fi_panel", "stylized": "car_paint_basic"}
        template = templates.get(style, "car_paint_basic")
        return self.server.material_template_service.create_material_from_template(template, material_name, parameters=parameters or {}, assign_to_object=assign_to_object, replace_existing=True, verify=verify)

    def create_paintable_texture(self, object_name, material_name=None, image_name=None, width=1024, height=1024, base_color=None, verify=True):
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        width = max(16, min(8192, int(width)))
        height = max(16, min(8192, int(height)))
        image = bpy.data.images.new(image_name or f"{object_name}_Paintable", width=width, height=height, alpha=True)
        if base_color:
            image.generated_color = [float(v) for v in base_color[:4]]
        material_name = material_name or f"{object_name}_Paintable_Material"
        material = self.server.material_authoring_service.create_basic_material(material_name, base_color=base_color or [1, 1, 1, 1], replace_existing=True)
        self.server.material_authoring_service.assign_material(object_name, material_name, verify=False)
        verification = self.server.material_intelligence_service.get_material_deep_info(material_name, include_node_graph=False) if verify else {}
        return {"status": "success", "object_name": obj.name, "material_name": material_name, "image_name": image.name, "size": [width, height], "material": material, "verification": verification, "warnings": ["created in-memory image; save/pack explicitly if persistence is required"]}

    def delete_images(self, image_names, confirm=False, allow_missing=False):
        if not confirm:
            return {"status": "error", "message": "delete_images requires confirm=True", "deleted": [], "missing": list(image_names or []), "refused": list(image_names or []), "warnings": []}
        deleted, missing, refused = [], [], []
        for name in image_names or []:
            if any(token in str(name) for token in ["*", "?", "["]):
                refused.append(str(name))
                continue
            image = bpy.data.images.get(str(name))
            if image is None:
                missing.append(str(name))
                continue
            bpy.data.images.remove(image)
            deleted.append(str(name))
        status = "success" if not refused and (allow_missing or not missing) else "partial"
        return {"status": status, "deleted": deleted, "missing": missing, "refused": refused, "warnings": []}


class UVSelectionMeasurementService:
    def __init__(self, server):
        self.server = server

    def list_uv_maps(self, object_name, include_island_estimate=True):
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        maps = [{"name": uv.name, "index": index, "active": obj.data.uv_layers.active == uv} for index, uv in enumerate(obj.data.uv_layers)]
        return {"status": "success", "object_name": obj.name, "uv_maps": maps, "island_estimate_available": bool(include_island_estimate), "warnings": []}

    def create_vertex_group_from_uv_island(self, object_name, group_name, uv_map_name=None, island_seed_face_index=None, weight=1.0, confirm=False):
        if not confirm:
            return {"status": "error", "message": "create_vertex_group_from_uv_island requires confirm=True", "warnings": []}
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            return {"status": "error", "message": f"Mesh object not found: {object_name}", "warnings": []}
        mesh = obj.data
        if not mesh.uv_layers:
            return {"status": "error", "message": f"Object has no UV maps: {object_name}", "warnings": []}
        uv_layer = mesh.uv_layers.get(uv_map_name) if uv_map_name else mesh.uv_layers.active
        if uv_layer is None:
            return {"status": "error", "message": f"UV map not found: {uv_map_name}", "warnings": []}
        if island_seed_face_index is None:
            return {"status": "error", "message": "island_seed_face_index is required for UV island traversal", "warnings": []}
        else:
            face_index = int(island_seed_face_index)
            if face_index < 0 or face_index >= len(mesh.polygons):
                return {"status": "error", "message": f"Face index out of range: {face_index}", "warnings": []}
            edge_to_faces = {}
            face_vertices = {}
            for poly in mesh.polygons:
                loops = list(poly.loop_indices)
                face_vertices[poly.index] = set(poly.vertices)
                for offset, loop_index in enumerate(loops):
                    next_loop_index = loops[(offset + 1) % len(loops)]
                    uv_a = uv_layer.data[loop_index].uv
                    uv_b = uv_layer.data[next_loop_index].uv
                    key = tuple(sorted(((round(float(uv_a.x), 6), round(float(uv_a.y), 6)), (round(float(uv_b.x), 6), round(float(uv_b.y), 6)))))
                    edge_to_faces.setdefault(key, set()).add(poly.index)
            adjacency = {poly.index: set() for poly in mesh.polygons}
            for faces in edge_to_faces.values():
                if len(faces) > 1:
                    for face in faces:
                        adjacency[face].update(other for other in faces if other != face)
            queue = [face_index]
            visited = {face_index}
            while queue:
                current = queue.pop(0)
                for neighbor in adjacency.get(current, set()):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            indices = sorted({vertex for face in visited for vertex in face_vertices.get(face, set())})
            warnings = []
        result = self.server.vertex_group_service.create_vertex_group(object_name, group_name, selection_mode="indices", indices=indices, weight=weight, replace_existing=True)
        result["warnings"] = result.get("warnings", []) + warnings
        result["uv_island"] = {"uv_map_name": uv_layer.name, "seed_face_index": int(island_seed_face_index), "face_count": len(visited), "method": "uv_edge_connectivity"}
        return result

    def measure_object(self, object_name, include_bounds=True):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        bounds = self.server.selection_intelligence_service._object_bounds([obj]) if include_bounds and getattr(obj, "bound_box", None) else {}
        return {"status": "success", "object_name": obj.name, "location": list(obj.location), "dimensions": list(obj.dimensions), "bounds": bounds, "warnings": []}

    def measure_distance(self, object_a, object_b):
        first = bpy.data.objects.get(object_a)
        second = bpy.data.objects.get(object_b)
        if not first or not second:
            return {"status": "error", "message": "Both objects must exist", "warnings": []}
        distance = (first.matrix_world.translation - second.matrix_world.translation).length
        return {"status": "success", "object_a": first.name, "object_b": second.name, "distance": float(distance), "warnings": []}

    def create_proportional_deformation(self, object_name, region, deformation, method="shape_key", name=None, confirm=False, verify=True):
        deformation = dict(deformation or {})
        deformation.setdefault("falloff", "smooth")
        return self.server.deformation_workflow_batch_service.create_region_deformation(object_name, region, method=method, deformation=deformation, name=name, confirm=confirm, verify=verify)


