from __future__ import annotations


def test_remote_browser_safe_blocks_high_risk_capabilities() -> None:
    from overtli_blender.runtime.capabilities import PROFILE_CAPABILITIES

    caps = PROFILE_CAPABILITIES["remote_browser_safe"]
    for blocked in [
        "raw_python",
        "filesystem.external.write",
        "filesystem.delete",
        "network.providers",
        "addon.execute",
        "external_process",
    ]:
        assert blocked not in caps


def test_chatgpt_profile_search_can_discover_workflows() -> None:
    from overtli_blender.runtime.tool_packs import search_tools

    results = search_tools("reference modeling workflow", limit=10)
    names = {item["name"] for item in results["results"]}
    assert results["status"] == "success"
    assert names
