"""Simulation workflow manifest schemas for Phase 9A."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SimulationSetup:
    object_name: str
    simulation_type: str
    frame_start: int
    frame_end: int
    settings: dict[str, Any] = field(default_factory=dict)
    bounded: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulationCacheStatus:
    target_name: str
    simulation_type: str
    frame_start: int | None = None
    frame_end: int | None = None
    is_baked: bool | None = None
    cache_path: str | None = None
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulationPreviewPlan:
    object_name: str
    frame_start: int
    frame_end: int
    max_frames: int = 48
    requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulationBakeManifest:
    target_name: str
    simulation_type: str
    frame_range: tuple[int, int]
    exact_target: bool = True
    requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulationCleanupPlan:
    target_name: str
    cache_items: tuple[str, ...] = ()
    exact_target: bool = True
    requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
