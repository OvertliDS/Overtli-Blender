from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase7c_file_access_runtime_has_escape_and_atomic_rules() -> None:
    text = (ROOT / "src/overtli_blender/runtime/file_access.py").read_text(encoding="utf-8")
    for marker in ["canonical_path", "has_symlink_escape", "atomic_write_text", "redact_text", "plan_delete"]:
        assert marker in text


def test_phase7c_file_access_addon_commands_exist() -> None:
    from tests._addon_source import ADDON_PACKAGE_SOURCE as addon
    assert "class FileAccessPolicyService" in addon
    for name in ["get_file_access_policy", "set_file_access_policy", "validate_path_access", "list_approved_roots", "add_approved_root", "remove_approved_root", "scan_project_files", "read_project_text_file", "write_project_text_file", "copy_file_into_project", "plan_file_delete", "execute_approved_file_delete"]:
        assert f'"{name}":' in addon
