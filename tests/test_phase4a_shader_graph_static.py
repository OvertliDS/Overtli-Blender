from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/shader_graph_tools.py").read_text(encoding="utf-8")


def test_shader_graph_allowlist_and_commands_exist() -> None:
    for text in [
        "ALLOWED_NODE_TYPES",
        "ShaderNodeTexNoise",
        "ShaderNodeValToRGB",
        "ShaderNodeBump",
        "ShaderNodeNormalMap",
        "get_shader_graph",
        "set_material_node_input",
        "add_material_node",
        "connect_material_nodes",
        "remove_material_node",
        "requires confirm=True",
        "Refusing to remove non-Overtli or non-allowlisted material node",
    ]:
        assert text in ADDON_TEXT


def test_shader_graph_mcp_tools_exist() -> None:
    assert "def register_shader_graph_tools" in TOOLS_TEXT
    for name in ["get_shader_graph", "set_material_node_input", "add_material_node", "connect_material_nodes", "remove_material_node"]:
        assert f"def {name}(" in TOOLS_TEXT
