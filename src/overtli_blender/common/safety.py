from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .operation_types import OperationType
from .permissions import Reversibility, RiskLevel


SAFETY_MODE_COMPAT = "compatibility"
SAFETY_MODE_AUDIT = "audit"
SAFETY_MODE_STRICT = "strict"
SAFETY_POLICY_VERSION = "1.0"
DEFAULT_SAFETY_MODE = SAFETY_MODE_COMPAT
AVAILABLE_SAFETY_MODES = [SAFETY_MODE_COMPAT, SAFETY_MODE_AUDIT, SAFETY_MODE_STRICT]


@dataclass(frozen=True)
class CommandSafetyMetadata:
    command_type: str
    operation_type: OperationType
    risk_level: RiskLevel
    reversibility: Reversibility
    can_mutate_scene: bool = False
    can_execute_code: bool = False
    can_call_network: bool = False
    can_write_files: bool = False
    provider_api_key_involved: bool = False
    strict_blocked: bool = False
    default_action: str = "allow"
    strict_action: str = "block"
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["operation_type"] = self.operation_type.value
        data["risk_level"] = self.risk_level.value
        data["reversibility"] = self.reversibility.value
        data["warnings"] = list(self.warnings)
        return data


def _spec(command_type: str, operation_type: OperationType, risk_level: RiskLevel, reversibility: Reversibility, **kwargs: Any) -> CommandSafetyMetadata:
    return CommandSafetyMetadata(
        command_type=command_type,
        operation_type=operation_type,
        risk_level=risk_level,
        reversibility=reversibility,
        **kwargs,
    )


