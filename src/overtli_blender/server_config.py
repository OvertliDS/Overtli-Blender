from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
DEFAULT_TIMEOUT_SECONDS = 15.0
ENV_HOST = "BLENDER_HOST"
ENV_PORT = "BLENDER_PORT"


@dataclass(frozen=True)
class BlenderServerConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


def get_default_config() -> BlenderServerConfig:
    host = os.getenv(ENV_HOST, DEFAULT_HOST)
    port = int(os.getenv(ENV_PORT, DEFAULT_PORT))
    return BlenderServerConfig(host=host, port=port, timeout_seconds=DEFAULT_TIMEOUT_SECONDS)

