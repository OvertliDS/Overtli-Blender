"""Pure cloth pattern planning data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PatternPanel:
    name: str
    points: list[list[float]]
    thickness: float = 0.01
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SeamPair:
    panel_a: str
    edge_a: list[int]
    panel_b: str
    edge_b: list[int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PinGroup:
    object_name: str
    vertex_indices: list[int]
    group_name: str = "Overtli_Pin"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CollisionTarget:
    object_name: str
    thickness_outer: float = 0.02
    thickness_inner: float = 0.01

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulationPreviewSettings:
    frame_start: int = 1
    frame_end: int = 24
    quality: int = 3
    max_seconds: int = 30

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClothWorkflowManifest:
    workflow_id: str
    panels: list[PatternPanel] = field(default_factory=list)
    seams: list[SeamPair] = field(default_factory=list)
    pins: list[PinGroup] = field(default_factory=list)
    collisions: list[CollisionTarget] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
