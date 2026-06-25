from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/deformation_tools.py").read_text(encoding="utf-8")


def test_deformation_services_and_allowlists_exist() -> None:
    for text in [
        "class DeformationModifierService",
        "class DirectMeshEditService",
        "class DeformationWorkflowBatchService",
        "def add_deformation_modifier(",
        "def update_deformation_modifier(",
        "def create_region_deformation(",
        "def run_deformation_workflow_batch(",
        "SIMPLE_DEFORM",
        "DISPLACE",
        "SHRINKWRAP",
        "create_region_deformation requires confirm=True",
        "batch_allow_destructive",
    ]:
        assert text in ADDON_TEXT


def test_deformation_mcp_tools_exist() -> None:
    for text in [
        "def register_deformation_tools",
        "def add_deformation_modifier(",
        "def update_deformation_modifier(",
        "def create_region_deformation(",
        "def run_deformation_workflow_batch(",
    ]:
        assert text in TOOLS_TEXT
