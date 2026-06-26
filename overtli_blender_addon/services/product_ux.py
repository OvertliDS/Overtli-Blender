from __future__ import annotations

from ..core import *

class PreferencesConfigurationService:
    def __init__(self, server):
        self.server = server
        self.path = runtime_preferences_config_path(ADDON_ROOT)
        self.preferences = runtime_load_preferences(self.path)

    def get_preferences_schema(self):
        return runtime_preferences_schema()

    def get_runtime_preferences(self):
        return {"status": "success", "config_path": str(self.path), "preferences": runtime_redact_sensitive_values(self.preferences)}

    def validate_runtime_preferences(self):
        result = runtime_validate_preferences(self.preferences)
        result["config_path"] = str(self.path)
        return result

    def update_runtime_preferences(self, changes, confirm=False):
        requested = json.loads(json.dumps(self.preferences))
        runtime_preferences_deep_update(requested, changes or {})
        validation = runtime_validate_preferences(requested)
        if validation.get("status") != "success":
            return validation
        if runtime_permission_expands(self.preferences, requested) and not confirm:
            return {"status": "requires_approval", "approval_required": True, "message": "Preference change expands permissions and requires confirmation.", "validation": validation}
        self.preferences = requested
        path = runtime_save_preferences(self.preferences, self.path)
        return {"status": "success", "config_path": str(path), "preferences": runtime_redact_sensitive_values(self.preferences), "validation": validation}

    def reset_runtime_preferences(self, confirm=False, preview=True):
        defaults = runtime_default_preferences()
        if preview and not confirm:
            return {"status": "requires_approval", "approval_required": True, "message": "Reset preview generated. Confirm to write defaults.", "preview": runtime_redact_sensitive_values(defaults)}
        self.preferences = defaults
        path = runtime_save_preferences(self.preferences, self.path)
        return {"status": "success", "config_path": str(path), "preferences": runtime_redact_sensitive_values(self.preferences)}


class ToolProfileService:
    def __init__(self, server):
        self.server = server

    def get_tool_profiles(self):
        return runtime_list_tool_profiles()

    def get_active_tool_profile(self):
        prefs = self.server.preferences_configuration_service.preferences
        name = prefs.get("tool_profiles", {}).get("active_profile", "safe_scene")
        profile = runtime_get_tool_profile(name) or runtime_get_tool_profile("safe_scene")
        return {"status": "success", "profile": profile.to_dict()}

    def set_active_tool_profile(self, profile_name, confirm=False):
        prefs = self.server.preferences_configuration_service.preferences
        current = prefs.get("tool_profiles", {}).get("active_profile", "safe_scene")
        preview = runtime_preview_profile_change(current, profile_name)
        if preview.get("status") != "success":
            return preview
        if preview.get("requires_approval") and not confirm:
            return {"status": "requires_approval", "approval_required": True, "message": "Profile increases risk and requires confirmation.", "preview": preview}
        profile = runtime_get_tool_profile(profile_name)
        prefs.setdefault("tool_profiles", {})["active_profile"] = profile_name
        prefs["tool_profiles"]["enabled_tool_packs"] = list(profile.enabled_tool_packs)
        prefs.setdefault("filesystem", {})["permission_profile"] = profile.permission_profile
        runtime_save_preferences(prefs, self.server.preferences_configuration_service.path)
        return {"status": "success", "profile": profile.to_dict(), "enabled_tool_packs": list(profile.enabled_tool_packs)}

    def preview_tool_profile(self, profile_name):
        prefs = self.server.preferences_configuration_service.preferences
        return runtime_preview_profile_change(prefs.get("tool_profiles", {}).get("active_profile", "safe_scene"), profile_name)

    def get_visible_tool_budget(self):
        active = self.get_active_tool_profile()["profile"]
        registry = command_registry_report()
        return {"status": "success", "active_packs": active["enabled_tool_packs"], "estimated_visible_tool_count": min(active["max_visible_tools"], registry.get("command_count", 0)), "hidden_packs": sorted(set(registry.get("tool_packs", [])) - set(active["enabled_tool_packs"])), "high_risk_hidden_tools": active["hidden_risky_tools"], "recommended_compact_core": ["get_runtime_dashboard", "search_tools", "explain_error", "get_setup_status"]}

    def get_enabled_tool_packs(self):
        prefs = self.server.preferences_configuration_service.preferences
        enabled = prefs.get("tool_profiles", {}).get("enabled_tool_packs")
        if not enabled:
            enabled = self.get_active_tool_profile()["profile"]["enabled_tool_packs"]
        return {"status": "success", "enabled_tool_packs": enabled}

    def set_enabled_tool_packs(self, tool_packs, confirm=False):
        known = set(command_registry_report().get("tool_packs", []))
        unknown = sorted(set(tool_packs or []) - known)
        if unknown:
            return {"status": "error", "message": f"Unknown tool packs: {unknown}"}
        high_risk_packs = {"addon_interop", "drivers", "simulation_workflows"}
        if high_risk_packs.intersection(tool_packs or []) and not confirm:
            return {"status": "requires_approval", "approval_required": True, "message": "Enabling high-risk tool packs requires confirmation.", "high_risk_packs": sorted(high_risk_packs.intersection(tool_packs or []))}
        prefs = self.server.preferences_configuration_service.preferences
        prefs.setdefault("tool_profiles", {})["enabled_tool_packs"] = list(tool_packs or [])
        runtime_save_preferences(prefs, self.server.preferences_configuration_service.path)
        return {"status": "success", "enabled_tool_packs": prefs["tool_profiles"]["enabled_tool_packs"]}

    def recommend_tool_profile(self, task_description, current_context=None):
        return runtime_recommend_tool_profile(task_description, current_context)


