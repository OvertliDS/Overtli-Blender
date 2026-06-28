from __future__ import annotations

from pathlib import Path

from tests._addon_source import ADDON_PACKAGE_SOURCE


ROOT = Path(__file__).resolve().parents[1]


def test_project_workspace_runtime_supports_folder_repair_move_and_drive_roots(tmp_path: Path) -> None:
    from overtli_blender.runtime.project_workspace import (
        copy_project_folder,
        detect_drive_roots,
        get_loaded_project_folder,
        plan_project_folder_move,
        repair_workspace_layout,
        resource_folder_manifest,
        validate_layout,
    )

    source = tmp_path / "Existing Project"
    source.mkdir()
    blend = source / "Scene.blend"
    blend.write_text("placeholder", encoding="utf-8")
    repaired = repair_workspace_layout(source, project_name="Existing Project", blend_filepath=blend)
    assert repaired["status"] == "success"
    assert (source / ".overtli" / "project.json").is_file()
    assert repaired["manifest"]["storage_backend"] == "json_files"
    assert repaired["manifest"]["persistence"]["sqlite"] is False
    assert repaired["manifest"]["resource_folders"]["texture_source"].endswith("textures\\source") or repaired["manifest"]["resource_folders"]["texture_source"].endswith("textures/source")
    assert "texture_baked" in resource_folder_manifest(source)
    assert validate_layout(source)["status"] == "success"

    loaded = get_loaded_project_folder(str(blend))
    assert loaded["project_folder"] == str(source.resolve())

    plan = plan_project_folder_move(source, tmp_path / "Moved", new_project_name="Scene Project", blend_filepath=blend)
    assert plan["status"] == "requires_approval"
    assert plan["target_blend_filepath"].endswith("Scene.blend")

    copied = copy_project_folder(source, tmp_path / "Moved" / "Scene Project")
    assert copied["status"] == "success"
    assert detect_drive_roots()["status"] == "success"


def test_project_folder_commands_are_wired_to_addon_and_mcp_wrappers() -> None:
    for name in [
        "get_loaded_project_folder",
        "resave_project_folder",
        "plan_project_folder_move",
        "move_project_folder",
        "detect_drive_roots",
        "approve_drive_roots",
    ]:
        assert f'"{name}":' in ADDON_PACKAGE_SOURCE

    project_tools = (ROOT / "src/overtli_blender/tools/project_workspace_tools.py").read_text(encoding="utf-8")
    file_tools = (ROOT / "src/overtli_blender/tools/file_access_tools.py").read_text(encoding="utf-8")
    for name in ["get_loaded_project_folder", "resave_project_folder", "plan_project_folder_move", "move_project_folder"]:
        assert f"def {name}" in project_tools
    for name in ["detect_drive_roots", "approve_drive_roots"]:
        assert f"def {name}" in file_tools
    assert "collect_external_images: bool = True" in project_tools
    assert "make_paths_relative: bool = True" in project_tools
    assert "copy_external_images: bool = False" in project_tools


def test_project_folder_commands_are_in_safety_and_browser_checks() -> None:
    safety = (ROOT / "src/overtli_blender/common/safety.py").read_text(encoding="utf-8")
    connector = (ROOT / "scripts/chatgpt_connector_check.py").read_text(encoding="utf-8")
    server = (ROOT / "src/overtli_blender/server.py").read_text(encoding="utf-8")
    for name in [
        "get_loaded_project_folder",
        "resave_project_folder",
        "plan_project_folder_move",
        "move_project_folder",
        "detect_drive_roots",
        "approve_drive_roots",
    ]:
        assert name in safety
        assert name in connector
        assert name in server


def test_browser_approval_tools_execute_from_approve_by_default() -> None:
    governance_tools = (ROOT / "src/overtli_blender/tools/governance_tools.py").read_text(encoding="utf-8")
    socket_server = (ROOT / "overtli_blender_addon/runtime/socket_server.py").read_text(encoding="utf-8")
    core = (ROOT / "overtli_blender_addon/core.py").read_text(encoding="utf-8")
    assert "def approve_operation(approval_id: str, execute_after_approval: bool = True, approve_only: bool = False)" in governance_tools
    assert "approve_only: bool = False" in governance_tools
    assert "def approve_operation(self, approval_id, execute_after_approval=True, approve_only=False)" in socket_server
    assert "def execute_approved_operation(approval_id: str, command_name: str | None = None" in governance_tools
    assert "def execute_approved_operation(self, approval_id, command_name=None" in socket_server
    assert "get_approval_record" in socket_server
    assert "def _normalize_handler_result" in socket_server
    assert "def _strip_transport_metadata" in socket_server
    assert '"ctx"' in socket_server
    assert "clean_params = self._strip_transport_metadata(params or {})" in socket_server
    assert "handler(**params)" in socket_server
    assert "requires confirm=True" in socket_server
    assert "approval_required" in socket_server
    assert "def get_approval_record" in core


def test_public_repo_zip_builder_excludes_private_and_generated_surfaces() -> None:
    script = (ROOT / "scripts/build_public_repo_zip.py").read_text(encoding="utf-8")
    assert "overtli_blender_addon" in script
    assert "src/overtli_blender" in script
    for forbidden in ["memory_bank", ".overtli_blender", "Overtli-Blender_AIReview_Drive", "tools", "AGENTS.md", "AIReview.config.json"]:
        assert forbidden in script


def test_workspace_restore_and_sculpt_approval_contracts_are_not_plan_only() -> None:
    workspace = (ROOT / "overtli_blender_addon/services/workspace.py").read_text(encoding="utf-8")
    sculpt = (ROOT / "overtli_blender_addon/services/sculpt.py").read_text(encoding="utf-8")
    approval = (ROOT / "src/overtli_blender/runtime/approval.py").read_text(encoding="utf-8")
    assert "bpy.ops.wm.open_mainfile" in workspace
    assert "pre_restore_backup" in workspace
    assert "Restore is planned but not executed automatically" not in workspace
    assert "configure_sculpt_brush requires confirm=True" in sculpt
    assert "run_shape_key_sculpt_workflow requires confirm=True" in sculpt
    assert '"status": "requires_approval"' in sculpt
    assert '"not_implemented"' not in approval
    assert '"dispatch_required": True' in approval
