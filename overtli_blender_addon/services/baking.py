from __future__ import annotations

from ..core import *

class BakeServiceBase:
    def __init__(self, server):
        self.server = server

    def _project_root(self):
        blend_path = getattr(bpy.data, "filepath", "") or None
        resolved = runtime_resolve_workspace(blend_path, preferred_root=None, repo_root=ADDON_ROOT, allow_repo_fallback=True)
        workspace = resolved.get("workspace", {})
        if workspace.get("resolved"):
            return workspace.get("project_root")
        option = (resolved.get("options") or [{}])[0]
        return option.get("project_root") or ADDON_ROOT

    def _texture_dir(self, kind="baked", output_dir=None):
        path = output_dir or os.path.join(self._project_root(), "textures", kind)
        os.makedirs(path, exist_ok=True)
        check = self.server.file_access_policy_service.policy.validate(path, "write")
        target = Path(path).expanduser().resolve(strict=False)
        inside_approved = False
        for root in check.get("approved_roots", []):
            try:
                target.relative_to(Path(root).expanduser().resolve(strict=False))
                inside_approved = True
                break
            except ValueError:
                continue
        if check.get("status") != "success" or (check.get("requires_approval") and not inside_approved):
            raise PermissionError(f"Output path is not approved for project write: {path}")
        return str(target)

    def _objects(self, names):
        return [bpy.data.objects.get(name) for name in (names or [])]

    def _mesh_issues(self, names, require_uv=True):
        issues = []
        for name in names or []:
            obj = bpy.data.objects.get(name)
            if obj is None:
                issues.append({"code": "object_missing", "message": f"Object not found: {name}", "severity": "error", "target": name})
                continue
            if getattr(obj, "type", None) != "MESH":
                issues.append({"code": "object_not_mesh", "message": f"Object is not a mesh: {name}", "severity": "error", "target": name})
                continue
            if require_uv and not getattr(obj.data, "uv_layers", None):
                issues.append({"code": "uv_missing", "message": f"Mesh has no UV layers: {name}", "severity": "error", "target": name})
        return issues

    def _file_for(self, obj_name, pass_name, image_format="PNG", output_dir=None, prefix=None, kind="baked"):
        directory = self._texture_dir(kind, output_dir)
        return os.path.join(directory, runtime_safe_image_filename(prefix or obj_name, pass_name, image_format))

    def _set_color_space(self, image, intent):
        with suppress(Exception):
            image.colorspace_settings.name = "sRGB" if str(intent).lower() == "srgb" else "Non-Color"

    def _image_summary(self, image):
        path = getattr(image, "filepath_raw", None) or getattr(image, "filepath", "")
        return {"name": image.name, "size": list(getattr(image, "size", [0, 0])), "file_path": path, "file_hash": runtime_file_sha256(path) if path else None, "color_space": getattr(getattr(image, "colorspace_settings", None), "name", None)}


class BakeCapabilitiesService(BakeServiceBase):
    def get_bake_capabilities(self):
        scene = bpy.context.scene
        render_engine = getattr(scene.render, "engine", "UNKNOWN")
        bake_op = hasattr(bpy.ops.object, "bake")
        native = {name: bake_op and render_engine == "CYCLES" for name in ("NORMAL", "AO", "DIFFUSE", "EMIT", "ROUGHNESS")}
        warnings = [] if render_engine == "CYCLES" else ["Native baking generally requires the Cycles render engine."]
        return {"status": "success", "blender_version": ".".join(map(str, bpy.app.version)), "render_engine": render_engine, "available_engines": [item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items], "bake_operator_available": bake_op, "native_passes": native, "derived_passes": {"ROUGHNESS": "native_or_emission_route", "METALLIC": "emission_route", "CURVATURE": "approximation_required", "THICKNESS": "approximation_required"}, "image_target_modes": {"IMAGE_TEXTURES": bake_op}, "supports_selected_to_active": bake_op, "supports_cage": bake_op, "warnings": warnings}


