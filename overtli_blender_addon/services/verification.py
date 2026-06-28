from __future__ import annotations

from ..core import *

class VerificationArtifactService:
    DEFAULT_VIEWS = ["perspective", "front", "right", "top"]
    SUPPORTED_VIEWS = {"perspective", "front", "right", "top", "back", "left", "bottom", "camera"}

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _utc_timestamp():
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @staticmethod
    def _snapshot_stamp():
        return time.strftime("%Y%m%d_%H%M%S", time.localtime())

    @staticmethod
    def _safe_label(label):
        if not label:
            return "scene"
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(label)).strip("._-")
        return safe[:60] or "scene"

    def _artifact_root(self, artifact_root=None):
        if artifact_root or os.environ.get("OVERTLI_BLENDER_ARTIFACT_ROOT"):
            root = artifact_root or os.environ.get("OVERTLI_BLENDER_ARTIFACT_ROOT")
            return os.path.abspath(os.path.expanduser(str(root)))
        resolved = runtime_resolve_artifact_workspace(getattr(bpy.data, "filepath", "") or None, create_if_missing=True)
        workspace = resolved.get("workspace", {})
        return os.path.abspath(os.path.expanduser(str(workspace.get("project_root") or ADDON_ROOT)))

    def _snapshot_dir(self, snapshot_name=None, label=None, artifact_root=None):
        snapshot_id = f"{self._snapshot_stamp()}_{self._safe_label(snapshot_name or label)}"
        base_dir = os.path.join(self._artifact_root(artifact_root), ".overtli_blender", "verification", "snapshots", snapshot_id)
        suffix = 1
        candidate = base_dir
        while os.path.exists(candidate):
            suffix += 1
            candidate = f"{base_dir}_{suffix}"
        os.makedirs(candidate, exist_ok=True)
        return os.path.basename(candidate), candidate

    @staticmethod
    def _write_json(path, data):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, sort_keys=True)

    def _find_viewport_context(self):
        screen = bpy.context.screen
        if not screen:
            return None
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            region = next((region for region in area.regions if region.type == "WINDOW"), None)
            space = next((space for space in area.spaces if space.type == "VIEW_3D"), None)
            if region and space and space.region_3d:
                return area, region, space, space.region_3d
        return None

    def _capture_named_view(self, view_name, filepath, max_size):
        viewport_context = self._find_viewport_context()
        if not viewport_context:
            return {"view": view_name, "path": filepath, "status": "error", "message": "No 3D viewport found"}

        area, region, space, region_3d = viewport_context
        original_state = {
            "view_perspective": region_3d.view_perspective,
            "view_location": region_3d.view_location.copy(),
            "view_rotation": region_3d.view_rotation.copy(),
            "view_distance": region_3d.view_distance,
            "view_camera_zoom": region_3d.view_camera_zoom,
            "view_camera_offset": tuple(region_3d.view_camera_offset),
        }

        try:
            with bpy.context.temp_override(area=area, region=region, space_data=space, region_data=region_3d):
                if view_name == "camera":
                    if bpy.context.scene.camera is None:
                        return {"view": view_name, "path": filepath, "status": "error", "message": "Scene has no active camera"}
                    region_3d.view_perspective = "CAMERA"
                elif view_name != "perspective":
                    bpy.ops.view3d.view_axis(type=view_name.upper(), align_active=False)
                else:
                    region_3d.view_perspective = "PERSP"
                bpy.ops.screen.screenshot_area(filepath=filepath)

            img = bpy.data.images.load(filepath)
            width, height = img.size
            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                width = max(1, int(width * scale))
                height = max(1, int(height * scale))
                img.scale(width, height)
                img.file_format = "PNG"
                img.save()
            bpy.data.images.remove(img)
            return {"view": view_name, "path": filepath, "width": width, "height": height, "status": "success"}
        except Exception as exc:
            return {"view": view_name, "path": filepath, "status": "error", "message": str(exc)}
        finally:
            try:
                region_3d.view_perspective = original_state["view_perspective"]
                region_3d.view_location = original_state["view_location"]
                region_3d.view_rotation = original_state["view_rotation"]
                region_3d.view_distance = original_state["view_distance"]
                region_3d.view_camera_zoom = original_state["view_camera_zoom"]
                region_3d.view_camera_offset = original_state["view_camera_offset"]
            except Exception:
                pass

    def _normalize_views(self, views):
        if not views:
            return list(self.DEFAULT_VIEWS), []
        normalized = []
        warnings = []
        for view in views:
            name = str(view).strip().lower()
            if name not in self.SUPPORTED_VIEWS:
                warnings.append(f"Unsupported view skipped: {view}")
                continue
            if name not in normalized:
                normalized.append(name)
        if not normalized:
            normalized = list(self.DEFAULT_VIEWS)
            warnings.append("No supported views requested; default views were used")
        return normalized, warnings

    def capture_viewport_pack(self, views=None, max_size=800, include_manifest=True, snapshot_name=None, artifact_dir=None, artifact_root=None):
        max_size = max(64, min(int(max_size), 4096))
        view_names, warnings = self._normalize_views(views)
        if artifact_dir:
            snapshot_id = os.path.basename(os.path.normpath(artifact_dir))
            target_dir = artifact_dir
            os.makedirs(target_dir, exist_ok=True)
        else:
            snapshot_id, target_dir = self._snapshot_dir(snapshot_name=snapshot_name or "viewport_pack", artifact_root=artifact_root)

        screenshot_dir = os.path.join(target_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshots = []
        for view_name in view_names:
            path = os.path.join(screenshot_dir, f"{view_name}.png")
            result = self._capture_named_view(view_name, path, max_size)
            screenshots.append(result)
            if result.get("status") != "success":
                warnings.append(f"{view_name}: {result.get('message', 'capture failed')}")

        if not any(item.get("status") == "success" for item in screenshots):
            return {
                "status": "error",
                "message": "No screenshots were captured",
                "snapshot_id": snapshot_id,
                "artifact_dir": target_dir,
                "screenshots": screenshots,
                "warnings": warnings,
            }

        manifest = {
            "snapshot_id": snapshot_id,
            "created_at": self._utc_timestamp(),
            "artifact_dir": target_dir,
            "command": "capture_viewport_pack",
            "parameters": {"views": view_names, "max_size": max_size, "include_manifest": include_manifest},
            "screenshots": screenshots,
            "warnings": warnings,
        }
        manifest_path = os.path.join(target_dir, "manifest.json")
        if include_manifest:
            self._write_json(manifest_path, manifest)

        return {
            "status": "success",
            "snapshot_id": snapshot_id,
            "artifact_dir": target_dir,
            "screenshots": screenshots,
            "manifest_path": manifest_path if include_manifest else None,
            "warnings": warnings,
        }

    def create_verification_snapshot(
        self,
        label=None,
        include_scene_index=True,
        include_scene_health=True,
        include_selection=True,
        include_screenshots=True,
        views=None,
        max_size=800,
        artifact_root=None,
    ):
        snapshot_id, target_dir = self._snapshot_dir(label=label or "scene", artifact_root=artifact_root)
        warnings = []
        artifacts = {"screenshots": []}

        if include_scene_index:
            path = os.path.join(target_dir, "scene_index.json")
            scene_index = self.server.scene_intelligence_service.get_scene_index()
            self._write_json(path, scene_index)
            artifacts["scene_index"] = "scene_index.json"
            warnings.extend(scene_index.get("warnings", []))

        if include_scene_health:
            path = os.path.join(target_dir, "scene_health.json")
            scene_health = self.server.scene_intelligence_service.get_scene_health()
            self._write_json(path, scene_health)
            artifacts["scene_health"] = "scene_health.json"
            warnings.extend(scene_health.get("warnings", []))

        if include_selection:
            path = os.path.join(target_dir, "selection_info.json")
            selection_info = self.server.scene_intelligence_service.get_selection_info()
            self._write_json(path, selection_info)
            artifacts["selection_info"] = "selection_info.json"
            warnings.extend(selection_info.get("warnings", []))

        if include_screenshots:
            pack_result = self.capture_viewport_pack(
                views=views,
                max_size=max_size,
                include_manifest=False,
                snapshot_name=snapshot_id,
                artifact_dir=target_dir,
                artifact_root=artifact_root,
            )
            artifacts["screenshots"] = [
                os.path.relpath(item.get("path"), target_dir).replace("\\", "/")
                for item in pack_result.get("screenshots", [])
                if item.get("status") == "success" and item.get("path")
            ]
            warnings.extend(pack_result.get("warnings", []))
            if pack_result.get("status") != "success":
                warnings.append(pack_result.get("message", "Screenshot pack failed"))

        manifest = {
            "snapshot_id": snapshot_id,
            "label": label,
            "created_at": self._utc_timestamp(),
            "blender_file": bpy.data.filepath or None,
            "scene_name": bpy.context.scene.name,
            "safety_mode": self.server.safety_policy_service.mode,
            "commands": {
                "include_scene_index": bool(include_scene_index),
                "include_scene_health": bool(include_scene_health),
                "include_selection": bool(include_selection),
                "include_screenshots": bool(include_screenshots),
            },
            "artifact_dir": target_dir,
            "artifacts": artifacts,
            "workspace_tasks": self.server.workspace_safety_diff_service.list_workspace_tasks(artifact_root=artifact_root).get("tasks", []),
            "workspace_todos": self.server.workspace_safety_diff_service.list_workspace_todos(artifact_root=artifact_root).get("todos", []),
            "warnings": warnings,
        }
        manifest_path = os.path.join(target_dir, "manifest.json")
        self._write_json(manifest_path, manifest)

        return {
            "status": "success",
            "snapshot_id": snapshot_id,
            "artifact_dir": target_dir,
            "manifest_path": manifest_path,
            "artifacts": artifacts,
            "warnings": warnings,
        }

    def list_verification_snapshots(self):
        snapshot_root = os.path.join(self._artifact_root(), ".overtli_blender", "verification", "snapshots")
        if not os.path.isdir(snapshot_root):
            return {"status": "success", "snapshot_root": snapshot_root, "snapshots": [], "warnings": []}

        snapshots = []
        for name in sorted(os.listdir(snapshot_root), reverse=True):
            path = os.path.join(snapshot_root, name)
            if not os.path.isdir(path):
                continue
            manifest_path = os.path.join(path, "manifest.json")
            snapshots.append({
                "snapshot_id": name,
                "artifact_dir": path,
                "manifest_path": manifest_path if os.path.exists(manifest_path) else None,
            })
        return {"status": "success", "snapshot_root": snapshot_root, "snapshots": snapshots, "warnings": []}


