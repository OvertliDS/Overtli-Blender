"""Pure sculpt workflow planning models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SculptSessionPlan:
    object_name: str
    brush: str = "SMOOTH"
    use_shape_key: bool = True
    symmetry: tuple[bool, bool, bool] = (False, False, False)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SculptStrokeBatch:
    object_name: str
    strokes: list[dict[str, Any]]
    approval_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SculptMaskPlan:
    object_name: str
    vertex_group_name: str
    invert: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FaceSetPlan:
    object_name: str
    face_indices: list[int]
    face_set_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShapeKeySculptPlan:
    object_name: str
    shape_key_name: str
    basis_name: str = "Basis"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