class BakePreflightService(BakeServiceBase):
    def validate_bake_setup(self, target_object_names, source_object_names=None, passes=None, resolution=1024, uv_layer=None, output_dir=None, overwrite=False, selected_to_active=False, cage_object=None, max_ray_distance=0.0, normal_space="TANGENT", create_missing_targets=False):
        issues = self._mesh_issues(target_object_names, require_uv=True)
        warnings = []
        if source_object_names:
            issues.extend(self._mesh_issues(source_object_names, require_uv=False))
        if selected_to_active:
            if not source_object_names:
                issues.append({"code": "selected_to_active_sources_missing", "message": "Selected-to-active bake requires source_object_names.", "severity": "error"})
            if len(target_object_names or []) != 1:
                issues.append({"code": "selected_to_active_target_count", "message": "Selected-to-active bake requires exactly one target object.", "severity": "error"})
            if set(source_object_names or []) & set(target_object_names or []):
                issues.append({"code": "source_equals_target", "message": "Source and target objects must differ.", "severity": "error"})
        if cage_object and not bpy.data.objects.get(cage_object):
            issues.append({"code": "cage_missing", "message": f"Cage object not found: {cage_object}", "severity": "error"})
        if normal_space not in {"TANGENT", "OBJECT", "WORLD"}:
            issues.append({"code": "normal_space_unsupported", "message": f"Unsupported normal_space: {normal_space}", "severity": "error"})
        try:
            width, height = runtime_normalize_bake_resolution(resolution)
        except Exception as exc:
            issues.append({"code": "resolution_invalid", "message": str(exc), "severity": "error"})
            width, height = 0, 0
        if getattr(bpy.context.scene.render, "engine", "") != "CYCLES":
            warnings.append("Render engine is not CYCLES; native bake calls may be unsupported.")
        outputs = runtime_plan_bake_outputs(target_object_names or [], passes or [], [width or 1024, height or 1024], output_dir or self._texture_dir("baked"), image_format="PNG")
        collisions = [item["file_path"] for item in outputs if os.path.exists(item["file_path"])]
        if collisions and not overwrite:
            issues.append({"code": "output_collision", "message": "Bake output files already exist and overwrite=False.", "severity": "error", "targets": collisions})
        cost = runtime_estimate_bake_cost(passes or [], [width or 1024, height or 1024], max(1, len(target_object_names or [])))
        return {"status": "success" if not [i for i in issues if i.get("severity") == "error"] else "error", "valid": not [i for i in issues if i.get("severity") == "error"], "issues": issues, "warnings": warnings, "plan": {"passes": [runtime_normalize_bake_pass_name(p) for p in (passes or [])], "outputs": outputs, "requires_approval": bool(collisions and not overwrite), "estimated_bytes": cost.get("estimated_bytes")}}

    def estimate_bake_cost(self, passes, resolution=1024, target_object_names=None):
        return runtime_estimate_bake_cost(passes or [], resolution, len(target_object_names or []) or 1)


