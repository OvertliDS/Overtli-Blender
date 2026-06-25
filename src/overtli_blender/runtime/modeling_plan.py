"""Pure planning helpers for structured modeling method selection."""

from __future__ import annotations

from typing import Any


METHOD_ORDER = (
    "reference_guided",
    "mesh_schema",
    "curve_profile",
    "modifier_stack",
    "geometry_nodes",
    "sculpt_shape_key",
    "cloth_pattern",
    "destructive_mesh",
)


def select_modeling_method(intent: str, constraints: dict[str, Any] | None = None) -> dict[str, Any]:
    text = intent.lower()
    constraints = constraints or {}
    if any(term in text for term in ("reference", "silhouette", "measurement", "calibrated")):
        method = "reference_guided"
    elif any(term in text for term in ("pipe", "rail", "cable", "rope", "curve", "trim")):
        method = "curve_profile"
    elif any(term in text for term in ("array", "repeat", "modular", "bevel", "mirror", "panel")):
        method = "modifier_stack"
    elif any(term in text for term in ("cloth", "fabric", "panel", "seam", "pin")):
        method = "cloth_pattern"
    elif any(term in text for term in ("sculpt", "organic", "smooth", "mask")):
        method = "sculpt_shape_key"
    else:
        method = "mesh_schema" if constraints.get("exact_geometry") else "modifier_stack"
    return {"status": "success", "method": method, "method_order": list(METHOD_ORDER), "warnings": []}


def plan_profile_workflow(kind: str, points: list[list[float]], **kwargs: Any) -> dict[str, Any]:
    if len(points) < 2:
        return {"status": "error", "message": "profile requires at least two points"}
    return {"status": "success", "kind": kind, "point_count": len(points), "steps": ["validate_profile", f"{kind}_profile", "verify_geometry"], "parameters": kwargs}


def plan_modifier_stack(modifiers: list[dict[str, Any]]) -> dict[str, Any]:
    allowed = {"BEVEL", "ARRAY", "MIRROR", "SOLIDIFY", "WEIGHTED_NORMAL", "BOOLEAN", "SHRINKWRAP", "SIMPLE_DEFORM", "CURVE", "SKIN", "WIREFRAME", "LATTICE", "DISPLACE", "SCREW"}
    invalid = [item.get("type") for item in modifiers if str(item.get("type", "")).upper() not in allowed]
    return {"status": "error" if invalid else "success", "invalid_types": invalid, "allowed_types": sorted(allowed), "modifier_count": len(modifiers)}


def plan_reference_construction(reference_set_id: str | None, target_description: str, measurement_ids: list[str] | None = None) -> dict[str, Any]:
    warnings = []
    if not reference_set_id:
        warnings.append("reference-set-not-provided")
    return {
        "status": "planned",
        "reference_set_id": reference_set_id,
        "target_description": target_description,
        "measurement_ids": measurement_ids or [],
        "steps": ["verify_reference_calibration", "create_guides", "construct_primary_forms", "validate_alignment"],
        "warnings": warnings,
    }
