from pathlib import Path


from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def test_phase9b_addon_service_classes_exist():
    for marker in [
        "class PreferencesConfigurationService",
        "class ToolProfileService",
        "class BundledSkillPackService",
        "class AddonInteropInspectionService",
        "class UserFacingErrorService",
        "class OnboardingWorkflowService",
        "class RuntimeUXStatusService",
        "class ProductPolishWorkflowBatchService",
        "class BLENDERMCP_AddonPreferences",
    ]:
        assert marker in ADDON_TEXT


def test_phase9b_socket_handlers_exist():
    for command in [
        "get_preferences_schema", "update_runtime_preferences", "get_tool_profiles",
        "set_active_tool_profile", "list_bundled_skill_packs", "scan_addon_sources_readonly",
        "plan_addon_operator_invocation", "get_error_catalog", "get_runtime_dashboard",
        "get_setup_status", "run_product_polish_workflow_batch",
    ]:
        assert f'"{command}"' in ADDON_TEXT


def test_phase9b_fallback_runtime_helpers_exist():
    for marker in [
        "def runtime_preferences_config_path",
        "def runtime_default_preferences",
        "def runtime_list_tool_profiles",
        "def runtime_recommend_tool_profile",
        "def runtime_list_bundled_skill_packs",
        "def runtime_scan_addon_sources",
        "def runtime_build_dashboard",
    ]:
        assert marker in ADDON_TEXT
