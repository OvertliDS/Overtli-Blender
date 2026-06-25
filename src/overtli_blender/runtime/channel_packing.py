"""Channel packing planning and validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


PACKING_LAYOUTS = {
    "ORM": {"R": "AO", "G": "ROUGHNESS", "B": "METALLIC"},
    "RMA": {"R": "ROUGHNESS", "G": "METALLIC", "B": "AO"},
    "MRA": {"R": "METALLIC", "G": "ROUGHNESS", "B": "AO"},
    "GLTF_METALLIC_ROUGHNESS": {"G": "ROUGHNESS", "B": "METALLIC"},
}


def normalize_layout(layout: str) -> str:
    return str(layout or "ORM").strip().upper()


def get_channel_layout(layout: str, custom_layout: dict[str, str] | None = None) -> dict[str, str]:
    normalized = normalize_layout(layout)
    if normalized == "CUSTOM":
        if not custom_layout:
            raise ValueError("CUSTOM layout requires custom_layout")
        return {str(k).upper(): str(v).upper() for k, v in custom_layout.items()}
    if normalized not in PACKING_LAYOUTS:
        raise ValueError(f"Unsupported channel packing layout: {layout}")
    return dict(PACKING_LAYOUTS[normalized])


def plan_channel_pack(source_images: dict[str, str], layout: str = "ORM", output_path: str | None = None, custom_layout: dict[str, str] | None = None) -> dict[str, Any]:
    mapping = get_channel_layout(layout, custom_layout)
    missing_sources = sorted({source for source in mapping.values() if source not in {k.upper(): v for k, v in source_images.items()}})
    return {
        "status": "success" if not missing_sources else "error",
        "layout": normalize_layout(layout),
        "channels": mapping,
        "source_images": source_images,
        "missing_sources": missing_sources,
        "output_path": output_path,
        "color_space_intent": "Non-Color",
        "classification": "derived",
    }


def validate_channel_pack_inputs(source_images: dict[str, str], layout: str = "ORM", overwrite: bool = False, output_path: str | None = None, custom_layout: dict[str, str] | None = None) -> dict[str, Any]:
    plan = plan_channel_pack(source_images, layout, output_path, custom_layout)
    missing_files = [path for path in source_images.values() if path and not Path(path).exists()]
    collision = bool(output_path and Path(output_path).exists() and not overwrite)
    return {
        **plan,
        "valid": plan["status"] == "success" and not missing_files and not collision,
        "missing_files": missing_files,
        "requires_approval": collision,
        "warnings": ["source-files-not-found"] if missing_files else [],
    }
