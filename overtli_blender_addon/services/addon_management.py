from __future__ import annotations

from ..core import *

PHASE6B_DOCS_ROOT = os.path.join(ADDON_ROOT, "memory_bank", "research", "blender_python_reference_5_1_md")
PHASE6B_SECRET_RE = re.compile(r"(key|token|secret|password|auth|credential)", re.IGNORECASE)
PHASE6B_BAD_SNIPPET_RE = re.compile(r"\b(exec|eval|compile|__import__|subprocess|socket|requests|urllib|open\s*\(|os\.system|shutil\.rmtree|addon_install|addon_remove)\b", re.IGNORECASE)


def _phase6b_slug(value, fallback="item"):
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "").strip()).strip("_").lower()
    if not text:
        text = fallback
    if not re.match(r"^[A-Za-z_]", text):
        text = f"{fallback}_{text}"
    return text[:80]


def _phase6b_workspace_path(*parts, artifact_root=None):
    root = os.path.abspath(os.path.join(artifact_root or ADDON_ROOT, ".overtli_blender"))
    path = os.path.abspath(os.path.join(root, *parts))
    if not (path == root or path.startswith(root + os.sep)):
        raise ValueError("Resolved path escaped .overtli_blender workspace")
    os.makedirs(os.path.dirname(path) if os.path.splitext(path)[1] else path, exist_ok=True)
    return path


def _phase6b_write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _phase6b_read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _phase6b_exact_module(module_name):
    module = str(module_name or "").strip()
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_.]*$", module):
        raise ValueError("module_name must be an exact Python module name")
    return module