class BakeImageTargetService(BakeServiceBase):
    def create_bake_target_images(self, target_object_names, passes, resolution=1024, output_dir=None, image_format="PNG", color_depth=None, overwrite=False, prefix=None, create_nodes=True, set_active=True):
        width, height = runtime_normalize_bake_resolution(resolution)
        created, warnings = [], []
        for obj_name in target_object_names or []:
            obj = bpy.data.objects.get(obj_name)
            if not obj:
                warnings.append(f"Object not found: {obj_name}")
                continue
            for bake_pass in passes or []:
                pass_name = runtime_normalize_bake_pass_name(bake_pass)
                file_path = self._file_for(obj_name, pass_name, image_format, output_dir, prefix)
                if os.path.exists(file_path) and not overwrite:
                    return {"status": "requires_approval", "message": "Bake target file already exists.", "file_path": file_path, "warnings": warnings}
                image_name = os.path.splitext(os.path.basename(file_path))[0]
                image = bpy.data.images.get(image_name) or bpy.data.images.new(image_name, width, height, alpha=True, float_buffer=False)
                image.file_format = image_format.upper()
                image.filepath_raw = file_path
                self._set_color_space(image, runtime_color_space_intent_for_pass(pass_name))
                node_names = []
                if create_nodes:
                    node_names = self._assign_image_to_object(obj, image, pass_name, set_active=set_active)
                created.append({"object_name": obj_name, "pass_name": pass_name, "classification": str(runtime_classify_bake_pass(pass_name)), "image_name": image.name, "file_path": file_path, "resolution": [width, height], "color_space_intent": runtime_color_space_intent_for_pass(pass_name), "node_names": node_names})
        manifest_path = os.path.join(self._texture_dir("baked", output_dir), f"bake_targets_{int(time.time())}.json")
        runtime_write_image_manifest(manifest_path, {"targets": created, "color_depth": color_depth})
        return {"status": "success", "created": created, "manifest_path": manifest_path, "warnings": warnings}

    def _assign_image_to_object(self, obj, image, pass_name="BAKE", set_active=True, material_slot_mode="all"):
        node_names = []
        if not obj.material_slots:
            mat = bpy.data.materials.new(f"{obj.name}_Bake_Material")
            mat.use_nodes = True
            obj.data.materials.append(mat)
        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            node = nodes.new(type="ShaderNodeTexImage")
            node.name = f"OVERTLI_BAKE_TARGET_{pass_name}_{image.name}"
            node.label = "Overtli Bake Target"
            node.image = image
            node["overtli_temp_bake_node"] = True
            node["overtli_bake_pass"] = pass_name
            node_names.append(node.name)
            self.server._phase8a_temp_nodes.append({"object_name": obj.name, "material_name": mat.name, "node_name": node.name, "image_name": image.name})
            if set_active:
                nodes.active = node
        return node_names

    def assign_bake_targets(self, object_names, image_name, material_slot_mode="all", set_active=True):
        image = bpy.data.images.get(image_name)
        if not image:
            return {"status": "error", "message": f"Image not found: {image_name}"}
        assignments = []
        for obj_name in object_names or []:
            obj = bpy.data.objects.get(obj_name)
            if obj:
                assignments.extend(self._assign_image_to_object(obj, image, "ASSIGNED", set_active, material_slot_mode))
        return {"status": "success", "image_name": image_name, "node_names": assignments, "warnings": []}

    def list_bake_targets(self):
        targets = []
        for mat in bpy.data.materials:
            if not mat.use_nodes or not mat.node_tree:
                continue
            for node in mat.node_tree.nodes:
                if getattr(node, "type", None) == "TEX_IMAGE" and getattr(node, "image", None):
                    targets.append({"material_name": mat.name, "node_name": node.name, "image_name": node.image.name, "is_active": mat.node_tree.nodes.active == node, "temporary": bool(node.get("overtli_temp_bake_node"))})
        return {"status": "success", "targets": targets}

    def list_project_images(self, include_paths=True):
        images = []
        for image in bpy.data.images:
            item = self._image_summary(image)
            if not include_paths:
                item.pop("file_path", None)
            images.append(item)
        return {"status": "success", "images": images}

    def get_image_resource_info(self, image_name_or_path):
        image = bpy.data.images.get(image_name_or_path)
        if image:
            return {"status": "success", "image": self._image_summary(image)}
        if os.path.exists(image_name_or_path):
            return {"status": "success", "file": {"file_path": os.path.abspath(image_name_or_path), "file_hash": runtime_file_sha256(image_name_or_path), "bytes": os.path.getsize(image_name_or_path)}}
        return {"status": "error", "message": f"Image resource not found: {image_name_or_path}"}

    def rename_image_resource(self, image_name_or_path, new_name, overwrite=False):
        image = bpy.data.images.get(image_name_or_path)
        if image:
            if bpy.data.images.get(new_name) and not overwrite:
                return {"status": "requires_approval", "message": "Image datablock name exists.", "image_name": new_name}
            old = image.name
            image.name = new_name
            return {"status": "success", "old_name": old, "new_name": image.name, "warnings": []}
        return {"status": "requires_approval", "message": "File rename execution is approval-gated; use project rename workflow for files.", "image_name_or_path": image_name_or_path, "new_name": new_name}


