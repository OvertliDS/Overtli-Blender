from __future__ import annotations

from overtli_blender.runtime.tool_packs import TOOL_PACK_DEFINITIONS, discover_tool_packs, get_tool_spec, search_tools


def test_tool_packs_and_search_cover_representative_terms() -> None:
    assert "core" in TOOL_PACK_DEFINITIONS
    assert "geometry_nodes" in TOOL_PACK_DEFINITIONS
    assert "materials" in TOOL_PACK_DEFINITIONS
    discovered = discover_tool_packs()
    assert discovered["status"] == "success"
    assert len(discovered["tool_packs"]) >= 8
    for query in ["material", "bake", "geometry nodes", "approval", "project workspace"]:
        result = search_tools(query)
        assert result["status"] == "success"
        assert result["results"]


def test_get_tool_spec_returns_command_spec_dict() -> None:
    spec = get_tool_spec("delete_objects")
    assert spec["status"] == "success"
    assert spec["tool"]["name"] == "delete_objects"
    assert spec["tool"]["requires_approval"] is True
