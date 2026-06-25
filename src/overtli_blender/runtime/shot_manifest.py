"""Shot and timeline marker schemas for Phase 9A."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ShotRange:
    name: str
    frame_start: int
    frame_end: int
    camera_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CameraCut:
    name: str
    frame: int
    camera_name: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarkerSpec:
    name: str
    frame: int
    camera_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShotValidationIssue:
    severity: str
    message: str
    shot_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShotPlan:
    name: str
    ranges: tuple[ShotRange, ...] = ()
    cuts: tuple[CameraCut, ...] = ()
    markers: tuple[MarkerSpec, ...] = ()
    issues: tuple[ShotValidationIssue, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ranges": [shot.to_dict() for shot in self.ranges],
            "cuts": [cut.to_dict() for cut in self.cuts],
            "markers": [marker.to_dict() for marker in self.markers],
            "issues": [issue.to_dict() for issue in self.issues],
        }