class AddonManagementService:
    def __init__(self, server):
        self.server = server

    def get_addon_management_status(self):
        return {"status": "success", "supports_addon_inspection": True, "supports_local_install": hasattr(bpy.ops.preferences, "addon_install"), "supports_enable_disable": hasattr(bpy.ops.preferences, "addon_enable"), "supports_remove": hasattr(bpy.ops.preferences, "addon_remove"), "local_only": True, "network_downloads_supported": False, "safety": {"install_requires_confirm": True, "remove_requires_confirm": True}, "warnings": []}

    def _addon_modules(self):
        import addon_utils
        return [(mod, getattr(mod, "__name__", ""), getattr(mod, "bl_info", {}) or {}, *addon_utils.check(getattr(mod, "__name__", ""))) for mod in addon_utils.modules(refresh=False)]

    def _summary(self, mod, module, info, enabled, loaded, include_paths=True, include_version=True):
        path = getattr(mod, "__file__", None)
        user_addons = bpy.utils.user_resource("SCRIPTS", path="addons", create=False)
        data = {"module": module, "name": info.get("name") or module, "enabled": bool(enabled), "loaded": bool(loaded), "category": info.get("category"), "is_user_addon": bool(path and user_addons and os.path.abspath(path).startswith(os.path.abspath(user_addons))), "warnings": []}
        if include_paths:
            data["path"] = path
        if include_version:
            data["version"] = list(info.get("version", ())) if isinstance(info.get("version"), tuple) else info.get("version")
        return data

    def list_blender_addons(self, include_enabled=True, include_disabled=True, include_paths=True, include_version=True, filter_text=None):
        addons, counts = [], {"enabled": 0, "disabled": 0}
        needle = str(filter_text or "").lower().strip()
        for mod, module, info, enabled, loaded in self._addon_modules():
            counts["enabled" if enabled else "disabled"] += 1
            if (enabled and not include_enabled) or (not enabled and not include_disabled):
                continue
            item = self._summary(mod, module, info, enabled, loaded, include_paths, include_version)
            if needle and needle not in f"{item.get('module')} {item.get('name')} {item.get('category')}".lower():
                continue
            addons.append(item)
        return {"status": "success", "addons": addons, "counts": counts, "warnings": []}

    def get_blender_addon_info(self, module_name, include_file_info=True, include_preferences_summary=True):
        module_name = _phase6b_exact_module(module_name)
        for mod, module, info, enabled, loaded in self._addon_modules():
            if module != module_name:
                continue
            addon = self._summary(mod, module, info, enabled, loaded, include_file_info, True)
            addon["bl_info"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in info.items() if k != "warning"}
            if include_file_info and getattr(mod, "__file__", None):
                path = getattr(mod, "__file__")
                addon["file_info"] = {"exists": os.path.exists(path), "size": os.path.getsize(path) if os.path.exists(path) else None}
            if include_preferences_summary and enabled:
                prefs = bpy.context.preferences.addons.get(module_name)
                addon["preferences_summary"] = {}
                if prefs and getattr(prefs, "preferences", None):
                    for attr in dir(prefs.preferences):
                        if not attr.startswith("_") and not callable(getattr(prefs.preferences, attr, None)):
                            addon["preferences_summary"][attr] = "<redacted>" if PHASE6B_SECRET_RE.search(attr) else str(getattr(prefs.preferences, attr))[:200]
            return {"status": "success", "addon": addon, "warnings": []}
        return {"status": "error", "message": f"Addon module not found: {module_name}"}

    def install_local_addon(self, addon_path, enable_after_install=False, confirm=False):
        if not confirm:
            return {"status": "error", "message": "install_local_addon requires confirm=True"}
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", str(addon_path or "")):
            return {"status": "error", "message": "Remote addon paths are not supported"}
        path = os.path.abspath(bpy.path.abspath(str(addon_path)))
        if not os.path.isfile(path) or os.path.splitext(path)[1].lower() not in {".py", ".zip"}:
            return {"status": "error", "message": "addon_path must be an existing local .py or .zip file"}
        before = {item["module"] for item in self.list_blender_addons().get("addons", [])}
        result = bpy.ops.preferences.addon_install(filepath=path, overwrite=True)
        after = {item["module"] for item in self.list_blender_addons().get("addons", [])}
        installed = sorted(after - before)
        if enable_after_install and installed:
            self.enable_blender_addon(installed[0], confirm=True)
        return {"status": "success", "operator_result": list(result), "installed_modules": installed, "warnings": []}

    def enable_blender_addon(self, module_name, confirm=False):
        if not confirm:
            return {"status": "error", "message": "enable_blender_addon requires confirm=True"}
        module_name = _phase6b_exact_module(module_name)
        before = bool(bpy.context.preferences.addons.get(module_name))
        result = bpy.ops.preferences.addon_enable(module=module_name)
        return {"status": "success", "module": module_name, "before_enabled": before, "after_enabled": bool(bpy.context.preferences.addons.get(module_name)), "operator_result": list(result)}

    def disable_blender_addon(self, module_name, confirm=False, allow_self_disable=False):
        if not confirm:
            return {"status": "error", "message": "disable_blender_addon requires confirm=True"}
        module_name = _phase6b_exact_module(module_name)
        if module_name in {__name__, "addon", "overtli_blender"} and not allow_self_disable:
            return {"status": "error", "message": "Refusing to disable Overtli-Blender without allow_self_disable=True"}
        before = bool(bpy.context.preferences.addons.get(module_name))
        result = bpy.ops.preferences.addon_disable(module=module_name)
        return {"status": "success", "module": module_name, "before_enabled": before, "after_enabled": bool(bpy.context.preferences.addons.get(module_name)), "operator_result": list(result)}

    def remove_blender_addon(self, module_name, confirm=False, delete_files=False):
        if not confirm:
            return {"status": "error", "message": "remove_blender_addon requires confirm=True"}
        if delete_files:
            return {"status": "error", "message": "Physical deletion is not implemented; use Blender's exact addon_remove operator only"}
        module_name = _phase6b_exact_module(module_name)
        if module_name in {__name__, "addon", "overtli_blender"}:
            return {"status": "error", "message": "Refusing to remove Overtli-Blender"}
        before = bool(bpy.context.preferences.addons.get(module_name))
        result = bpy.ops.preferences.addon_remove(module=module_name)
        return {"status": "success", "module": module_name, "before_enabled": before, "after_enabled": bool(bpy.context.preferences.addons.get(module_name)), "operator_result": list(result)}


