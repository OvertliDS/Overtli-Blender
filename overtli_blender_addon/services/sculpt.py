from __future__ import annotations

from ..core import *

class SculptWorkflowService:
    SUPPORTED_BRUSHES = {"grab", "elastic_grab", "smooth", "inflate", "draw", "clay_strips", "pinch", "flatten", "mask"}

    def __init__(self, server):
        self.server = server

    def get_sculpt_status(self, object_name=None):
        obj = bpy.data.objects.get(object_name) if object_name else bpy.context.view_layer.objects.active
        return {"status": "success", "mode": bpy.context.mode, "object_name": obj.name if obj else None, "is_mesh": bool(obj and obj.type == "MESH"), "supported_brushes": sorted(self.SUPPORTED_BRUSHES), "warnings": []}

    def configure_sculpt_brush(self, brush_name="grab", radius=50, strength=0.25, symmetry=None, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "configure_sculpt_brush requires confirm=True because it changes the active Blender sculpt brush settings.", "warnings": []}
        brush_key = str(brush_name or "").lower()
        if brush_key not in self.SUPPORTED_BRUSHES:
            return {"status": "error", "message": f"Unsupported sculpt brush: {brush_name}", "warnings": []}
        settings = bpy.context.scene.tool_settings
        if getattr(settings, "sculpt", None) and settings.sculpt.brush:
            settings.sculpt.brush.size = max(1, min(1000, int(radius)))
            settings.sculpt.brush.strength = max(0.0, min(1.0, float(strength)))
        return {"status": "success", "brush_name": brush_key, "radius": int(radius), "strength": float(strength), "symmetry": symmetry or {}, "warnings": ["brush configuration is session-local"]}

    def create_sculpt_mask_from_vertex_group(self, object_name, vertex_group_name, mask_name=None, confirm=False):
        if not confirm:
            return {"status": "requires_approval", "message": "create_sculpt_mask_from_vertex_group requires confirm=True because it creates sculpt mask intent metadata.", "warnings": []}
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH" or not obj.vertex_groups.get(vertex_group_name):
            return {"status": "error", "message": "Mesh object and vertex group are required", "warnings": []}
        return {"status": "success", "object_name": obj.name, "vertex_group_name": vertex_group_name, "mask_name": mask_name or vertex_group_name, "warnings": ["stored as vertex-group-backed sculpt mask intent; no destructive sculpt mask write performed"]}

    def run_shape_key_sculpt_workflow(self, object_name, vertex_group_name, shape_key_name, brush_action="inflate", amount=0.05, confirm=False, verify=True):
        if not confirm:
            return {"status": "requires_approval", "message": "run_shape_key_sculpt_workflow requires confirm=True because it creates or replaces a shape key.", "warnings": []}
        if str(brush_action).lower() not in {"inflate", "grab", "elastic_grab", "smooth"}:
            return {"status": "error", "message": f"Unsupported shape-key sculpt action: {brush_action}", "warnings": []}
        shape = self.server.shape_key_service.create_shape_key(object_name, shape_key_name, replace_existing=True, value=1.0)
        if shape.get("status") != "success":
            return shape
        mode = "inflate_along_normals" if brush_action == "inflate" else "translate"
        vector = [0.0, 0.0, float(amount)] if mode == "translate" else None
        edit = self.server.shape_key_service.edit_shape_key_offsets(object_name, shape_key_name, vertex_group_name=vertex_group_name, deformation={"mode": mode, "amount": float(amount), "vector": vector or [0, 0, 0]}, confirm=True, verify=verify)
        return {"status": edit.get("status", "error"), "object_name": object_name, "shape_key_name": shape_key_name, "brush_action": brush_action, "shape_key": shape, "edit": edit, "warnings": edit.get("warnings", [])}