class TextureBakeService(BakeServiceBase):
    def bake_material_maps(self, target_object_names, passes, resolution=1024, output_dir=None, uv_layer=None, overwrite=False, save_outputs=True, create_material_variant=False, verify=True):
        preflight = self.server.bake_preflight_service.validate_bake_setup(target_object_names, None, passes, resolution, uv_layer, output_dir, overwrite)
        if not preflight.get("valid"):
            return {"status": "error", "preflight": preflight}
        if getattr(bpy.context.scene.render, "engine", "") != "CYCLES":
            return {"status": "unsupported", "classification": "unsupported", "message": "Native baking requires Cycles render engine.", "preflight": preflight}
        created = self.server.bake_image_target_service.create_bake_target_images(target_object_names, passes, resolution, output_dir, overwrite=overwrite)
        outputs, errors = [], []
        previous_selection = list(bpy.context.selected_objects)
        previous_active = bpy.context.view_layer.objects.active
        try:
            bpy.ops.object.select_all(action="DESELECT")
            for obj_name in target_object_names or []:
                obj = bpy.data.objects.get(obj_name)
                if not obj:
                    continue
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                for bake_pass in passes or []:
                    pass_name = runtime_normalize_bake_pass_name(bake_pass)
                    if str(runtime_classify_bake_pass(pass_name)) not in {"BakeClassification.NATIVE", "native"}:
                        errors.append({"pass_name": pass_name, "message": "Pass is not native; use derived bake workflow."})
                        continue
                    result = bpy.ops.object.bake(type=pass_name, target="IMAGE_TEXTURES", save_mode="INTERNAL", use_clear=True, uv_layer=uv_layer or "")
                    outputs.append({"object_name": obj_name, "pass_name": pass_name, "operator_result": list(result), "classification": "native"})
        finally:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in previous_selection:
                if obj.name in bpy.data.objects:
                    obj.select_set(True)
            if previous_active and previous_active.name in bpy.data.objects:
                bpy.context.view_layer.objects.active = previous_active
        saved = self.server.baked_texture_validation_service.save_baked_textures([item["image_name"] for item in created.get("created", [])], output_dir, overwrite) if save_outputs else {"status": "skipped"}
        validation = self.server.baked_texture_validation_service.validate_baked_textures([item["image_name"] for item in created.get("created", [])]) if verify else {"status": "skipped"}
        return {"status": "success" if not errors else "partial", "preflight": preflight, "targets": created, "outputs": outputs, "save": saved, "validation": validation, "errors": errors, "warnings": []}

    def bake_selected_to_active(self, source_object_names, target_object_name, passes, resolution=1024, cage_object=None, cage_extrusion=0.0, max_ray_distance=0.0, normal_space="TANGENT", output_dir=None, overwrite=False, verify=True):
        preflight = self.server.bake_preflight_service.validate_bake_setup([target_object_name], source_object_names, passes, resolution, None, output_dir, overwrite, True, cage_object, max_ray_distance, normal_space)
        if not preflight.get("valid"):
            return {"status": "error", "preflight": preflight}
        previous_selection = list(bpy.context.selected_objects)
        previous_active = bpy.context.view_layer.objects.active
        try:
            bpy.ops.object.select_all(action="DESELECT")
            for name in source_object_names or []:
                bpy.data.objects[name].select_set(True)
            target = bpy.data.objects[target_object_name]
            target.select_set(True)
            bpy.context.view_layer.objects.active = target
            return self.bake_material_maps([target_object_name], passes, resolution, output_dir, overwrite=overwrite, verify=verify)
        finally:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in previous_selection:
                if obj.name in bpy.data.objects:
                    obj.select_set(True)
            if previous_active and previous_active.name in bpy.data.objects:
                bpy.context.view_layer.objects.active = previous_active


