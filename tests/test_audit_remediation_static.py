from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_transform_dimensions_preserve_anchor_initializes_preserved_point_in_scope() -> None:
    modeling = _read("overtli_blender_addon/services/modeling.py")
    transform_start = modeling.index("def transform_object(")
    transform_end = modeling.index("def transform_object_dimensions(")
    section = modeling[transform_start:transform_end]

    assert 'preserved_point = self._anchor_point(obj, anchor or "center") if dimensions is not None and preserve_anchor else None' in section
    assert section.index("preserved_point =") < section.index("if dimensions is not None:")
    assert modeling.count("preserved_point =") == 1


def test_arm_packed_shader_socket_lookup_is_introspected_not_image_hardcoded() -> None:
    assets = _read("overtli_blender_addon/services/assets.py")
    socket_server = _read("overtli_blender_addon/runtime/socket_server.py")

    assert "def overtli_separate_color_input" in assets
    assert '("Color", "Image", "Vector")' in assets
    assert "overtli_node_output(texture_nodes['arm']" in assets
    assert "overtli_node_output(texture_nodes['arm']" in socket_server
    assert "separate_rgb.inputs['Image']" not in assets
    assert "separate_rgb.inputs['Image']" not in socket_server


def test_driver_armature_and_pose_runtime_guards_are_explicit() -> None:
    modeling = _read("overtli_blender_addon/services/modeling.py")

    assert "Material driver variables require object_name or target_type='scene'" in modeling
    assert "var.targets[0].id = source" in modeling
    assert "var.targets[0].id = bpy.data.objects.get(spec.get(\"object_name\")) if spec.get(\"object_name\") else target" not in modeling
    assert "has zero or near-zero length" in modeling
    assert "auto_offset_tail" in modeling
    assert 'bone.rotation_mode = "XYZ"' in modeling
    assert 'bone.keyframe_insert(rotation_channel' in modeling
    assert '"rotation_quaternion"' in modeling


def test_raw_code_and_context_script_security_are_scoped_and_structured() -> None:
    diagnostics = _read("overtli_blender_addon/services/diagnostics.py")
    context = _read("overtli_blender_addon/services/context.py")
    socket_server = _read("overtli_blender_addon/runtime/socket_server.py")

    assert "DANGEROUS_CODE_RE" in diagnostics
    assert "RAW_CODE_STATIC_SCAN_BLOCK" in diagnostics
    assert '"status": "blocked"' in diagnostics
    assert '"traceback_summary"' in diagnostics
    assert "raise Exception(error_msg)" not in diagnostics

    assert "ScriptRegistryService(self)" in socket_server
    assert "Overtli-Blender" in context
    assert "script_registry" in context
    assert "pid_{os.getpid()}_port_{port}" in context
    assert '".blendermcp"' not in context
    for helper in ["shared", "get_object", "get_material", "get_operation", "store_object", "store_material", "store_operation"]:
        assert helper in context


def test_workspace_task_indexes_are_scoped_by_blend_identity_with_migration_copy() -> None:
    workspace = _read("overtli_blender_addon/services/workspace.py")
    core = _read("overtli_blender_addon/core.py")

    assert "def _workspace_identity" in workspace
    assert "hashlib.sha256(os.path.abspath(filepath).encode" in workspace
    assert "migration_manifest.json" in workspace
    assert "shutil.copy2(old_path, new_path)" in workspace
    assert "runtime_temp_workspace_root" in workspace
    assert "temp_workspace_root as runtime_temp_workspace_root" in core
    assert "self._index_path(name, artifact_root=artifact_root)" in workspace
    assert "self._index_path(name, artifact_root)" not in workspace


def test_spatial_and_reference_scaffolds_are_replaced_with_bounded_real_work() -> None:
    workspace = _read("overtli_blender_addon/services/workspace.py")
    spatial = _read("overtli_blender_addon/services/spatial.py")

    for text in [
        "evaluated_mesh_surface_area",
        "evaluated_bmesh_volume",
        "spline_sampled_length",
        "world_bounding_box_clearance",
        "world_bounding_box_overlap",
        "world_bounds_center_alignment",
    ]:
        assert text in workspace

    for old_text in [
        "mesh-evaluation-deferred",
        "oriented_bounds_product",
        "Phase 7C uses bounds-first intersection scaffolding.",
        "single-face UV island approximation used",
        "no island seed supplied; captured all UV-mapped vertices",
    ]:
        assert old_text not in workspace
        assert old_text not in spatial

    assert "island_seed_face_index is required for UV island traversal" in spatial
    assert "uv_edge_connectivity" in spatial
    assert "obj.empty_image_depth" in workspace
    assert "obj.hide_viewport = not visible" in workspace
    assert "obj.lock_location = (locked, locked, locked)" in workspace
