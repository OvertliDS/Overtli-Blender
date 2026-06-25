"""Pure keyframe and F-curve planning helpers for Phase 9A."""

from __future__ import annotations

from typing import Any


ALLOWED_INTERPOLATIONS = {"CONSTANT", "LINEAR", "BEZIER", "SINE", "QUAD", "CUBIC", "QUART", "QUINT", "EXPO", "CIRC", "BACK", "BOUNCE", "ELASTIC"}
ALLOWED_EASING = {None, "AUTO", "EASE_IN", "EASE_OUT", "EASE_IN_OUT"}
ALLOWED_KEYFRAME_PATHS = {"location", "rotation_euler", "rotation_quaternion", "scale"}
ALLOWED_FCURVE_MODIFIERS = {"CYCLES", "NOISE", "LIMITS", "STEPPED"}
MAX_KEYFRAMES_PER_BATCH = 512
MIN_FRAME = -1048574
MAX_FRAME = 1048574


def normalize_interpolation(interpolation: str | None = None, easing: str | None = None) -> dict[str, Any]:
    interp = (interpolation or "BEZIER").upper()
    ease = easing.upper() if isinstance(easing, str) else easing
    if interp not in ALLOWED_INTERPOLATIONS:
        raise ValueError(f"Unsupported interpolation: {interpolation}")
    if ease not in ALLOWED_EASING:
        raise ValueError(f"Unsupported easing: {easing}")
    return {"interpolation": interp, "easing": ease}


def validate_frame_range(frame_start: int | float, frame_end: int | float, *, max_span: int = 10000) -> dict[str, Any]:
    start = float(frame_start)
    end = float(frame_end)
    if start < MIN_FRAME or end > MAX_FRAME:
        raise ValueError("Frame range exceeds Blender animation bounds")
    if end < start:
        raise ValueError("frame_end must be greater than or equal to frame_start")
    if end - start > max_span:
        raise ValueError(f"Frame range exceeds max span {max_span}")
    return {"frame_start": start, "frame_end": end, "frame_count": int(end - start + 1)}


def validate_keyframe_batch(keyframes: list[dict[str, Any]], *, allowed_paths: set[str] | None = None, max_keyframes: int = MAX_KEYFRAMES_PER_BATCH) -> dict[str, Any]:
    if not keyframes:
        raise ValueError("At least one keyframe is required")
    if len(keyframes) > max_keyframes:
        raise ValueError(f"Too many keyframes: {len(keyframes)} > {max_keyframes}")
    paths = allowed_paths or ALLOWED_KEYFRAME_PATHS
    frames: list[float] = []
    data_paths: set[str] = set()
    for item in keyframes:
        frame = float(item.get("frame"))
        data_path = str(item.get("data_path") or "")
        if frame < MIN_FRAME or frame > MAX_FRAME:
            raise ValueError(f"Frame outside supported range: {frame}")
        base_path = data_path.split("[", 1)[0]
        if base_path not in paths and not base_path.startswith('key_blocks["'):
            raise ValueError(f"Unsupported keyframe data_path: {data_path}")
        normalize_interpolation(item.get("interpolation"), item.get("easing"))
        frames.append(frame)
        data_paths.add(data_path)
    return {"count": len(keyframes), "frame_range": [min(frames), max(frames)], "data_paths": sorted(data_paths)}


def build_retime_plan(frame_start: float, frame_end: float, new_start: float, new_end: float) -> dict[str, Any]:
    validate_frame_range(frame_start, frame_end)
    validate_frame_range(new_start, new_end)
    source_span = float(frame_end) - float(frame_start)
    target_span = float(new_end) - float(new_start)
    scale = 1.0 if source_span == 0 else target_span / source_span
    return {"source_range": [frame_start, frame_end], "target_range": [new_start, new_end], "scale": scale}


def build_fcurve_modifier_plan(modifier_type: str, settings: dict[str, Any] | None = None) -> dict[str, Any]:
    mod_type = modifier_type.upper()
    if mod_type not in ALLOWED_FCURVE_MODIFIERS:
        raise ValueError(f"Unsupported F-curve modifier: {modifier_type}")
    return {"modifier_type": mod_type, "settings": dict(settings or {})}


def summarize_motion_path(points: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    points = points or []
    frames = [float(item["frame"]) for item in points if "frame" in item]
    return {"point_count": len(points), "frame_range": [min(frames), max(frames)] if frames else None}
