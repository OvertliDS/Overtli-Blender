"""Phase 9B runtime preference schema and validation helpers."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


PERMISSION_PROFILES = {"read_only", "browser_standard", "remote_browser_safe", "standard", "trusted_project", "developer", "custom"}
APPROVAL_MODES = {"always_ask", "ask_for_medium_high", "ask_for_high_destructive", "ask_for_destructive_only", "full_access_developer", "read_only"}
SENSITIVE_KEY_FRAGMENTS = ("api" + "_key", "api" + "key", "tok" + "en", "sec" + "ret", "pass" + "word", "cred" + "ential")


@dataclass
class ProjectPreferenceSection:
    project_specific: bool = True
    auto_initialize_workspace: bool = False
    require_saved_blend_for_writes: bool = True


@dataclass
class FileSystemPreferenceSection:
    approved_roots: list[str] = field(default_factory=list)
    approved_addon_source_roots: list[str] = field(default_factory=list)
    permission_profile: str = "standard"
    allow_external_reads: bool = False
    allow_external_writes: bool = False


@dataclass
class SecurityPreferenceSection:
    strict_mode: bool = False
    raw_python_enabled: bool = False
    addon_interop_enabled: bool = False
    require_approval_for_permission_expansion: bool = True
    default_local_tool_profile: str = "full_standard"
    default_local_permission_profile: str = "standard"
    default_local_approval_mode: str = "ask_for_high_destructive"
    default_browser_tool_profile: str = "browser_full_standard"
    default_browser_permission_profile: str = "browser_standard"
    default_browser_approval_mode: str = "ask_for_destructive_only"
    approval_timeout_seconds: int = 900
    require_approval_for_external_writes: bool = True
    require_approval_for_file_delete: bool = True
    require_approval_for_raw_python: bool = True
    require_approval_for_provider_downloads: bool = True
    require_approval_for_addon_lifecycle: bool = True
    browser_connector_write_policy: str = "safe_structured_writes_enabled"


@dataclass
class ArtifactPreferenceSection:
    cache_policy: str = "project_scoped"
    log_retention_days: int = 14
    operation_timeout_seconds: int = 120


@dataclass
class McpPreferenceSection:
    host: str = "localhost"
    port: int = 9876
    max_response_items: int = 200


@dataclass
class KnowledgePreferenceSection:
    knowledge_roots: list[str] = field(default_factory=list)
    docs_index_enabled: bool = True


@dataclass
class ToolProfilePreferenceSection:
    active_profile: str = "full_standard"
    enabled_tool_packs: list[str] = field(default_factory=list)
    active_skill_packs: list[str] = field(default_factory=list)
    max_visible_tools: int = 80


@dataclass
class ProviderPreferenceSection:
    network_providers_enabled: bool = False
    provider_downloads_enabled: bool = False


@dataclass
class DiagnosticsPreferenceSection:
    log_level: str = "INFO"
    diagnostics_enabled: bool = True
    support_bundle_redaction: bool = True


@dataclass
class OvertliPreferenceManifest:
    schema_version: int = 1
    project: ProjectPreferenceSection = field(default_factory=ProjectPreferenceSection)
    filesystem: FileSystemPreferenceSection = field(default_factory=FileSystemPreferenceSection)
    security: SecurityPreferenceSection = field(default_factory=SecurityPreferenceSection)
    artifacts: ArtifactPreferenceSection = field(default_factory=ArtifactPreferenceSection)
    mcp: McpPreferenceSection = field(default_factory=McpPreferenceSection)
    knowledge: KnowledgePreferenceSection = field(default_factory=KnowledgePreferenceSection)
    tool_profiles: ToolProfilePreferenceSection = field(default_factory=ToolProfilePreferenceSection)
    providers: ProviderPreferenceSection = field(default_factory=ProviderPreferenceSection)
    diagnostics: DiagnosticsPreferenceSection = field(default_factory=DiagnosticsPreferenceSection)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_preferences() -> dict[str, Any]:
    return OvertliPreferenceManifest().to_dict()


def preferences_schema() -> dict[str, Any]:
    return {
        "status": "success",
        "schema_version": 1,
        "sections": {
            "Project": sorted(ProjectPreferenceSection().__dict__),
            "Filesystem": sorted(FileSystemPreferenceSection().__dict__),
            "Security": sorted(SecurityPreferenceSection().__dict__),
            "Artifacts": sorted(ArtifactPreferenceSection().__dict__),
            "MCP": sorted(McpPreferenceSection().__dict__),
            "Knowledge": sorted(KnowledgePreferenceSection().__dict__),
            "Tool Profiles": sorted(ToolProfilePreferenceSection().__dict__),
            "Providers": sorted(ProviderPreferenceSection().__dict__),
            "Diagnostics": sorted(DiagnosticsPreferenceSection().__dict__),
        },
    }


def config_path(repo_root: str | os.PathLike[str] | None = None, project_root: str | os.PathLike[str] | None = None) -> Path:
    if project_root:
        return Path(project_root) / ".overtli" / "config.json"
    base = Path(repo_root or os.getcwd())
    return base / ".overtli_blender" / "config" / "runtime_preferences.json"


def load_preferences(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    target = Path(path) if path else config_path()
    if not target.exists():
        return default_preferences()
    data = json.loads(target.read_text(encoding="utf-8"))
    merged = default_preferences()
    deep_update(merged, data)
    return merged


def save_preferences(preferences: dict[str, Any], path: str | os.PathLike[str] | None = None) -> Path:
    target = Path(path) if path else config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(redact_sensitive_values(preferences), indent=2, sort_keys=True), encoding="utf-8")
    return target


def deep_update(target: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_update(target[key], value)
        else:
            target[key] = value
    return target


def redact_sensitive_values(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if any(marker in str(key).lower() for marker in SENSITIVE_KEY_FRAGMENTS):
                result[key] = "<redacted>"
            else:
                result[key] = redact_sensitive_values(item)
        return result
    if isinstance(value, list):
        return [redact_sensitive_values(item) for item in value]
    return value


def _path_errors(paths: list[str], label: str) -> list[str]:
    errors = []
    for raw in paths:
        if not raw or not isinstance(raw, str):
            errors.append(f"{label} contains a non-string path")
            continue
        expanded = Path(os.path.expandvars(os.path.expanduser(raw)))
        if not expanded.exists():
            errors.append(f"{label} path does not exist: {raw}")
    return errors


def validate_preferences(preferences: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    fs = preferences.get("filesystem", {})
    security = preferences.get("security", {})
    artifacts = preferences.get("artifacts", {})
    tools = preferences.get("tool_profiles", {})
    providers = preferences.get("providers", {})

    profile = fs.get("permission_profile", "standard")
    if profile not in PERMISSION_PROFILES:
        errors.append(f"Unknown permission profile: {profile}")
    if security.get("raw_python_enabled"):
        warnings.append("Raw Python is enabled and should remain approval-gated.")
    for key in ("default_local_approval_mode", "default_browser_approval_mode"):
        if security.get(key, "") not in APPROVAL_MODES:
            errors.append(f"Unknown approval mode: {security.get(key)}")
    if int(security.get("approval_timeout_seconds", 0)) <= 0:
        errors.append("Approval timeout must be greater than zero.")
    if providers.get("provider_downloads_enabled") and not providers.get("network_providers_enabled"):
        errors.append("Provider downloads require network providers to be enabled.")
    if int(artifacts.get("operation_timeout_seconds", 0)) <= 0:
        errors.append("Operation timeout must be greater than zero.")
    if int(artifacts.get("log_retention_days", 0)) < 0:
        errors.append("Log retention days cannot be negative.")
    if int(tools.get("max_visible_tools", 0)) <= 0:
        errors.append("Max visible tools must be greater than zero.")
    errors.extend(_path_errors(fs.get("approved_roots", []), "approved_roots"))
    errors.extend(_path_errors(fs.get("approved_addon_source_roots", []), "approved_addon_source_roots"))
    errors.extend(_path_errors(preferences.get("knowledge", {}).get("knowledge_roots", []), "knowledge_roots"))
    if json.dumps(preferences).lower().find("sk-") >= 0:
        errors.append("Potential sensitive value found in preferences.")
    return {"status": "success" if not errors else "error", "valid": not errors, "errors": errors, "warnings": warnings}


def permission_expands(current: dict[str, Any], requested: dict[str, Any]) -> bool:
    current_fs = current.get("filesystem", {})
    requested_fs = requested.get("filesystem", {})
    if set(requested_fs.get("approved_roots", [])) - set(current_fs.get("approved_roots", [])):
        return True
    if set(requested_fs.get("approved_addon_source_roots", [])) - set(current_fs.get("approved_addon_source_roots", [])):
        return True
    rank = {"read_only": 0, "browser_standard": 1, "remote_browser_safe": 1, "standard": 1, "trusted_project": 2, "developer": 3, "custom": 1}
    if rank.get(requested_fs.get("permission_profile", current_fs.get("permission_profile", "standard")), 1) > rank.get(current_fs.get("permission_profile", "standard"), 1):
        return True
    approval_rank = {
        "read_only": 0,
        "always_ask": 1,
        "ask_for_medium_high": 2,
        "ask_for_high_destructive": 3,
        "ask_for_destructive_only": 4,
        "full_access_developer": 5,
    }
    current_mode = current.get("security", {}).get("default_local_approval_mode", "ask_for_high_destructive")
    requested_mode = requested.get("security", {}).get("default_local_approval_mode", current_mode)
    if approval_rank.get(requested_mode, 0) > approval_rank.get(current_mode, 0):
        return True
    for section, key in [("security", "raw_python_enabled"), ("security", "addon_interop_enabled"), ("providers", "network_providers_enabled"), ("providers", "provider_downloads_enabled")]:
        if requested.get(section, {}).get(key) and not current.get(section, {}).get(key):
            return True
    return False
