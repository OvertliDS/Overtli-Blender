"""Capability-based runtime permission policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .command_registry import get_command_spec


CAPABILITIES = {
    "scene.read",
    "scene.write",
    "scene.destructive",
    "filesystem.project.read",
    "filesystem.project.write",
    "filesystem.external.read",
    "filesystem.external.write",
    "filesystem.delete",
    "network.providers",
    "addon.inspect",
    "addon.manage",
    "raw_python",
    "external_process",
    "knowledge.read",
    "knowledge.write",
    "release.export",
}

PROFILE_CAPABILITIES = {
    "read_only": {"scene.read", "filesystem.project.read", "addon.inspect", "knowledge.read"},
    "standard": {"scene.read", "scene.write", "filesystem.project.read", "filesystem.project.write", "addon.inspect", "knowledge.read", "knowledge.write"},
    "trusted_project": {"scene.read", "scene.write", "filesystem.project.read", "filesystem.project.write", "scene.destructive", "addon.inspect", "knowledge.read", "knowledge.write", "release.export"},
    "developer": set(CAPABILITIES),
    "custom": {"scene.read"},
}


@dataclass
class CapabilityPolicy:
    profile: str = "standard"

    def allowed(self) -> set[str]:
        return set(PROFILE_CAPABILITIES.get(self.profile, PROFILE_CAPABILITIES["standard"]))


DEFAULT_CAPABILITY_POLICY = CapabilityPolicy()


def get_permission_profile() -> dict[str, Any]:
    return {"status": "success", "profile": DEFAULT_CAPABILITY_POLICY.profile, "capabilities": sorted(DEFAULT_CAPABILITY_POLICY.allowed())}


def set_permission_profile(profile: str, confirm: bool = False) -> dict[str, Any]:
    if profile not in PROFILE_CAPABILITIES:
        return {"status": "error", "message": f"Unknown permission profile: {profile}"}
    current = DEFAULT_CAPABILITY_POLICY.allowed()
    requested = PROFILE_CAPABILITIES[profile]
    expands = bool(requested - current)
    if expands and not confirm:
        return {"status": "requires_approval", "message": "Expanding permissions requires confirmation.", "requested_profile": profile}
    DEFAULT_CAPABILITY_POLICY.profile = profile
    return get_permission_profile()


def get_capability_policy() -> dict[str, Any]:
    return {
        "status": "success",
        "capabilities": sorted(CAPABILITIES),
        "profiles": {name: sorted(values) for name, values in PROFILE_CAPABILITIES.items()},
        "active_profile": DEFAULT_CAPABILITY_POLICY.profile,
    }


def validate_command_capabilities(command_name: str, profile: str | None = None) -> dict[str, Any]:
    spec = get_command_spec(command_name)
    if not spec:
        return {"status": "error", "message": f"Unknown command: {command_name}"}
    profile_name = profile or DEFAULT_CAPABILITY_POLICY.profile
    allowed = PROFILE_CAPABILITIES.get(profile_name)
    if allowed is None:
        return {"status": "error", "message": f"Unknown permission profile: {profile_name}"}
    required = set(spec.allowed_capabilities)
    missing = sorted(required - allowed)
    return {
        "status": "success" if not missing else "error",
        "command_name": command_name,
        "profile": profile_name,
        "allowed": not missing,
        "required_capabilities": sorted(required),
        "missing_capabilities": missing,
    }
