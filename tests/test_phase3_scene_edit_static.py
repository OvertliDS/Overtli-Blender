from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")


PHASE3_COMMANDS = [
    "get_supported_edit_operations",
    "create_primitive_object",
    "transform_object",
    "duplicate_object",
    "delete_objects",
    "set_object_visibility",
    "create_basic_material",
    "assign_material",
    "update_material_properties",
    "add_object_modifier",
    "update_object_modifier",
    "remove_object_modifier",
    "create_collection",
    "move_objects_to_collection",
    "delete_collection",
    "run_verified_edit_batch",
]


def test_phase3_addon_service_classes_exist() -> None:
    for name in [
        "class SceneEditService",
        "class MaterialAuthoringService",
        "class ModifierService",
        "class CollectionOrganizationService",
        "class VerifiedEditBatchService",
    ]:
        assert name in ADDON_TEXT


def test_phase3_services_are_initialized_and_bound() -> None:
    for name in [
        "self.scene_edit_service = SceneEditService(self)",
        "self.material_authoring_service = MaterialAuthoringService(self)",
        "self.modifier_service = ModifierService(self)",
        "self.collection_organization_service = CollectionOrganizationService(self)",
        "self.verified_edit_batch_service = VerifiedEditBatchService(self)",
    ]:
        assert name in ADDON_TEXT


def test_phase3_command_handlers_are_mapped() -> None:
    for name in PHASE3_COMMANDS:
        assert f'"{name}": self.{name}' in ADDON_TEXT


def test_phase3_scene_edit_is_explicit_target_and_confirmed_for_delete() -> None:
    for text in [
        "object_name",
        "object_names",
        "delete_objects requires confirm=True",
        "delete_collection requires confirm=True",
        "Wildcard-like object name refused",
        "get_supported_edit_operations",
    ]:
        assert text in ADDON_TEXT
