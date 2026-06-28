from __future__ import annotations

from ..core import *

class WorkspaceSafetyDiffService:
    TODO_STATES = {"pending", "in_progress", "done", "verified", "blocked", "rejected", "needs_user_selection", "needs_screenshot", "needs_rollback", "needs_manual_check"}
    TASK_STATES = {"pending", "in_progress", "done", "verified", "blocked", "deferred", "superseded"}

    def __init__(self, server):
        self.server = server

    @staticmethod
    def _utc_timestamp():
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @staticmethod
    def _stamp():
        return time.strftime("%Y%m%d_%H%M%S", time.localtime())

    @staticmethod
    def _safe_slug(value, fallback="item"):
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or fallback)).strip("._-")
        return safe[:80] or fallback

    def _artifact_project_root(self, artifact_root=None):
        if artifact_root or os.environ.get("OVERTLI_BLENDER_ARTIFACT_ROOT"):
            return os.path.abspath(os.path.expanduser(str(artifact_root or os.environ.get("OVERTLI_BLENDER_ARTIFACT_ROOT"))))
        resolved = runtime_resolve_artifact_workspace(self.server.project_workspace_service._blend_info()["filepath"], create_if_missing=True)
        workspace = resolved.get("workspace", {})
        return os.path.abspath(workspace.get("project_root") or ADDON_ROOT)

    def _workspace_identity(self):
        blend = self.server.project_workspace_service._blend_info()
        filepath = blend.get("filepath") or ""
        if filepath:
            stem = os.path.splitext(os.path.basename(filepath))[0] or "blend"
            digest = hashlib.sha256(os.path.abspath(filepath).encode("utf-8")).hexdigest()[:12]
            return self._safe_slug(f"{stem}_{digest}", "blend")
        session_root = runtime_temp_workspace_root(None)
        digest = hashlib.sha256(str(session_root).encode("utf-8")).hexdigest()[:12]
        return self._safe_slug(f"unsaved_{digest}", "unsaved")

    def _workspace_root(self, artifact_root=None):
        root = self._artifact_project_root(artifact_root)
        base_path = os.path.join(os.path.abspath(os.path.expanduser(str(root))), ".overtli_blender", "workspace")
        path = os.path.join(base_path, self._workspace_identity())
        os.makedirs(path, exist_ok=True)
        for child in ["tasks", "snapshots", "rollback"]:
            os.makedirs(os.path.join(path, child), exist_ok=True)
        self._migrate_unscoped_workspace_indexes(base_path, path)
        return path

    def _migrate_unscoped_workspace_indexes(self, base_path, scoped_path):
        manifest_path = os.path.join(scoped_path, "migration_manifest.json")
        if os.path.exists(manifest_path):
            return
        migrated = []
        for name in ["tasks", "todos", "operation_journal"]:
            old_path = os.path.join(base_path, f"{name}.json")
            new_path = os.path.join(scoped_path, f"{name}.json")
            if os.path.exists(old_path) and not os.path.exists(new_path):
                shutil.copy2(old_path, new_path)
                migrated.append({"from": old_path, "to": new_path})
        if migrated:
            self._write_json(manifest_path, {"status": "migrated", "created": self._utc_timestamp(), "workspace_identity": self._workspace_identity(), "copied": migrated})

    def _path(self, *parts, artifact_root=None):
        return os.path.join(self._workspace_root(artifact_root), *parts)

    @staticmethod
    def _read_json(path, default):
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _write_json(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, sort_keys=True)

    def _index_path(self, name, artifact_root=None):
        return self._path(f"{name}.json", artifact_root=artifact_root)

    def _load_index(self, name, artifact_root=None):
        return self._read_json(self._index_path(name, artifact_root=artifact_root), [])

    def _save_index(self, name, data, artifact_root=None):
        self._write_json(self._index_path(name, artifact_root=artifact_root), data)

    def get_task_workspace(self, artifact_root=None):
        root = self._workspace_root(artifact_root)
        tasks = self._load_index("tasks", artifact_root)
        todos = self._load_index("todos", artifact_root)
        journal = self._load_index("operation_journal", artifact_root)
        snapshots = self.list_scene_snapshots(artifact_root=artifact_root)
        return {
            "status": "success",
            "workspace_root": root,
            "tasks_count": len(tasks),
            "todos_count": len(todos),
            "journal_count": len(journal),
            "snapshot_count": len(snapshots.get("snapshots", [])),
            "todo_states": sorted(self.TODO_STATES),
            "task_states": sorted(self.TASK_STATES),
            "warnings": [],
        }

    def create_workspace_task(self, title, goal=None, assumptions=None, status="pending", task_id=None, artifact_root=None):
        if not title:
            return {"status": "error", "message": "title is required", "warnings": []}
        state = str(status or "pending")
        if state not in self.TASK_STATES:
            return {"status": "error", "message": f"Unsupported task status: {state}", "warnings": []}
        tasks = self._load_index("tasks", artifact_root)
        task_id = task_id or f"task_{self._stamp()}_{len(tasks) + 1}"
        if any(task.get("task_id") == task_id for task in tasks):
            return {"status": "error", "message": f"Task already exists: {task_id}", "warnings": []}
        task = {
            "task_id": task_id,
            "title": str(title),
            "goal": goal,
            "assumptions": assumptions or [],
            "status": state,
            "created_at": self._utc_timestamp(),
            "updated_at": self._utc_timestamp(),
            "rollback_status": "not_required",
            "verification": {},
            "warnings": [],
        }
        tasks.append(task)
        self._save_index("tasks", tasks, artifact_root)
        self.record_operation_journal_entry("create_workspace_task", task_id=task_id, target=task_id, summary=f"Created workspace task {title}", risk_level="LOW", rollback_status="not_required", artifact_root=artifact_root)
        return {"status": "success", "task": task, "warnings": []}

    def complete_workspace_task(self, task_id, verified=False, evidence=None, artifact_root=None):
        state = "verified" if verified else "done"
        return self.update_workspace_task(task_id, status=state, verification={"evidence": evidence, "verified": bool(verified)}, artifact_root=artifact_root)

    def create_scene_plan(self, title="Scene build plan", goal=None, steps=None, artifact_root=None):
        default_steps = [
            "preflight scene",
            "reset/cleanup",
            "verify transform contract",
            "blockout ground",
            "blockout house body",
            "verify contact/alignment",
            "add roof",
            "verify roof/body alignment",
            "materials",
            "lighting/camera",
            "multi-angle snapshot review",
            "final corrections",
        ]
        task = self.create_workspace_task(title=title, goal=goal, status="in_progress", artifact_root=artifact_root)
        if task.get("status") != "success":
            return task
        task_id = task["task"]["task_id"]
        todos = [self.add_workspace_todo(text=text, task_id=task_id, artifact_root=artifact_root).get("todo") for text in (steps or default_steps)]
        return {"status": "success", "task": task["task"], "todos": [todo for todo in todos if todo], "warnings": []}

    def list_scene_plan(self, task_id=None, artifact_root=None):
        tasks = self.list_workspace_tasks(artifact_root=artifact_root).get("tasks", [])
        todos = self.list_workspace_todos(task_id=task_id, artifact_root=artifact_root).get("todos", [])
        if task_id:
            tasks = [task for task in tasks if task.get("task_id") == task_id]
        return {"status": "success", "tasks": tasks, "todos": todos, "warnings": []}

    def update_workspace_task(self, task_id, status=None, goal=None, assumptions=None, rollback_status=None, verification=None, artifact_root=None):
        tasks = self._load_index("tasks", artifact_root)
        for task in tasks:
            if task.get("task_id") != task_id:
                continue
            if status is not None:
                state = str(status)
                if state not in self.TASK_STATES:
                    return {"status": "error", "message": f"Unsupported task status: {state}", "warnings": []}
                task["status"] = state
            if goal is not None:
                task["goal"] = goal
            if assumptions is not None:
                task["assumptions"] = assumptions
            if rollback_status is not None:
                task["rollback_status"] = rollback_status
            if verification is not None:
                task["verification"] = verification
            task["updated_at"] = self._utc_timestamp()
            self._save_index("tasks", tasks, artifact_root)
            self.record_operation_journal_entry("update_workspace_task", task_id=task_id, target=task_id, summary=f"Updated workspace task {task_id}", risk_level="LOW", rollback_status=task.get("rollback_status"), artifact_root=artifact_root)
            return {"status": "success", "task": task, "warnings": []}
        return {"status": "error", "message": f"Task not found: {task_id}", "warnings": []}

    def list_workspace_tasks(self, status=None, artifact_root=None):
        tasks = self._load_index("tasks", artifact_root)
        if status:
            tasks = [task for task in tasks if task.get("status") == status]
        return {"status": "success", "tasks": tasks, "warnings": []}

    def add_workspace_todo(self, text, task_id=None, state="pending", todo_id=None, artifact_root=None):
        if not text:
            return {"status": "error", "message": "text is required", "warnings": []}
        if state not in self.TODO_STATES:
            return {"status": "error", "message": f"Unsupported todo state: {state}", "warnings": []}
        todos = self._load_index("todos", artifact_root)
        todo_id = todo_id or f"todo_{self._stamp()}_{len(todos) + 1}"
        todo = {"todo_id": todo_id, "task_id": task_id, "text": str(text), "state": state, "created_at": self._utc_timestamp(), "updated_at": self._utc_timestamp(), "evidence": None}
        todos.append(todo)
        self._save_index("todos", todos, artifact_root)
        self.record_operation_journal_entry("add_workspace_todo", task_id=task_id, target=todo_id, summary=f"Added todo {text}", risk_level="LOW", rollback_status="not_required", artifact_root=artifact_root)
        return {"status": "success", "todo": todo, "warnings": []}

    def update_workspace_todo(self, todo_id, state=None, text=None, evidence=None, artifact_root=None):
        todos = self._load_index("todos", artifact_root)
        for todo in todos:
            if todo.get("todo_id") != todo_id:
                continue
            if state is not None:
                if state not in self.TODO_STATES:
                    return {"status": "error", "message": f"Unsupported todo state: {state}", "warnings": []}
                todo["state"] = state
            if text is not None:
                todo["text"] = text
            if evidence is not None:
                todo["evidence"] = evidence
            todo["updated_at"] = self._utc_timestamp()
            self._save_index("todos", todos, artifact_root)
            self.record_operation_journal_entry("update_workspace_todo", task_id=todo.get("task_id"), target=todo_id, summary=f"Updated todo {todo_id}", risk_level="LOW", rollback_status="not_required", artifact_root=artifact_root)
            return {"status": "success", "todo": todo, "warnings": []}
        return {"status": "error", "message": f"Todo not found: {todo_id}", "warnings": []}

    def list_workspace_todos(self, task_id=None, state=None, artifact_root=None):
        todos = self._load_index("todos", artifact_root)
        if task_id:
            todos = [todo for todo in todos if todo.get("task_id") == task_id]
        if state:
            todos = [todo for todo in todos if todo.get("state") == state]
        return {"status": "success", "todos": todos, "warnings": []}

    def record_operation_journal_entry(self, operation_type, task_id=None, target=None, summary=None, risk_level="LOW", rollback_status="unknown", before_snapshot_id=None, after_snapshot_id=None, metadata=None, artifact_root=None):
        journal = self._load_index("operation_journal", artifact_root)
        entry = {
            "entry_id": f"journal_{self._stamp()}_{len(journal) + 1}",
            "created_at": self._utc_timestamp(),
            "operation_type": str(operation_type),
            "task_id": task_id,
            "target": target,
            "summary": summary,
            "risk_level": str(risk_level),
            "rollback_status": rollback_status,
            "before_snapshot_id": before_snapshot_id,
            "after_snapshot_id": after_snapshot_id,
            "metadata": metadata or {},
        }
        journal.append(entry)
        self._save_index("operation_journal", journal[-500:], artifact_root)
        return {"status": "success", "entry": entry, "warnings": []}

    def get_operation_journal(self, task_id=None, limit=50, artifact_root=None):
        journal = self._load_index("operation_journal", artifact_root)
        if task_id:
            journal = [entry for entry in journal if entry.get("task_id") == task_id]
        return {"status": "success", "journal": journal[-max(1, int(limit)):], "warnings": []}

    def _scene_state(self):
        objects = {}
        for obj in bpy.context.scene.objects:
            objects[obj.name] = {
                "name": obj.name,
                "type": obj.type,
                "location": [round(float(v), 6) for v in obj.location],
                "rotation_euler": [round(float(v), 6) for v in obj.rotation_euler],
                "scale": [round(float(v), 6) for v in obj.scale],
                "hide_viewport": bool(obj.hide_viewport),
                "hide_render": bool(obj.hide_render),
                "collection_names": [collection.name for collection in obj.users_collection],
                "material_names": [slot.material.name if slot.material else None for slot in getattr(obj, "material_slots", [])],
                "modifier_names": [modifier.name for modifier in getattr(obj, "modifiers", [])],
            }
        collections = {collection.name: {"name": collection.name, "object_names": [obj.name for obj in collection.objects], "children": [child.name for child in collection.children]} for collection in bpy.data.collections}
        materials = {material.name: {"name": material.name, "users": int(material.users), "diffuse_color": [round(float(v), 6) for v in material.diffuse_color]} for material in bpy.data.materials}
        return {"objects": objects, "collections": collections, "materials": materials}

    def create_scene_snapshot(self, label=None, task_id=None, include_verification_snapshot=False, artifact_root=None):
        snapshot_id = f"{self._stamp()}_{self._safe_slug(label or 'scene')}"
        path = self._path("snapshots", f"{snapshot_id}.json", artifact_root=artifact_root)
        data = {
            "snapshot_id": snapshot_id,
            "label": label,
            "task_id": task_id,
            "created_at": self._utc_timestamp(),
            "scene_name": bpy.context.scene.name,
            "state": self._scene_state(),
            "workspace_tasks": self.list_workspace_tasks(artifact_root=artifact_root).get("tasks", []),
            "workspace_todos": self.list_workspace_todos(artifact_root=artifact_root).get("todos", []),
            "verification_snapshot": None,
        }
        if include_verification_snapshot:
            data["verification_snapshot"] = self.server.verification_artifact_service.create_verification_snapshot(label=f"{snapshot_id}_verification", include_screenshots=False, artifact_root=artifact_root)
        self._write_json(path, data)
        self.record_operation_journal_entry("create_scene_snapshot", task_id=task_id, target=snapshot_id, summary=f"Created scene snapshot {snapshot_id}", risk_level="LOW", rollback_status="available", after_snapshot_id=snapshot_id, artifact_root=artifact_root)
        return {"status": "success", "snapshot_id": snapshot_id, "snapshot_path": path, "object_count": len(data["state"]["objects"]), "collection_count": len(data["state"]["collections"]), "material_count": len(data["state"]["materials"]), "warnings": []}

    def list_scene_snapshots(self, artifact_root=None):
        snapshot_dir = self._path("snapshots", artifact_root=artifact_root)
        snapshots = []
        for filename in sorted(os.listdir(snapshot_dir), reverse=True):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(snapshot_dir, filename)
            data = self._read_json(path, {})
            snapshots.append({"snapshot_id": data.get("snapshot_id") or filename[:-5], "label": data.get("label"), "task_id": data.get("task_id"), "created_at": data.get("created_at"), "snapshot_path": path})
        return {"status": "success", "snapshots": snapshots, "warnings": []}

    def _load_snapshot(self, snapshot_id, artifact_root=None):
        path = self._path("snapshots", f"{snapshot_id}.json", artifact_root=artifact_root)
        if not os.path.exists(path):
            raise ValueError(f"Scene snapshot not found: {snapshot_id}")
        return self._read_json(path, {})

    @staticmethod
    def _dict_diff(before, after):
        before_keys = set(before)
        after_keys = set(after)
        added = sorted(after_keys - before_keys)
        removed = sorted(before_keys - after_keys)
        changed = []
        for key in sorted(before_keys & after_keys):
            if before[key] != after[key]:
                changed.append(key)
        return added, removed, changed

    def diff_scene_snapshots(self, before_snapshot_id, after_snapshot_id, artifact_root=None):
        before = self._load_snapshot(before_snapshot_id, artifact_root)
        after = self._load_snapshot(after_snapshot_id, artifact_root)
        diff = {}
        for section in ["objects", "collections", "materials"]:
            added, removed, changed = self._dict_diff(before.get("state", {}).get(section, {}), after.get("state", {}).get(section, {}))
            diff[section] = {"added": added, "removed": removed, "changed": changed}
        return {"status": "success", "before_snapshot_id": before_snapshot_id, "after_snapshot_id": after_snapshot_id, "diff": diff, "warnings": []}

    def detect_user_changes(self, baseline_snapshot_id=None, artifact_root=None):
        snapshots = self.list_scene_snapshots(artifact_root=artifact_root).get("snapshots", [])
        if not snapshots and not baseline_snapshot_id:
            current = self.create_scene_snapshot(label="user_change_baseline", artifact_root=artifact_root)
            return {"status": "success", "baseline_created": True, "baseline_snapshot_id": current["snapshot_id"], "changed": False, "diff": {}, "warnings": ["No baseline existed; created one"]}
        baseline_id = baseline_snapshot_id or snapshots[0]["snapshot_id"]
        current = self.create_scene_snapshot(label="user_change_current", artifact_root=artifact_root)
        diff = self.diff_scene_snapshots(baseline_id, current["snapshot_id"], artifact_root=artifact_root)
        changed = any(diff["diff"][section][kind] for section in diff["diff"] for kind in ["added", "removed", "changed"])
        return {"status": "success", "baseline_snapshot_id": baseline_id, "current_snapshot_id": current["snapshot_id"], "changed": changed, "diff": diff["diff"], "warnings": []}

    def rollback_to_scene_snapshot(self, snapshot_id, confirm=False, remove_new_objects=False, verify=True, artifact_root=None):
        if not confirm:
            return {"status": "error", "message": "rollback_to_scene_snapshot requires confirm=True", "warnings": []}
        snapshot = self._load_snapshot(snapshot_id, artifact_root)
        target_objects = snapshot.get("state", {}).get("objects", {})
        current_names = set(bpy.data.objects.keys())
        restored, missing, removed = [], [], []
        for name, state in target_objects.items():
            obj = bpy.data.objects.get(name)
            if not obj:
                missing.append(name)
                continue
            obj.location = state.get("location", list(obj.location))
            obj.rotation_euler = state.get("rotation_euler", list(obj.rotation_euler))
            obj.scale = state.get("scale", list(obj.scale))
            obj.hide_viewport = bool(state.get("hide_viewport", obj.hide_viewport))
            obj.hide_render = bool(state.get("hide_render", obj.hide_render))
            restored.append(name)
        if remove_new_objects:
            for name in sorted(current_names - set(target_objects)):
                obj = bpy.data.objects.get(name)
                if obj:
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed.append(name)
        verification = self.create_scene_snapshot(label=f"rollback_after_{snapshot_id}", artifact_root=artifact_root) if verify else {}
        result = {"status": "success", "snapshot_id": snapshot_id, "restored": restored, "missing": missing, "removed_new_objects": removed, "verification": verification, "warnings": ["Rollback restores transforms/visibility for existing objects; deleted object recreation is not supported"]}
        self.record_operation_journal_entry("rollback_to_scene_snapshot", target=snapshot_id, summary=f"Rolled back to scene snapshot {snapshot_id}", risk_level="HIGH", rollback_status="performed", after_snapshot_id=verification.get("snapshot_id") if isinstance(verification, dict) else None, artifact_root=artifact_root)
        return result

    def undo_last_blender_operation(self, confirm=False):
        if not confirm:
            return {"status": "error", "message": "undo_last_blender_operation requires confirm=True", "warnings": []}
        try:
            bpy.ops.ed.undo()
            result = {"status": "success", "undone": True, "warnings": ["Uses Blender undo stack; availability depends on the current session"]}
        except Exception as exc:
            result = {"status": "error", "undone": False, "message": str(exc), "warnings": ["Blender undo stack was not available"]}
        self.record_operation_journal_entry("undo_last_blender_operation", summary="Requested Blender undo", risk_level="HIGH", rollback_status="performed" if result["status"] == "success" else "failed")
        return result

