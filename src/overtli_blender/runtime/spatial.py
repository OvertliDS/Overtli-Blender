"""Dependency-free spatial math helpers."""

from __future__ import annotations

import math
from typing import Any


def distance(a: list[float] | tuple[float, ...], b: list[float] | tuple[float, ...]) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def angle_degrees(a: list[float], b: list[float], c: list[float]) -> float:
    ba = [x - y for x, y in zip(a, b)]
    bc = [x - y for x, y in zip(c, b)]
    dot = sum(x * y for x, y in zip(ba, bc))
    denom = math.sqrt(sum(x * x for x in ba)) * math.sqrt(sum(x * x for x in bc))
    if denom == 0:
        raise ValueError("Cannot calculate angle with zero-length vector.")
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / denom))))


def convert_units(value: float, from_unit: str = "BLENDER_UNIT", to_unit: str = "METERS", scale_length: float = 1.0) -> dict[str, Any]:
    meters = float(value) * float(scale_length) if from_unit.upper() in {"BLENDER_UNIT", "BU"} else float(value)
    converted = meters / float(scale_length) if to_unit.upper() in {"BLENDER_UNIT", "BU"} and scale_length else meters
    return {"status": "success", "value": converted, "value_meters": meters, "from_unit": from_unit, "to_unit": to_unit, "confidence": "high"}
