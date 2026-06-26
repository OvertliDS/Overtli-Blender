from __future__ import annotations

from ..core import *

class SharedContextService:
    def __init__(self, shared_context):
        self.shared_context = shared_context

    def add_to_history(self, operation, input_data, result):
        """Add operation to history"""
        self.shared_context['history'].append({
            'operation': operation,
            'input': input_data,
            'result': str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
            'timestamp': time.time()
        })
        # Keep only last 50 operations
        if len(self.shared_context['history']) > 50:
            self.shared_context['history'] = self.shared_context['history'][-50:]

    def store_object_handle(self, handle, obj_name):
        """Store object reference by handle"""
        obj = bpy.data.objects.get(obj_name)
        if obj:
            self.shared_context['objects'][handle] = obj
            return f"Stored object '{obj_name}' as handle '{handle}'"
        return f"Object '{obj_name}' not found"

    def store_material_handle(self, handle, mat_name):
        """Store material reference by handle"""
        mat = bpy.data.materials.get(mat_name)
        if mat:
            self.shared_context['materials'][handle] = mat
            return f"Stored material '{mat_name}' as handle '{handle}'"
        return f"Material '{mat_name}' not found"

    def store_operation_result(self, op_id, result):
        """Store operation result by ID"""
        self.shared_context['operations'][op_id] = result
        return f"Stored operation result as '{op_id}'"

    def get_shared_context(self):
        """Get current shared context state"""
        return {
            "variables": self.shared_context['variables'],
            "object_handles": list(self.shared_context['objects'].keys()),
            "material_handles": list(self.shared_context['materials'].keys()),
            "operation_ids": list(self.shared_context['operations'].keys()),
            "history_count": len(self.shared_context['history'])
        }

    def clear_shared_context(self, section="all"):
        """Clear shared context (all, variables, objects, materials, operations, history)"""
        if section == "all":
            self.shared_context['variables'].clear()
            self.shared_context['objects'].clear()
            self.shared_context['materials'].clear()
            self.shared_context['operations'].clear()
            self.shared_context['history'].clear()
            return "Cleared all shared context"
        elif section == "variables":
            self.shared_context['variables'].clear()
            return "Cleared shared variables"
        elif section == "objects":
            self.shared_context['objects'].clear()
            return "Cleared object handles"
        elif section == "materials":
            self.shared_context['materials'].clear()
            return "Cleared material handles"
        elif section == "operations":
            self.shared_context['operations'].clear()
            return "Cleared operation results"
        elif section == "history":
            self.shared_context['history'].clear()
            return "Cleared operation history"
        else:
            return f"Unknown section: {section}. Use: all, variables, objects, materials, operations, history"

    def get_operation_history(self, count=10):
        """Get recent operation history"""
        recent_history = self.shared_context['history'][-count:] if count else self.shared_context['history']
        return {"history": recent_history, "total_operations": len(self.shared_context['history'])}

    def create_object_handle(self, handle, object_name):
        """Create a handle for an object to reference in future operations"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object '{object_name}' not found"}

        self.shared_context['objects'][handle] = obj
        self.add_to_history("create_object_handle", f"{handle} -> {object_name}", f"Created handle '{handle}'")

        return {
            "success": True,
            "handle": handle,
            "object_name": object_name,
            "object_type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z]
        }

    def create_material_handle(self, handle, material_name):
        """Create a handle for a material to reference in future operations"""
        mat = bpy.data.materials.get(material_name)
        if not mat:
            return {"error": f"Material '{material_name}' not found"}

        self.shared_context['materials'][handle] = mat
        self.add_to_history("create_material_handle", f"{handle} -> {material_name}", f"Created handle '{handle}'")

        return {
            "success": True,
            "handle": handle,
            "material_name": material_name,
            "uses_nodes": mat.use_nodes
        }

    def list_object_handles(self):
        """List all object handles and their details"""
        handles = {}
        for handle, obj in self.shared_context['objects'].items():
            handles[handle] = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "visible": obj.visible_get()
            }
        return {"object_handles": handles}

    def list_material_handles(self):
        """List all material handles and their details"""
        handles = {}
        for handle, mat in self.shared_context['materials'].items():
            handles[handle] = {
                "name": mat.name,
                "uses_nodes": mat.use_nodes,
                "users": mat.users
            }
        return {"material_handles": handles}


class ScriptRegistryService:
    def _get_script_directory(self, category):
        """Get the script directory path for a given category"""
        import tempfile
        temp_dir = tempfile.gettempdir()
        script_dir = os.path.join(temp_dir, ".blendermcp", category)
        os.makedirs(script_dir, exist_ok=True)
        return script_dir

    def _get_metadata_path(self, script_dir):
        """Get the metadata file path for a script directory"""
        return os.path.join(script_dir, ".meta.json")

    def _load_metadata(self, script_dir):
        """Load metadata for a script directory"""
        metadata_path = self._get_metadata_path(script_dir)
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_script_metadata(self, script_dir, script_name, permanent):
        """Save metadata for a script"""
        import time
        metadata = self._load_metadata(script_dir)
        metadata[script_name] = {
            "permanent": permanent,
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "description": f"{'Permanent' if permanent else 'Temporary'} script"
        }

        metadata_path = self._get_metadata_path(script_dir)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def register_context_script(self, script_name, script_content, category="default", permanent=False):
        """Register a Python script for later execution"""
        try:
            # Validate script syntax
            try:
                compile(script_content, f"{script_name}.py", 'exec')
            except SyntaxError as e:
                return {
                    "status": "error",
                    "message": f"Script syntax error: {str(e)}"
                }

            # Save script to file
            script_dir = self._get_script_directory(category)
            script_path = os.path.join(script_dir, f"{script_name}.py")

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # Save metadata
            self._save_script_metadata(script_dir, script_name, permanent)

            permanence = "permanent" if permanent else "temporary"
            return {
                "status": "success",
                "message": f"Script '{script_name}' registered as {permanence} in category '{category}'"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error registering script: {str(e)}"
            }

    def execute_context_script(self, script_name, category="default"):
        """Execute a previously registered script"""
        try:
            script_dir = self._get_script_directory(category)
            script_path = os.path.join(script_dir, f"{script_name}.py")

            if not os.path.exists(script_path):
                return {
                    "status": "error",
                    "message": f"Script '{script_name}' not found in category '{category}'"
                }

            # Read script content
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Execute script and capture output
            import io
            from contextlib import redirect_stdout, redirect_stderr

            output_buffer = io.StringIO()
            error_buffer = io.StringIO()

            try:
                with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                    # Create a safe execution environment
                    exec_globals = {
                        'bpy': bpy,
                        'mathutils': mathutils,
                        '__name__': '__main__'
                    }
                    exec(script_content, exec_globals)

                output = output_buffer.getvalue()
                errors = error_buffer.getvalue()

                if errors:
                    return {
                        "status": "error",
                        "message": f"Script execution error: {errors}",
                        "output": output
                    }

                return {
                    "status": "success",
                    "output": output if output else "Script executed successfully (no output)"
                }

            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Script execution error: {str(e)}",
                    "output": output_buffer.getvalue()
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing script: {str(e)}"
            }

    def list_context_scripts(self, category=None):
        """List all registered scripts"""
        try:
            import tempfile
            import time

            base_dir = os.path.join(tempfile.gettempdir(), ".blendermcp")

            if not os.path.exists(base_dir):
                return {
                    "status": "success",
                    "scripts": {}
                }

            scripts = {}

            if category:
                categories = [category]
            else:
                categories = [d for d in os.listdir(base_dir)
                            if os.path.isdir(os.path.join(base_dir, d))]

            for cat in categories:
                cat_dir = os.path.join(base_dir, cat)
                if not os.path.exists(cat_dir):
                    continue

                metadata = self._load_metadata(cat_dir)
                script_list = []

                for filename in os.listdir(cat_dir):
                    if filename.endswith('.py'):
                        script_name = filename[:-3]  # Remove .py extension
                        script_path = os.path.join(cat_dir, filename)
                        stat = os.stat(script_path)

                        script_meta = metadata.get(script_name, {})
                        script_list.append({
                            "name": script_name,
                            "size": stat.st_size,
                            "created": script_meta.get("created", time.ctime(stat.st_ctime)),
                            "permanent": script_meta.get("permanent", False),
                            "description": script_meta.get("description", "")
                        })

                if script_list:
                    # Sort by permanence (permanent first), then by name
                    script_list.sort(key=lambda x: (not x["permanent"], x["name"]))
                    scripts[cat] = script_list

            return {
                "status": "success",
                "scripts": scripts
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error listing scripts: {str(e)}"
            }

    def clear_context_scripts(self, category=None, script_name=None, clear_permanent=False):
        """Clear scripts from the registry"""
        try:
            import tempfile
            import shutil

            base_dir = os.path.join(tempfile.gettempdir(), ".blendermcp")

            if not os.path.exists(base_dir):
                return {
                    "status": "success",
                    "message": "No scripts to clear"
                }

            if script_name and category:
                # Clear specific script
                cat_dir = os.path.join(base_dir, category)
                script_path = os.path.join(cat_dir, f"{script_name}.py")

                if not os.path.exists(script_path):
                    return {
                        "status": "error",
                        "message": f"Script '{script_name}' not found in category '{category}'"
                    }

                # Check if script is permanent
                metadata = self._load_metadata(cat_dir)
                script_meta = metadata.get(script_name, {})
                is_permanent = script_meta.get("permanent", False)

                if is_permanent and not clear_permanent:
                    return {
                        "status": "error",
                        "message": f"Script '{script_name}' is permanent. Use clear_permanent=True to force deletion."
                    }

                # Remove script file
                os.remove(script_path)

                # Remove from metadata
                if script_name in metadata:
                    del metadata[script_name]
                    metadata_path = self._get_metadata_path(cat_dir)
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)

                return {
                    "status": "success",
                    "message": f"Script '{script_name}' cleared from category '{category}'"
                }

            elif category:
                # Clear entire category (respecting permanent scripts)
                cat_dir = os.path.join(base_dir, category)
                if not os.path.exists(cat_dir):
                    return {
                        "status": "success",
                        "message": f"Category '{category}' was already empty"
                    }

                metadata = self._load_metadata(cat_dir)
                cleared_count = 0
                permanent_count = 0

                # Process each script in the category
                for filename in os.listdir(cat_dir):
                    if filename.endswith('.py'):
                        script_name = filename[:-3]
                        script_meta = metadata.get(script_name, {})
                        is_permanent = script_meta.get("permanent", False)

                        if is_permanent and not clear_permanent:
                            permanent_count += 1
                        else:
                            script_path = os.path.join(cat_dir, filename)
                            os.remove(script_path)
                            if script_name in metadata:
                                del metadata[script_name]
                            cleared_count += 1

                # Update metadata file
                if metadata or permanent_count > 0:
                    metadata_path = self._get_metadata_path(cat_dir)
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                else:
                    # No scripts left, remove entire directory
                    shutil.rmtree(cat_dir)

                message = f"Cleared {cleared_count} temporary scripts from category '{category}'"
                if permanent_count > 0:
                    message += f". {permanent_count} permanent scripts preserved."

                return {
                    "status": "success",
                    "message": message
                }

            else:
                # Clear all scripts (respecting permanent scripts)
                cleared_count = 0
                permanent_count = 0

                for cat_name in os.listdir(base_dir):
                    cat_dir = os.path.join(base_dir, cat_name)
                    if not os.path.isdir(cat_dir):
                        continue

                    metadata = self._load_metadata(cat_dir)
                    cat_cleared = 0

                    for filename in os.listdir(cat_dir):
                        if filename.endswith('.py'):
                            script_name = filename[:-3]
                            script_meta = metadata.get(script_name, {})
                            is_permanent = script_meta.get("permanent", False)

                            if is_permanent and not clear_permanent:
                                permanent_count += 1
                            else:
                                script_path = os.path.join(cat_dir, filename)
                                os.remove(script_path)
                                if script_name in metadata:
                                    del metadata[script_name]
                                cleared_count += 1
                                cat_cleared += 1

                    # Update or remove category
                    if metadata or (permanent_count > 0 and cat_cleared < len([f for f in os.listdir(cat_dir) if f.endswith('.py')])):
                        metadata_path = self._get_metadata_path(cat_dir)
                        with open(metadata_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2)
                    else:
                        # Check if directory is empty (except metadata)
                        remaining_files = [f for f in os.listdir(cat_dir) if not f.startswith('.meta')]
                        if not remaining_files:
                            shutil.rmtree(cat_dir)

                message = f"Cleared {cleared_count} temporary scripts"
                if permanent_count > 0:
                    message += f". {permanent_count} permanent scripts preserved."

                return {
                    "status": "success",
                    "message": message
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error clearing scripts: {str(e)}"
            }

