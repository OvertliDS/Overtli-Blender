from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
SAFETY_TEXT = (ROOT / "src/overtli_blender/common/safety.py").read_text(encoding="utf-8")
REGISTRY_TEXT = (ROOT / "src/overtli_blender/tools/registry.py").read_text(encoding="utf-8")


PHASE5B_COMMANDS = [
    "get_supported_asset_formats",
    "scan_asset_folder",
    "list_asset_libraries",
    "list_scene_assets",
    "get_asset_file_info",
    "get_asset_dependency_report",
    "create_asset_manifest",
    "append_blend_asset",
    "import_model_file",
    "export_selected_objects",
    "export_scene",
    "create_asset_preview",
    "create_asset_contact_sheet",
    "create_scene_kit",
    "import_scene_kit",
    "validate_scene_kit",
    "list_scene_kits",
    "collect_external_dependencies",
    "validate_external_dependencies",
    "pack_external_data",
    "make_paths_relative",
    "cleanup_asset_artifacts",
    "run_asset_workflow_batch",
]


def test_phase5b_addon_services_are_present_and_initialized() -> None:
    for text in [
        "class AssetLibraryIntelligenceService",
        "class AssetDependencyService",
        "class AssetImportService",
        "class AssetExportService",
        "class BlendLibraryService",
        "class SceneKitService",
        "class AssetPreviewService",
        "class AssetWorkflowBatchService",
        "self.asset_library_intelligence_service = AssetLibraryIntelligenceService(self)",
        "self.asset_dependency_service = AssetDependencyService(self)",
        "self.asset_import_service = AssetImportService(self)",
        "self.asset_export_service = AssetExportService(self)",
        "self.blend_library_service = BlendLibraryService(self)",
        "self.scene_kit_service = SceneKitService(self)",
        "self.asset_preview_service = AssetPreviewService(self)",
        "self.asset_workflow_batch_service = AssetWorkflowBatchService(self)",
    ]:
        assert text in ADDON_TEXT


def test_phase5b_commands_are_exposed_by_addon_handlers() -> None:
    missing = [command for command in PHASE5B_COMMANDS if f'"{command}": self.{command}' not in ADDON_TEXT]
    assert missing == []


def test_phase5b_runtime_detection_and_workspace_paths_are_present() -> None:
    for text in [
        "IMPORT_OPERATORS",
        "EXPORT_OPERATORS",
        "bpy.ops.import_scene.gltf",
        "bpy.ops.wm.obj_import",
        "bpy.ops.export_scene.gltf",
        "bpy.ops.wm.obj_export",
        '".overtli_blender"',
        '"assets", "scans"',
        '"exports", "selected"',
        '"scene_kits"',
    ]:
        assert text in ADDON_TEXT


def test_phase5b_mcp_modules_and_registry_are_present() -> None:
    modules = {
        "asset_library_tools.py": "register_asset_library_tools",
        "dependency_tools.py": "register_dependency_tools",
        "import_export_tools.py": "register_import_export_tools",
        "scene_kit_tools.py": "register_scene_kit_tools",
        "asset_workflow_tools.py": "register_asset_workflow_tools",
    }
    for filename, helper in modules.items():
        text = (ROOT / f"src/overtli_blender/tools/{filename}").read_text(encoding="utf-8")
        assert f"def {helper}" in text
        assert helper in REGISTRY_TEXT
    for command in PHASE5B_COMMANDS:
        assert command in "".join((ROOT / f"src/overtli_blender/tools/{name}").read_text(encoding="utf-8") for name in modules)


def test_phase5b_safety_risk_classes_are_present() -> None:
    for command in ["get_supported_asset_formats", "scan_asset_folder", "list_scene_assets", "validate_scene_kit"]:
        assert f'"{command}": _spec("{command}"' in SAFETY_TEXT
        assert "RiskLevel.LOW" in SAFETY_TEXT.split(f'"{command}": _spec("{command}"', 1)[1].split("),", 1)[0]
    for command in ["import_model_file", "export_selected_objects", "create_scene_kit", "run_asset_workflow_batch"]:
        assert f'"{command}": _spec("{command}"' in SAFETY_TEXT
        assert "RiskLevel.MEDIUM" in SAFETY_TEXT.split(f'"{command}": _spec("{command}"', 1)[1].split("),", 1)[0]
    for command in ["pack_external_data", "make_paths_relative", "cleanup_asset_artifacts"]:
        entry = SAFETY_TEXT.split(f'"{command}": _spec("{command}"', 1)[1].split("),", 1)[0]
        assert "RiskLevel.HIGH" in entry
        assert "strict_blocked=True" in entry
