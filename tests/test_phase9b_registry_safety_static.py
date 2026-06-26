from overtli_blender.common.safety import build_command_safety_map
from overtli_blender.runtime.command_registry import build_command_registry
from overtli_blender.runtime.tool_packs import TOOL_PACK_DEFINITIONS, search_tools


PHASE9B_COMMANDS = [
    "get_preferences_schema", "get_runtime_preferences", "update_runtime_preferences",
    "validate_runtime_preferences", "reset_runtime_preferences", "get_tool_profiles",
    "get_active_tool_profile", "set_active_tool_profile", "preview_tool_profile",
    "get_visible_tool_budget", "get_enabled_tool_packs", "set_enabled_tool_packs",
    "recommend_tool_profile", "list_bundled_skill_packs", "get_bundled_skill_pack",
    "search_bundled_skill_packs", "activate_skill_pack", "deactivate_skill_pack",
    "recommend_skill_packs", "validate_skill_pack_readiness", "list_addon_source_roots",
    "scan_addon_sources_readonly", "get_addon_source_summary", "search_addon_operators",
    "search_addon_panels", "search_addon_properties", "plan_addon_operator_invocation",
    "execute_approved_addon_operator", "get_error_catalog", "explain_error",
    "get_remediation_steps", "get_runtime_dashboard", "get_approval_queue_summary",
    "get_recent_operation_summary", "get_setup_status", "run_onboarding_checklist",
    "run_product_polish_workflow_batch",
]


def test_phase9b_commands_have_specs_and_safety():
    registry = build_command_registry()
    safety = build_command_safety_map()
    for command in PHASE9B_COMMANDS:
        assert command in registry
        assert command in safety
    assert registry["execute_approved_addon_operator"].requires_approval is True
    assert safety["execute_approved_addon_operator"].strict_blocked is True


def test_phase9b_tool_packs_and_search_terms_exist():
    for pack in ["product_ux", "preferences", "tool_profiles", "bundled_skills", "addon_interop", "error_help", "onboarding"]:
        assert pack in TOOL_PACK_DEFINITIONS
    for query in ["change permission mode", "show active tool packs", "scan installed addons", "why did path access fail", "show dashboard"]:
        assert search_tools(query)["results"]
