from overtli_blender.runtime.ux_status import approval_queue_summary, recent_operation_summary, runtime_dashboard


def test_phase9b_dashboard_contains_core_sections():
    result = runtime_dashboard(
        {"filesystem": {"permission_profile": "standard", "approved_roots": []}, "tool_profiles": {"active_profile": "safe_scene"}},
        {"enabled_tool_packs": ["core"]},
        {"status": "success", "blockers": [], "next_actions": []},
    )
    dashboard = result["dashboard"]
    assert dashboard["active_tool_profile"] == "safe_scene"
    assert "approval_queue" in dashboard
    assert dashboard["warnings"]


def test_phase9b_queue_and_recent_summaries():
    assert approval_queue_summary({"approvals": [{"id": "a"}]})["pending_count"] == 1
    assert recent_operation_summary({"operations": [{"status": "error"}]})["failure_count"] == 1
