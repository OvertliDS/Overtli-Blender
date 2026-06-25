"""Stdlib-safe animation workflow schemas for Phase 9A."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TimelineRange:
    frame_start: int
    frame_end: int
    current_frame: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InterpolationSpec:
    interpolation: str = "BEZIER"
    easing: str | None = None
    handle_left_type: str | None = None
    handle_right_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KeyframeSpec:
    frame: float
    data_path: str
    array_index: int | None = None
    value: Any = None
    interpolation: str = "BEZIER"
    easing: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FcurveManifest:
    data_path: str
    array_index: int
    keyframe_count: int = 0
    frame_range: tuple[float, float] | None = None
    modifiers: tuple[dict[str, Any], ...] = ()
    group: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionManifest:
    name: str
    users: int = 0
    frame_range: tuple[float, float] | None = None
    fcurve_count: int = 0
    groups: tuple[str, ...] = ()
    pose_markers: tuple[str, ...] = ()
    assigned_objects: tuple[str, ...] = ()
    asset_status: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NlaStripSpec:
    name: str
    action_name: str | None = None
    frame_start: float = 1.0
    frame_end: float = 1.0
    blend_type: str = "REPLACE"
    extrapolation: str = "HOLD"
    muted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NlaTrackSpec:
    name: str
    muted: bool = False
    solo: bool = False
    strips: tuple[NlaStripSpec, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["strips"] = [strip.to_dict() for strip in self.strips]
        return data


@dataclass(frozen=True)
class AnimationClipSummary:
    object_name: str
    action: ActionManifest | None = None
    fcurves: tuple[FcurveManifest, ...] = ()
    nla_tracks: tuple[NlaTrackSpec, ...] = ()
    drivers: tuple[dict[str, Any], ...] = ()
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_name": self.object_name,
            "action": self.action.to_dict() if self.action else None,
            "fcurves": [fcurve.to_dict() for fcurve in self.fcurves],
            "nla_tracks": [track.to_dict() for track in self.nla_tracks],
            "drivers": list(self.drivers),
            "warnings": list(self.warnings),
        }
