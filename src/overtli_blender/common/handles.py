from __future__ import annotations

from enum import Enum


class HandleType(str, Enum):
    OBJECT = "OBJECT"
    MATERIAL = "MATERIAL"
    COLLECTION = "COLLECTION"
    IMAGE = "IMAGE"
    TEXTURE = "TEXTURE"
    NODE_GROUP = "NODE_GROUP"
    SCRIPT = "SCRIPT"
    OPERATION = "OPERATION"
    REGION = "REGION"
    ASSET = "ASSET"


def make_handle(handle_type: HandleType, name: str) -> str:
    if not name or not name.strip():
        raise ValueError("Handle name must not be empty")
    return f"{handle_type.value.lower()}:{name}"


def split_handle(handle: str) -> tuple[str, str]:
    if not handle or not handle.strip():
        raise ValueError("Handle must not be empty")
    if ":" not in handle:
        raise ValueError("Handle must contain a type prefix and name")
    handle_type, name = handle.split(":", 1)
    if not handle_type or not name:
        raise ValueError("Handle must contain both a type prefix and name")
    return handle_type, name