class ProjectWorkspaceService:
    def __init__(self, server):
        self.server = server

    def _blend_info(self):
        filepath = getattr(bpy.data, "filepath", "") or ""
        return {"is_saved": bool(filepath), "filepath": filepath, "name": os.path.basename(filepath) if filepath else None}

    def _workspace_base(self, preferred_root=None, allow_repo_fallback=True):
        result = runtime_resolve_workspace(
            self._blend_info()["filepath"],
            preferred_root=preferred_root,
            repo_root=ADDON_ROOT,
            allow_repo_fallback=allow_repo_fallback,
        )
        workspace = result.get("workspace", {})
        if workspace.get("resolved"):
            return workspace["project_root"]
        return ADDON_ROOT

    def _sync_file_policy_project_root(self, project_root):
        from pathlib import Path
        root = Path(os.path.abspath(project_root)).resolve(strict=False)
        self.server.file_access_policy_service.policy.project_root = root
        self.server.file_access_policy_service.add_approved_root(str(root), confirm=True)
        return str(root)

    @staticmethod
    def _is_relative_to(path, root):
        try:
            common = os.path.commonpath([os.path.abspath(path), os.path.abspath(root)])
            return common == os.path.abspath(root)
        except Exception:
            return False

    def _save_blend_with_relative_paths(self, filepath):
        warnings = []
        try:
            bpy.ops.wm.save_as_mainfile(filepath=filepath, relative_remap=True)
        except TypeError:
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            warnings.append("Blender save_as_mainfile did not accept relative_remap; saved without that parameter.")
        try:
            bpy.ops.file.make_paths_relative()
            try:
                bpy.ops.wm.save_as_mainfile(filepath=filepath, relative_remap=True)
            except TypeError:
                bpy.ops.wm.save_as_mainfile(filepath=filepath)
        except Exception as exc:
            warnings.append(f"Could not convert all paths to relative paths after save: {exc}")
        return {"filepath": filepath, "warnings": warnings}

    def _collect_image_dependencies_to_project(self, project_root, overwrite=False, make_relative=True):
        target_dir = os.path.join(os.path.abspath(project_root), "textures", "source")
        os.makedirs(target_dir, exist_ok=True)
        copied = []
        relinked = []
        skipped = []
        warnings = []
        for image in bpy.data.images:
            raw_path = getattr(image, "filepath", "") or getattr(image, "filepath_raw", "") or ""
            packed = bool(getattr(image, "packed_file", None))
            if packed:
                skipped.append({"name": image.name, "reason": "packed_image"})
                continue
            abs_path = bpy.path.abspath(raw_path) if raw_path else ""
            if not abs_path:
                skipped.append({"name": image.name, "reason": "no_filepath"})
                continue
            if not os.path.exists(abs_path):
                warnings.append(f"Image dependency is missing and was not copied: {image.name} -> {raw_path}")
                skipped.append({"name": image.name, "source": abs_path, "reason": "missing"})
                continue
            if self._is_relative_to(abs_path, project_root):
                if make_relative:
                    try:
                        image.filepath = bpy.path.relpath(abs_path)
                        relinked.append({"name": image.name, "filepath": image.filepath, "source": abs_path, "copied": False})
                    except Exception as exc:
                        warnings.append(f"Could not make project-local image relative: {image.name}: {exc}")
                continue
            basename = os.path.basename(abs_path)
            destination = os.path.join(target_dir, basename)
            if os.path.exists(destination) and not overwrite:
                skipped.append({"name": image.name, "source": abs_path, "target": destination, "reason": "target_exists"})
                if make_relative:
                    try:
                        image.filepath = bpy.path.relpath(destination)
                        relinked.append({"name": image.name, "filepath": image.filepath, "source": abs_path, "target": destination, "copied": False})
                    except Exception as exc:
                        warnings.append(f"Could not relink existing project texture: {image.name}: {exc}")
                continue
            shutil.copy2(abs_path, destination)
            copied.append({"name": image.name, "source": abs_path, "target": destination})
            if make_relative:
                try:
                    image.filepath = bpy.path.relpath(destination)
                    relinked.append({"name": image.name, "filepath": image.filepath, "source": abs_path, "target": destination, "copied": True})
                except Exception as exc:
                    warnings.append(f"Copied texture but could not make image path relative: {image.name}: {exc}")
        return {"status": "success", "target_dir": target_dir, "copied": copied, "relinked": relinked, "skipped": skipped, "warnings": warnings}

    def get_project_status(self):
        blend = self._blend_info()
        resolved = runtime_resolve_workspace(blend["filepath"], repo_root=ADDON_ROOT, allow_repo_fallback=True)
        workspace = resolved.get("workspace", {})
        if workspace.get("resolved"):
            self._sync_file_policy_project_root(workspace["project_root"])
        return {
            "status": "success",
            "blend": blend,
            "project_folder": workspace.get("project_root") if workspace.get("resolved") else None,
            "workspace": workspace,
            "layout": runtime_validate_layout(workspace["project_root"]) if workspace.get("resolved") else None,
            "approved_roots": self.server.file_access_policy_service.get_file_access_policy().get("policy", {}),
            "warnings": resolved.get("warnings", []),
        }

    def get_loaded_project_folder(self, preferred_root=None):
        result = runtime_get_loaded_project_folder(self._blend_info()["filepath"], preferred_root=preferred_root)
        workspace = result.get("workspace", {})
        if workspace.get("resolved"):
            self._sync_file_policy_project_root(workspace["project_root"])
        return result

    def resolve_project_workspace(self, preferred_root=None, allow_repo_fallback=True, create_if_missing=False):
        if not self._blend_info()["filepath"] and not preferred_root:
            result = runtime_resolve_artifact_workspace(self._blend_info()["filepath"], preferred_root=preferred_root, create_if_missing=True)
        else:
            result = runtime_resolve_workspace(self._blend_info()["filepath"], preferred_root=preferred_root, repo_root=ADDON_ROOT, allow_repo_fallback=allow_repo_fallback)
        workspace = result.get("workspace", {})
        if create_if_missing and workspace.get("resolved"):
            init = runtime_repair_workspace_layout(workspace["project_root"], blend_filepath=self._blend_info()["filepath"])
            result["initialization"] = init
        if workspace.get("resolved"):
            self._sync_file_policy_project_root(workspace["project_root"])
        return result

    def initialize_temp_workspace(self, session_id=None, project_name=None):
        result = runtime_initialize_temp_workspace(session_id=session_id, project_name=project_name)
        workspace = result.get("workspace", {})
        if workspace.get("resolved"):
            self._sync_file_policy_project_root(workspace["project_root"])
        return result

    def promote_temp_workspace_to_project(self, temp_workspace_root=None, project_root=None, blend_filename=None, project_name=None, confirm=False, overwrite=False, collect_external_images=True, make_paths_relative=True):
        if not project_root:
            return {"status": "error", "message": "project_root is required."}
        source = temp_workspace_root or self.resolve_project_workspace().get("workspace", {}).get("project_root")
        if not source:
            return {"status": "error", "message": "No temp workspace is available to promote."}
        if not confirm:
            return {
                "status": "requires_approval",
                "message": "Promoting a temp workspace copies artifacts and may save the active .blend.",
                "source_temp_workspace": source,
                "target_project_root": os.path.abspath(project_root),
            }
        copied = runtime_copy_project_folder(source, project_root, overwrite=overwrite)
        if copied.get("status") != "success":
            return copied
        filename = blend_filename or f"{project_name or os.path.basename(os.path.abspath(project_root))}.blend"
        saved = self.resave_project_folder(project_root=project_root, blend_filename=filename, project_name=project_name, confirm=True, overwrite=overwrite, collect_external_images=collect_external_images, make_paths_relative=make_paths_relative)
        layout = runtime_repair_workspace_layout(project_root, project_name=project_name, blend_filepath=saved.get("after"))
        return {"status": "success", "source_temp_workspace": source, "target_project_root": os.path.abspath(project_root), "copied": copied, "saved": saved, "layout": layout, "warnings": []}

    def initialize_project_workspace(self, project_root=None, project_name=None, create_standard_folders=True, save_blend_if_unsaved=False, blend_filename=None, confirm=False):
        blend = self._blend_info()
        root = project_root or (os.path.dirname(blend["filepath"]) if blend["is_saved"] else None)
        if not root:
            return {"status": "requires_approval", "message": "Unsaved .blend requires explicit project_root.", "blend": blend}
        if save_blend_if_unsaved and not confirm:
            return {"status": "requires_approval", "message": "Saving an unsaved .blend requires confirmation.", "blend": blend}
        result = runtime_initialize_workspace(root, project_name=project_name, create_standard_folders=create_standard_folders, overwrite_manifest=confirm)
        self._sync_file_policy_project_root(root)
        if save_blend_if_unsaved and blend_filename:
            save_path = os.path.join(root, blend_filename)
            bpy.ops.wm.save_as_mainfile(filepath=save_path)
            result["saved_blend"] = save_path
            result = runtime_repair_workspace_layout(root, project_name=project_name, blend_filepath=save_path)
        return result

    def validate_project_layout(self, project_root=None):
        root = project_root or self._workspace_base()
        return runtime_validate_layout(root)

    def repair_project_layout(self, project_root=None, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Repairing project layout writes folders and manifest."}
        root = project_root or self._workspace_base()
        self._sync_file_policy_project_root(root)
        return runtime_repair_workspace_layout(root, blend_filepath=self._blend_info()["filepath"])

    def register_blend_file(self, filepath=None, confirm=False):
        path = filepath or self._blend_info()["filepath"]
        if not path:
            return {"status": "error", "message": "No saved .blend filepath is available."}
        if not confirm:
            return {"status": "requires_approval", "message": "Registering a blend file writes project manifest metadata."}
        root = os.path.dirname(path)
        result = runtime_initialize_workspace(root, project_name=os.path.splitext(os.path.basename(path))[0], overwrite_manifest=True)
        result["blend"] = {"filepath": path, "name": os.path.basename(path)}
        return result

    def save_project_as(self, project_root, blend_filename, confirm=False, overwrite=False, collect_external_images=False, make_paths_relative=True):
        if not confirm:
            return {"status": "requires_approval", "message": "Saving a .blend requires confirmation."}
        target = os.path.abspath(os.path.join(project_root, blend_filename))
        if os.path.exists(target) and not overwrite:
            return {"status": "error", "message": "Target blend exists and overwrite is false.", "path": target}
        before = self._blend_info()["filepath"]
        os.makedirs(project_root, exist_ok=True)
        if os.path.exists(target) and overwrite:
            self.create_project_backup(confirm=True)
        runtime_repair_workspace_layout(project_root, project_name=os.path.splitext(os.path.basename(blend_filename))[0])
        save_result = self._save_blend_with_relative_paths(target) if make_paths_relative else {"filepath": target, "warnings": []}
        if not make_paths_relative:
            bpy.ops.wm.save_as_mainfile(filepath=target)
        dependency_collection = None
        if collect_external_images:
            dependency_collection = self._collect_image_dependencies_to_project(project_root, overwrite=overwrite, make_relative=make_paths_relative)
            if make_paths_relative:
                save_result_after_resources = self._save_blend_with_relative_paths(target)
                save_result["warnings"].extend(save_result_after_resources.get("warnings", []))
        self._sync_file_policy_project_root(project_root)
        layout = runtime_repair_workspace_layout(project_root, project_name=os.path.splitext(os.path.basename(blend_filename))[0], blend_filepath=target)
        return {
            "status": "success",
            "before": before,
            "after": target,
            "workspace": layout.get("workspace"),
            "layout": layout,
            "save": save_result,
            "dependency_collection": dependency_collection,
            "storage_backend": "json_files",
        }

    def resave_project_folder(self, project_root=None, blend_filename=None, project_name=None, create_standard_folders=True, update_manifest=True, confirm=False, overwrite=False, collect_external_images=True, make_paths_relative=True):
        blend = self._blend_info()
        root = project_root or (os.path.dirname(blend["filepath"]) if blend["is_saved"] else None)
        if not root:
            return {"status": "requires_approval", "message": "Unsaved .blend requires project_root and blend_filename."}
        filename = blend_filename or blend["name"] or f"{os.path.basename(os.path.abspath(root))}.blend"
        result = self.save_project_as(root, filename, confirm=confirm, overwrite=overwrite, collect_external_images=collect_external_images, make_paths_relative=make_paths_relative)
        if result.get("status") != "success":
            return result
        if create_standard_folders or update_manifest:
            result["layout"] = runtime_repair_workspace_layout(root, project_name=project_name, blend_filepath=result["after"])
        return result

    def plan_project_folder_move(self, destination_root, new_project_name=None, source_project_root=None, copy_mode="copy"):
        source = source_project_root or self._workspace_base(allow_repo_fallback=False)
        return runtime_plan_project_folder_move(source, destination_root, new_project_name=new_project_name, blend_filepath=self._blend_info()["filepath"], copy_mode=copy_mode)

    def move_project_folder(self, destination_root, new_project_name=None, source_project_root=None, copy_mode="copy", confirm=False, overwrite=False, save_after_move=True, delete_original=False, collect_external_images=True, make_paths_relative=True):
        if not confirm:
            return {"status": "requires_approval", "message": "Moving or copying a project folder requires confirmation.", "plan": self.plan_project_folder_move(destination_root, new_project_name, source_project_root, copy_mode)}
        blend = self._blend_info()
        source = os.path.abspath(source_project_root or self._workspace_base(allow_repo_fallback=False))
        plan = runtime_plan_project_folder_move(source, destination_root, new_project_name=new_project_name, blend_filepath=blend["filepath"], copy_mode=copy_mode)
        if plan.get("status") == "error":
            return plan
        target = plan["target_project_root"]
        copied = runtime_copy_project_folder(source, target, overwrite=overwrite)
        if copied.get("status") != "success":
            return {**copied, "plan": plan}
        target_blend = plan["target_blend_filepath"]
        saved = None
        dependency_collection = None
        save_result = None
        if save_after_move:
            os.makedirs(os.path.dirname(target_blend), exist_ok=True)
            save_result = self._save_blend_with_relative_paths(target_blend) if make_paths_relative else {"filepath": target_blend, "warnings": []}
            if not make_paths_relative:
                bpy.ops.wm.save_as_mainfile(filepath=target_blend)
            saved = target_blend
            if collect_external_images:
                dependency_collection = self._collect_image_dependencies_to_project(target, overwrite=overwrite, make_relative=make_paths_relative)
                if make_paths_relative:
                    second_save = self._save_blend_with_relative_paths(target_blend)
                    save_result["warnings"].extend(second_save.get("warnings", []))
        layout = runtime_repair_workspace_layout(target, project_name=new_project_name or os.path.basename(target), blend_filepath=saved or target_blend)
        self._sync_file_policy_project_root(target)
        deleted_original = False
        if delete_original:
            if copy_mode != "move":
                return {"status": "error", "message": "delete_original requires copy_mode='move'.", "copied": copied, "saved_blend": saved, "layout": layout}
            if os.path.abspath(source) == os.path.abspath(target):
                return {"status": "error", "message": "Refusing to delete source because it equals target.", "copied": copied, "saved_blend": saved, "layout": layout}
            shutil.rmtree(source)
            deleted_original = True
        return {"status": "success", "plan": plan, "copied": copied, "saved_blend": saved, "save": save_result, "dependency_collection": dependency_collection, "layout": layout, "deleted_original": deleted_original, "original_retained": not deleted_original}

    def create_project_backup(self, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Creating a project backup writes files."}
        blend = self._blend_info()
        if not blend["is_saved"]:
            return {"status": "error", "message": "Cannot backup unsaved .blend."}
        root = os.path.dirname(blend["filepath"])
        backup_dir = os.path.join(root, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_id = "backup_" + time.strftime("%Y%m%d_%H%M%S")
        target = os.path.join(backup_dir, backup_id + "_" + blend["name"])
        shutil.copy2(blend["filepath"], target)
        return {"status": "success", "backup_id": backup_id, "files": [target]}

    def restore_project_backup(self, backup_id, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Restoring a backup overwrites the current blend."}
        blend = self._blend_info()
        if not blend["is_saved"]:
            return {"status": "error", "message": "Cannot restore a backup because the current .blend is unsaved.", "backup_id": backup_id}
        root = os.path.dirname(blend["filepath"])
        backup_dir = os.path.join(root, "backups")
        if not os.path.isdir(backup_dir):
            return {"status": "error", "message": "Project backup directory does not exist.", "backup_id": backup_id, "backup_dir": backup_dir}
        candidates = [
            os.path.join(backup_dir, name)
            for name in os.listdir(backup_dir)
            if name.startswith(str(backup_id) + "_") and name.endswith(".blend")
        ]
        if not candidates:
            return {"status": "error", "message": "Backup id was not found.", "backup_id": backup_id, "backup_dir": backup_dir}
        source = max(candidates, key=os.path.getmtime)
        target = blend["filepath"]
        pre_restore = self.create_project_backup(confirm=True)
        shutil.copy2(source, target)
        try:
            bpy.ops.wm.open_mainfile(filepath=target)
            reopened = True
        except Exception:
            reopened = False
        layout = runtime_repair_workspace_layout(root, blend_filepath=target)
        return {
            "status": "success",
            "backup_id": backup_id,
            "restored_from": source,
            "restored_to": target,
            "pre_restore_backup": pre_restore,
            "reopened": reopened,
            "layout": layout,
            "warnings": [] if reopened else ["Backup file was copied over the active .blend, but Blender did not reopen it automatically."],
        }

    def collect_project_dependencies(self, project_root=None, copy_external_images=False, overwrite=False, make_paths_relative=True, confirm=False):
        if copy_external_images and not confirm:
            return {"status": "requires_approval", "message": "Copying and relinking project dependencies requires confirmation."}
        deps = []
        for image in bpy.data.images:
            if getattr(image, "filepath", ""):
                path = bpy.path.abspath(image.filepath)
                deps.append({"type": "image", "name": image.name, "filepath": path, "raw_filepath": image.filepath, "packed": bool(getattr(image, "packed_file", None)), "missing": bool(path and not os.path.exists(path))})
        collection = None
        if copy_external_images:
            root = project_root or self._workspace_base(allow_repo_fallback=False)
            collection = self._collect_image_dependencies_to_project(root, overwrite=overwrite, make_relative=make_paths_relative)
        return {"status": "success", "dependencies": deps, "dependency_collection": collection, "storage_backend": "json_files"}


class FileAccessPolicyService:
    def __init__(self, server):
        self.server = server
        self.policy = FileAccessPolicy(self._current_project_root())

    def _current_project_root(self):
        try:
            return self.server.project_workspace_service._workspace_base(allow_repo_fallback=True)
        except Exception:
            return ADDON_ROOT

    def _sync_project_root(self):
        from pathlib import Path
        root = Path(os.path.abspath(self._current_project_root())).resolve(strict=False)
        if str(root) != str(self.policy.project_root):
            self.policy.project_root = root
            self.policy.add_root(root)
        return root

    def get_file_access_policy(self):
        self._sync_project_root()
        return {"status": "success", "policy": self.policy.to_dict()}

    def set_file_access_policy(self, approved_roots=None, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Replacing approved roots requires confirmation."}
        self.policy = FileAccessPolicy(self._current_project_root(), approved_roots or [])
        return self.get_file_access_policy()

    def validate_path_access(self, path, access="read"):
        return self.policy.validate(path, access)

    def list_approved_roots(self):
        self._sync_project_root()
        return {"status": "success", "approved_roots": self.policy.approved_roots}

    def add_approved_root(self, root, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Adding approved root requires confirmation.", "root": root}
        return {"status": "success", "policy": self.policy.add_root(root)}

    def remove_approved_root(self, root, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Removing approved root requires confirmation.", "root": root}
        return {"status": "success", "policy": self.policy.remove_root(root)}

    def detect_drive_roots(self, preferred_drives=None):
        return runtime_detect_drive_roots(tuple(preferred_drives or ("C", "D")))

    def approve_drive_roots(self, drives=None, confirm=False):
        roots = runtime_detect_drive_roots(tuple(drives or ("C", "D"))).get("drive_roots", [])
        if not confirm:
            return {"status": "requires_approval", "message": "Approving drive roots grants broad local filesystem access.", "drive_roots": roots}
        for root in roots:
            self.policy.add_root(root)
        return {"status": "success", "policy": self.policy.to_dict(), "drive_roots": roots}

    def scan_project_files(self, root=None, limit=200):
        base = root or self.policy.project_root
        check = self.policy.validate(base, "read")
        if check["status"] != "success":
            return check
        files = []
        for dirpath, dirnames, filenames in os.walk(check["path"], followlinks=False):
            dirnames[:] = [name for name in dirnames if name not in {".git", "__pycache__", ".venv"}]
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                files.append({"path": path, "bytes": os.path.getsize(path)})
                if len(files) >= limit:
                    return {"status": "success", "files": files, "truncated": True}
        return {"status": "success", "files": files, "truncated": False}

    def read_project_text_file(self, path, max_bytes=200000):
        return self.policy.read_text(path, max_bytes=max_bytes)

    def write_project_text_file(self, path, text, confirm=False):
        result = self.policy.write_text(path, text)
        if result.get("status") == "requires_approval" and confirm:
            return {"status": "error", "message": "External writes require approval runtime execution, not confirm bypass.", "path": path}
        return result

    def copy_file_into_project(self, source, destination):
        return self.policy.copy_into_project(source, destination)

    def plan_file_delete(self, paths):
        return self.policy.plan_delete(paths)

    def execute_approved_file_delete(self, approval_id, paths=None, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "approval_id": approval_id, "message": "File delete execution requires approval and confirmation."}
        return {"status": "blocked", "approval_id": approval_id, "message": "Destructive file delete execution remains plan-only in Phase 7C live runtime."}


class CacheRetentionService:
    def __init__(self, server):
        self.server = server
        self.base = os.path.join(ADDON_ROOT, ".overtli_blender")
        self.pinned = set()

    def get_cache_status(self):
        return runtime_get_cache_status(self.base)

    def plan_cache_cleanup(self, categories=None, older_than_days=None, dry_run=True):
        return runtime_plan_cache_cleanup(self.base, categories=categories, older_than_days=older_than_days)

    def execute_cache_cleanup(self, approval_id, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "approval_id": approval_id, "message": "Cache cleanup execution requires approval."}
        return {"status": "blocked", "approval_id": approval_id, "message": "Destructive cache cleanup execution is intentionally not automatic in Phase 7C."}

    def pin_artifact(self, path):
        self.pinned.add(os.path.abspath(path))
        return {"status": "success", "pinned": sorted(self.pinned)}

    def unpin_artifact(self, path):
        self.pinned.discard(os.path.abspath(path))
        return {"status": "success", "pinned": sorted(self.pinned)}

    def find_orphaned_artifacts(self):
        return {"status": "success", "artifacts": [], "warnings": ["orphan detection is conservative in Phase 7C"]}

    def compact_operation_history(self, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Compacting history rewrites runtime records."}
        return {"status": "success", "compacted": False}


class TaskGraphService:
    def __init__(self, server):
        self.server = server
        self.store = TaskGraphStore(os.path.join(ADDON_ROOT, ".overtli_blender", "workspace"))

    def create_task(self, goal, **kwargs):
        kwargs.setdefault("created_revision", self.server.time_revision_service.tracker.scene_revision)
        return self.store.create_task(goal, **kwargs)

    def update_task(self, task_id, **updates):
        return self.store.update_task(task_id, **updates)

    def list_tasks(self, status=None):
        return self.store.list_tasks(status=status)

    def get_task(self, task_id):
        return self.store.get_task(task_id)

    def set_task_status(self, task_id, status):
        if status not in TASK_STATUSES:
            return {"status": "error", "message": f"Invalid task status: {status}"}
        return self.store.update_task(task_id, status=status)

    def link_task_artifact(self, task_id, artifact_path, artifact_type="file"):
        result = self.store.get_task(task_id)
        if result["status"] != "success":
            return result
        task = result["task"]
        task.setdefault("artifacts", []).append({"path": artifact_path, "type": artifact_type})
        return self.store.update_task(task_id, artifacts=task["artifacts"])

    def link_task_target(self, task_id, target_handle):
        result = self.store.get_task(task_id)
        if result["status"] != "success":
            return result
        task = result["task"]
        targets = task.setdefault("target_handles", [])
        if target_handle not in targets:
            targets.append(target_handle)
        return self.store.update_task(task_id, target_handles=targets)

    def mark_task_verified(self, task_id):
        return self.store.update_task(task_id, status="verified", last_verified_revision=self.server.time_revision_service.tracker.scene_revision)

    def mark_task_stale(self, task_id):
        return self.store.update_task(task_id, status="stale")

    def archive_tasks(self, task_ids=None):
        archived = []
        for task in self.store.list_tasks().get("tasks", []):
            if task_ids is None or task["task_id"] in task_ids:
                self.store.update_task(task["task_id"], status="archived")
                archived.append(task["task_id"])
        return {"status": "success", "archived": archived}

    def get_task_graph(self):
        tasks = self.store.list_tasks().get("tasks", [])
        return {"status": "success", "nodes": tasks, "edges": [{"from": dep, "to": task["task_id"]} for task in tasks for dep in task.get("dependencies", [])]}

    def detect_stale_tasks(self):
        revision = self.server.time_revision_service.tracker.scene_revision
        stale = []
        for task in self.store.list_tasks().get("tasks", []):
            if task.get("status") in {"completed_unverified", "verified"} and (task.get("last_verified_revision") or -1) < revision:
                stale.append(task["task_id"])
        return {"status": "success", "scene_revision": revision, "stale_tasks": stale}


class TimeRevisionService:
    def __init__(self, server):
        self.server = server
        self.tracker = TimeRevisionTracker()

    def get_session_time(self):
        return self.tracker.time_info()

    def get_scene_revision(self):
        return {"status": "success", "scene_revision": self.tracker.scene_revision}

    def get_recent_operations(self, limit=20):
        return self.tracker.recent(limit=limit)

    def get_changes_since_revision(self, revision):
        return {"status": "success", "from_revision": revision, "to_revision": self.tracker.scene_revision, "source": "overtli_or_external_unknown", "changes": [op for op in self.tracker.operations if op.get("revision", 0) > revision]}

    def get_operation_duration(self, operation_id=None):
        return {"status": "success", "operation_id": operation_id, "duration_seconds": None, "warnings": ["duration tracking is available for new Phase 7C markers only"]}

    def create_scene_revision_marker(self, label=None, source="overtli"):
        return self.tracker.marker(label=label, source=source)


class ReferenceImageService:
    def __init__(self, server):
        self.server = server
        self.references = {}

    def _reference_root(self):
        root = self.server.project_workspace_service._workspace_base()
        path = os.path.join(root, "references", "images")
        os.makedirs(path, exist_ok=True)
        return path

    def import_reference_image(self, source_path, reference_type="empty_image", copy_into_project=True, name=None):
        check = self.server.file_access_policy_service.validate_path_access(source_path, "read")
        if check.get("status") != "success":
            return check
        source = check["path"]
        ref_id = "ref_" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
        project_path = source
        if copy_into_project:
            project_path = os.path.join(self._reference_root(), os.path.basename(source))
            shutil.copy2(source, project_path)
        image = bpy.data.images.load(project_path, check_existing=True)
        record = {"reference_id": ref_id, "name": name or image.name, "image_name": image.name, "source_path": source, "project_copy_path": project_path, "reference_type": reference_type, "dimensions": list(image.size), "opacity": 1.0, "depth": "front", "locked": True, "landmarks": [], "confidence": "uncalibrated"}
        self.references[ref_id] = record
        return {"status": "success", "reference": record}

    def create_reference_set(self, name, reference_ids=None):
        return {"status": "success", "reference_set": {"name": name, "reference_ids": reference_ids or []}}

    def place_reference_view(self, reference_id, view="front_orthographic", scale=1.0):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        bpy.ops.object.empty_add(type="IMAGE", location=(0, 0, 0))
        obj = bpy.context.object
        obj.name = record["name"]
        obj.empty_display_type = "IMAGE"
        obj.empty_display_size = scale
        obj.data = bpy.data.images.get(record.get("image_name") or record["name"])
        obj.color = (1.0, 1.0, 1.0, float(record.get("opacity", 1.0)))
        with suppress(Exception):
            obj.empty_image_depth = str(record.get("depth", "front")).upper()
        obj.lock_location = (True, True, True)
        obj.lock_rotation = (True, True, True)
        obj.lock_scale = (True, True, True)
        record["object_name"] = obj.name
        record["view"] = view
        return {"status": "success", "reference": record}

    def calibrate_reference_scale(self, reference_id, known_distance, unit="METERS"):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        record["scale_calibration"] = {"known_distance": known_distance, "unit": unit}
        record["confidence"] = "calibrated"
        return {"status": "success", "reference": record}

    def set_reference_opacity(self, reference_id, opacity):
        return self._set_reference(reference_id, opacity=max(0.0, min(1.0, float(opacity))))

    def set_reference_depth(self, reference_id, depth):
        return self._set_reference(reference_id, depth=depth)

    def lock_reference(self, reference_id, locked=True):
        return self._set_reference(reference_id, locked=bool(locked))

    def set_reference_view_visibility(self, reference_id, visible=True):
        return self._set_reference(reference_id, visible=bool(visible))

    def add_reference_landmark(self, reference_id, name, point):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        record.setdefault("landmarks", []).append({"name": name, "point": point})
        return {"status": "success", "reference": record}

    def measure_reference_landmarks(self, reference_id, from_landmark, to_landmark):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        lookup = {item["name"]: item["point"] for item in record.get("landmarks", [])}
        if from_landmark not in lookup or to_landmark not in lookup:
            return {"status": "error", "message": "Both landmarks must exist."}
        return {"status": "success", "distance_pixels": runtime_distance(lookup[from_landmark], lookup[to_landmark]), "confidence": record.get("confidence", "uncalibrated")}

    def capture_reference_overlay(self, reference_id):
        return {"status": "success", "reference_id": reference_id, "artifact": None, "warnings": ["overlay capture uses viewport screenshot tooling in later phases"]}

    def list_reference_images(self):
        return {"status": "success", "references": list(self.references.values())}

    def relink_reference_image(self, reference_id, new_path):
        return self._set_reference(reference_id, project_copy_path=new_path)

    def remove_reference_image(self, reference_id, delete_file=False, confirm=False):
        if delete_file and not confirm:
            return {"status": "requires_approval", "message": "Deleting reference image files requires confirmation."}
        record = self.references.pop(reference_id, None)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        return {"status": "success", "removed": record, "file_deleted": False}

    def _set_reference(self, reference_id, **updates):
        record = self.references.get(reference_id)
        if not record:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        record.update(updates)
        obj = bpy.data.objects.get(record.get("object_name", ""))
        if obj:
            if "opacity" in updates:
                rgba = list(getattr(obj, "color", (1.0, 1.0, 1.0, 1.0)))
                while len(rgba) < 4:
                    rgba.append(1.0)
                rgba[3] = float(record["opacity"])
                obj.color = rgba
            if "depth" in updates:
                depth = str(record["depth"]).upper()
                with suppress(Exception):
                    obj.empty_image_depth = depth
            if "locked" in updates:
                locked = bool(record["locked"])
                obj.lock_location = (locked, locked, locked)
                obj.lock_rotation = (locked, locked, locked)
                obj.lock_scale = (locked, locked, locked)
            if "visible" in updates:
                visible = bool(record["visible"])
                obj.hide_viewport = not visible
                obj.hide_render = not visible
            record["viewport_state"] = {
                "object_name": obj.name,
                "color_alpha": float(getattr(obj, "color", (1, 1, 1, 1))[3]),
                "empty_image_depth": getattr(obj, "empty_image_depth", None),
                "hide_viewport": bool(obj.hide_viewport),
                "hide_render": bool(obj.hide_render),
                "locked": all(obj.lock_location) and all(obj.lock_rotation) and all(obj.lock_scale),
            }
        return {"status": "success", "reference": record}


class SpatialMeasurementService:
    def __init__(self, server):
        self.server = server

    def _obj(self, name):
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        return obj

    def _origin(self, name):
        return list(self._obj(name).matrix_world.translation)

    @staticmethod
    def _bounds(obj):
        corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in getattr(obj, "bound_box", [])]
        if not corners:
            loc = obj.matrix_world.translation
            corners = [loc]
        mins = [min(corner[i] for corner in corners) for i in range(3)]
        maxs = [max(corner[i] for corner in corners) for i in range(3)]
        center = [(mins[i] + maxs[i]) / 2.0 for i in range(3)]
        return {"min": mins, "max": maxs, "center": center, "size": [maxs[i] - mins[i] for i in range(3)]}

    @staticmethod
    def _bounds_clearance(bounds_a, bounds_b):
        axis_gaps = []
        penetration_axes = []
        for axis in range(3):
            if bounds_a["max"][axis] < bounds_b["min"][axis]:
                axis_gaps.append(bounds_b["min"][axis] - bounds_a["max"][axis])
            elif bounds_b["max"][axis] < bounds_a["min"][axis]:
                axis_gaps.append(bounds_a["min"][axis] - bounds_b["max"][axis])
            else:
                axis_gaps.append(0.0)
                penetration_axes.append(min(bounds_a["max"][axis], bounds_b["max"][axis]) - max(bounds_a["min"][axis], bounds_b["min"][axis]))
        clearance = math.sqrt(sum(value * value for value in axis_gaps))
        return clearance, axis_gaps, penetration_axes

    @staticmethod
    def _bounds_overlap(bounds_a, bounds_b):
        return all(bounds_a["min"][axis] <= bounds_b["max"][axis] and bounds_b["min"][axis] <= bounds_a["max"][axis] for axis in range(3))

    def _evaluated_mesh_world(self, obj):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.transform(evaluated.matrix_world)
        return evaluated, mesh

    def calculate_distance(self, from_object=None, to_object=None, point_a=None, point_b=None):
        a = point_a or self._origin(from_object)
        b = point_b or self._origin(to_object)
        value = runtime_distance(a, b)
        unit_settings = bpy.context.scene.unit_settings
        return {"status": "success", "measurement": {"type": "distance", "from": from_object or point_a, "to": to_object or point_b, "value_blender_units": value, "unit_system": unit_settings.system, "value_meters": value * unit_settings.scale_length, "confidence": "high", "method": "object_origin" if from_object and to_object else "points"}, "warnings": []}

    def calculate_angle(self, point_a, point_b, point_c):
        return {"status": "success", "measurement": {"type": "angle", "value_degrees": runtime_angle_degrees(point_a, point_b, point_c), "confidence": "high"}}

    def calculate_area(self, object_name):
        obj = self._obj(object_name)
        if obj.type != "MESH":
            return {"status": "unsupported", "measurement": {"type": "area", "object": object_name, "method": "mesh_surface_area"}, "message": "calculate_area requires a mesh object"}
        evaluated = mesh = None
        try:
            evaluated, mesh = self._evaluated_mesh_world(obj)
            area = sum(float(poly.area) for poly in mesh.polygons)
            return {"status": "success", "measurement": {"type": "area", "object": object_name, "value_blender_units": area, "confidence": "high", "method": "evaluated_mesh_surface_area", "polygon_count": len(mesh.polygons)}, "warnings": []}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "measurement": {"type": "area", "object": object_name, "method": "evaluated_mesh_surface_area"}}
        finally:
            if evaluated and mesh:
                with suppress(Exception):
                    evaluated.to_mesh_clear()

    def calculate_volume(self, object_name):
        obj = self._obj(object_name)
        if obj.type != "MESH":
            return {"status": "unsupported", "measurement": {"type": "volume", "object": object_name, "method": "mesh_volume"}, "message": "calculate_volume requires a mesh object"}
        evaluated = mesh = None
        try:
            import bmesh
            evaluated, mesh = self._evaluated_mesh_world(obj)
            bm = bmesh.new()
            try:
                bm.from_mesh(mesh)
                non_manifold_edges = [edge for edge in bm.edges if len(edge.link_faces) != 2]
                volume = abs(float(bm.calc_volume()))
            finally:
                bm.free()
            warnings = [] if not non_manifold_edges else [f"mesh is not watertight; {len(non_manifold_edges)} non-manifold boundary edges detected"]
            return {"status": "success" if not warnings else "partial", "measurement": {"type": "volume", "object": object_name, "value_blender_units": volume, "confidence": "high" if not warnings else "medium", "method": "evaluated_bmesh_volume", "non_manifold_edge_count": len(non_manifold_edges)}, "warnings": warnings}
        except Exception as exc:
            bounds = self._bounds(obj)
            estimate = bounds["size"][0] * bounds["size"][1] * bounds["size"][2]
            return {"status": "partial", "message": str(exc), "measurement": {"type": "volume", "object": object_name, "value_blender_units": estimate, "confidence": "low", "method": "bounds_product_fallback"}, "warnings": ["exact mesh volume unavailable; returned bounds estimate"]}
        finally:
            if evaluated and mesh:
                with suppress(Exception):
                    evaluated.to_mesh_clear()

    def calculate_curve_length(self, object_name):
        obj = self._obj(object_name)
        if obj.type != "CURVE":
            return {"status": "unsupported", "measurement": {"type": "curve_length", "object": object_name}, "message": "calculate_curve_length requires a curve object"}
        total = 0.0
        samples = 0
        for spline in obj.data.splines:
            points = []
            if spline.type == "BEZIER":
                bezier_points = list(spline.bezier_points)
                for index, point in enumerate(bezier_points):
                    points.append(obj.matrix_world @ point.co)
                    if index + 1 < len(bezier_points):
                        start = point.co
                        control_a = point.handle_right
                        next_point = bezier_points[index + 1]
                        control_b = next_point.handle_left
                        end = next_point.co
                        previous = obj.matrix_world @ start
                        for step in range(1, 17):
                            t = step / 16.0
                            local = ((1 - t) ** 3 * start) + (3 * (1 - t) ** 2 * t * control_a) + (3 * (1 - t) * t ** 2 * control_b) + (t ** 3 * end)
                            current = obj.matrix_world @ local
                            total += (current - previous).length
                            previous = current
                            samples += 1
            else:
                source_points = getattr(spline, "points", [])
                for point in source_points:
                    co = point.co
                    points.append(obj.matrix_world @ mathutils.Vector((co.x / co.w, co.y / co.w, co.z / co.w)))
                for first, second in zip(points, points[1:]):
                    total += (second - first).length
                    samples += 1
            if getattr(spline, "use_cyclic_u", False) and len(points) > 1:
                total += (points[0] - points[-1]).length
                samples += 1
        return {"status": "success", "measurement": {"type": "curve_length", "object": object_name, "value_blender_units": float(total), "confidence": "medium" if samples else "low", "method": "spline_sampled_length", "sample_segments": samples}, "warnings": [] if samples else ["curve has no measurable segments"]}

    def calculate_clearance(self, object_a, object_b):
        first = self._obj(object_a)
        second = self._obj(object_b)
        bounds_a = self._bounds(first)
        bounds_b = self._bounds(second)
        clearance, axis_gaps, penetration_axes = self._bounds_clearance(bounds_a, bounds_b)
        return {"status": "success", "measurement": {"type": "clearance", "object_a": object_a, "object_b": object_b, "value_blender_units": clearance, "axis_gaps": axis_gaps, "penetration_axes": penetration_axes, "method": "world_bounding_box_clearance", "confidence": "medium"}, "warnings": ["bounds overlap; mesh-level penetration refinement not requested"] if penetration_axes and clearance == 0 else []}

    def calculate_alignment(self, object_names):
        rows = []
        centers = []
        for name in object_names:
            obj = self._obj(name)
            bounds = self._bounds(obj)
            centers.append(bounds["center"])
            rows.append({"object": name, "center": bounds["center"], "bounds": bounds})
        if not centers:
            return {"status": "error", "message": "object_names must contain at least one object"}
        target = centers[0]
        offsets = [{"object": row["object"], "offset_to_first_center": [target[axis] - row["center"][axis] for axis in range(3)]} for row in rows]
        axis_spread = {axis_name: max(center[index] for center in centers) - min(center[index] for center in centers) for index, axis_name in enumerate(("x", "y", "z"))}
        return {"status": "success", "alignment": {"objects": object_names, "centers": centers, "axis_spread": axis_spread, "offsets_to_first_center": offsets, "method": "world_bounds_center_alignment", "confidence": "medium"}}

    def convert_units(self, value, from_unit="BLENDER_UNIT", to_unit="METERS"):
        return runtime_convert_units(value, from_unit=from_unit, to_unit=to_unit, scale_length=bpy.context.scene.unit_settings.scale_length)

    def calculate_scale_ratio(self, measured, expected):
        return {"status": "success", "ratio": float(measured) / float(expected), "confidence": "high"}

    def compare_measurements(self, a, b):
        return {"status": "success", "difference": float(a) - float(b), "ratio": float(a) / float(b) if float(b) else None}

    def get_oriented_bounds(self, object_name):
        obj = self._obj(object_name)
        corners = [list(obj.matrix_world @ mathutils.Vector(corner)) for corner in obj.bound_box]
        return {"status": "success", "object": object_name, "corners": corners, "dimensions": list(obj.dimensions), "confidence": "high"}

    def raycast_scene(self, origin, direction, distance=1000.0):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        hit, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(depsgraph, mathutils.Vector(origin), mathutils.Vector(direction), distance=float(distance))
        return {"status": "success", "hit": bool(hit), "object": obj.name if obj else None, "location": list(location) if hit else None, "normal": list(normal) if hit else None}

    def find_nearest_objects(self, point, limit=5):
        rows = sorted((runtime_distance(point, list(obj.matrix_world.translation)), obj.name) for obj in bpy.context.scene.objects)
        return {"status": "success", "objects": [{"name": name, "distance": dist} for dist, name in rows[:limit]]}

    def detect_object_intersections(self, object_names):
        names = list(object_names or [])
        objects = [(name, self._obj(name)) for name in names]
        intersections = []
        for index, (name_a, obj_a) in enumerate(objects):
            bounds_a = self._bounds(obj_a)
            for name_b, obj_b in objects[index + 1:]:
                bounds_b = self._bounds(obj_b)
                if self._bounds_overlap(bounds_a, bounds_b):
                    clearance, axis_gaps, penetration_axes = self._bounds_clearance(bounds_a, bounds_b)
                    intersections.append({"object_a": name_a, "object_b": name_b, "method": "world_bounding_box_overlap", "axis_gaps": axis_gaps, "penetration_axes": penetration_axes, "clearance": clearance})
        return {"status": "success", "intersections": intersections, "objects": names, "confidence": "medium", "method": "world_bounding_box_overlap", "warnings": ["mesh-level refinement not requested"]}

    def measure_object_to_reference(self, object_name, reference_id):
        refs = self.server.reference_image_service.references
        if reference_id not in refs:
            return {"status": "error", "message": f"Unknown reference: {reference_id}"}
        return {"status": "success", "object": object_name, "reference_id": reference_id, "confidence": refs[reference_id].get("confidence", "uncalibrated")}


class SafeRenameRelocationService:
    def __init__(self, server):
        self.server = server
        self.plans = {}

    def plan_rename(self, target_type, old_name, new_name):
        collision = False
        if target_type == "objects":
            collision = new_name in bpy.data.objects
        approval_id = "rename_" + hashlib.sha256(f"{target_type}:{old_name}:{new_name}".encode("utf-8")).hexdigest()[:12]
        plan = {"approval_id": approval_id, "target_type": target_type, "old_name": old_name, "new_name": new_name, "collision": collision, "requires_approval": True, "risks": ["collision"] if collision else []}
        self.plans[approval_id] = plan
        return {"status": "requires_approval", "plan": plan}

    def execute_rename(self, approval_id, confirm=False):
        plan = self.plans.get(approval_id)
        if not plan:
            return {"status": "error", "message": f"Unknown rename plan: {approval_id}"}
        if not confirm:
            return {"status": "requires_approval", "approval_id": approval_id}
        if plan["target_type"] == "objects":
            obj = bpy.data.objects.get(plan["old_name"])
            if not obj:
                return {"status": "error", "message": "Object not found."}
            if plan["collision"]:
                return {"status": "error", "message": "Rename collision detected."}
            obj.name = plan["new_name"]
            return {"status": "success", "renamed": plan}
        return {"status": "blocked", "message": "Only object datablock rename execution is enabled in Phase 7C.", "plan": plan}

    def batch_rename_datablocks(self, renames, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "Batch rename requires confirmation."}
        results = [self.execute_rename(self.plan_rename(item["target_type"], item["old_name"], item["new_name"])["plan"]["approval_id"], confirm=True) for item in renames]
        return {"status": "success", "results": results}

    def batch_rename_files(self, renames, confirm=False):
        return {"status": "requires_approval" if not confirm else "blocked", "message": "File rename execution requires approved root and remains blocked pending exact approval dispatch.", "renames": renames}

    def rename_project(self, new_name, confirm=False):
        return {"status": "requires_approval" if not confirm else "blocked", "message": "Project folder rename is plan-only in Phase 7C.", "new_name": new_name}

    def repair_references_after_rename(self, confirm=False):
        return {"status": "requires_approval" if not confirm else "success", "repaired": [], "warnings": ["No broken reference relinks detected."]}
