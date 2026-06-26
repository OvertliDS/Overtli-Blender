from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT
ADVANCED_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/advanced_material_tools.py").read_text(encoding="utf-8")
PREVIEW_TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/material_preview_tools.py").read_text(encoding="utf-8")


def test_material_preview_batch_and_cleanup_surfaces_exist() -> None:
    for text in [
        "class MaterialPreviewService",
        "class MaterialWorkflowBatchService",
        ".overtli_blender",
        "material_previews",
        "run_material_workflow_batch",
        "before_snapshot",
        "after_snapshot",
        "delete_materials requires confirm=True",
    ]:
        assert text in ADDON_TEXT


def test_advanced_material_mcp_tools_exist() -> None:
    assert "def register_advanced_material_tools" in ADVANCED_TOOLS_TEXT
    for name in [
        "create_material_from_template",
        "create_custom_material",
        "create_procedural_material",
        "create_material_variant",
        "apply_material_to_objects",
        "run_material_workflow_batch",
        "delete_materials",
    ]:
        assert f"def {name}(" in ADVANCED_TOOLS_TEXT
    assert "def register_material_preview_tools" in PREVIEW_TOOLS_TEXT
    assert "def create_material_preview(" in PREVIEW_TOOLS_TEXT
