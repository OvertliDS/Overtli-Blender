"""Pose snapshot and pose asset schemas for Phase 9A."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PoseSnapshot:
    snapshot_id: str
    armature_name: str
    frame: int | None = None
    bones: dict[str, dict[str, Any]] = field(default_factory=dict)
    storage: str = "manifest"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PoseAssetManifest:
    asset_id: str
    name: str
    armature_name: str
    snapshot_id: str
    native_asset: bool = False
    storage: str = "manifest"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PoseComparison:
    source_id: str
    target_id: str
    changed_bones: tuple[str, ...] = ()
    max_delta: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PoseApplicationPlan:
    snapshot_id: str
    armature_name: str
    bone_count: int
    requires_approval: bool = True
    destructive: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