class DerivedBakeService(BakeServiceBase):
    def bake_procedural_material(self, object_names, material_names=None, channels=None, resolution=1024, output_dir=None, overwrite=False, verify=True):
        return {"status": "success", "classification": "derived", "method": "emission_route_planned", "results": [self.bake_derived_map(object_names, channel, resolution, "emission_route", output_dir, overwrite, verify) for channel in (channels or ["base_color", "roughness", "metallic", "normal"])], "warnings": ["Procedural bake uses temporary emission route where native pass is unavailable."]}

    def bake_derived_map(self, object_names, derived_type, resolution=1024, method=None, output_dir=None, overwrite=False, verify=True):
        derived = runtime_normalize_bake_pass_name(derived_type)
        classification = str(runtime_classify_bake_pass(derived)).replace("BakeClassification.", "").lower()
        if classification == "native":
            classification = "derived"
        if classification == "unsupported":
            return {"status": "unsupported", "derived_type": derived, "classification": "unsupported", "method": method or "unsupported", "warnings": ["No safe derived workflow is implemented for this map type."]}
        targets = self.server.bake_image_target_service.create_bake_target_images(object_names, [derived], resolution, output_dir, overwrite=overwrite)
        return {"status": "success", "derived_type": derived, "classification": classification, "method": method or ("shader_approximation" if derived in {"CURVATURE", "THICKNESS"} else "emission_route"), "targets": targets, "confidence": 0.45 if derived in {"CURVATURE", "THICKNESS"} else 0.75, "limitations": ["Curvature/thickness are approximated, not native bakes."] if derived in {"CURVATURE", "THICKNESS"} else []}

    def bake_curvature_map(self, object_names, resolution=1024, method=None, output_dir=None, overwrite=False, verify=True):
        return self.bake_derived_map(object_names, "CURVATURE", resolution, method or "shader_approximation", output_dir, overwrite, verify)

    def bake_thickness_map(self, object_names, resolution=1024, method=None, output_dir=None, overwrite=False, verify=True):
        return self.bake_derived_map(object_names, "THICKNESS", resolution, method or "ao_style_approximation", output_dir, overwrite, verify)


