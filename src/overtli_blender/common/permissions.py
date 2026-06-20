from __future__ import annotations

from enum import Enum


class PermissionMode(str, Enum):
    SAFE = "SAFE"
    ARTIST = "ARTIST"
    TECHNICAL_DIRECTOR = "TECHNICAL_DIRECTOR"
    RAW_PYTHON = "RAW_PYTHON"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    DESTRUCTIVE = "DESTRUCTIVE"


class Reversibility(str, Enum):
    REVERSIBLE = "REVERSIBLE"
    PARTIAL = "PARTIAL"
    IRREVERSIBLE = "IRREVERSIBLE"
    UNKNOWN = "UNKNOWN"

