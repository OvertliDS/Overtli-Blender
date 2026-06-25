"""Manifest models for texture baking workflows."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class BakeClassification(str, Enum):
    NATIVE = "native"
    DERIVED = "derived"
    APPROXIMATED = "approximated"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class BakeValidationIssue:
    code: str
    message: str
    severity: str = "warning"
    target: str | None = None


@dataclass(frozen=True)
class BakeTargetImage:
    image_name: str
    pass_name: str
    resolution: tuple[int, int]
    color_space_intent: str
    file_path: str
    image_format: str = "PNG"
    node_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class BakeOutput:
    pass_name: str
    output_type: str
    classification: BakeClassification
    method: str
    source_objects: tuple[str, ...]
    target_object: str | None
    uv_layer: str | None
    resolution: tuple[int, int]
    color_space_intent: str
    file_path: str
    file_hash: str | None = None
    validation_status: str = "unverified"
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BakePassManifest:
    pass_name: str
    classification: BakeClassification
    method: str
    targets: tuple[BakeTargetImage, ...] = ()
    outputs: tuple[BakeOutput, ...] = ()
    issues: tuple[BakeValidationIssue, ...] = ()


@dataclass(frozen=True)
class BakeWorkflowManifest:
    workflow_id: str
    workflow_name: str | None
    source_objects: tuple[str, ...] = ()
    target_objects: tuple[str, ...] = ()
    passes: tuple[BakePassManifest, ...] = ()
    outputs: tuple[BakeOutput, ...] = ()
    temporary_nodes: tuple[dict[str, Any], ...] = ()
    temporary_images: tuple[str, ...] = ()
    cleanup_plan_id: str | None = None
    status: str = "planned"
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for bake_pass in data["passes"]:
            bake_pass["classification"] = bake_pass["classification"].value
            for output in bake_pass["outputs"]:
                output["classification"] = output["classification"].value
        for output in data["outputs"]:
            output["classification"] = output["classification"].value
        return data


def manifest_to_json(manifest: BakeWorkflowManifest) -> str:
    return json.dumps(manifest.to_dict(), indent=2, sort_keys=True)


def write_manifest(path: str | Path, manifest: BakeWorkflowManifest) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(manifest_to_json(manifest), encoding="utf-8")
    return target