class AddonDevelopmentService:
    def __init__(self, server):
        self.server = server

    def create_addon_skeleton(self, addon_name, module_name=None, output_dir=None, include_operator=True, include_panel=True, include_preferences=True, include_property_group=True, include_readme=True, include_manifest=True):
        module = _phase6b_slug(module_name or addon_name, "addon")
        root = os.path.abspath(output_dir) if output_dir else _phase6b_workspace_path("addon_dev", "skeletons", module)
        os.makedirs(root, exist_ok=True)
        prefix = "".join(part.capitalize() for part in module.split("_"))
        lines = [f'bl_info = {{"name": "{str(addon_name).replace(chr(34), chr(39))}", "author": "Overtli-Blender", "version": (0, 1, 0), "blender": (4, 0, 0), "category": "Development"}}', "import bpy", "from bpy.types import Operator, Panel, AddonPreferences, PropertyGroup", "from bpy.props import StringProperty, BoolProperty", ""]
        classes = []
        if include_property_group:
            classes.append(f"{prefix}Properties"); lines += [f"class {prefix}Properties(PropertyGroup):", '    label: StringProperty(name="Label", default="Overtli")', ""]
        if include_preferences:
            classes.append(f"{prefix}Preferences"); lines += [f"class {prefix}Preferences(AddonPreferences):", f'    bl_idname = "{module}"', '    enabled: BoolProperty(name="Enabled", default=True)', "    def draw(self, context):", '        self.layout.prop(self, "enabled")', ""]
        if include_operator:
            classes.append(f"{prefix}Operator"); lines += [f"class {prefix}Operator(Operator):", f'    bl_idname = "{module}.sample_operator"', f'    bl_label = "{addon_name} Sample Operator"', "    def execute(self, context):", "        return {'FINISHED'}", ""]
        if include_panel:
            classes.append(f"{prefix}Panel"); lines += [f"class {prefix}Panel(Panel):", f'    bl_idname = "VIEW3D_PT_{module}"', f'    bl_label = "{addon_name}"', '    bl_space_type = "VIEW_3D"', '    bl_region_type = "UI"', '    bl_category = "Overtli"', "    def draw(self, context):", f'        self.layout.operator("{module}.sample_operator")' if include_operator else '        self.layout.label(text="Ready")', ""]
        lines += [f"CLASSES = ({', '.join(classes)},)", "", "def register():", "    for cls in CLASSES:", "        bpy.utils.register_class(cls)", "", "def unregister():", "    for cls in reversed(CLASSES):", "        bpy.utils.unregister_class(cls)", ""]
        init_path = os.path.join(root, "__init__.py")
        with open(init_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
        files = [init_path]
        if include_readme:
            readme = os.path.join(root, "README.md"); open(readme, "w", encoding="utf-8").write(f"# {addon_name}\n\nGenerated local Overtli-Blender addon scaffold.\n"); files.append(readme)
        if include_manifest:
            manifest = os.path.join(root, "blender_manifest.toml"); open(manifest, "w", encoding="utf-8").write(f'id = "{module}"\nname = "{addon_name}"\nversion = "0.1.0"\nschema_version = "1.0.0"\n'); files.append(manifest)
        return {"status": "success", "module_name": module, "addon_dir": root, "files": files, "warnings": []}

    def validate_addon_skeleton(self, addon_dir_or_file, check_register_functions=True, check_bl_info=True, check_operator_ids=True, check_no_secrets=True):
        target = os.path.abspath(str(addon_dir_or_file))
        if os.path.isdir(target):
            target = os.path.join(target, "__init__.py")
        if not os.path.isfile(target):
            return {"status": "error", "message": "Addon skeleton file not found"}
        text = open(target, "r", encoding="utf-8", errors="replace").read()
        issues = []
        if check_register_functions and ("def register(" not in text or "def unregister(" not in text): issues.append("missing register/unregister")
        if check_bl_info and "bl_info" not in text: issues.append("missing bl_info")
        if check_operator_ids:
            for match in re.findall(r"bl_idname\s*=\s*['\"]([^'\"]+)['\"]", text):
                if "." in match and not re.match(r"^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$", match): issues.append(f"invalid operator bl_idname: {match}")
        if check_no_secrets and PHASE6B_SECRET_RE.search(text): issues.append("possible secret-like field or text")
        return {"status": "success", "valid": not issues, "issues": issues, "file": target}

    def package_addon_zip(self, addon_dir_or_file, output_path=None, overwrite=False):
        source = os.path.abspath(str(addon_dir_or_file))
        if not os.path.exists(source):
            return {"status": "error", "message": "Addon source not found"}
        output = os.path.abspath(output_path) if output_path else _phase6b_workspace_path("addon_dev", "packages", f"{_phase6b_slug(os.path.splitext(os.path.basename(source))[0], 'addon')}.zip")
        if os.path.exists(output) and not overwrite:
            return {"status": "error", "message": "Output zip exists; pass overwrite=True"}
        excluded, manifest = [], []
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            root = os.path.dirname(source)
            candidates = [source] if os.path.isfile(source) else [os.path.join(d, n) for d, _, names in os.walk(source) for n in names]
            for file_path in candidates:
                rel = os.path.relpath(file_path, root).replace("\\", "/")
                if any(part in rel.split("/") for part in [".git", "__pycache__", "memory_bank", ".overtli_blender"]) or rel.endswith((".pyc", ".env")):
                    excluded.append(rel); continue
                archive.write(file_path, rel); manifest.append({"path": rel, "size": os.path.getsize(file_path)})
        return {"status": "success", "zip_path": output, "manifest": manifest, "excluded": excluded}


