from __future__ import annotations

from enum import Enum


class OperationType(str, Enum):
    OBSERVE = "OBSERVE"
    PLAN = "PLAN"
    SELECT_REGION = "SELECT_REGION"
    CREATE = "CREATE"
    EDIT = "EDIT"
    DEFORM = "DEFORM"
    SCULPT = "SCULPT"
    MATERIAL = "MATERIAL"
    SHADER = "SHADER"
    TEXTURE = "TEXTURE"
    MODIFIER = "MODIFIER"
    GEOMETRY_NODES = "GEOMETRY_NODES"
    ANIMATE = "ANIMATE"
    RIG = "RIG"
    CAMERA = "CAMERA"
    LIGHTING = "LIGHTING"
    RENDER = "RENDER"
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    ASSET_LIBRARY = "ASSET_LIBRARY"
    INSTALL_ADDON = "INSTALL_ADDON"
    UPDATE_KNOWLEDGE = "UPDATE_KNOWLEDGE"
    VERIFY = "VERIFY"
    ROLLBACK = "ROLLBACK"
    CLEANUP = "CLEANUP"


def operation_type_values() -> list[str]:
    return [operation_type.value for operation_type in OperationType]

