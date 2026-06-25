from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_TEXT = (ROOT / "src" / "overtli_blender" / "tools" / "governance_tools.py").read_text(encoding="utf-8")
REGISTRY_TEXT = (ROOT / "src" / "overtli_blender" / "tools" / "registry.py").read_text(encoding="utf-8")


def test_governance_tools_are_registered() -> None:
    assert "def register_governance_tools" in TOOLS_TEXT
    assert "register_governance_tools" in REGISTRY_TEXT
    for name in [
        "discover_tool_packs",
        "get_tool_pack",
        "search_tools",
        "get_tool_spec",
        "prepare_operation",
        "get_pending_approvals",
        "approve_operation",
        "deny_operation",
        "execute_approved_operation",
        "get_operation_status",
        "list_recent_operations",
        "cancel_operation",
        "get_permission_profile",
        "get_capability_policy",
        "validate_command_capabilities",
        "get_log_status",
    ]:
        assert f"def {name}(" in TOOLS_TEXT
        assert f'"{name}"' in TOOLS_TEXT