class BundledSkillPackService:
    def __init__(self, server):
        self.server = server

    def list_bundled_skill_packs(self):
        return runtime_list_bundled_skill_packs()

    def get_bundled_skill_pack(self, skill_pack_id):
        return runtime_get_bundled_skill_pack(skill_pack_id)

    def search_bundled_skill_packs(self, query, top_k=10):
        return runtime_search_bundled_skill_packs(query, top_k)

    def activate_skill_pack(self, skill_pack_id, confirm=False):
        pack = RUNTIME_BUNDLED_SKILL_PACKS.get(skill_pack_id)
        if not pack:
            return {"status": "error", "message": f"Unknown bundled skill pack: {skill_pack_id}"}
        if pack.risk_level == "HIGH" and not confirm:
            return {"status": "requires_approval", "approval_required": True, "message": "High-risk skill pack activation requires confirmation.", "skill_pack": pack.to_dict()}
        prefs = self.server.preferences_configuration_service.preferences
        active = set(prefs.setdefault("tool_profiles", {}).setdefault("active_skill_packs", []))
        active.add(skill_pack_id)
        prefs["tool_profiles"]["active_skill_packs"] = sorted(active)
        runtime_save_preferences(prefs, self.server.preferences_configuration_service.path)
        return {"status": "success", "active_skill_packs": prefs["tool_profiles"]["active_skill_packs"], "skill_pack": pack.to_dict()}

    def deactivate_skill_pack(self, skill_pack_id):
        prefs = self.server.preferences_configuration_service.preferences
        active = set(prefs.setdefault("tool_profiles", {}).setdefault("active_skill_packs", []))
        active.discard(skill_pack_id)
        prefs["tool_profiles"]["active_skill_packs"] = sorted(active)
        runtime_save_preferences(prefs, self.server.preferences_configuration_service.path)
        return {"status": "success", "active_skill_packs": prefs["tool_profiles"]["active_skill_packs"]}

    def recommend_skill_packs(self, task_description):
        return runtime_recommend_skill_packs(task_description)

    def validate_skill_pack_readiness(self, skill_pack_id, context=None):
        pack = RUNTIME_BUNDLED_SKILL_PACKS.get(skill_pack_id)
        if not pack:
            return {"status": "error", "message": f"Unknown bundled skill pack: {skill_pack_id}"}
        enabled = set(self.server.tool_profile_service.get_enabled_tool_packs().get("enabled_tool_packs", []))
        missing = sorted(set(pack.tool_packs) - enabled)
        prefs = self.server.preferences_configuration_service.preferences
        blockers = []
        if missing:
            blockers.append("required tool packs disabled")
        if not prefs.get("filesystem", {}).get("approved_roots"):
            blockers.append("no approved roots configured")
        return {"status": "success", "ready": not blockers, "skill_pack": pack.to_dict(), "missing_tool_packs": missing, "blockers": blockers, "context": context or {}}


