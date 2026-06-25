"""Construction manifest helpers for Phase 8B workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def new_workflow_id(prefix: str = "construct") -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class ConstructionManifest:
    workflow_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_objects: list[str] = field(default_factory=list)
    created_materials: list[str] = field(default_factory=list)
    created_modifiers: list[dict[str, Any]] = field(default_factory=list)
    reference_inputs: list[dict[str, Any]] = field(default_factory=list)
    measurement_checks: list[dict[str, Any]] = field(default_factory=list)
    approval_ids: list[str] = field(default_factory=list)
    verification_snapshots: list[dict[str, Any]] = field(default_factory=list)
    cleanup_targets: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def manifest_summary(manifest: ConstructionManifest | dict[str, Any]) -> dict[str, Any]:
    data = manifest.to_dict() if hasattr(manifest, "to_dict") else dict(manifest)
    return {
        "workflow_id": data.get("workflow_id"),
        "object_count": len(data.get("created_objects", [])),
        "material_count": len(data.get("created_materials", [])),
        "modifier_count": len(data.get("created_modifiers", [])),
        "cleanup_target_count": len(data.get("cleanup_targets", [])),
    }
