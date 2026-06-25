from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE_TEXT = (ROOT / "scripts/smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_phase7c_smoke_flags_exist() -> None:
    for flag in [
        "--include-project-workspace",
        "--include-file-access-policy",
        "--include-cache-management",
        "--include-task-graph",
        "--include-time-revision",
        "--include-reference-images",
        "--include-spatial-measurement",
        "--include-rename-planning",
        "--phase7c-full",
    ]:
        assert flag in SMOKE_TEXT


def test_phase7c_full_smoke_uses_contained_project_workspace() -> None:
    block = SMOKE_TEXT[SMOKE_TEXT.index("def run_phase7c_full_smoke"):SMOKE_TEXT.index("def build_parser")]
    for marker in [
        ".overtli_blender",
        "phase7c_smoke",
        "initialize_project_workspace",
        "write_project_text_file",
        "create_task",
        "import_reference_image",
        "calculate_distance",
        "plan_rename",
        "plan_cache_cleanup",
        "plan_file_delete",
    ]:
        assert marker in block
    for forbidden in ["execute_code", "download_polyhaven_asset", "download_sketchfab_model", "execute_cache_cleanup"]:
        assert forbidden not in block