def build_command_safety_map() -> dict[str, CommandSafetyMetadata]:
    return {
        "get_scene_info": _spec("get_scene_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_object_info": _spec("get_object_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_shared_context": _spec("get_shared_context", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_operation_history": _spec("get_operation_history", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_object_handles": _spec("list_object_handles", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_material_handles": _spec("list_material_handles", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "list_context_scripts": _spec("list_context_scripts", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_polyhaven_status": _spec("get_polyhaven_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_hyper3d_status": _spec("get_hyper3d_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE, provider_api_key_involved=True),
        "get_sketchfab_status": _spec("get_sketchfab_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE, provider_api_key_involved=True),
        "get_geometry_nodes_status": _spec("get_geometry_nodes_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_safety_status": _spec("get_safety_status", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_viewport_screenshot": _spec(
            "get_viewport_screenshot",
            OperationType.CAMERA,
            RiskLevel.MEDIUM,
            Reversibility.REVERSIBLE,
            can_mutate_scene=False,
            warnings=("viewport-context-dependent",),
        ),
        "get_scene_index": _spec("get_scene_index", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_object_deep_info": _spec("get_object_deep_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_selection_info": _spec("get_selection_info", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_scene_health": _spec("get_scene_health", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "capture_viewport_pack": _spec(
            "capture_viewport_pack",
            OperationType.CAMERA,
            RiskLevel.MEDIUM,
            Reversibility.REVERSIBLE,
            can_write_files=True,
            warnings=("writes-local-verification-artifacts", "viewport-context-dependent"),
        ),
        "create_verification_snapshot": _spec(
            "create_verification_snapshot",
            OperationType.VERIFY,
            RiskLevel.MEDIUM,
            Reversibility.REVERSIBLE,
            can_write_files=True,
            warnings=("writes-local-verification-artifacts",),
        ),
        "list_verification_snapshots": _spec("list_verification_snapshots", OperationType.VERIFY, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "get_supported_edit_operations": _spec("get_supported_edit_operations", OperationType.OBSERVE, RiskLevel.LOW, Reversibility.REVERSIBLE),
        "create_primitive_object": _spec("create_primitive_object", OperationType.CREATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "transform_object": _spec("transform_object", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "duplicate_object": _spec("duplicate_object", OperationType.CREATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "delete_objects": _spec("delete_objects", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required",)),
        "set_object_visibility": _spec("set_object_visibility", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_basic_material": _spec("create_basic_material", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "assign_material": _spec("assign_material", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "update_material_properties": _spec("update_material_properties", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "add_object_modifier": _spec("add_object_modifier", OperationType.MODIFIER, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "update_object_modifier": _spec("update_object_modifier", OperationType.MODIFIER, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "remove_object_modifier": _spec("remove_object_modifier", OperationType.MODIFIER, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required",)),
        "create_collection": _spec("create_collection", OperationType.CREATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "move_objects_to_collection": _spec("move_objects_to_collection", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True),
        "delete_collection": _spec("delete_collection", OperationType.CLEANUP, RiskLevel.HIGH, Reversibility.PARTIAL, can_mutate_scene=True, strict_blocked=True, warnings=("explicit-confirmation-required", "empty-collection-only-by-default")),
        "run_verified_edit_batch": _spec("run_verified_edit_batch", OperationType.EDIT, RiskLevel.MEDIUM, Reversibility.PARTIAL, can_mutate_scene=True, can_write_files=True, warnings=("writes-local-verification-artifacts",)),
        "create_object_handle": _spec("create_object_handle", OperationType.CREATE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "create_material_handle": _spec("create_material_handle", OperationType.MATERIAL, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_mutate_scene=True),
        "register_context_script": _spec("register_context_script", OperationType.UPDATE_KNOWLEDGE, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_write_files=True),
        "execute_context_script": _spec(
            "execute_context_script",
            OperationType.UPDATE_KNOWLEDGE,
            RiskLevel.HIGH,
            Reversibility.UNKNOWN,
            can_execute_code=True,
            can_write_files=True,
            strict_blocked=True,
            warnings=("executes-user-registered-python",),
        ),
        "clear_context_scripts": _spec(
            "clear_context_scripts",
            OperationType.CLEANUP,
            RiskLevel.MEDIUM,
            Reversibility.PARTIAL,
            can_write_files=True,
            strict_blocked=True,
        ),
        "clear_shared_context": _spec(
            "clear_shared_context",
            OperationType.CLEANUP,
            RiskLevel.MEDIUM,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            strict_blocked=True,
        ),
        "get_polyhaven_categories": _spec("get_polyhaven_categories", OperationType.ASSET_LIBRARY, RiskLevel.LOW, Reversibility.REVERSIBLE, can_call_network=True),
        "search_polyhaven_assets": _spec("search_polyhaven_assets", OperationType.ASSET_LIBRARY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_call_network=True),
        "download_polyhaven_asset": _spec(
            "download_polyhaven_asset",
            OperationType.ASSET_LIBRARY,
            RiskLevel.HIGH,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            can_call_network=True,
            can_write_files=True,
            strict_blocked=True,
        ),
        "set_texture": _spec(
            "set_texture",
            OperationType.TEXTURE,
            RiskLevel.MEDIUM,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
        ),
        "search_sketchfab_models": _spec("search_sketchfab_models", OperationType.ASSET_LIBRARY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_call_network=True, provider_api_key_involved=True),
        "download_sketchfab_model": _spec(
            "download_sketchfab_model",
            OperationType.ASSET_LIBRARY,
            RiskLevel.HIGH,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            can_call_network=True,
            can_write_files=True,
            provider_api_key_involved=True,
            strict_blocked=True,
        ),
        "create_rodin_job": _spec(
            "create_rodin_job",
            OperationType.ASSET_LIBRARY,
            RiskLevel.HIGH,
            Reversibility.UNKNOWN,
            can_call_network=True,
            provider_api_key_involved=True,
            strict_blocked=True,
        ),
        "poll_rodin_job_status": _spec("poll_rodin_job_status", OperationType.VERIFY, RiskLevel.MEDIUM, Reversibility.REVERSIBLE, can_call_network=True, provider_api_key_involved=True),
        "import_generated_asset": _spec(
            "import_generated_asset",
            OperationType.IMPORT,
            RiskLevel.HIGH,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            can_call_network=True,
            can_write_files=True,
            provider_api_key_involved=True,
            strict_blocked=True,
        ),
        "complete_geometry_node": _spec(
            "complete_geometry_node",
            OperationType.GEOMETRY_NODES,
            RiskLevel.HIGH,
            Reversibility.PARTIAL,
            can_mutate_scene=True,
            strict_blocked=True,
        ),
        "execute_code": _spec(
            "execute_code",
            OperationType.VERIFY,
            RiskLevel.HIGH,
            Reversibility.UNKNOWN,
            can_execute_code=True,
            strict_blocked=True,
            warnings=("arbitrary-python-execution",),
        ),
    }


def get_command_safety(command_type: str) -> CommandSafetyMetadata | None:
    return build_command_safety_map().get(command_type)
