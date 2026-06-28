from __future__ import annotations


def test_remote_browser_safe_allows_full_capabilities_with_approval_gates() -> None:
    from overtli_blender.runtime.capabilities import PROFILE_CAPABILITIES

    caps = PROFILE_CAPABILITIES["remote_browser_safe"]
    assert PROFILE_CAPABILITIES["browser_standard"] == caps
    assert {"raw_python", "filesystem.external.write", "addon.execute", "addon.manage", "external_process", "filesystem.delete", "network.providers"} <= caps


def test_chatgpt_profile_search_can_discover_workflows() -> None:
    from overtli_blender.runtime.tool_packs import search_tools

    results = search_tools("reference modeling workflow", limit=10)
    names = {item["name"] for item in results["results"]}
    assert results["status"] == "success"
    assert names