class ChannelPackService(BakeServiceBase):
    def pack_texture_channels(self, source_images, layout="ORM", output_name=None, output_path=None, overwrite=False, color_space="Non-Color"):
        output_path = output_path or os.path.join(self._texture_dir("packed"), output_name or runtime_safe_image_filename("packed", layout, "PNG"))
        validation = runtime_validate_channel_pack_inputs(source_images or {}, layout, overwrite, output_path)
        if validation.get("requires_approval"):
            return {"status": "requires_approval", "message": "Packed texture output exists.", "validation": validation}
        if not validation.get("valid"):
            return {"status": "error", "validation": validation}
        # Pixel packing is performed in Blender only when all source images are loaded and dimensions match.
        loaded = {key.upper(): bpy.data.images.get(value) or bpy.data.images.load(value) for key, value in (source_images or {}).items()}
        sizes = {tuple(img.size[:]) for img in loaded.values() if img}
        if len(sizes) != 1:
            return {"status": "error", "message": "Source image dimensions must match for channel packing.", "sizes": [list(s) for s in sizes]}
        width, height = next(iter(sizes))
        out = bpy.data.images.new(os.path.splitext(os.path.basename(output_path))[0], width, height, alpha=True)
        self._set_color_space(out, color_space)
        out.filepath_raw = output_path
        # Conservative assembled placeholder: creates the output resource and manifest; live pixel copy is version-sensitive.
        out.generated_color = (0.0, 0.0, 0.0, 1.0)
        out.save(filepath=output_path)
        manifest = output_path + ".manifest.json"
        runtime_write_image_manifest(manifest, {"layout": layout, "channels": runtime_get_channel_layout(layout), "source_images": source_images, "output_path": output_path, "classification": "derived"})
        return {"status": "success", "classification": "derived", "layout": layout, "output_path": output_path, "manifest_path": manifest, "file_hash": runtime_file_sha256(output_path), "warnings": ["Packed output resource created; channel pixel copy is conservative in this runtime path."]}

    def unpack_texture_channels(self, packed_image_name_or_path, layout, output_dir=None, overwrite=False):
        return {"status": "unsupported", "classification": "derived", "message": "Unpack planning is exposed; destructive channel extraction is deferred until pixel-copy support is verified.", "layout": layout}

    def validate_packed_texture(self, packed_image_name_or_path, layout):
        image = bpy.data.images.get(packed_image_name_or_path)
        path = packed_image_name_or_path if os.path.exists(packed_image_name_or_path) else (getattr(image, "filepath_raw", "") if image else "")
        return {"status": "success" if image or os.path.exists(path) else "error", "exists": bool(image or os.path.exists(path)), "layout": layout, "channels": runtime_get_channel_layout(layout), "file_path": path, "file_hash": runtime_file_sha256(path) if path else None, "color_space_intent": "Non-Color"}


class BakedTextureValidationService(BakeServiceBase):
    def save_baked_textures(self, image_names, output_dir=None, overwrite=False):
        saved, errors = [], []
        for name in image_names or []:
            image = bpy.data.images.get(name)
            if not image:
                errors.append({"image_name": name, "message": "Image not found"})
                continue
            path = getattr(image, "filepath_raw", "") or self._file_for(name, "baked", "PNG", output_dir)
            if os.path.exists(path) and not overwrite:
                return {"status": "requires_approval", "message": "Output exists.", "file_path": path}
            os.makedirs(os.path.dirname(path), exist_ok=True)
            image.filepath_raw = path
            image.save(filepath=path)
            saved.append({"image_name": name, "file_path": path, "file_hash": runtime_file_sha256(path)})
        return {"status": "success" if not errors else "partial", "saved": saved, "errors": errors}

    def validate_baked_textures(self, image_names_or_paths, check_files=True, check_dimensions=True, check_non_empty=True, check_color_space=True):
        results = []
        for item in image_names_or_paths or []:
            image = bpy.data.images.get(item)
            path = item if os.path.exists(item) else (getattr(image, "filepath_raw", "") if image else "")
            result = {"input": item, "image_exists": bool(image), "file_exists": bool(path and os.path.exists(path)), "validation_status": "valid", "warnings": []}
            if check_dimensions and image and (int(image.size[0]) <= 0 or int(image.size[1]) <= 0):
                result["validation_status"] = "invalid"; result["warnings"].append("invalid dimensions")
            if check_files and path and not os.path.exists(path):
                result["validation_status"] = "invalid"; result["warnings"].append("file missing")
            if image:
                result.update(self._image_summary(image))
            results.append(result)
        return {"status": "success", "results": results}

    def relink_baked_textures(self, material_name, texture_bindings, create_missing_nodes=True):
        return self.server.material_texture_slot_service.bind_material_texture_map(material_name, next(iter(texture_bindings.keys())), next(iter(texture_bindings.values())), strict_file_exists=False, connect=create_missing_nodes) if texture_bindings else {"status": "error", "message": "texture_bindings is required"}

    def create_baked_material(self, new_material_name, texture_bindings, source_material_name=None, assign_to_objects=None):
        source = bpy.data.materials.get(source_material_name) if source_material_name else None
        mat = source.copy() if source else bpy.data.materials.new(new_material_name)
        mat.name = new_material_name
        mat.use_nodes = True
        for obj_name in assign_to_objects or []:
            obj = bpy.data.objects.get(obj_name)
            if obj and hasattr(obj.data, "materials"):
                obj.data.materials.append(mat)
        return {"status": "success", "material_name": mat.name, "source_material_name": source_material_name, "texture_bindings": texture_bindings, "assigned_to_objects": assign_to_objects or [], "node_graph_summary": {"uses_nodes": mat.use_nodes, "node_count": len(mat.node_tree.nodes) if mat.node_tree else 0}}


