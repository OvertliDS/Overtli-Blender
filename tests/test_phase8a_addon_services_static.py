from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON


def test_phase8a_addon_service_classes_exist():
    for name in (
        "BakeCapabilitiesService",
        "BakePreflightService",
        "BakeImageTargetService",
        "TextureBakeService",
        "DerivedBakeService",
        "ChannelPackService",
        "BakedTextureValidationService",
        "BakeWorkflowBatchService",
    ):
        assert f"class {name}" in ADDON


def test_phase8a_socket_handlers_exist():
    for command in (
        "get_bake_capabilities",
        "validate_bake_setup",
        "create_bake_target_images",
        "bake_material_maps",
        "bake_selected_to_active",
        "bake_derived_map",
        "pack_texture_channels",
        "run_verified_bake_workflow",
    ):
        assert f'"{command}": self.{command}' in ADDON


def test_phase8a_honest_curvature_thickness_labels():
    assert "Curvature/thickness are approximated, not native bakes." in ADDON
    assert '"unsupported"' in ADDON
