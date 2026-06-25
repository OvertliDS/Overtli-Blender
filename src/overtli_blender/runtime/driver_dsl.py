"""Allowlisted driver DSL used instead of arbitrary Python expressions."""

from __future__ import annotations

from typing import Any


ALLOWED_OPERATIONS = {"copy", "add", "subtract", "multiply", "divide", "clamp", "map_range", "min", "max", "abs", "negate"}
ALLOWED_TARGET_TYPES = {"OBJECT", "ARMATURE", "BONE", "MATERIAL", "SHAPE_KEY"}
ALLOWED_SOURCE_PATHS = {
    "location.x": ("location", 0),
    "location.y": ("location", 1),
    "location.z": ("location", 2),
    "rotation_euler.x": ("rotation_euler", 0),
    "rotation_euler.y": ("rotation_euler", 1),
    "rotation_euler.z": ("rotation_euler", 2),
    "scale.x": ("scale", 0),
    "scale.y": ("scale", 1),
    "scale.z": ("scale", 2),
}


def _source(dsl: dict[str, Any]) -> dict[str, Any]:
    source = dsl.get("source")
    if not isinstance(source, dict):
        raise ValueError("Driver DSL requires a source object")
    target_type = str(source.get("target_type", "OBJECT")).upper()
    target_name = str(source.get("target_name") or "")
    data_path = str(source.get("data_path") or "")
    if target_type not in ALLOWED_TARGET_TYPES:
        raise ValueError(f"Unsupported driver target_type: {target_type}")
    if not target_name:
        raise ValueError("Driver source target_name is required")
    if data_path not in ALLOWED_SOURCE_PATHS and not data_path.startswith('["'):
        raise ValueError(f"Unsupported driver source data_path: {data_path}")
    return {"target_type": target_type, "target_name": target_name, "data_path": data_path}


def validate_driver_dsl(dsl: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(dsl, dict):
        raise ValueError("Driver DSL must be an object")
    operation = str(dsl.get("operation") or "").lower()
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(f"Unsupported driver DSL operation: {operation}")
    source = _source(dsl)
    if operation == "map_range":
        for key in ("from_min", "from_max", "to_min", "to_max"):
            if key not in dsl:
                raise ValueError(f"map_range requires {key}")
            float(dsl[key])
        if float(dsl["from_min"]) == float(dsl["from_max"]):
            raise ValueError("map_range source range cannot be zero")
    for key in ("value", "min", "max", "operand"):
        if key in dsl and dsl[key] is not None:
            float(dsl[key])
    return {"status": "success", "operation": operation, "source": source, "dsl_only": True}


def compile_driver_expression(dsl: dict[str, Any]) -> dict[str, Any]:
    validated = validate_driver_dsl(dsl)
    op = validated["operation"]
    expr = "var"
    if op == "add":
        expr = f"(var + {float(dsl.get('value', dsl.get('operand', 0.0)))})"
    elif op == "subtract":
        expr = f"(var - {float(dsl.get('value', dsl.get('operand', 0.0)))})"
    elif op == "multiply":
        expr = f"(var * {float(dsl.get('value', dsl.get('operand', 1.0)))})"
    elif op == "divide":
        divisor = float(dsl.get("value", dsl.get("operand", 1.0)))
        if divisor == 0:
            raise ValueError("divide operand cannot be zero")
        expr = f"(var / {divisor})"
    elif op == "clamp":
        expr = f"min(max(var, {float(dsl.get('min', 0.0))}), {float(dsl.get('max', 1.0))})"
    elif op == "map_range":
        fmin, fmax = float(dsl["from_min"]), float(dsl["from_max"])
        tmin, tmax = float(dsl["to_min"]), float(dsl["to_max"])
        expr = f"(({tmin}) + ((var - ({fmin})) * (({tmax}) - ({tmin})) / (({fmax}) - ({fmin}))))"
        if bool(dsl.get("clamp", False)):
            lo, hi = sorted((tmin, tmax))
            expr = f"min(max({expr}, {lo}), {hi})"
    elif op == "min":
        expr = f"min(var, {float(dsl.get('value', dsl.get('operand', 0.0)))})"
    elif op == "max":
        expr = f"max(var, {float(dsl.get('value', dsl.get('operand', 0.0)))})"
    elif op == "abs":
        expr = "abs(var)"
    elif op == "negate":
        expr = "(-var)"
    return {"expression": expr, "variables": [{"name": "var", **validated["source"]}], "operation": op}