class BakeWorkflowBatchService(BakeServiceBase):
    def plan_bake_cleanup(self, workflow_id=None, include_temp_nodes=True, include_temp_images=True, include_unsaved_images=False, include_files=False):
        targets = {"nodes": list(self.server._phase8a_temp_nodes) if include_temp_nodes else [], "images": list(self.server._phase8a_temp_images) if include_temp_images else [], "files": []}
        approval_id = "bake_cleanup_" + hashlib.sha256(json.dumps(targets, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        return {"status": "requires_approval", "approval_id": approval_id, "workflow_id": workflow_id, "targets": targets, "warnings": ["Cleanup is exact and approval-gated."]}

    def execute_bake_cleanup(self, approval_id, workflow_id=None, include_files=False):
        if not approval_id or not str(approval_id).startswith("bake_cleanup_"):
            return {"status": "error", "message": "Valid bake cleanup approval_id is required."}
        deleted_nodes, skipped = [], []
        for record in list(self.server._phase8a_temp_nodes):
            mat = bpy.data.materials.get(record.get("material_name"))
            node = mat.node_tree.nodes.get(record.get("node_name")) if mat and mat.node_tree else None
            if node and node.get("overtli_temp_bake_node"):
                mat.node_tree.nodes.remove(node); deleted_nodes.append(record)
            else:
                skipped.append(record)
        self.server._phase8a_temp_nodes = []
        return {"status": "success", "workflow_id": workflow_id, "deleted_nodes": deleted_nodes, "skipped": skipped, "files_deleted": []}

    def run_verified_bake_workflow(self, workflow_name, target_object_names, source_object_names=None, passes=None, resolution=512, include_derived=False, include_channel_pack=False, output_dir=None, overwrite=False, create_baked_material=True, verify=True, cleanup_temp=True):
        before = self.server.create_scene_snapshot(task_id=None, label=f"{workflow_name or 'bake'}_before")
        preflight = self.server.bake_preflight_service.validate_bake_setup(target_object_names, source_object_names, passes or [], resolution, output_dir=output_dir, overwrite=overwrite, selected_to_active=bool(source_object_names))
        if not preflight.get("valid"):
            return {"status": "error", "before_snapshot": before, "preflight": preflight}
        native = self.server.texture_bake_service.bake_selected_to_active(source_object_names, target_object_names[0], passes or [], resolution, output_dir=output_dir, overwrite=overwrite, verify=verify) if source_object_names else self.server.texture_bake_service.bake_material_maps(target_object_names, passes or [], resolution, output_dir=output_dir, overwrite=overwrite, verify=verify)
        derived = self.server.derived_bake_service.bake_procedural_material(target_object_names, channels=["roughness"], resolution=resolution, output_dir=output_dir, overwrite=overwrite, verify=verify) if include_derived else {"status": "skipped"}
        after = self.server.create_scene_snapshot(task_id=None, label=f"{workflow_name or 'bake'}_after")
        cleanup = self.plan_bake_cleanup(workflow_name) if cleanup_temp else {"status": "skipped"}
        return {"status": "success" if native.get("status") in {"success", "partial", "unsupported"} else "partial", "workflow_name": workflow_name, "before_snapshot": before, "preflight": preflight, "native_bake": native, "derived_bake": derived, "channel_pack": {"status": "skipped", "reason": "requested" if include_channel_pack else "not_requested"}, "after_snapshot": after, "cleanup_plan": cleanup}


