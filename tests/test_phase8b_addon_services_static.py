from pathlib import Path


from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def test_phase8b_addon_service_classes_exist():
    for marker in [
        "class MeshSchemaConstructionService",
        "class ProfileModelingService",
        "class ModifierConstructionService",
        "class ReferenceDrivenConstructionService",
        "class SculptWorkflowPhase8BService",
        "class ClothPatternWorkflowService",
        "class ConstructionValidationService",
        "class AdvancedModelingWorkflowBatchService",
    ]:
        assert marker in ADDON_TEXT


def test_phase8b_socket_handlers_exist():
    for command in [
        "get_modeling_capabilities",
        "create_mesh_from_schema",
        "lathe_profile",
        "create_modifier_stack",
        "plan_reference_construction",
        "apply_sculpt_stroke_batch",
        "simulate_cloth_preview",
        "validate_construction_geometry",
        "run_advanced_modeling_workflow_batch",
    ]:
        assert f'"{command}"' in ADDON_TEXT


def test_phase8b_high_risk_paths_are_honest():
    assert "requires_approval" in ADDON_TEXT
    assert "unsupported" in ADDON_TEXT
    assert "stroke playback is high risk" in ADDON_TEXT
