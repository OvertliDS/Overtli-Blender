"""Rigging schema dataclasses for Phase 9A."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class BoneSpec:
    name: str
    head: tuple[float, float, float]
    tail: tuple[float, float, float]
    parent: str | None = None
    roll: float = 0.0
    deform: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConstraintSpec:
    name: str
    type: str
    owner_bone: str | None = None
    target_object: str | None = None
    target_bone: str | None = None
    influence: float = 1.0
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControlSpec:
    name: str
    bone_name: str
    shape: str = "PLAIN_AXES"
    layer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IKChainSpec:
    owner_bone: str
    target_object: str
    target_bone: str | None = None
    chain_count: int = 2
    pole_object: str | None = None
    pole_bone: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CustomPropertySpec:
    name: str
    default: float | int | bool | str
    min_value: float | None = None
    max_value: float | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RigTemplate:
    name: str
    bones: tuple[BoneSpec, ...]
    controls: tuple[ControlSpec, ...] = ()
    constraints: tuple[ConstraintSpec, ...] = ()
    custom_properties: tuple[CustomPropertySpec, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "bones": [bone.to_dict() for bone in self.bones],
            "controls": [control.to_dict() for control in self.controls],
            "constraints": [constraint.to_dict() for constraint in self.constraints],
            "custom_properties": [prop.to_dict() for prop in self.custom_properties],
        }


@dataclass(frozen=True)
class WeightDiagnosticSummary:
    mesh_name: str
    armature_name: str | None = None
    vertex_group_count: int = 0
    missing_bone_groups: tuple[str, ...] = ()
    empty_groups: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
