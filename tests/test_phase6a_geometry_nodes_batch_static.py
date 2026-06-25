from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
SMOKE_TEXT = (ROOT / "scripts" / "smoke_blender_addon_socket.py").read_text(encoding="utf-8")
REGISTRY_TEXT = (ROOT / "src" / "overtli_blender" / "tools" / "registry.py").read_text(encoding="utf-8")
INIT_TEXT = (ROOT / "src" / "overtli_blender" / "tools" / "__init__.py").read_text(encoding="utf-8")
SAFETY_TEXT = (ROOT / "src" / "overtli_blender" / "common" / "safety.py").read_text(encoding="utf-8")


MCP_MODULES = [
    "geometry_nodes_intelligence_tools.py",
    "geometry_nodes_template_tools.py",
    "geometry_nodes_modifier_tools.py",
    "procedural_asset_tools.py",
    "geometry_nodes_workflow_tools.py",
]


def test_phase6a_mcp_modules_and_registry_are_present() -> None:
    for module in MCP_MODULES:
        assert (ROOT / "src" / "overtli_blender" / "tools" / module).exists()

    for helper in [
        "register_geometry_nodes_intelligence_tools",
        "register_geometry_nodes_template_tools",
        "register_geometry_nodes_modifier_tools",
        "register_procedural_asset_tools",
        "register_geometry_nodes_workflow_tools",
    ]:
        assert helper in REGISTRY_TEXT
        assert helper in INIT_TEXT


def test_phase6a_workflow_batch_allowlist_and_destructive_guards_are_present() -> None:
    block = ADDON_TEXT[ADDON_TEXT.index("class GeometryNodesWorkflowBatchService"):ADDON_TEXT.index("class GeometryNodesService")]
    assert "ALLOWED_COMMANDS" in block
    assert "DESTRUCTIVE_COMMANDS" in block
    assert "batch_allow_destructive" in block
    assert "operation confirm=True" in block
    for forbidden in ["execute_code", "download_polyhaven_asset", "download_sketchfab_model", "create_rodin_job"]:
        assert forbidden not in block


def test_phase6a_safety_risk_classes_are_present() -> None:
    for command in [
        '"get_geometry_nodes_capabilities", OperationType.GEOMETRY_NODES, RiskLevel.LOW',
        '"create_geometry_node_group_from_template", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM',
        '"create_procedural_asset", OperationType.GEOMETRY_NODES, RiskLevel.MEDIUM',
        '"delete_geometry_node_groups", OperationType.CLEANUP, RiskLevel.HIGH',
        '"remove_geometry_nodes_modifiers", OperationType.CLEANUP, RiskLevel.HIGH',
    ]:
        assert command in SAFETY_TEXT
    assert '"delete_geometry_node_groups"' in SAFETY_TEXT and "strict_blocked=True" in SAFETY_TEXT


def test_phase6a_smoke_flags_are_present() -> None:
    for flag in [
        "--include-geometry-nodes-capabilities",
        "--include-geometry-nodes-intelligence",
        "--include-geometry-node-templates",
        "--include-geometry-node-recipe",
        "--include-procedural-assets",
        "--include-scatter-system",
        "--include-curve-generator",
        "--include-radial-array-system",
        "--include-panel-generator",
        "--include-geometry-nodes-preview",
        "--include-geometry-nodes-workflow-batch",
        "--phase6a-full",
    ]:
        assert flag in SMOKE_TEXT
