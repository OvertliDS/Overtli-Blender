from __future__ import annotations

from ..core import *

class AnimationIntelligenceService:
    def __init__(self, server):
        self.server = server

    def get_timeline_info(self, include_markers=True, include_playback=True):
        scene = bpy.context.scene
        fps = int(scene.render.fps)
        fps_base = float(scene.render.fps_base or 1.0)
        frame_start = int(scene.frame_start)
        frame_end = int(scene.frame_end)
        duration_frames = max(0, frame_end - frame_start + 1)
        result = {
            "status": "success",
            "frame_current": int(scene.frame_current),
            "frame_start": frame_start,
            "frame_end": frame_end,
            "fps": fps,
            "fps_base": fps_base,
            "duration_frames": duration_frames,
            "duration_seconds": round(duration_frames / max(1.0, fps / fps_base), 4),
            "warnings": [],
        }
        if include_markers:
            result["markers"] = [{"name": marker.name, "frame": int(marker.frame)} for marker in scene.timeline_markers]
        if include_playback:
            result["playback"] = {"use_preview_range": bool(scene.use_preview_range), "frame_preview_start": int(scene.frame_preview_start), "frame_preview_end": int(scene.frame_preview_end)}
        return result

    @staticmethod
    def _action_fcurves(action):
        return list(getattr(action, "fcurves", []) or [])

    @staticmethod
    def _animation_summary(animation_data, include_keyframes=False, include_drivers=True, max_keyframes=200):
        action = animation_data.action if animation_data else None
        fcurves = []
        truncated = False
        if action:
            for fcurve in AnimationIntelligenceService._action_fcurves(action):
                points = list(fcurve.keyframe_points)
                frames = [float(point.co.x) for point in points]
                interpolation_summary = {}
                keyframes = []
                for point in points:
                    interpolation_summary[point.interpolation] = interpolation_summary.get(point.interpolation, 0) + 1
                    if include_keyframes and len(keyframes) < max_keyframes:
                        keyframes.append({"frame": float(point.co.x), "value": float(point.co.y), "interpolation": point.interpolation})
                if include_keyframes and len(points) > len(keyframes):
                    truncated = True
                item = {"data_path": fcurve.data_path, "array_index": int(fcurve.array_index), "keyframe_count": len(points), "frame_range": [min(frames), max(frames)] if frames else None, "interpolation_summary": interpolation_summary}
                if include_keyframes:
                    item["keyframes"] = keyframes
                fcurves.append(item)
        drivers = []
        if include_drivers and animation_data:
            for fcurve in getattr(animation_data, "drivers", []) or []:
                driver = getattr(fcurve, "driver", None)
                drivers.append({"data_path": fcurve.data_path, "array_index": int(fcurve.array_index), "type": getattr(driver, "type", None), "expression": getattr(driver, "expression", None), "variable_count": len(getattr(driver, "variables", []) or [])})
        return {"action_name": action.name if action else None, "fcurves": fcurves, "drivers": drivers, "truncated": truncated}

    def list_animated_objects(self, include_material_animation=True, include_shape_key_animation=True, include_drivers=True, max_objects=None):
        objects = []
        warnings = []
        limit = int(max_objects) if max_objects is not None else None
        for obj in bpy.context.scene.objects:
            object_animation = self._animation_summary(obj.animation_data, include_drivers=include_drivers)
            material_animation = []
            shape_key_animation = None
            if include_material_animation:
                for slot in obj.material_slots:
                    if slot.material and slot.material.animation_data:
                        material_animation.append({"material_name": slot.material.name, **self._animation_summary(slot.material.animation_data, include_drivers=include_drivers)})
            if include_shape_key_animation and getattr(obj.data, "shape_keys", None) and obj.data.shape_keys.animation_data:
                shape_key_animation = self._animation_summary(obj.data.shape_keys.animation_data, include_drivers=include_drivers)
            if object_animation["fcurves"] or object_animation["drivers"] or material_animation or shape_key_animation:
                objects.append({"name": obj.name, "type": obj.type, "object_animation": object_animation, "material_animation": material_animation, "shape_key_animation": shape_key_animation, "driver_count": len(object_animation["drivers"])})
            if limit is not None and len(objects) >= limit:
                warnings.append("Animated object list truncated by max_objects")
                break
        return {"status": "success", "objects": objects, "count": len(objects), "warnings": warnings}

    def get_animation_deep_info(self, object_name=None, material_name=None, include_keyframes=True, include_fcurves=True, include_drivers=True, max_keyframes=200):
        target = None
        target_type = None
        if object_name:
            target = bpy.data.objects.get(object_name)
            target_type = "OBJECT"
        elif material_name:
            target = bpy.data.materials.get(material_name)
            target_type = "MATERIAL"
        if target is None and (object_name or material_name):
            return {"status": "error", "message": "Animation target not found", "warnings": []}
        if target is None:
            return {"status": "success", "target": {"type": "SCENE"}, "timeline": self.get_timeline_info(), "animated_objects": self.list_animated_objects(max_objects=100), "warnings": []}
        animation_data = self._animation_summary(target.animation_data, include_keyframes, include_drivers, max(1, min(int(max_keyframes), 1000)))
        if not include_fcurves:
            animation_data["fcurves"] = []
        return {"status": "success", "target": {"type": target_type, "name": target.name}, "animation_data": animation_data, "truncated": animation_data["truncated"], "warnings": []}

    def set_timeline_range(self, frame_start, frame_end, fps=None, current_frame=None):
        before = self.get_timeline_info()
        frame_start = int(frame_start)
        frame_end = int(frame_end)
        if frame_start >= frame_end or frame_end - frame_start > 10000:
            return {"status": "error", "message": "frame_start must be less than frame_end and range must be <= 10000 frames", "warnings": []}
        scene = bpy.context.scene
        scene.frame_start = frame_start
        scene.frame_end = frame_end
        if fps is not None:
            scene.render.fps = max(1, min(int(fps), 240))
        if current_frame is not None:
            scene.frame_set(max(frame_start, min(int(current_frame), frame_end)))
        after = self.get_timeline_info()
        self.server._add_to_history("set_timeline_range", {"frame_start": frame_start, "frame_end": frame_end, "fps": fps, "current_frame": current_frame}, after)
        return {"status": "success", "before": before, "after": after, "warnings": []}

    def set_current_frame(self, frame):
        scene = bpy.context.scene
        before = int(scene.frame_current)
        frame = int(frame)
        if frame < -100000 or frame > 100000:
            return {"status": "error", "message": "frame is outside safety bounds", "warnings": []}
        scene.frame_set(frame)
        return {"status": "success", "before_frame": before, "frame_current": int(scene.frame_current), "warnings": []}


