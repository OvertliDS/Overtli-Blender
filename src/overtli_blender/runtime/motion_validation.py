"""Pure motion validation helpers for Phase 9A."""

from __future__ import annotations

from typing import Any


def validate_missing_targets(targets: list[dict[str, Any]]) -> dict[str, Any]:
    missing = [item for item in targets if not item.get("exists", False)]
    return {"status": "success" if not missing else "warning", "missing_targets": missing, "missing_count": len(missing)}


def validate_nla_overlaps(strips: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    by_track: dict[str, list[dict[str, Any]]] = {}
    for strip in strips:
        by_track.setdefault(str(strip.get("track_name", "")), []).append(strip)
    for track_name, items in by_track.items():
        ordered = sorted(items, key=lambda item: float(item.get("frame_start", 0)))
        for left, right in zip(ordered, ordered[1:]):
            if float(left.get("frame_end", 0)) > float(right.get("frame_start", 0)):
                issues.append({"track_name": track_name, "left": left.get("name"), "right": right.get("name"), "issue": "overlap"})
    return {"status": "success" if not issues else "warning", "issues": issues}


def validate_rig_names(bone_names: list[str]) -> dict[str, Any]:
    duplicates = sorted({name for name in bone_names if bone_names.count(name) > 1})
    empty = [name for name in bone_names if not name.strip()]
    return {"status": "success" if not duplicates and not empty else "warning", "duplicates": duplicates, "empty_names": empty}


def validate_bone_hierarchy(bones: list[dict[str, Any]]) -> dict[str, Any]:
    names = {str(item.get("name")) for item in bones}
    missing_parents = [item for item in bones if item.get("parent") and item.get("parent") not in names]
    return {"status": "success" if not missing_parents else "warning", "missing_parents": missing_parents}


def validate_driver_variables(drivers: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for driver in drivers:
        if not driver.get("variables"):
            issues.append({"driver": driver.get("data_path"), "issue": "missing_variables"})
        if driver.get("expression") and "__" in str(driver.get("expression")):
            issues.append({"driver": driver.get("data_path"), "issue": "unsafe_expression_marker"})
    return {"status": "success" if not issues else "warning", "issues": issues}


def validate_motion_bounds(samples: list[dict[str, Any]], bounds: dict[str, float] | None = None) -> dict[str, Any]:
    bounds = bounds or {}
    issues = []
    for sample in samples:
        loc = sample.get("location") or [0, 0, 0]
        for axis, value in zip(("x", "y", "z"), loc):
            min_key = f"min_{axis}"
            max_key = f"max_{axis}"
            if min_key in bounds and float(value) < float(bounds[min_key]):
                issues.append({"frame": sample.get("frame"), "axis": axis, "issue": "below_min"})
            if max_key in bounds and float(value) > float(bounds[max_key]):
                issues.append({"frame": sample.get("frame"), "axis": axis, "issue": "above_max"})
    return {"status": "success" if not issues else "warning", "issues": issues}


def simulation_cache_status_schema(target_name: str, simulation_type: str, **kwargs: Any) -> dict[str, Any]:
    return {"target_name": target_name, "simulation_type": simulation_type, **kwargs}
