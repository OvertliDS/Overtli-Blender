"""Data models for Phase 8B structured modeling workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class MeshSchema:
    vertices: list[list[float]]
    edges: list[list[int]] = field(default_factory=list)
    faces: list[list[int]] = field(default_factory=list)
    uvs: dict[str, Any] = field(default_factory=dict)
    materials: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProfileSchema:
    name: str
    points: list[list[float]]
    closed: bool = True
    plane: str = "XY"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurvePathSchema:
    name: str
    points: list[list[float]]
    curve_type: str = "polyline"
    bevel_depth: float = 0.0
    resolution: int = 12

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModifierStackSchema:
    object_name: str
    modifiers: list[dict[str, Any]]
    stack_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConstructionStep:
    command: str
    params: dict[str, Any]
    requires_approval: bool = False
    destructive: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConstructionWorkflowManifest:
    workflow_id: str
    name: str
    steps: list[ConstructionStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["steps"] = [step.to_dict() if hasattr(step, "to_dict") else step for step in self.steps]
        return data
