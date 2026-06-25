"""Image resource path, metadata, manifest, and hashing helpers."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {"PNG": ".png", "JPEG": ".jpg", "JPG": ".jpg", "TARGA": ".tga", "TIFF": ".tif", "OPEN_EXR": ".exr", "EXR": ".exr"}
DATA_PASSES = {"NORMAL", "AO", "ROUGHNESS", "METALLIC", "HEIGHT", "CURVATURE", "THICKNESS", "ORM", "RMA", "MRA", "GLTF_METALLIC_ROUGHNESS", "ALPHA", "OBJECT_ID", "MATERIAL_ID", "UV"}
COLOR_PASSES = {"DIFFUSE", "BASE_COLOR", "ALBEDO", "EMIT", "COMBINED"}


def resolve_texture_folder(project_root: str | Path, kind: str = "baked") -> Path:
    if kind not in {"source", "working", "baked", "packed"}:
        raise ValueError("texture folder kind must be source, working, baked, or packed")
    return Path(project_root).resolve() / "textures" / kind


def sanitize_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    return cleaned.strip("._") or "texture"


def safe_image_filename(prefix: str, pass_name: str, image_format: str = "PNG") -> str:
    ext = IMAGE_EXTENSIONS.get(str(image_format).upper(), f".{str(image_format).lower()}")
    return f"{sanitize_filename_part(prefix)}_{sanitize_filename_part(pass_name).lower()}{ext}"


def color_space_intent_for_pass(pass_name: str) -> str:
    normalized = str(pass_name or "").upper()
    if normalized in COLOR_PASSES:
        return "sRGB"
    if normalized in DATA_PASSES:
        return "Non-Color"
    return "Non-Color"


def file_sha256(path: str | Path) -> str | None:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return None
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_format_metadata(image_format: str = "PNG", color_depth: str | None = None) -> dict[str, Any]:
    fmt = str(image_format or "PNG").upper()
    return {"image_format": fmt, "extension": IMAGE_EXTENSIONS.get(fmt, f".{fmt.lower()}"), "color_depth": color_depth}


def write_image_manifest(path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return target
