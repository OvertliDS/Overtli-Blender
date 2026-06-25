"""Pure mesh schema validation helpers for advanced modeling workflows."""

from __future__ import annotations

from collections import Counter
from math import isfinite
from typing import Any


def _point3(value: Any) -> tuple[float, float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    try:
        point = tuple(float(axis) for axis in value)
    except (TypeError, ValueError):
        return None
    return point if all(isfinite(axis) for axis in point) else None


def estimate_mesh_memory(vertex_count: int, edge_count: int, face_count: int) -> int:
    return vertex_count * 32 + edge_count * 16 + face_count * 48


def validate_mesh_schema(schema: dict[str, Any], max_vertices: int = 10000, max_faces: int = 20000, check_non_manifold: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(schema, dict):
        return {"status": "error", "valid": False, "errors": ["schema-must-be-dict"], "warnings": warnings}

    raw_vertices = schema.get("vertices", [])
    raw_edges = schema.get("edges", [])
    raw_faces = schema.get("faces", [])
    if not isinstance(raw_vertices, list) or not isinstance(raw_edges, list) or not isinstance(raw_faces, list):
        errors.append("vertices-edges-faces-must-be-lists")
        raw_vertices, raw_edges, raw_faces = [], [], []

    vertices: list[tuple[float, float, float]] = []
    for index, value in enumerate(raw_vertices):
        point = _point3(value)
        if point is None:
            errors.append(f"invalid-vertex-{index}")
        else:
            vertices.append(point)

    if len(vertices) > max_vertices:
        errors.append(f"vertex-count-exceeds-limit:{len(vertices)}>{max_vertices}")
    if len(raw_faces) > max_faces:
        errors.append(f"face-count-exceeds-limit:{len(raw_faces)}>{max_faces}")
    if len(vertices) < 3 and raw_faces:
        errors.append("faces-require-at-least-three-vertices")

    duplicate_vertices = [point for point, count in Counter(vertices).items() if count > 1]
    if duplicate_vertices:
        warnings.append(f"duplicate-vertices:{len(duplicate_vertices)}")

    edge_keys: list[tuple[int, int]] = []
    for index, edge in enumerate(raw_edges):
        if not isinstance(edge, (list, tuple)) or len(edge) != 2 or not all(isinstance(item, int) for item in edge):
            errors.append(f"invalid-edge-{index}")
            continue
        a, b = edge
        if a == b:
            errors.append(f"degenerate-edge-{index}")
        if a < 0 or b < 0 or a >= len(vertices) or b >= len(vertices):
            errors.append(f"edge-index-out-of-range-{index}")
        edge_keys.append(tuple(sorted((a, b))))

    face_edge_counts: Counter[tuple[int, int]] = Counter()
    for index, face in enumerate(raw_faces):
        if not isinstance(face, (list, tuple)) or len(face) < 3 or not all(isinstance(item, int) for item in face):
            errors.append(f"invalid-face-{index}")
            continue
        if len(set(face)) != len(face):
            errors.append(f"degenerate-face-{index}")
        if any(item < 0 or item >= len(vertices) for item in face):
            errors.append(f"face-index-out-of-range-{index}")
            continue
        for a, b in zip(face, list(face[1:]) + [face[0]]):
            face_edge_counts[tuple(sorted((a, b)))] += 1

    if check_non_manifold:
        boundary_edges = [edge for edge, count in face_edge_counts.items() if count == 1]
        overused_edges = [edge for edge, count in face_edge_counts.items() if count > 2]
        if boundary_edges:
            warnings.append(f"boundary-edge-risk:{len(boundary_edges)}")
        if overused_edges:
            warnings.append(f"non-manifold-edge-risk:{len(overused_edges)}")

    bounds = None
    if vertices:
        bounds = {
            "min": [min(point[axis] for point in vertices) for axis in range(3)],
            "max": [max(point[axis] for point in vertices) for axis in range(3)],
        }

    return {
        "status": "success" if not errors else "error",
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "vertices": len(vertices),
            "edges": len(raw_edges),
            "faces": len(raw_faces),
            "estimated_memory_bytes": estimate_mesh_memory(len(vertices), len(raw_edges), len(raw_faces)),
            "bounds": bounds,
        },
    }
