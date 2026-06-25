from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "src/overtli_blender/tools"


def test_phase7c_tool_modules_exist_and_are_bpy_free() -> None:
    for filename, helper in {
        "project_workspace_tools.py": "register_project_workspace_tools",
        "file_access_tools.py": "register_file_access_tools",
        "cache_tools.py": "register_cache_tools",
        "task_graph_tools.py": "register_task_graph_tools",
        "reference_tools.py": "register_reference_tools",
        "spatial_tools.py": "register_spatial_tools",
    }.items():
        text = (TOOLS / filename).read_text(encoding="utf-8")
        assert f"def {helper}" in text
        assert "import bpy" not in text


def test_phase7c_registry_references_new_tool_helpers() -> None:
    registry = (TOOLS / "registry.py").read_text(encoding="utf-8")
    for helper in ["register_project_workspace_tools", "register_file_access_tools", "register_cache_tools", "register_task_graph_tools", "register_reference_tools", "register_spatial_tools"]:
        assert helper in registry
