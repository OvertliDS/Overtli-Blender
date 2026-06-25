"""Stdlib-safe planning helpers for texture baking."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .bake_manifest import BakeClassification
from .image_resources import color_space_intent_for_pass, safe_image_filename


NATIVE_PASSES = {"COMBINED", "DIFFUSE", "GLOSSY", "TRANSMISSION", "EMIT", "AO", "SHADOW", "NORMAL", "UV", "ROUGHNESS"}
DERIVED_PASSES = {"METALLIC", "ALPHA", "HEIGHT", "OBJECT_ID", "MATERIAL_ID", "BASE_COLOR", "ALBEDO"}
APPROXIMATED_PASSES = {"CURVATURE", "THICKNESS"}


def normalize_bake_pass_name(pass_name: str) -> str:
    value = str(pass_name or "").strip().replace("-", "_").replace(" ", "_").upper()
    aliases = {"AMBIENT_OCCLUSION": "AO", "COLOR": "DIFFUSE", "BASECOLOR": "BASE_COLOR", "BASE_COLOUR": "BASE_COLOR"}
    return aliases.get(value, value)


def classify_bake_pass(pass_name: str) -> BakeClassification:
    normalized = normalize_bake_pass_name(pass_name)
    if normalized in NATIVE_PASSES:
        return BakeClassification.NATIVE
    if normalized in DERIVED_PASSES:
        return BakeClassification.DERIVED
    if normalized in APPROXIMATED_PASSES:
        return BakeClassification.APPROXIMATED
    return BakeClassification.UNSUPPORTED


def normalize_resolution(resolution: int | list[int] | tuple[int, int]) -> tuple[int, int]:
    if isinstance(resolution, int):
        width = height = resolution
    else:
        values = list(resolution)
        if len(values) != 2:
            raise ValueError("resolution must be an int or two-item list")
        width, height = int(values[0]), int(values[1])
    if width < 4 or height < 4 or width > 10000 or height > 10000:
        raise ValueError("resolution must be between 4 and 10000 pixels per side")
    return width, height


def estimate_bake_cost(passes: list[str], resolution: int | list[int] | tuple[int, int] = 1024, object_count: int = 1) -> dict[str, Any]:
    width, height = normalize_resolution(resolution)
    pass_count = max(1, len(passes or []))
    pixels = width * height * pass_count * max(1, int(object_count))
    bytes_estimate = pixels * 4 * 4
    return {
        "status": "success",
        "resolution": [width, height],
        "pass_count": pass_count,
        "object_count": max(1, int(object_count)),
        "pixels": pixels,
        "estimated_bytes": bytes_estimate,
        "estimated_disk_bytes": max(1024, bytes_estimate // 4),
        "time_category": "small" if pixels <= 512 * 512 * 2 else ("medium" if pixels <= 2048 * 2048 * 4 else "large"),
        "memory_category": "small" if bytes_estimate < 64 * 1024 * 1024 else ("medium" if bytes_estimate < 512 * 1024 * 1024 else "large"),
        "risk_flags": ["large-texture-memory"] if bytes_estimate >= 512 * 1024 * 1024 else [],
    }


def plan_bake_outputs(
    target_object_names: list[str],
    passes: list[str],
    resolution: int | list[int] | tuple[int, int] = 1024,
    output_dir: str | None = None,
    prefix: str | None = None,
    image_format: str = "PNG",
) -> list[dict[str, Any]]:
    width, height = normalize_resolution(resolution)
    root = Path(output_dir or "textures/baked")
    outputs = []
    for obj in target_object_names or []:
        for bake_pass in passes or []:
            normalized = normalize_bake_pass_name(bake_pass)
            filename = safe_image_filename(prefix or obj, normalized, image_format)
            outputs.append({
                "object_name": obj,
                "pass_name": normalized,
                "classification": classify_bake_pass(normalized).value,
                "resolution": [width, height],
                "color_space_intent": color_space_intent_for_pass(normalized),
                "file_path": str(root / filename),
                "image_format": image_format.upper(),
            })
    return outputs


def validate_output_conflicts(outputs: list[dict[str, Any]], overwrite: bool = False) -> dict[str, Any]:
    collisions = [item["file_path"] for item in outputs if Path(item["file_path"]).exists()]
    return {
        "status": "success" if overwrite or not collisions else "requires_approval",
        "valid": overwrite or not collisions,
        "collisions": collisions,
        "requires_approval": bool(collisions and not overwrite),
    }
