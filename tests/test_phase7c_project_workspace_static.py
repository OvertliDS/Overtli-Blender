from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def test_phase7c_project_workspace_service_and_commands_exist() -> None:
    assert "class ProjectWorkspaceService" in ADDON_TEXT
    for name in [
        "get_project_status",
        "resolve_project_workspace",
        "initialize_project_workspace",
        "validate_project_layout",
        "repair_project_layout",
        "register_blend_file",
        "save_project_as",
        "create_project_backup",
        "restore_project_backup",
        "collect_project_dependencies",
    ]:
        assert f'"{name}":' in ADDON_TEXT


def test_project_workspace_runtime_module_has_standard_layout() -> None:
    text = (ROOT / "src/overtli_blender/runtime/project_workspace.py").read_text(encoding="utf-8")
    for folder in [".overtli", "textures/source", "references/images", "renders/finals", "backups"]:
        assert folder in text
    assert "def resolve_workspace" in text
    assert "def initialize_workspace" in text