class AddonInteropInspectionService:
    def __init__(self, server):
        self.server = server
        self.last_scan = None

    def list_addon_source_roots(self):
        roots = []
        try:
            for path in bpy.utils.script_paths():
                addon_dir = os.path.join(path, "addons")
                if os.path.isdir(addon_dir):
                    roots.append(addon_dir)
        except Exception:
            pass
        approved = self.server.preferences_configuration_service.preferences.get("filesystem", {}).get("approved_addon_source_roots", [])
        return {"status": "success", "roots": [{"path": p.replace(str(Path.home()), "~"), "approved": p in approved} for p in sorted(set(roots + approved))]}

    def scan_addon_sources_readonly(self, root, max_files=80, max_bytes=1000000):
        approved = self.server.preferences_configuration_service.preferences.get("filesystem", {}).get("approved_addon_source_roots", [])
        result = runtime_scan_addon_sources(root, approved, max_files=max_files, max_bytes=max_bytes)
        if result.get("status") == "success":
            self.last_scan = result
        return result

    def get_addon_source_summary(self, scan_id=None):
        if not self.last_scan:
            return {"status": "blocked", "message": "No read-only addon source scan has been run."}
        if scan_id and self.last_scan.get("scan_id") != scan_id:
            return {"status": "error", "message": f"Unknown scan_id: {scan_id}"}
        return {"status": "success", "summary": self.last_scan}

    def _search_scan(self, key, query, scan_id=None, limit=20):
        summary = self.get_addon_source_summary(scan_id)
        if summary.get("status") != "success":
            return summary
        terms = [t.lower() for t in str(query).split() if t.strip()]
        items = summary["summary"].get(key, [])
        matches = []
        for item in items:
            haystack = json.dumps(item).lower()
            if not terms or any(t in haystack for t in terms):
                matches.append(item)
        return {"status": "success", "results": matches[: max(1, min(int(limit), 50))]}

    def search_addon_operators(self, query, scan_id=None, limit=20):
        return self._search_scan("operators", query, scan_id, limit)

    def search_addon_panels(self, query, scan_id=None, limit=20):
        return self._search_scan("panels", query, scan_id, limit)

    def search_addon_properties(self, query, scan_id=None, limit=20):
        return self._search_scan("properties", query, scan_id, limit)

    def plan_addon_operator_invocation(self, operator_id, addon_module=None, properties=None):
        return runtime_plan_operator_invocation(operator_id, addon_module, properties)

    def execute_approved_addon_operator(self, approval_id, operator_id, properties=None):
        return {"status": "requires_approval", "approval_required": True, "message": "Third-party addon operator execution is not automatic in Phase 9B. Use exact approval through the governance runtime before any execution.", "approval_id": approval_id, "operator_id": operator_id, "properties": properties or {}}


class UserFacingErrorService:
    def __init__(self, server): self.server = server
    def get_error_catalog(self): return runtime_get_error_catalog()
    def explain_error(self, code, context=None): return runtime_explain_error(code, context)
    def get_remediation_steps(self, code): return runtime_get_remediation_steps(code)


class OnboardingWorkflowService:
    def __init__(self, server): self.server = server
    def get_setup_status(self): return runtime_run_setup_checks(self.server.preferences_configuration_service.preferences, ADDON_ROOT)
    def run_onboarding_checklist(self, fix_safe_defaults=False, confirm=False):
        result = self.get_setup_status()
        if fix_safe_defaults and not confirm:
            result["status"] = "requires_approval"
            result["approval_required"] = True
            result["message"] = "Safe defaults require confirmation before writing preferences."
        return result


class RuntimeUXStatusService:
    def __init__(self, server): self.server = server
    def get_runtime_dashboard(self):
        prefs = self.server.preferences_configuration_service.preferences
        profile = self.server.tool_profile_service.get_active_tool_profile().get("profile", {})
        setup = self.server.onboarding_workflow_service.get_setup_status()
        approvals = DEFAULT_APPROVAL_RUNTIME.get_pending_approvals()
        operations = DEFAULT_OPERATION_RUNTIME.list_recent_operations(20)
        return runtime_build_dashboard(prefs, profile, setup, approvals, operations)
    def get_approval_queue_summary(self): return runtime_approval_queue_summary(DEFAULT_APPROVAL_RUNTIME.get_pending_approvals())
    def get_recent_operation_summary(self): return runtime_recent_operation_summary(DEFAULT_OPERATION_RUNTIME.list_recent_operations(20))


class ProductPolishWorkflowBatchService:
    def __init__(self, server): self.server = server
    def run_product_polish_workflow_batch(self):
        return {
            "status": "success",
            "checks": {
                "preferences": self.server.preferences_configuration_service.validate_runtime_preferences(),
                "setup": self.server.onboarding_workflow_service.get_setup_status(),
                "tool_profile": self.server.tool_profile_service.get_active_tool_profile(),
                "dashboard": self.server.runtime_ux_status_service.get_runtime_dashboard(),
                "error_catalog": {"status": "success", "count": len(runtime_get_error_catalog().get("errors", []))},
            },
            "permissions_expanded": False,
            "third_party_code_executed": False,
        }