class AnimationAuthoringService:
    TRANSFORM_PROPERTIES = {"location", "rotation_euler", "scale"}
    INTERPOLATIONS = {"CONSTANT", "LINEAR", "BEZIER"}
    LIGHT_PROPERTIES = {"energy", "color", "spot_size", "shadow_soft_size"}
    MATERIAL_CHANNELS = {"base_color", "metallic", "roughness", "alpha", "emission_color", "emission_strength"}

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _frames(values):
        frames = [int(value) for value in values]
        if not frames or len(frames) > 200 or min(frames) < -100000 or max(frames) > 100000:
            raise ValueError("frames/keyframes must contain 1-200 bounded frame values")
        return frames

    @staticmethod
    def _vec(value, length, label):
        if not isinstance(value, (list, tuple)) or len(value) != length:
            raise ValueError(f"{label} must be a {length}-item numeric list")
        return [float(item) for item in value]

    def _apply_interpolation(self, target, interpolation):
        interpolation = str(interpolation or "BEZIER").upper()
        if interpolation not in self.INTERPOLATIONS:
            raise ValueError(f"Unsupported interpolation: {interpolation}")
        if target.animation_data and target.animation_data.action:
            for fcurve in AnimationIntelligenceService._action_fcurves(target.animation_data.action):
                for point in fcurve.keyframe_points:
                    point.interpolation = interpolation

    def insert_transform_keyframes(self, object_name, frames, properties=None):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        properties = properties or ["location", "rotation_euler", "scale"]
        if any(prop not in self.TRANSFORM_PROPERTIES for prop in properties):
            return {"status": "error", "message": "Unsupported transform property requested", "warnings": []}
        try:
            frames = self._frames(frames)
            inserted = []
            for frame in frames:
                bpy.context.scene.frame_set(frame)
                for prop in properties:
                    obj.keyframe_insert(data_path=prop, frame=frame)
                    inserted.append({"property": prop, "frame": frame})
            return {"status": "success", "object_name": obj.name, "inserted": inserted, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def _animate_transform(self, obj, keyframes, interpolation, clear_existing, confirm_clear_existing, verify):
        if clear_existing:
            if not confirm_clear_existing:
                return {"status": "error", "message": "clear_existing requires confirm_clear_existing=True", "warnings": []}
            obj.animation_data_clear()
        try:
            frames = self._frames([item.get("frame") for item in keyframes])
            inserted = []
            for frame, item in zip(frames, keyframes):
                bpy.context.scene.frame_set(frame)
                if "location" in item:
                    obj.location = self._vec(item["location"], 3, "location")
                    obj.keyframe_insert(data_path="location", frame=frame)
                    inserted.append({"property": "location", "frame": frame})
                if "rotation" in item or "rotation_euler" in item:
                    obj.rotation_euler = self._vec(item.get("rotation", item.get("rotation_euler")), 3, "rotation")
                    obj.keyframe_insert(data_path="rotation_euler", frame=frame)
                    inserted.append({"property": "rotation_euler", "frame": frame})
                if "scale" in item:
                    obj.scale = self._vec(item["scale"], 3, "scale")
                    obj.keyframe_insert(data_path="scale", frame=frame)
                    inserted.append({"property": "scale", "frame": frame})
            self._apply_interpolation(obj, interpolation)
            verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_animation_{obj.name}", include_screenshots=False) if verify else None
            return {"status": "success", "object_name": obj.name, "keyframe_count": len(keyframes), "inserted": inserted, "interpolation": str(interpolation).upper(), "verification": verification, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def animate_object_transform(self, object_name, keyframes, interpolation="BEZIER", clear_existing=False, confirm_clear_existing=False, verify=False):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        return self._animate_transform(obj, keyframes, interpolation, clear_existing, confirm_clear_existing, verify)

    def animate_camera_transform(self, camera_name, keyframes, interpolation="BEZIER", clear_existing=False, confirm_clear_existing=False, verify=False):
        obj = bpy.data.objects.get(camera_name)
        if not obj or obj.type != "CAMERA":
            return {"status": "error", "message": f"Camera not found: {camera_name}", "warnings": []}
        return self._animate_transform(obj, keyframes, interpolation, clear_existing, confirm_clear_existing, verify)

    def animate_light_property(self, light_name, property_name, keyframes, interpolation="BEZIER"):
        obj = bpy.data.objects.get(light_name)
        if not obj or obj.type != "LIGHT":
            return {"status": "error", "message": f"Light not found: {light_name}", "warnings": []}
        property_name = str(property_name)
        if property_name not in self.LIGHT_PROPERTIES:
            return {"status": "error", "message": f"Unsupported light property: {property_name}", "warnings": []}
        try:
            frames = self._frames([item.get("frame") for item in keyframes])
            for frame, item in zip(frames, keyframes):
                bpy.context.scene.frame_set(frame)
                value = item.get("value")
                setattr(obj.data, property_name, self._vec(value, 3, property_name) if property_name == "color" else float(value))
                obj.data.keyframe_insert(data_path=property_name, frame=frame)
            self._apply_interpolation(obj.data, interpolation)
            return {"status": "success", "light_name": obj.name, "property_name": property_name, "keyframe_count": len(keyframes), "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def animate_material_property(self, material_name, channel, keyframes, interpolation="BEZIER"):
        mat = bpy.data.materials.get(material_name)
        if not mat:
            return {"status": "error", "message": f"Material not found: {material_name}", "warnings": []}
        channel = str(channel)
        if channel not in self.MATERIAL_CHANNELS:
            return {"status": "error", "message": f"Unsupported material channel: {channel}", "warnings": []}
        mat.use_nodes = True
        node = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        socket_names = {"base_color": "Base Color", "metallic": "Metallic", "roughness": "Roughness", "alpha": "Alpha", "emission_color": "Emission Color", "emission_strength": "Emission Strength"}
        try:
            socket = node.inputs.get(socket_names[channel]) if node else None
            if socket is None and channel == "emission_color" and node:
                socket = node.inputs.get("Emission")
            if socket is None:
                return {"status": "error", "message": f"Material channel unavailable: {channel}", "warnings": []}
            frames = self._frames([item.get("frame") for item in keyframes])
            for frame, item in zip(frames, keyframes):
                bpy.context.scene.frame_set(frame)
                socket.default_value = self._vec(item.get("value"), 4, channel) if channel in {"base_color", "emission_color"} else float(item.get("value"))
                socket.keyframe_insert(data_path="default_value", frame=frame)
            return {"status": "success", "material_name": mat.name, "channel": channel, "keyframe_count": len(keyframes), "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def animate_shape_key_value(self, object_name, shape_key_name, keyframes, interpolation="BEZIER"):
        obj = bpy.data.objects.get(object_name)
        key = obj.data.shape_keys.key_blocks.get(shape_key_name) if obj and getattr(obj.data, "shape_keys", None) else None
        if not key:
            return {"status": "error", "message": f"Shape key not found: {shape_key_name}", "warnings": []}
        try:
            frames = self._frames([item.get("frame") for item in keyframes])
            for frame, item in zip(frames, keyframes):
                bpy.context.scene.frame_set(frame)
                key.value = float(item.get("value"))
                key.keyframe_insert(data_path="value", frame=frame)
            self._apply_interpolation(obj.data.shape_keys, interpolation)
            return {"status": "success", "object_name": obj.name, "shape_key_name": key.name, "keyframe_count": len(keyframes), "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def delete_animation_data(self, target_type, target_name, data_paths=None, confirm=False):
        if not confirm:
            return {"status": "error", "message": "delete_animation_data requires confirm=True", "warnings": []}
        target_type = str(target_type).lower()
        target = bpy.data.materials.get(target_name) if target_type == "material" else bpy.data.objects.get(target_name)
        if target_type == "camera" and (not target or target.type != "CAMERA"):
            target = None
        if target_type == "light" and (not target or target.type != "LIGHT"):
            target = None
        if not target:
            return {"status": "error", "message": f"Animation target not found: {target_name}", "warnings": []}
        deleted = []
        if data_paths and target.animation_data and target.animation_data.action:
            action = target.animation_data.action
            for fcurve in AnimationIntelligenceService._action_fcurves(action):
                if fcurve.data_path in data_paths:
                    deleted.append({"data_path": fcurve.data_path, "array_index": int(fcurve.array_index)})
                    if hasattr(action, "fcurves"):
                        action.fcurves.remove(fcurve)
        elif target.animation_data:
            action_name = target.animation_data.action.name if target.animation_data.action else None
            target.animation_data_clear()
            deleted.append({"action_name": action_name, "cleared": True})
        return {"status": "success", "target_type": target_type, "target_name": target_name, "deleted": deleted, "warnings": []}


class CameraCompositionService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _unique(base):
        base = re.sub(r"[^A-Za-z0-9_. -]+", "_", str(base or "OVERTLI_CAMERA")).strip() or "OVERTLI_CAMERA"
        if base not in bpy.data.objects:
            return base
        index = 1
        while f"{base}.{index:03d}" in bpy.data.objects:
            index += 1
        return f"{base}.{index:03d}"

    @staticmethod
    def _vec(value, default, length=3):
        if value is None:
            return list(default)
        if not isinstance(value, (list, tuple)) or len(value) != length:
            raise ValueError(f"Expected a {length}-item numeric list")
        return [float(item) for item in value]

    @staticmethod
    def _summary(obj):
        return {"name": obj.name, "type": obj.type, "location": list(obj.location), "rotation": list(obj.rotation_euler), "lens": float(obj.data.lens), "clip_start": float(obj.data.clip_start), "clip_end": float(obj.data.clip_end)}

    def create_camera(self, camera_name=None, location=None, rotation=None, lens=None, sensor_width=None, clip_start=None, clip_end=None, collection_name=None, set_active=False, verify=False):
        name = self._unique(camera_name or "OVERTLI_CAMERA")
        data = bpy.data.cameras.new(name)
        obj = bpy.data.objects.new(name, data)
        obj.location = self._vec(location, [0.0, -6.0, 3.0])
        obj.rotation_euler = self._vec(rotation, [math.radians(60.0), 0.0, 0.0])
        if lens is not None:
            data.lens = max(1.0, min(float(lens), 300.0))
        if sensor_width is not None:
            data.sensor_width = max(1.0, min(float(sensor_width), 200.0))
        if clip_start is not None:
            data.clip_start = max(0.001, float(clip_start))
        if clip_end is not None:
            data.clip_end = max(data.clip_start + 0.1, min(float(clip_end), 100000.0))
        collection = bpy.data.collections.get(collection_name) if collection_name else bpy.context.scene.collection
        if collection is None and collection_name:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        collection.objects.link(obj)
        if set_active:
            bpy.context.scene.camera = obj
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_camera_{name}", include_screenshots=False) if verify else None
        return {"status": "success", "camera": self._summary(obj), "set_active": bool(set_active), "verification": verification, "warnings": []}

    def _bounds(self, object_names):
        if not object_names:
            raise ValueError("object_names must contain at least one object")
        corners = []
        for name in object_names:
            obj = bpy.data.objects.get(name)
            if not obj:
                raise ValueError(f"Object not found: {name}")
            corners.extend([obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box])
        min_corner = mathutils.Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
        max_corner = mathutils.Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
        return (min_corner + max_corner) * 0.5, max_corner - min_corner, min_corner, max_corner

    def frame_camera_to_objects(self, camera_name, object_names, view="front_perspective", margin=1.25, distance_multiplier=1.0, look_at=True, set_active=True, verify=False):
        camera = bpy.data.objects.get(camera_name)
        if not camera or camera.type != "CAMERA":
            return {"status": "error", "message": f"Camera not found: {camera_name}", "warnings": []}
        directions = {
            "front": mathutils.Vector((0, -1, 0)),
            "back": mathutils.Vector((0, 1, 0)),
            "left": mathutils.Vector((-1, 0, 0)),
            "right": mathutils.Vector((1, 0, 0)),
            "top": mathutils.Vector((0, 0, 1)),
            "bottom": mathutils.Vector((0, 0, -1)),
            "front_perspective": mathutils.Vector((0.65, -1, 0.45)),
            "isometric": mathutils.Vector((1, -1, 0.75)),
            "camera_current": None,
        }
        if view not in directions:
            return {"status": "error", "message": f"Unsupported view: {view}", "warnings": []}
        try:
            center, size, min_corner, max_corner = self._bounds(object_names)
            direction = (camera.location - center).normalized() if view == "camera_current" else directions[view].normalized()
            if direction.length == 0:
                direction = directions["front_perspective"].normalized()
            distance = max(size.length * 0.5, 0.5) * max(1.0, float(margin)) * max(1.0, float(distance_multiplier)) * 2.5
            camera.location = center + direction * distance
            if look_at:
                camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
            if set_active:
                bpy.context.scene.camera = camera
            verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_frame_{camera.name}", include_screenshots=False) if verify else None
            return {"status": "success", "camera": self._summary(camera), "framed_bounds": {"center": list(center), "size": list(size), "min": list(min_corner), "max": list(max_corner)}, "verification": verification, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "warnings": []}

    def set_active_camera(self, camera_name):
        camera = bpy.data.objects.get(camera_name)
        if not camera or camera.type != "CAMERA":
            return {"status": "error", "message": f"Camera not found: {camera_name}", "warnings": []}
        bpy.context.scene.camera = camera
        return {"status": "success", "camera_name": camera.name, "warnings": []}


class LightingSetupService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def _vec(value, default, length=3):
        if value is None:
            return list(default)
        if not isinstance(value, (list, tuple)) or len(value) != length:
            raise ValueError(f"Expected a {length}-item numeric list")
        return [float(item) for item in value]

    @staticmethod
    def _unique(base):
        base = re.sub(r"[^A-Za-z0-9_. -]+", "_", str(base or "OVERTLI_LIGHT")).strip() or "OVERTLI_LIGHT"
        if base not in bpy.data.objects:
            return base
        index = 1
        while f"{base}.{index:03d}" in bpy.data.objects:
            index += 1
        return f"{base}.{index:03d}"

    @staticmethod
    def _summary(obj):
        data = obj.data
        return {"name": obj.name, "type": data.type, "location": list(obj.location), "rotation": list(obj.rotation_euler), "energy": float(data.energy), "color": list(data.color), "size": float(getattr(data, "size", getattr(data, "shadow_soft_size", 0.0)))}

    def create_light(self, light_name=None, light_type="AREA", location=None, rotation=None, energy=None, color=None, size=None, collection_name=None, verify=False):
        light_type = str(light_type or "AREA").upper()
        if light_type not in {"POINT", "SUN", "SPOT", "AREA"}:
            return {"status": "error", "message": f"Unsupported light_type: {light_type}", "warnings": []}
        name = self._unique(light_name or f"OVERTLI_{light_type}_LIGHT")
        data = bpy.data.lights.new(name, type=light_type)
        obj = bpy.data.objects.new(name, data)
        obj.location = self._vec(location, [3.0, -4.0, 4.0])
        obj.rotation_euler = self._vec(rotation, [math.radians(60), 0.0, math.radians(35)])
        data.energy = max(0.0, min(float(energy if energy is not None else 500.0), 100000.0))
        if color is not None:
            data.color = self._vec(color, [1, 1, 1])
        if size is not None:
            if hasattr(data, "size"):
                data.size = max(0.01, min(float(size), 1000.0))
            if hasattr(data, "shadow_soft_size"):
                data.shadow_soft_size = max(0.01, min(float(size), 1000.0))
        collection = bpy.data.collections.get(collection_name) if collection_name else bpy.context.scene.collection
        if collection is None and collection_name:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        collection.objects.link(obj)
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_light_{name}", include_screenshots=False) if verify else None
        return {"status": "success", "light": self._summary(obj), "verification": verification, "warnings": []}

    def create_lighting_setup(self, setup_name, target_object_names=None, preset="three_point", collection_name=None, replace_existing_with_prefix=False, confirm_replace=False, verify=False):
        preset = str(preset or "three_point").lower()
        if preset not in {"three_point", "studio", "product", "softbox"}:
            return {"status": "error", "message": f"Unsupported lighting preset: {preset}", "warnings": []}
        prefix = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(setup_name or "OVERTLI_LIGHT_SETUP")).strip("._-")
        if replace_existing_with_prefix:
            if not confirm_replace:
                return {"status": "error", "message": "replace_existing_with_prefix requires confirm_replace=True", "warnings": []}
            for obj in list(bpy.data.objects):
                if obj.type == "LIGHT" and obj.name.startswith(prefix):
                    bpy.data.objects.remove(obj, do_unlink=True)
        specs = [("KEY", "AREA", [-3, -4, 5], 650, [1, .95, .9], 5), ("FILL", "AREA", [4, -3, 3], 180, [.75, .85, 1], 7), ("RIM", "POINT", [0, 4, 4], 260, [1, 1, 1], 2)]
        if preset == "softbox":
            specs = [("SOFTBOX", "AREA", [0, -4, 4], 750, [1, 1, 1], 6)]
        lights = []
        for suffix, light_type, location, energy, color, size in specs:
            result = self.create_light(f"{prefix}_{suffix}", light_type, location, energy=energy, color=color, size=size, collection_name=collection_name)
            if result.get("status") == "success":
                lights.append(result["light"])
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_lighting_{prefix}", include_screenshots=False) if verify else None
        return {"status": "success", "setup_name": prefix, "preset": preset, "lights": lights, "verification": verification, "warnings": []}

    def update_light(self, light_name, energy=None, color=None, size=None, location=None, rotation=None, verify=False):
        obj = bpy.data.objects.get(light_name)
        if not obj or obj.type != "LIGHT":
            return {"status": "error", "message": f"Light not found: {light_name}", "warnings": []}
        if energy is not None:
            obj.data.energy = max(0.0, min(float(energy), 100000.0))
        if color is not None:
            obj.data.color = self._vec(color, [1, 1, 1])
        if size is not None and hasattr(obj.data, "size"):
            obj.data.size = max(0.01, min(float(size), 1000.0))
        if location is not None:
            obj.location = self._vec(location, [0, 0, 0])
        if rotation is not None:
            obj.rotation_euler = self._vec(rotation, [0, 0, 0])
        verification = self.server.verification_artifact_service.create_verification_snapshot(label=f"phase5a_update_light_{obj.name}", include_screenshots=False) if verify else None
        return {"status": "success", "light": self._summary(obj), "verification": verification, "warnings": []}

    def set_world_lighting(self, color=None, strength=None, verify=False):
        world = bpy.context.scene.world or bpy.data.worlds.new("World")
        bpy.context.scene.world = world
        world.use_nodes = True
        bg = next((node for node in world.node_tree.nodes if node.type == "BACKGROUND"), None)
        if not bg:
            bg = world.node_tree.nodes.new("ShaderNodeBackground")
        if color is not None:
            bg.inputs["Color"].default_value = self._vec(color, [1, 1, 1, 1], 4)
        if strength is not None:
            bg.inputs["Strength"].default_value = max(0.0, min(float(strength), 1000.0))
        verification = self.server.verification_artifact_service.create_verification_snapshot(label="phase5a_world_lighting", include_screenshots=False) if verify else None
        return {"status": "success", "world": world.name, "color": list(bg.inputs["Color"].default_value), "strength": float(bg.inputs["Strength"].default_value), "verification": verification, "warnings": []}


class RenderSettingsService:
    def __init__(self, server):
        self.server = server

    def get_render_settings(self):
        scene = bpy.context.scene
        return {"status": "success", "engine": scene.render.engine, "resolution": {"x": int(scene.render.resolution_x), "y": int(scene.render.resolution_y), "percentage": int(scene.render.resolution_percentage)}, "fps": int(scene.render.fps), "frame_range": {"start": int(scene.frame_start), "end": int(scene.frame_end), "current": int(scene.frame_current)}, "filepath": scene.render.filepath, "image_format": scene.render.image_settings.file_format, "cycles_samples": int(getattr(scene.cycles, "samples", 0)) if hasattr(scene, "cycles") else None, "warnings": []}

    def set_render_settings(self, engine=None, resolution_x=None, resolution_y=None, resolution_percentage=None, samples=None, image_format=None, transparent=None, color_management=None, clamp_for_smoke=False):
        scene = bpy.context.scene
        before = self.get_render_settings()
        if engine:
            engine = str(engine).upper()
            if engine not in {"BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES", "BLENDER_WORKBENCH"}:
                return {"status": "error", "message": f"Unsupported render engine: {engine}", "warnings": []}
            scene.render.engine = engine
        max_res = 640 if clamp_for_smoke else 8192
        if resolution_x is not None:
            scene.render.resolution_x = max(16, min(int(resolution_x), max_res))
        if resolution_y is not None:
            scene.render.resolution_y = max(16, min(int(resolution_y), max_res))
        if resolution_percentage is not None:
            scene.render.resolution_percentage = max(1, min(int(resolution_percentage), 100))
        if samples is not None and hasattr(scene, "cycles"):
            scene.cycles.samples = max(1, min(int(samples), 32 if clamp_for_smoke else 4096))
        if image_format:
            scene.render.image_settings.file_format = str(image_format).upper()
        if transparent is not None:
            scene.render.film_transparent = bool(transparent)
        if color_management:
            for key, value in color_management.items():
                if hasattr(scene.view_settings, key):
                    setattr(scene.view_settings, key, value)
        return {"status": "success", "before": before, "after": self.get_render_settings(), "warnings": ["Render settings were clamped for smoke-safe cost"] if clamp_for_smoke else []}

    def set_output_path(self, output_path=None, artifact_root=None, subdir="renders/stills", filename=None):
        path = RenderArtifactService.safe_output_path(output_path, artifact_root, subdir, filename or "render.png")
        bpy.context.scene.render.filepath = path
        return {"status": "success", "output_path": path, "warnings": []}


class RenderArtifactService:
    def __init__(self, server):
        self.server = server

    @staticmethod
    def artifact_root(artifact_root=None):
        return os.path.abspath(os.path.expanduser(str(artifact_root or os.environ.get("OVERTLI_BLENDER_ARTIFACT_ROOT") or ADDON_ROOT)))

    @staticmethod
    def stamp():
        return time.strftime("%Y%m%d_%H%M%S", time.localtime()) + f"_{time.time_ns()}"

    @staticmethod
    def safe_output_path(output_path=None, artifact_root=None, subdir="renders/stills", filename="render.png"):
        if output_path:
            return os.path.abspath(os.path.expanduser(str(output_path)))
        base = os.path.join(RenderArtifactService.artifact_root(artifact_root), ".overtli_blender", *str(subdir).split("/"))
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    @staticmethod
    def write_json(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, sort_keys=True)

    def render_still(self, output_path=None, artifact_root=None, filename=None, camera_name=None, frame=None, clamp_for_smoke=True, write_manifest=True):
        scene = bpy.context.scene
        if camera_name:
            camera = bpy.data.objects.get(camera_name)
            if not camera or camera.type != "CAMERA":
                return {"status": "error", "message": f"Camera not found: {camera_name}", "warnings": []}
            scene.camera = camera
        if frame is not None:
            scene.frame_set(int(frame))
        if clamp_for_smoke:
            self.server.render_settings_service.set_render_settings(resolution_x=min(scene.render.resolution_x, 640), resolution_y=min(scene.render.resolution_y, 640), samples=32, clamp_for_smoke=True)
        path = self.safe_output_path(output_path, artifact_root, "renders/stills", filename or f"OVERTLI_PHASE5A_STILL_{self.stamp()}.png")
        previous = scene.render.filepath
        try:
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "output_path": path, "warnings": []}
        finally:
            scene.render.filepath = previous
        artifact = {"path": path, "exists": os.path.exists(path), "bytes": os.path.getsize(path) if os.path.exists(path) else 0, "frame": int(scene.frame_current), "camera": scene.camera.name if scene.camera else None}
        manifest_path = None
        if write_manifest:
            manifest_path = path + ".manifest.json"
            self.write_json(manifest_path, {"command": "render_still", "artifact": artifact, "settings": self.server.render_settings_service.get_render_settings()})
        return {"status": "success", "artifact": artifact, "manifest_path": manifest_path, "warnings": []}

    def render_contact_sheet(self, object_names=None, camera_name=None, views=None, artifact_root=None, filename=None, clamp_for_smoke=True):
        views = (views or ["front", "right", "top"])[:8]
        manifest_path = self.safe_output_path(None, artifact_root, "renders/contact_sheets", filename or f"OVERTLI_PHASE5A_CONTACT_{self.stamp()}.json")
        artifacts = []
        for index, view in enumerate(views):
            still = self.render_still(artifact_root=artifact_root, filename=f"{os.path.splitext(os.path.basename(manifest_path))[0]}_{index}_{view}.png", camera_name=camera_name, clamp_for_smoke=clamp_for_smoke, write_manifest=False)
            artifacts.append({"view": view, "result": still})
        self.write_json(manifest_path, {"command": "render_contact_sheet", "object_names": object_names or [], "camera_name": camera_name, "views": views, "artifacts": artifacts})
        return {"status": "success", "manifest_path": manifest_path, "artifacts": artifacts, "warnings": []}

    def create_turntable_animation(self, object_name, frame_start=1, frame_end=48, axis="Z", rotations=1.0, empty_name=None, camera_name=None, confirm_clear_existing=False):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"status": "error", "message": f"Object not found: {object_name}", "warnings": []}
        frame_start = int(frame_start)
        frame_end = int(frame_end)
        if frame_start >= frame_end or frame_end - frame_start > 240:
            return {"status": "error", "message": "Turntable frame range must be 1-240 frames", "warnings": []}
        axis = str(axis or "Z").upper()
        if axis not in {"X", "Y", "Z"}:
            return {"status": "error", "message": f"Unsupported axis: {axis}", "warnings": []}
        idx = {"X": 0, "Y": 1, "Z": 2}[axis]
        start = list(obj.rotation_euler)
        obj.rotation_euler[idx] = start[idx]
        obj.keyframe_insert(data_path="rotation_euler", frame=frame_start)
        obj.rotation_euler[idx] = start[idx] + math.tau * float(rotations)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame_end)
        if obj.animation_data and obj.animation_data.action:
            for fcurve in AnimationIntelligenceService._action_fcurves(obj.animation_data.action):
                for point in fcurve.keyframe_points:
                    point.interpolation = "LINEAR"
        bpy.context.scene.frame_start = frame_start
        bpy.context.scene.frame_end = frame_end
        return {"status": "success", "object_name": obj.name, "frame_start": frame_start, "frame_end": frame_end, "axis": axis, "warnings": []}

    def render_preview_animation(self, output_dir=None, artifact_root=None, frame_start=None, frame_end=None, step=1, max_frames=24, camera_name=None, clamp_for_smoke=True):
        scene = bpy.context.scene
        start = int(frame_start if frame_start is not None else scene.frame_start)
        end = int(frame_end if frame_end is not None else scene.frame_end)
        frames = list(range(start, end + 1, max(1, int(step))))[:max(1, min(int(max_frames), 24))]
        base = output_dir or os.path.join(self.artifact_root(artifact_root), ".overtli_blender", "renders", "previews", f"OVERTLI_PHASE5A_PREVIEW_{self.stamp()}")
        os.makedirs(base, exist_ok=True)
        artifacts = []
        for frame in frames:
            artifacts.append({"frame": frame, "result": self.render_still(output_path=os.path.join(base, f"frame_{frame:04d}.png"), camera_name=camera_name, frame=frame, clamp_for_smoke=clamp_for_smoke, write_manifest=False)})
        manifest_path = os.path.join(base, "manifest.json")
        self.write_json(manifest_path, {"command": "render_preview_animation", "frames": frames, "artifacts": artifacts})
        return {"status": "success", "output_dir": base, "manifest_path": manifest_path, "frames": frames, "artifacts": artifacts, "warnings": []}


class CompositorPassService:
    def __init__(self, server):
        self.server = server

    def get_compositor_status(self):
        scene = bpy.context.scene
        layer = scene.view_layers[0] if scene.view_layers else None
        node_tree = getattr(scene, "node_tree", None)
        warnings = [] if node_tree is not None else ["Compositor node tree is not available in this Blender context"]
        return {"status": "success", "use_nodes": bool(getattr(scene, "use_nodes", False)), "node_count": len(node_tree.nodes) if node_tree else 0, "render_passes": {"use_pass_z": bool(getattr(layer, "use_pass_z", False)), "use_pass_mist": bool(getattr(layer, "use_pass_mist", False)), "use_pass_normal": bool(getattr(layer, "use_pass_normal", False))}, "warnings": warnings}

    def set_compositor_preset(self, preset="basic_viewer", confirm_replace=False):
        preset = str(preset or "basic_viewer").lower()
        if preset not in {"none", "basic_viewer", "transparent_preview", "mist_depth_preview"}:
            return {"status": "error", "message": f"Unsupported compositor preset: {preset}", "warnings": []}
        scene = bpy.context.scene
        if not hasattr(scene, "use_nodes"):
            return {"status": "error", "message": "Compositor nodes are not available in this Blender context", "warnings": []}
        node_tree = getattr(scene, "node_tree", None)
        if scene.use_nodes and node_tree and node_tree.nodes and preset != "none" and not confirm_replace:
            return {"status": "error", "message": "Existing compositor nodes require confirm_replace=True", "warnings": []}
        if preset == "none":
            scene.use_nodes = False
            return {"status": "success", "preset": preset, "warnings": []}
        scene.use_nodes = True
        tree = getattr(scene, "node_tree", None)
        if tree is None:
            return {"status": "error", "message": "Compositor node tree is not available in this Blender context", "warnings": []}
        tree.nodes.clear()
        layers = tree.nodes.new("CompositorNodeRLayers")
        composite = tree.nodes.new("CompositorNodeComposite")
        viewer = tree.nodes.new("CompositorNodeViewer")
        tree.links.new(layers.outputs["Image"], composite.inputs["Image"])
        tree.links.new(layers.outputs["Image"], viewer.inputs["Image"])
        return {"status": "success", "preset": preset, "node_count": len(tree.nodes), "warnings": []}

    def set_render_passes(self, use_pass_z=None, use_pass_mist=None, use_pass_normal=None, use_pass_diffuse_color=None):
        layer = bpy.context.scene.view_layers[0]
        changed = {}
        for name, value in {"use_pass_z": use_pass_z, "use_pass_mist": use_pass_mist, "use_pass_normal": use_pass_normal, "use_pass_diffuse_color": use_pass_diffuse_color}.items():
            if value is not None and hasattr(layer, name):
                setattr(layer, name, bool(value))
                changed[name] = bool(value)
        return {"status": "success", "changed": changed, "status_after": self.get_compositor_status(), "warnings": []}


class PresentationWorkflowBatchService:
    ALLOWED_COMMANDS = {"get_timeline_info", "list_animated_objects", "get_animation_deep_info", "set_timeline_range", "set_current_frame", "insert_transform_keyframes", "animate_object_transform", "animate_camera_transform", "animate_light_property", "animate_material_property", "animate_shape_key_value", "set_render_settings", "render_still", "render_contact_sheet", "create_turntable_animation", "render_preview_animation", "get_compositor_status", "set_compositor_preset", "set_render_passes", "delete_animation_data", "cleanup_presentation_artifacts"}
    DESTRUCTIVE_COMMANDS = {"delete_animation_data", "cleanup_presentation_artifacts"}

    def __init__(self, server):
        self.server = server

    def run_presentation_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=20, batch_allow_destructive=False, artifact_root=None):
        operations = operations or []
        if len(operations) > max(1, min(int(max_operations), 50)):
            return {"status": "error", "message": "Too many batch operations", "warnings": []}
        batch_id = f"presentation_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()}"
        batch_dir = os.path.join(RenderArtifactService.artifact_root(artifact_root), ".overtli_blender", "presentation", "batches", batch_id)
        os.makedirs(batch_dir, exist_ok=True)
        before = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_before", include_screenshots=False, artifact_root=artifact_root) if create_before_snapshot else None
        results = []
        errors = []
        for op in operations:
            command = op.get("command")
            params = dict(op.get("params") or {})
            if command not in self.ALLOWED_COMMANDS:
                errors.append({"command": command, "message": "Command is not allowed in presentation batches"})
                if stop_on_error:
                    break
                continue
            if command in self.DESTRUCTIVE_COMMANDS and not (batch_allow_destructive and params.get("confirm") is True):
                errors.append({"command": command, "message": "Destructive batch operation requires batch_allow_destructive=True and operation confirm=True"})
                if stop_on_error:
                    break
                continue
            if command in {"render_still", "render_contact_sheet", "render_preview_animation"}:
                params.setdefault("artifact_root", artifact_root)
                params.setdefault("clamp_for_smoke", True)
            try:
                result = self.server._build_command_handlers()[command](**params)
            except Exception as exc:
                result = {"status": "error", "message": str(exc), "warnings": []}
            results.append({"command": command, "params": params, "result": result})
            if result.get("status") == "error":
                errors.append({"command": command, "message": result.get("message")})
                if stop_on_error:
                    break
        after = self.server.verification_artifact_service.create_verification_snapshot(label=f"{batch_id}_after", include_screenshots=False, artifact_root=artifact_root) if create_after_snapshot else None
        manifest_path = os.path.join(batch_dir, "manifest.json")
        RenderArtifactService.write_json(manifest_path, {"batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "operation_results": results, "errors": errors})
        return {"status": "partial" if errors else "success", "batch_id": batch_id, "label": label, "before_snapshot": before, "after_snapshot": after, "render_artifacts": [], "operation_results": results, "errors": errors, "manifest_path": manifest_path, "warnings": []}

    def cleanup_presentation_artifacts(self, prefix, confirm=False, cleanup_scene_data=True, cleanup_render_artifacts=False, artifact_root=None):
        if not confirm:
            return {"status": "error", "message": "cleanup_presentation_artifacts requires confirm=True", "warnings": []}
        prefix = str(prefix or "")
        if len(prefix) < 6:
            return {"status": "error", "message": "A safe prefix is required", "warnings": []}
        deleted = {"objects": [], "collections": [], "materials": [], "cameras": [], "lights": []}
        if cleanup_scene_data:
            for obj in list(bpy.data.objects):
                if obj.name.startswith(prefix):
                    bucket = "cameras" if obj.type == "CAMERA" else "lights" if obj.type == "LIGHT" else "objects"
                    deleted[bucket].append(obj.name)
                    bpy.data.objects.remove(obj, do_unlink=True)
            for mat in list(bpy.data.materials):
                if mat.name.startswith(prefix):
                    deleted["materials"].append(mat.name)
                    bpy.data.materials.remove(mat)
            for col in list(bpy.data.collections):
                if col.name.startswith(prefix) and len(col.objects) == 0 and len(col.children) == 0:
                    deleted["collections"].append(col.name)
                    bpy.data.collections.remove(col)
        artifact_deleted = []
        if cleanup_render_artifacts:
            root = os.path.join(RenderArtifactService.artifact_root(artifact_root), ".overtli_blender")
            for current_root, _dirs, files in os.walk(root):
                for filename in files:
                    if filename.startswith(prefix):
                        path = os.path.join(current_root, filename)
                        os.remove(path)
                        artifact_deleted.append(path)
        return {"status": "success", "prefix": prefix, "deleted": deleted, "artifact_deleted": artifact_deleted, "warnings": []}

_PHASE9A_ALLOWED_INTERPOLATIONS = {"CONSTANT", "LINEAR", "BEZIER", "SINE", "QUAD", "CUBIC", "QUART", "QUINT", "EXPO", "CIRC", "BACK", "BOUNCE", "ELASTIC"}
_PHASE9A_ALLOWED_EASING = {None, "AUTO", "EASE_IN", "EASE_OUT", "EASE_IN_OUT"}
_PHASE9A_ALLOWED_KEYFRAME_PATHS = {"location", "rotation_euler", "rotation_quaternion", "scale"}
_PHASE9A_ALLOWED_FCURVE_MODIFIERS = {"CYCLES", "NOISE", "LIMITS", "STEPPED"}
_PHASE9A_ALLOWED_DRIVER_OPS = {"copy", "add", "subtract", "multiply", "divide", "clamp", "map_range", "min", "max", "abs", "negate"}
_PHASE9A_ALLOWED_DRIVER_TARGETS = {"OBJECT", "ARMATURE", "BONE", "MATERIAL", "SHAPE_KEY"}
_PHASE9A_ALLOWED_DRIVER_PATHS = {"location.x", "location.y", "location.z", "rotation_euler.x", "rotation_euler.y", "rotation_euler.z", "scale.x", "scale.y", "scale.z"}

def phase9a_normalize_interpolation(interpolation=None, easing=None):
    interp = (interpolation or "BEZIER").upper()
    ease = easing.upper() if isinstance(easing, str) else easing
    if interp not in _PHASE9A_ALLOWED_INTERPOLATIONS:
        raise ValueError(f"Unsupported interpolation: {interpolation}")
    if ease not in _PHASE9A_ALLOWED_EASING:
        raise ValueError(f"Unsupported easing: {easing}")
    return {"interpolation": interp, "easing": ease}

def phase9a_validate_keyframe_batch(keyframes):
    if not keyframes:
        raise ValueError("At least one keyframe is required")
    if len(keyframes) > 512:
        raise ValueError("Too many keyframes")
    frames, paths = [], set()
    for item in keyframes:
        frame = float(item.get("frame"))
        data_path = str(item.get("data_path") or "")
        base_path = data_path.split("[", 1)[0]
        if base_path not in _PHASE9A_ALLOWED_KEYFRAME_PATHS and not base_path.startswith('key_blocks["'):
            raise ValueError(f"Unsupported keyframe data_path: {data_path}")
        phase9a_normalize_interpolation(item.get("interpolation"), item.get("easing"))
        frames.append(frame); paths.add(data_path)
    return {"count": len(keyframes), "frame_range": [min(frames), max(frames)], "data_paths": sorted(paths)}

def phase9a_build_retime_plan(frame_start, frame_end, new_start, new_end):
    frame_start, frame_end, new_start, new_end = float(frame_start), float(frame_end), float(new_start), float(new_end)
    if frame_end < frame_start or new_end < new_start:
        raise ValueError("Frame ranges must be ascending")
    source_span = frame_end - frame_start
    target_span = new_end - new_start
    return {"source_range": [frame_start, frame_end], "target_range": [new_start, new_end], "scale": 1.0 if source_span == 0 else target_span / source_span}

def phase9a_build_fcurve_modifier_plan(modifier_type, settings=None):
    mod_type = str(modifier_type or "").upper()
    if mod_type not in _PHASE9A_ALLOWED_FCURVE_MODIFIERS:
        raise ValueError(f"Unsupported F-curve modifier: {modifier_type}")
    return {"modifier_type": mod_type, "settings": dict(settings or {})}

def phase9a_validate_nla_overlaps(strips):
    issues, by_track = [], {}
    for strip in strips:
        by_track.setdefault(str(strip.get("track_name", "")), []).append(strip)
    for track_name, items in by_track.items():
        ordered = sorted(items, key=lambda item: float(item.get("frame_start", 0)))
        for left, right in zip(ordered, ordered[1:]):
            if float(left.get("frame_end", 0)) > float(right.get("frame_start", 0)):
                issues.append({"track_name": track_name, "left": left.get("name"), "right": right.get("name"), "issue": "overlap"})
    return {"status": "success" if not issues else "warning", "issues": issues}

def phase9a_driver_source(dsl):
    source = dsl.get("source")
    if not isinstance(source, dict):
        raise ValueError("Driver DSL requires a source object")
    target_type = str(source.get("target_type", "OBJECT")).upper()
    target_name = str(source.get("target_name") or "")
    data_path = str(source.get("data_path") or "")
    if target_type not in _PHASE9A_ALLOWED_DRIVER_TARGETS:
        raise ValueError(f"Unsupported driver target_type: {target_type}")
    if not target_name:
        raise ValueError("Driver source target_name is required")
    if data_path not in _PHASE9A_ALLOWED_DRIVER_PATHS and not data_path.startswith('["'):
        raise ValueError(f"Unsupported driver source data_path: {data_path}")
    return {"target_type": target_type, "target_name": target_name, "data_path": data_path}

def phase9a_validate_driver_dsl(dsl):
    if not isinstance(dsl, dict):
        raise ValueError("Driver DSL must be an object")
    operation = str(dsl.get("operation") or "").lower()
    if operation not in _PHASE9A_ALLOWED_DRIVER_OPS:
        raise ValueError(f"Unsupported driver DSL operation: {operation}")
    source = phase9a_driver_source(dsl)
    for key in ("value", "min", "max", "operand", "from_min", "from_max", "to_min", "to_max"):
        if key in dsl and dsl[key] is not None:
            float(dsl[key])
    if operation == "map_range" and float(dsl.get("from_min", 0)) == float(dsl.get("from_max", 0)):
        raise ValueError("map_range source range cannot be zero")
    return {"status": "success", "operation": operation, "source": source, "dsl_only": True}

def phase9a_compile_driver_expression(dsl):
    validated = phase9a_validate_driver_dsl(dsl)
    op = validated["operation"]
    expr = "var"
    if op == "add":
        expr = f"(var + {float(dsl.get('value', dsl.get('operand', 0.0)))})"
    elif op == "subtract":
        expr = f"(var - {float(dsl.get('value', dsl.get('operand', 0.0)))})"
    elif op == "multiply":
        expr = f"(var * {float(dsl.get('value', dsl.get('operand', 1.0)))})"
    elif op == "divide":
        divisor = float(dsl.get("value", dsl.get("operand", 1.0)))
        if divisor == 0:
            raise ValueError("divide operand cannot be zero")
        expr = f"(var / {divisor})"
    elif op == "clamp":
        expr = f"min(max(var, {float(dsl.get('min', 0.0))}), {float(dsl.get('max', 1.0))})"
    elif op == "map_range":
        fmin, fmax, tmin, tmax = float(dsl["from_min"]), float(dsl["from_max"]), float(dsl["to_min"]), float(dsl["to_max"])
        expr = f"(({tmin}) + ((var - ({fmin})) * (({tmax}) - ({tmin})) / (({fmax}) - ({fmin}))))"
    elif op == "min":
        expr = f"min(var, {float(dsl.get('value', dsl.get('operand', 0.0)))})"
    elif op == "max":
        expr = f"max(var, {float(dsl.get('value', dsl.get('operand', 0.0)))})"
    elif op == "abs":
        expr = "abs(var)"
    elif op == "negate":
        expr = "(-var)"
    return {"expression": expr, "variables": [{"name": "var", **validated["source"]}], "operation": op}

def phase9a_validate_rig_names(bone_names):
    duplicates = sorted({name for name in bone_names if bone_names.count(name) > 1})
    empty = [name for name in bone_names if not str(name).strip()]
    return {"status": "success" if not duplicates and not empty else "warning", "duplicates": duplicates, "empty_names": empty}

def phase9a_validate_bone_hierarchy(bones):
    names = {str(item.get("name")) for item in bones}
    missing_parents = [item for item in bones if item.get("parent") and item.get("parent") not in names]
    return {"status": "success" if not missing_parents else "warning", "missing_parents": missing_parents}

def phase9a_action_fcurves(action):
    if not action:
        return []
    direct = getattr(action, "fcurves", None)
    if direct is not None:
        try:
            return list(direct)
        except TypeError:
            pass
    curves, seen = [], set()
    for layer in getattr(action, "layers", []) or []:
        for strip in getattr(layer, "strips", []) or []:
            for channelbag in getattr(strip, "channelbags", []) or []:
                for fcurve in getattr(channelbag, "fcurves", []) or []:
                    key = id(fcurve)
                    if key not in seen:
                        curves.append(fcurve)
                        seen.add(key)
    return curves

def phase9a_find_fcurve(action, data_path, array_index=0):
    direct = getattr(action, "fcurves", None)
    if direct is not None and hasattr(direct, "find"):
        found = direct.find(data_path, index=int(array_index))
        if found:
            return found
    for fcurve in phase9a_action_fcurves(action):
        if fcurve.data_path == data_path and int(fcurve.array_index) == int(array_index):
            return fcurve
    return None

def phase9a_action_groups(action):
    direct = getattr(action, "groups", None)
    if direct is not None:
        return [group.name for group in direct]
    names = set()
    for layer in getattr(action, "layers", []) or []:
        for strip in getattr(layer, "strips", []) or []:
            for channelbag in getattr(strip, "channelbags", []) or []:
                for group in getattr(channelbag, "groups", []) or []:
                    names.add(group.name)
    return sorted(names)


class AnimationIntelligenceAdvancedService:
    def __init__(self, server): self.server = server
    def get_animation_system_capabilities(self):
        version = ".".join(str(part) for part in getattr(bpy.app, "version", (0, 0, 0)))
        return {"status": "success", "blender_version": version, "actions": {"available": hasattr(bpy.data, "actions")}, "fcurves": {"available": hasattr(bpy.types, "FCurve"), "modifiers": hasattr(bpy.types, "FCurveModifiers")}, "keyframes": {"available": hasattr(bpy.types, "Keyframe")}, "nla": {"tracks": hasattr(bpy.types, "NlaTrack"), "strips": hasattr(bpy.types, "NlaStrip")}, "drivers": {"available": hasattr(bpy.types, "Driver"), "dsl_only": True}, "rigging": {"armatures": hasattr(bpy.data, "armatures"), "pose_bones": hasattr(bpy.types, "PoseBone"), "constraints": hasattr(bpy.types, "Constraint")}, "pose_library": {"snapshots": True, "native_pose_assets": hasattr(bpy.types, "ActionPoseMarkers")}, "shots": {"timeline_markers": hasattr(bpy.types, "TimelineMarker"), "camera_markers": True}, "motion_paths": {"available": hasattr(bpy.types, "MotionPath")}, "simulation": {"point_cache": hasattr(bpy.types, "PointCache"), "rigid_body": "available" if hasattr(bpy.types, "RigidBodyObject") else "unknown", "cloth": "available" if hasattr(bpy.types, "ClothModifier") else "unknown", "soft_body": "available" if hasattr(bpy.types, "SoftBodySettings") else "unknown", "hair_curve_dynamics": "unknown"}, "warnings": []}
    def inspect_animation_system(self, object_names=None, include_actions=True, include_fcurves=True, include_nla=True, include_drivers=True, include_constraints=True, include_pose=True, include_simulation=True):
        names = object_names or [obj.name for obj in bpy.context.scene.objects]
        objects = []
        for name in names:
            obj = bpy.data.objects.get(name)
            if not obj:
                objects.append({"name": name, "status": "missing"}); continue
            anim = getattr(obj, "animation_data", None)
            item = {"name": obj.name, "type": obj.type, "has_animation_data": bool(anim)}
            if include_actions and anim and anim.action: item["action"] = self.server.action_library_service._action_summary(anim.action)
            if include_fcurves and anim and anim.action: item["fcurves"] = self.server.action_library_service._fcurve_summaries(anim.action, include_keyframes=False)
            if include_nla and anim: item["nla_tracks"] = self.server.nla_workflow_service._nla_tracks(anim)
            if include_drivers and anim: item["drivers"] = self.server.driver_dsl_service._drivers_for_id(obj)
            if include_constraints: item["constraints"] = [{"name": con.name, "type": con.type, "target": getattr(getattr(con, "target", None), "name", None), "subtarget": getattr(con, "subtarget", None)} for con in getattr(obj, "constraints", [])]
            if include_pose and obj.type == "ARMATURE": item["pose_bones"] = [bone.name for bone in getattr(obj.pose, "bones", [])]
            if include_simulation: item["simulation"] = self.server.simulation_workflow_service._object_simulation_summary(obj)
            objects.append(item)
        actions = [self.server.action_library_service._action_summary(action) for action in bpy.data.actions] if include_actions else []
        return {"status": "success", "objects": objects, "actions": actions, "warnings": []}


class ActionLibraryService:
    def __init__(self, server): self.server = server
    def _action_summary(self, action):
        assigned = [obj.name for obj in bpy.data.objects if getattr(getattr(obj, "animation_data", None), "action", None) == action]
        fcurves = phase9a_action_fcurves(action)
        return {"name": action.name, "users": int(action.users), "frame_range": list(action.frame_range) if hasattr(action, "frame_range") else None, "fcurve_count": len(fcurves), "groups": phase9a_action_groups(action), "pose_markers": [marker.name for marker in getattr(action, "pose_markers", [])], "assigned_objects": assigned, "asset_status": "native" if getattr(action, "asset_data", None) else "not_asset"}
    def _fcurve_summaries(self, action, include_keyframes=False, max_keyframes=200):
        rows = []
        for fcurve in phase9a_action_fcurves(action):
            keyframes = []
            if include_keyframes:
                for point in list(fcurve.keyframe_points)[: int(max_keyframes)]:
                    keyframes.append({"frame": float(point.co.x), "value": float(point.co.y), "interpolation": point.interpolation, "easing": getattr(point, "easing", None)})
            rows.append({"data_path": fcurve.data_path, "array_index": int(fcurve.array_index), "keyframe_count": len(fcurve.keyframe_points), "keyframes": keyframes, "modifiers": [{"type": mod.type, "name": mod.name} for mod in getattr(fcurve, "modifiers", [])], "group": fcurve.group.name if getattr(fcurve, "group", None) else None})
        return rows
    def list_actions(self): return {"status": "success", "actions": [self._action_summary(action) for action in bpy.data.actions]}
    def get_action_deep_info(self, action_name, include_keyframes=False, max_keyframes=200):
        action = bpy.data.actions.get(action_name)
        if not action: return {"status": "error", "message": f"Action not found: {action_name}"}
        info = self._action_summary(action); info["fcurves"] = self._fcurve_summaries(action, include_keyframes, max_keyframes); return {"status": "success", "action": info}
    def create_action(self, action_name, object_name=None, frame_start=None, frame_end=None, assign_to_object=False):
        if not action_name: return {"status": "error", "message": "action_name is required"}
        if bpy.data.actions.get(action_name): return {"status": "error", "message": f"Action already exists: {action_name}"}
        action = bpy.data.actions.new(action_name)
        if frame_start is not None and frame_end is not None: action.frame_start = float(frame_start); action.frame_end = float(frame_end)
        assigned = self.assign_action(object_name, action_name) if assign_to_object else None
        return {"status": "success", "action": self._action_summary(action), "assigned": assigned}
    def duplicate_action(self, source_action_name, new_action_name, assign_to_object=None):
        source = bpy.data.actions.get(source_action_name)
        if not source: return {"status": "error", "message": f"Action not found: {source_action_name}"}
        if bpy.data.actions.get(new_action_name): return {"status": "error", "message": f"Action already exists: {new_action_name}"}
        action = source.copy(); action.name = new_action_name
        assigned = self.assign_action(assign_to_object, action.name) if assign_to_object else None
        return {"status": "success", "action": self._action_summary(action), "assigned": assigned}
    def rename_action(self, action_name, new_action_name, confirm=False):
        action = bpy.data.actions.get(action_name)
        if not action: return {"status": "error", "message": f"Action not found: {action_name}"}
        if bpy.data.actions.get(new_action_name): return {"status": "error", "message": f"Action already exists: {new_action_name}"}
        if action.users and not confirm: return {"status": "requires_approval", "message": "Renaming a used action requires confirmation.", "action": self._action_summary(action)}
        action.name = new_action_name; return {"status": "success", "action": self._action_summary(action)}
    def assign_action(self, object_name, action_name, create_animation_data=True):
        obj, action = bpy.data.objects.get(object_name or ""), bpy.data.actions.get(action_name or "")
        if not obj: return {"status": "error", "message": f"Object not found: {object_name}"}
        if not action: return {"status": "error", "message": f"Action not found: {action_name}"}
        if not obj.animation_data and create_animation_data: obj.animation_data_create()
        if not obj.animation_data: return {"status": "error", "message": "Object has no animation data and create_animation_data is false."}
        before = obj.animation_data.action.name if obj.animation_data.action else None; obj.animation_data.action = action
        return {"status": "success", "object_name": obj.name, "before_action": before, "action": self._action_summary(action)}
    def delete_actions(self, action_names, allow_used=False, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "delete_actions requires confirmation and exact action names.", "action_names": action_names}
        removed, refused = [], []
        for name in action_names or []:
            action = bpy.data.actions.get(name)
            if not action: refused.append({"name": name, "reason": "missing"}); continue
            if action.users and not allow_used: refused.append({"name": name, "reason": "action_has_users", "users": int(action.users)}); continue
            bpy.data.actions.remove(action); removed.append(name)
        return {"status": "success" if not refused else "partial", "removed": removed, "refused": refused}


class FCurveEditingService:
    def __init__(self, server): self.server = server
    def _action(self, name):
        action = bpy.data.actions.get(name or "")
        if not action: raise ValueError(f"Action not found: {name}")
        return action
    def insert_keyframe_batch(self, object_name, keyframes, create_action=True, action_name=None):
        phase9a_validate_keyframe_batch(keyframes or [])
        obj = bpy.data.objects.get(object_name or "")
        if not obj: return {"status": "error", "message": f"Object not found: {object_name}"}
        old_frame = bpy.context.scene.frame_current
        if create_action and action_name:
            if not bpy.data.actions.get(action_name): bpy.data.actions.new(action_name)
            self.server.action_library_service.assign_action(obj.name, action_name, create_animation_data=True)
        inserted = []
        try:
            for item in keyframes:
                data_path, frame, value = item["data_path"], int(item["frame"]), item.get("value")
                if value is not None and hasattr(obj, data_path): setattr(obj, data_path, value)
                obj.keyframe_insert(data_path=data_path, frame=frame, index=-1 if item.get("array_index") is None else int(item.get("array_index")))
                inserted.append({"frame": frame, "data_path": data_path, "array_index": item.get("array_index")})
            action = getattr(getattr(obj, "animation_data", None), "action", None)
            if action: self.set_fcurve_interpolation(action.name, [{"data_path": item["data_path"], "array_index": item.get("array_index")} for item in keyframes], keyframes[0].get("interpolation", "BEZIER"))
            return {"status": "success", "object_name": obj.name, "inserted": inserted, "action": action.name if action else None}
        finally:
            bpy.context.scene.frame_set(old_frame)
    def edit_keyframes(self, action_name, edits, confirm=False):
        if any(edit.get("operation") in {"delete", "delete_keyframe"} for edit in edits or []) and not confirm: return {"status": "requires_approval", "message": "Deleting keyframes requires confirmation."}
        action, results = self._action(action_name), []
        for edit in edits or []:
            fcurve = phase9a_find_fcurve(action, edit.get("data_path"), int(edit.get("array_index", 0)))
            if not fcurve: results.append({"operation": edit.get("operation"), "status": "missing_fcurve"}); continue
            for point in list(fcurve.keyframe_points):
                if float(point.co.x) == float(edit.get("frame", point.co.x)):
                    if edit.get("operation") == "move_frame": point.co.x = float(edit["new_frame"])
                    elif edit.get("operation") == "set_value": point.co.y = float(edit["value"])
                    elif edit.get("operation") in {"delete", "delete_keyframe"}: fcurve.keyframe_points.remove(point)
                    results.append({"operation": edit.get("operation"), "status": "success"})
        return {"status": "success", "results": results}
    def retime_action(self, action_name, frame_start, frame_end, new_start, new_end, confirm=False):
        action = self._action(action_name)
        if action.users and not confirm: return {"status": "requires_approval", "message": "Retiming a used action requires confirmation.", "action": action.name}
        plan = phase9a_build_retime_plan(frame_start, frame_end, new_start, new_end)
        for fcurve in phase9a_action_fcurves(action):
            for point in fcurve.keyframe_points:
                if frame_start <= point.co.x <= frame_end: point.co.x = new_start + ((point.co.x - frame_start) * plan["scale"])
        return {"status": "success", "action": self.server.action_library_service._action_summary(action), "retime_plan": plan}
    def set_fcurve_interpolation(self, action_name, fcurves=None, interpolation="BEZIER", easing=None):
        normalized = phase9a_normalize_interpolation(interpolation, easing); action = self._action(action_name); changed = []
        wanted = {(item.get("data_path"), item.get("array_index")) for item in (fcurves or [])}
        for fcurve in phase9a_action_fcurves(action):
            if wanted and (fcurve.data_path, fcurve.array_index) not in wanted and (fcurve.data_path, None) not in wanted: continue
            for point in fcurve.keyframe_points:
                point.interpolation = normalized["interpolation"]
                if normalized.get("easing") and hasattr(point, "easing"): point.easing = normalized["easing"]
            changed.append({"data_path": fcurve.data_path, "array_index": int(fcurve.array_index)})
        return {"status": "success", "changed": changed}
    def add_fcurve_modifier(self, action_name, data_path, array_index=0, modifier_type="CYCLES", settings=None):
        plan = phase9a_build_fcurve_modifier_plan(modifier_type, settings); fcurve = phase9a_find_fcurve(self._action(action_name), data_path, int(array_index))
        if not fcurve: return {"status": "error", "message": "F-curve not found."}
        mod = fcurve.modifiers.new(type=plan["modifier_type"])
        for key, value in (settings or {}).items():
            if hasattr(mod, key): setattr(mod, key, value)
        return {"status": "success", "modifier": {"type": mod.type, "name": mod.name}, "plan": plan}
    def remove_fcurve_modifier(self, action_name, data_path, array_index=0, modifier_name=None, modifier_type=None, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Removing F-curve modifiers requires confirmation."}
        fcurve = phase9a_find_fcurve(self._action(action_name), data_path, int(array_index))
        if not fcurve: return {"status": "error", "message": "F-curve not found."}
        removed = []
        for mod in list(fcurve.modifiers):
            if (modifier_name and mod.name == modifier_name) or (modifier_type and mod.type == modifier_type) or (not modifier_name and not modifier_type):
                removed.append({"name": mod.name, "type": mod.type}); fcurve.modifiers.remove(mod)
        return {"status": "success", "removed": removed}
    def validate_fcurves(self, action_name):
        action = self._action(action_name); fcurves = phase9a_action_fcurves(action); issues = [{"data_path": fcurve.data_path, "array_index": fcurve.array_index, "issue": "empty_fcurve"} for fcurve in fcurves if not fcurve.keyframe_points and not fcurve.modifiers]
        return {"status": "success", "valid": not issues, "issues": issues, "fcurve_count": len(fcurves)}


class NLAWorkflowService:
    def __init__(self, server): self.server = server
    def _object_anim(self, object_name):
        obj = bpy.data.objects.get(object_name or "")
        if not obj: raise ValueError(f"Object not found: {object_name}")
        if not obj.animation_data: obj.animation_data_create()
        return obj, obj.animation_data
    def _nla_tracks(self, anim):
        return [{"name": track.name, "muted": bool(track.mute), "solo": bool(track.is_solo), "strips": [{"name": strip.name, "action": strip.action.name if strip.action else None, "frame_start": float(strip.frame_start), "frame_end": float(strip.frame_end), "blend_type": strip.blend_type, "muted": bool(strip.mute)} for strip in track.strips]} for track in getattr(anim, "nla_tracks", [])]
    def create_nla_track(self, object_name, track_name):
        obj, anim = self._object_anim(object_name)
        if any(track.name == track_name for track in anim.nla_tracks): return {"status": "error", "message": f"NLA track already exists: {track_name}"}
        track = anim.nla_tracks.new(); track.name = track_name
        return {"status": "success", "object_name": obj.name, "track": {"name": track.name}}
    def add_action_to_nla(self, object_name, action_name, track_name=None, strip_name=None, frame_start=1, frame_end=None, blend_type="REPLACE"):
        obj, anim = self._object_anim(object_name); action = bpy.data.actions.get(action_name or "")
        if not action: return {"status": "error", "message": f"Action not found: {action_name}"}
        track = next((item for item in anim.nla_tracks if item.name == track_name), None) if track_name else None
        if track is None: track = anim.nla_tracks.new(); track.name = track_name or f"{action.name}_Track"
        end = float(frame_end if frame_end is not None else (frame_start + max(1.0, action.frame_range[1] - action.frame_range[0])))
        strip = track.strips.new(strip_name or action.name, float(frame_start), action); strip.frame_end = end; strip.blend_type = blend_type
        return {"status": "success", "object_name": obj.name, "track": track.name, "strip": {"name": strip.name, "frame_start": float(strip.frame_start), "frame_end": float(strip.frame_end)}}
    def edit_nla_strip(self, object_name, track_name, strip_name, frame_start=None, frame_end=None, mute=None, blend_type=None):
        obj, anim = self._object_anim(object_name)
        for track in anim.nla_tracks:
            if track.name == track_name:
                for strip in track.strips:
                    if strip.name == strip_name:
                        if frame_start is not None: strip.frame_start = float(frame_start)
                        if frame_end is not None: strip.frame_end = float(frame_end)
                        if mute is not None: strip.mute = bool(mute)
                        if blend_type: strip.blend_type = blend_type
                        return {"status": "success", "object_name": obj.name, "strip": {"name": strip.name, "frame_start": float(strip.frame_start), "frame_end": float(strip.frame_end), "muted": bool(strip.mute)}}
        return {"status": "error", "message": "NLA strip not found."}
    def mute_nla_track(self, object_name, track_name, mute=True):
        obj, anim = self._object_anim(object_name)
        for track in anim.nla_tracks:
            if track.name == track_name: track.mute = bool(mute); return {"status": "success", "object_name": obj.name, "track": {"name": track.name, "muted": bool(track.mute)}}
        return {"status": "error", "message": "NLA track not found."}
    def delete_nla_tracks(self, object_name, track_names, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Deleting NLA tracks requires confirmation.", "track_names": track_names}
        obj, anim = self._object_anim(object_name); removed = []
        for track in list(anim.nla_tracks):
            if track.name in (track_names or []): removed.append(track.name); anim.nla_tracks.remove(track)
        return {"status": "success", "object_name": obj.name, "removed": removed}
    def validate_nla_stack(self, object_name):
        obj, anim = self._object_anim(object_name); strips = [{"track_name": track.name, "name": strip.name, "frame_start": float(strip.frame_start), "frame_end": float(strip.frame_end)} for track in anim.nla_tracks for strip in track.strips]
        result = phase9a_validate_nla_overlaps(strips); result.update({"object_name": obj.name, "tracks": self._nla_tracks(anim)}); return result


class DriverDSLService:
    def __init__(self, server): self.server = server
    def validate_driver_dsl(self, dsl):
        result = phase9a_validate_driver_dsl(dsl or {}); result["compiled"] = phase9a_compile_driver_expression(dsl or {}); return result
    def _target_id(self, target_type, target_name):
        target_type = str(target_type or "OBJECT").upper()
        if target_type in {"OBJECT", "ARMATURE"}: return bpy.data.objects.get(target_name or "")
        if target_type == "MATERIAL": return bpy.data.materials.get(target_name or "")
        if target_type == "SHAPE_KEY": return bpy.data.shape_keys.get(target_name or "")
        return None
    def create_driver_from_dsl(self, target_type, target_name, data_path, dsl, array_index=-1, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Driver creation requires confirmation and allowlisted DSL.", "dsl": dsl}
        target = self._target_id(target_type, target_name)
        if not target: return {"status": "error", "message": f"Target not found: {target_type}:{target_name}"}
        compiled = phase9a_compile_driver_expression(dsl or {}); fcurve = target.driver_add(data_path, int(array_index)) if int(array_index) >= 0 else target.driver_add(data_path)
        driver = fcurve.driver; driver.type = "SCRIPTED"; driver.expression = compiled["expression"]; driver.variables.clear()
        mapping = {"location.x": ("location", 0), "location.y": ("location", 1), "location.z": ("location", 2), "rotation_euler.x": ("rotation_euler", 0), "rotation_euler.y": ("rotation_euler", 1), "rotation_euler.z": ("rotation_euler", 2), "scale.x": ("scale", 0), "scale.y": ("scale", 1), "scale.z": ("scale", 2)}
        for var_spec in compiled["variables"]:
            var = driver.variables.new(); var.name = var_spec["name"]; var.targets[0].id = self._target_id(var_spec["target_type"], var_spec["target_name"])
            data_path_mapped, index = mapping.get(var_spec["data_path"], (var_spec["data_path"], -1)); var.targets[0].data_path = data_path_mapped if index < 0 else f"{data_path_mapped}[{index}]"
        return {"status": "success", "target": target_name, "data_path": data_path, "array_index": int(array_index), "driver": {"expression": driver.expression, "dsl_only": True, "operation": compiled["operation"]}}
    def _drivers_for_id(self, datablock):
        anim = getattr(datablock, "animation_data", None)
        return [{"data_path": fcurve.data_path, "array_index": int(fcurve.array_index), "expression": fcurve.driver.expression, "variables": [var.name for var in fcurve.driver.variables]} for fcurve in (getattr(anim, "drivers", []) if anim else [])]
    def list_drivers(self, target_type=None, target_name=None):
        targets = [self._target_id(target_type, target_name)] if target_name else list(bpy.data.objects) + list(bpy.data.materials); rows = []
        for target in [item for item in targets if item is not None]:
            for driver in self._drivers_for_id(target): rows.append({"target_name": target.name, **driver})
        return {"status": "success", "drivers": rows}
    def get_driver_info(self, target_type, target_name, data_path, array_index=-1):
        target = self._target_id(target_type, target_name)
        if not target: return {"status": "error", "message": "Target not found."}
        return {"status": "success", "drivers": [row for row in self._drivers_for_id(target) if row["data_path"] == data_path and (int(array_index) < 0 or row["array_index"] == int(array_index))]}
    def remove_drivers(self, target_type, target_name, data_paths, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Removing drivers requires confirmation.", "data_paths": data_paths}
        target = self._target_id(target_type, target_name)
        if not target: return {"status": "error", "message": "Target not found."}
        removed = []
        for item in data_paths or []:
            path = item.get("data_path") if isinstance(item, dict) else item; index = int(item.get("array_index", -1)) if isinstance(item, dict) else -1
            try: target.driver_remove(path, index) if index >= 0 else target.driver_remove(path); removed.append({"data_path": path, "array_index": index})
            except Exception as exc: removed.append({"data_path": path, "array_index": index, "error": str(exc)})
        return {"status": "success", "removed": removed}


class RigTemplateService:
    def __init__(self, server): self.server = server
    def create_rig_template(self, armature_name, template="basic_biped", bones=None, collection_name=None, location=None):
        bones = bones or [{"name": "root", "head": [0, 0, 0], "tail": [0, 0, 1]}, {"name": "spine", "head": [0, 0, 1], "tail": [0, 0, 2], "parent": "root"}]
        result = self.server.rigging_simulation_service.create_armature(armature_name=armature_name, bones=bones, collection_name=collection_name, location=location)
        if result.get("status") == "success": result["template"] = template
        return result
    def create_control_bones(self, armature_name, controls=None): return {"status": "success", "armature_name": armature_name, "controls": controls or [], "classification": "metadata_control_recipe", "warnings": ["Control bones are recipe-backed by default."]}
    def create_ik_chain(self, armature_name, owner_bone, target_object=None, target_bone=None, chain_count=2, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "IK chain creation requires confirmation and exact targets."}
        return self.server.rig_validation_service.add_rig_constraint(armature_name, owner_bone, "IK", target_object=target_object, target_bone=target_bone, settings={"chain_count": chain_count})
    def add_custom_rig_properties(self, armature_name, properties):
        obj = bpy.data.objects.get(armature_name or "")
        if not obj or obj.type != "ARMATURE": return {"status": "error", "message": f"Armature not found: {armature_name}"}
        added = []
        for prop in properties or []:
            obj[prop.get("name")] = prop.get("default"); added.append(prop.get("name"))
        return {"status": "success", "armature_name": obj.name, "properties": added}


class RigValidationService:
    def __init__(self, server): self.server = server
    def add_rig_constraint(self, armature_name, bone_name, constraint_type, target_object=None, target_bone=None, settings=None):
        obj = bpy.data.objects.get(armature_name or "")
        if not obj or obj.type != "ARMATURE" or not obj.pose or bone_name not in obj.pose.bones: return {"status": "error", "message": "Armature or pose bone not found."}
        bone = obj.pose.bones[bone_name]; con = bone.constraints.new(type=constraint_type)
        if target_object: con.target = bpy.data.objects.get(target_object)
        if target_bone and hasattr(con, "subtarget"): con.subtarget = target_bone
        for key, value in (settings or {}).items():
            if hasattr(con, key): setattr(con, key, value)
        return {"status": "success", "constraint": {"name": con.name, "type": con.type, "owner_bone": bone.name, "target": target_object, "target_bone": target_bone}}
    def remove_rig_constraints(self, armature_name, bone_name, constraint_names, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Removing rig constraints requires confirmation."}
        obj = bpy.data.objects.get(armature_name or "")
        if not obj or obj.type != "ARMATURE" or bone_name not in obj.pose.bones: return {"status": "error", "message": "Armature or pose bone not found."}
        bone, removed = obj.pose.bones[bone_name], []
        for con in list(bone.constraints):
            if con.name in (constraint_names or []): removed.append(con.name); bone.constraints.remove(con)
        return {"status": "success", "removed": removed}
    def validate_rig(self, armature_name):
        obj = bpy.data.objects.get(armature_name or "")
        if not obj or obj.type != "ARMATURE": return {"status": "error", "message": f"Armature not found: {armature_name}"}
        bones = [{"name": bone.name, "parent": bone.parent.name if bone.parent else None} for bone in obj.data.bones]; issues = []
        for pose_bone in obj.pose.bones:
            for con in pose_bone.constraints:
                if hasattr(con, "target") and getattr(con, "target", None) is None and con.type in {"COPY_LOCATION", "COPY_ROTATION", "IK", "DAMPED_TRACK", "TRACK_TO", "CHILD_OF"}: issues.append({"bone": pose_bone.name, "constraint": con.name, "issue": "missing_target"})
        return {"status": "success", "armature_name": obj.name, "bone_count": len(bones), "name_check": phase9a_validate_rig_names([b["name"] for b in bones]), "hierarchy_check": phase9a_validate_bone_hierarchy(bones), "constraint_issues": issues, "valid": not issues}


class PoseLibraryWorkflowService:
    def __init__(self, server): self.server = server; self.snapshots = {}; self.assets = {}
    def inspect_pose(self, armature_name):
        obj = bpy.data.objects.get(armature_name or "")
        if not obj or obj.type != "ARMATURE": return {"status": "error", "message": f"Armature not found: {armature_name}"}
        return {"status": "success", "armature_name": obj.name, "bones": {bone.name: {"location": list(bone.location), "rotation_euler": list(bone.rotation_euler), "scale": list(bone.scale)} for bone in obj.pose.bones}}
    def create_pose_snapshot(self, armature_name, snapshot_id=None, include_custom_properties=True):
        pose = self.inspect_pose(armature_name)
        if pose.get("status") != "success": return pose
        sid = snapshot_id or f"pose_{int(time.time() * 1000)}"; snapshot = {"snapshot_id": sid, "armature_name": armature_name, "frame": int(bpy.context.scene.frame_current), "bones": pose["bones"], "storage": "memory_manifest"}; self.snapshots[sid] = snapshot
        return {"status": "success", "snapshot": snapshot}
    def apply_pose_snapshot(self, snapshot_id, armature_name=None, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Applying a pose snapshot mutates pose data and requires confirmation.", "snapshot_id": snapshot_id}
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot: return {"status": "error", "message": f"Pose snapshot not found: {snapshot_id}"}
        obj = bpy.data.objects.get(armature_name or snapshot["armature_name"])
        if not obj or obj.type != "ARMATURE": return {"status": "error", "message": "Armature not found."}
        applied = []
        for name, data in snapshot["bones"].items():
            if name in obj.pose.bones:
                bone = obj.pose.bones[name]; bone.location = data["location"]; bone.rotation_euler = data["rotation_euler"]; bone.scale = data["scale"]; applied.append(name)
        return {"status": "success", "applied_bones": applied}
    def create_pose_asset(self, snapshot_id, asset_name, native_asset=False):
        if snapshot_id not in self.snapshots: return {"status": "error", "message": f"Pose snapshot not found: {snapshot_id}"}
        aid = f"pose_asset_{hashlib.sha256(asset_name.encode('utf-8')).hexdigest()[:12]}"; self.assets[aid] = {"asset_id": aid, "name": asset_name, "snapshot_id": snapshot_id, "native_asset": False, "storage": "manifest", "classification": "manifest_backed_pose_asset"}
        return {"status": "success", "pose_asset": self.assets[aid], "warnings": ["Native pose asset creation is not claimed; this is manifest-backed."]}
    def list_pose_assets(self, armature_name=None): return {"status": "success", "pose_assets": list(self.assets.values()), "storage": "manifest"}
    def compare_poses(self, source_snapshot_id, target_snapshot_id):
        a, b = self.snapshots.get(source_snapshot_id), self.snapshots.get(target_snapshot_id)
        if not a or not b: return {"status": "error", "message": "Both pose snapshots must exist."}
        changed = [name for name, pose in a["bones"].items() if b["bones"].get(name) != pose]
        return {"status": "success", "source_id": source_snapshot_id, "target_id": target_snapshot_id, "changed_bones": changed, "max_delta": 0.0 if not changed else None}
    def delete_pose_assets(self, asset_ids, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Deleting pose assets requires confirmation.", "asset_ids": asset_ids}
        return {"status": "success", "removed": [aid for aid in (asset_ids or []) if self.assets.pop(aid, None) is not None]}


class ShotWorkflowService:
    def __init__(self, server): self.server = server; self.shot_plans = {}
    def create_shot_range(self, name, frame_start, frame_end, camera_name=None, set_scene_range=False):
        if frame_end < frame_start: return {"status": "error", "message": "frame_end must be >= frame_start"}
        if camera_name and camera_name not in bpy.data.objects: return {"status": "error", "message": f"Camera not found: {camera_name}"}
        if set_scene_range: bpy.context.scene.frame_start = int(frame_start); bpy.context.scene.frame_end = int(frame_end)
        return {"status": "success", "shot_range": {"name": name, "frame_start": int(frame_start), "frame_end": int(frame_end), "camera_name": camera_name}}
    def create_camera_cut(self, name, frame, camera_name):
        camera = bpy.data.objects.get(camera_name or "")
        if not camera or camera.type != "CAMERA": return {"status": "error", "message": f"Camera not found: {camera_name}"}
        marker = bpy.context.scene.timeline_markers.new(name, frame=int(frame)); marker.camera = camera
        return {"status": "success", "camera_cut": {"name": marker.name, "frame": int(marker.frame), "camera_name": camera.name}}
    def create_timeline_marker(self, name, frame, camera_name=None):
        marker = bpy.context.scene.timeline_markers.new(name, frame=int(frame))
        if camera_name: marker.camera = bpy.data.objects.get(camera_name)
        return {"status": "success", "marker": {"name": marker.name, "frame": int(marker.frame), "camera_name": marker.camera.name if marker.camera else None}}
    def create_shot_plan(self, plan_name, ranges=None, cuts=None, markers=None):
        plan = {"name": plan_name, "ranges": ranges or [], "cuts": cuts or [], "markers": markers or []}; self.shot_plans[plan_name] = plan; plan["validation"] = self.validate_shot_plan(plan_name)
        return {"status": "success", "shot_plan": plan}
    def validate_shot_plan(self, plan_name=None, plan=None):
        plan = plan or self.shot_plans.get(plan_name or "")
        if not plan: return {"status": "error", "message": "Shot plan not found."}
        issues = []
        for shot in plan.get("ranges", []):
            if shot.get("frame_end", 0) < shot.get("frame_start", 0): issues.append({"severity": "error", "message": "Invalid shot range", "shot_name": shot.get("name")})
            if shot.get("camera_name") and shot.get("camera_name") not in bpy.data.objects: issues.append({"severity": "error", "message": "Missing shot camera", "shot_name": shot.get("name")})
        return {"status": "success", "valid": not issues, "issues": issues, "plan_name": plan.get("name")}


class SimulationWorkflowService:
    def __init__(self, server): self.server = server
    def _cache_summary(self, point_cache): return {"frame_start": int(point_cache.frame_start), "frame_end": int(point_cache.frame_end), "is_baked": bool(getattr(point_cache, "is_baked", False)), "name": getattr(point_cache, "name", "")} if point_cache else None
    def _object_simulation_summary(self, obj):
        return {"modifiers": [{"name": mod.name, "type": mod.type, "cache": self._cache_summary(getattr(mod, "point_cache", None))} for mod in getattr(obj, "modifiers", []) if mod.type in {"CLOTH", "SOFT_BODY"}], "rigid_body": bool(getattr(obj, "rigid_body", None))}
    def get_simulation_capabilities(self): result = self.server.animation_intelligence_advanced_service.get_animation_system_capabilities()["simulation"]; result["status"] = "success"; return result
    def inspect_simulation_state(self, object_names=None):
        names = object_names or [obj.name for obj in bpy.context.scene.objects]
        return {"status": "success", "objects": [{"name": name, **self._object_simulation_summary(bpy.data.objects[name])} for name in names if name in bpy.data.objects], "rigid_body_world": bool(getattr(bpy.context.scene, "rigidbody_world", None))}
    def configure_rigidbody_basic(self, object_name, body_type="ACTIVE", mass=1.0):
        obj = bpy.data.objects.get(object_name or "")
        if not obj: return {"status": "error", "message": f"Object not found: {object_name}"}
        bpy.context.view_layer.objects.active = obj; obj.select_set(True)
        try: bpy.ops.rigidbody.object_add(type=body_type); obj.rigid_body.mass = float(mass); return {"status": "success", "object_name": obj.name, "rigid_body": {"type": obj.rigid_body.type, "mass": obj.rigid_body.mass}}
        except Exception as exc: return {"status": "unsupported", "message": str(exc)}
    def configure_cloth_simulation_advanced(self, object_name, frame_start=1, frame_end=48, settings=None):
        obj = bpy.data.objects.get(object_name or "")
        if not obj or obj.type != "MESH": return {"status": "error", "message": f"Mesh object not found: {object_name}"}
        mod = obj.modifiers.new("Overtli_Cloth_Advanced", "CLOTH"); cache = getattr(mod, "point_cache", None)
        if cache: cache.frame_start = int(frame_start); cache.frame_end = int(frame_end)
        for key, value in (settings or {}).items():
            if hasattr(mod.settings, key): setattr(mod.settings, key, value)
        return {"status": "success", "object_name": obj.name, "modifier": mod.name, "cache": self._cache_summary(cache), "bounded": True}
    def configure_softbody_basic(self, object_name, frame_start=1, frame_end=48):
        obj = bpy.data.objects.get(object_name or "")
        if not obj or obj.type != "MESH": return {"status": "error", "message": f"Mesh object not found: {object_name}"}
        mod = obj.modifiers.new("Overtli_SoftBody_Basic", "SOFT_BODY"); cache = getattr(mod, "point_cache", None)
        if cache: cache.frame_start = int(frame_start); cache.frame_end = int(frame_end)
        return {"status": "success", "object_name": obj.name, "modifier": mod.name, "cache": self._cache_summary(cache)}
    def configure_hair_curve_dynamics_basic(self, object_name, frame_start=1, frame_end=48): return {"status": "unsupported", "object_name": object_name, "message": "Hair curve dynamics are inspected but not configured automatically in Phase 9A."}
    def get_simulation_cache_status(self, object_name=None):
        names = [object_name] if object_name else [obj.name for obj in bpy.context.scene.objects]; rows = []
        for name in names:
            obj = bpy.data.objects.get(name or "")
            if obj:
                for mod in obj.modifiers:
                    if hasattr(mod, "point_cache"): rows.append({"object_name": obj.name, "modifier": mod.name, "type": mod.type, "cache": self._cache_summary(mod.point_cache)})
        return {"status": "success", "caches": rows}
    def simulate_preview_range(self, object_name, frame_start=1, frame_end=24, max_frames=48, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Simulation preview changes evaluated frame and requires exact target confirmation.", "object_name": object_name}
        return {"status": "success", "object_name": object_name, "frame_start": frame_start, "frame_end": min(frame_end, frame_start + max_frames - 1), "previewed": False, "warnings": ["Phase 9A reports bounded preview plan; cache baking is not run by default."]}
    def bake_simulation_cache(self, object_name=None, world=False, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Simulation cache bake requires exact object/world target and confirmation.", "object_name": object_name, "world": world}
        return {"status": "unsupported", "message": "Cache baking is approval-gated and not executed automatically in Phase 9A.", "object_name": object_name, "world": world}
    def clear_simulation_cache(self, object_name=None, world=False, confirm=False):
        if not confirm: return {"status": "requires_approval", "message": "Simulation cache clear requires exact object/world target and confirmation.", "object_name": object_name, "world": world}
        return {"status": "unsupported", "message": "Cache clearing is approval-gated and not executed automatically in Phase 9A.", "object_name": object_name, "world": world}


class MotionValidationService:
    def __init__(self, server): self.server = server
    def create_motion_path_preview(self, object_name, frame_start=None, frame_end=None):
        obj = bpy.data.objects.get(object_name or "")
        if not obj: return {"status": "error", "message": f"Object not found: {object_name}"}
        return {"status": "success", "object_name": obj.name, "motion_path_preview": {"frame_start": frame_start or bpy.context.scene.frame_start, "frame_end": frame_end or bpy.context.scene.frame_end, "classification": "plan_only"}, "warnings": ["Motion path calculation is context-dependent; Phase 9A returns a bounded preview plan."]}
    def validate_motion(self, object_names=None, include_rig=True, include_drivers=True, include_nla=True, include_simulation=True):
        reports = []
        for name in (object_names or [obj.name for obj in bpy.context.scene.objects]):
            obj = bpy.data.objects.get(name)
            if not obj: reports.append({"name": name, "status": "missing"}); continue
            item = {"name": obj.name, "type": obj.type, "issues": []}
            if include_drivers: item["drivers"] = self.server.driver_dsl_service.list_drivers("OBJECT", obj.name).get("drivers", [])
            if include_nla and obj.animation_data: item["nla"] = self.server.nla_workflow_service.validate_nla_stack(obj.name)
            if include_rig and obj.type == "ARMATURE": item["rig"] = self.server.rig_validation_service.validate_rig(obj.name)
            if include_simulation: item["simulation"] = self.server.simulation_workflow_service._object_simulation_summary(obj)
            reports.append(item)
        return {"status": "success", "reports": reports}


class AnimationRiggingWorkflowBatchService:
    def __init__(self, server): self.server = server
    def run_animation_rigging_workflow_batch(self, label=None, operations=None, stop_on_error=True, max_operations=40, allow_high_risk=False):
        high = {"delete_actions", "delete_nla_tracks", "remove_drivers", "apply_pose_snapshot", "delete_pose_assets", "simulate_preview_range", "bake_simulation_cache", "clear_simulation_cache"}
        handlers, results = self.server._build_command_handlers(), []
        for op in (operations or [])[: int(max_operations)]:
            command, params = op.get("command"), op.get("params", {})
            if command not in handlers: result = {"status": "error", "message": f"Unknown command: {command}"}
            elif command in high and not allow_high_risk: result = {"status": "blocked", "message": f"High-risk operation blocked in batch: {command}"}
            else: result = handlers[command](**params)
            results.append({"command": command, "result": result})
            if stop_on_error and result.get("status") not in {"success", "unsupported", "requires_approval"}: break
        return {"status": "success", "label": label, "results": results}


PHASE9A_COMMANDS = ["get_animation_system_capabilities", "inspect_animation_system", "list_actions", "get_action_deep_info", "create_action", "duplicate_action", "rename_action", "assign_action", "delete_actions", "insert_keyframe_batch", "edit_keyframes", "retime_action", "set_fcurve_interpolation", "add_fcurve_modifier", "remove_fcurve_modifier", "validate_fcurves", "create_nla_track", "add_action_to_nla", "edit_nla_strip", "mute_nla_track", "delete_nla_tracks", "validate_nla_stack", "create_driver_from_dsl", "validate_driver_dsl", "list_drivers", "get_driver_info", "remove_drivers", "create_rig_template", "create_control_bones", "create_ik_chain", "add_rig_constraint", "remove_rig_constraints", "add_custom_rig_properties", "validate_rig", "inspect_pose", "create_pose_snapshot", "apply_pose_snapshot", "create_pose_asset", "list_pose_assets", "compare_poses", "delete_pose_assets", "create_shot_range", "create_camera_cut", "create_timeline_marker", "create_shot_plan", "validate_shot_plan", "create_motion_path_preview", "validate_motion", "get_simulation_capabilities", "inspect_simulation_state", "configure_rigidbody_basic", "configure_cloth_simulation_advanced", "configure_softbody_basic", "configure_hair_curve_dynamics_basic", "get_simulation_cache_status", "simulate_preview_range", "bake_simulation_cache", "clear_simulation_cache", "run_animation_rigging_workflow_batch"]
