from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")


def test_phase6b_services_exist_and_are_initialized() -> None:
    for name in [
        "class AddonManagementService",
        "class AddonDevelopmentService",
        "class BlenderApiKnowledgeService",
        "class VerifiedSnippetLibraryService",
        "class SkillPackService",
        "class ReviewPackageExportService",
        "class AdvancedKnowledgeWorkflowBatchService",
        "self.addon_management_service = AddonManagementService(self)",
        "self.addon_development_service = AddonDevelopmentService(self)",
        "self.blender_api_knowledge_service = BlenderApiKnowledgeService(self)",
        "self.advanced_knowledge_workflow_batch_service = AdvancedKnowledgeWorkflowBatchService(self)",
    ]:
        assert name in ADDON_TEXT


def test_phase6b_all_command_strings_exist() -> None:
    for command in [
        "get_addon_management_status",
        "list_blender_addons",
        "get_blender_addon_info",
        "install_local_addon",
        "enable_blender_addon",
        "disable_blender_addon",
        "remove_blender_addon",
        "create_addon_skeleton",
        "validate_addon_skeleton",
        "package_addon_zip",
        "inspect_blender_api_docs",
        "build_blender_api_index",
        "search_blender_api_docs",
        "get_blender_api_topic",
        "create_verified_snippet",
        "validate_verified_snippet",
        "list_verified_snippets",
        "search_verified_snippets",
        "get_verified_snippet",
        "run_verified_snippet_smoke",
        "delete_verified_snippets",
        "create_skill_pack",
        "validate_skill_pack",
        "list_skill_packs",
        "get_skill_pack",
        "run_skill_pack",
        "delete_skill_packs",
        "export_project_review_package",
        "validate_review_package",
        "run_advanced_knowledge_workflow_batch",
    ]:
        assert f'"{command}":' in ADDON_TEXT or f"self.{command} =" in ADDON_TEXT


def test_addon_lifecycle_commands_are_confirm_gated_and_local_only() -> None:
    for text in [
        "install_local_addon requires confirm=True",
        "enable_blender_addon requires confirm=True",
        "disable_blender_addon requires confirm=True",
        "remove_blender_addon requires confirm=True",
        "Remote addon paths are not supported",
        "module_name must be an exact Python module name",
    ]:
        assert text in ADDON_TEXT
