from __future__ import annotations

from ..core import *

class SafetyPolicyService:
    def __init__(self, server):
        self.server = server
        self.command_safety_map = build_command_safety_map()
        self.mode, self.warnings = self._resolve_mode()

    @staticmethod
    def _metadata_attr(metadata, name):
        if hasattr(metadata, name):
            return getattr(metadata, name)
        if isinstance(metadata, dict):
            return metadata.get(name)
        return None

    def _resolve_mode(self):
        raw_mode = os.environ.get("OVERTLI_BLENDER_SAFETY_MODE", "").strip().lower()
        if not raw_mode:
            return SAFETY_MODE_COMPAT, []

        aliases = {
            "legacy": SAFETY_MODE_COMPAT,
            "permissive": SAFETY_MODE_COMPAT,
            SAFETY_MODE_COMPAT: SAFETY_MODE_COMPAT,
            SAFETY_MODE_AUDIT: SAFETY_MODE_AUDIT,
            SAFETY_MODE_STRICT: SAFETY_MODE_STRICT,
        }
        resolved_mode = aliases.get(raw_mode)
        if resolved_mode:
            return resolved_mode, []

        return SAFETY_MODE_COMPAT, [f"Invalid safety mode '{raw_mode}', defaulting to compatibility"]

    def _build_decision(self, command_type, metadata, allowed, reason):
        operation_type = self._metadata_attr(metadata, "operation_type")
        risk_level = self._metadata_attr(metadata, "risk_level")
        reversibility = self._metadata_attr(metadata, "reversibility")
        if hasattr(operation_type, "value"):
            operation_type = operation_type.value
        if hasattr(risk_level, "value"):
            risk_level = risk_level.value
        if hasattr(reversibility, "value"):
            reversibility = reversibility.value
        return {
            "allowed": allowed,
            "mode": self.mode,
            "command_type": command_type,
            "operation_type": operation_type,
            "risk_level": risk_level,
            "reversibility": reversibility,
            "can_mutate_scene": bool(self._metadata_attr(metadata, "can_mutate_scene")),
            "can_execute_code": bool(self._metadata_attr(metadata, "can_execute_code")),
            "can_call_network": bool(self._metadata_attr(metadata, "can_call_network")),
            "can_write_files": bool(self._metadata_attr(metadata, "can_write_files")),
            "provider_api_key_involved": bool(self._metadata_attr(metadata, "provider_api_key_involved")),
            "strict_blocked": bool(self._metadata_attr(metadata, "strict_blocked")),
            "default_action": self._metadata_attr(metadata, "default_action") or "allow",
            "strict_action": self._metadata_attr(metadata, "strict_action") or "block",
            "warnings": list(self.warnings) + list(self._metadata_attr(metadata, "warnings") or []),
            "reason": reason,
        }

    def evaluate_command(self, command_type: str, params: dict | None = None) -> dict:
        metadata = self.command_safety_map.get(command_type)
        if metadata is None:
            return {
                "allowed": True,
                "mode": self.mode,
                "command_type": command_type,
                "operation_type": "UNKNOWN",
                "risk_level": "LOW",
                "reversibility": "UNKNOWN",
                "can_mutate_scene": False,
                "can_execute_code": False,
                "can_call_network": False,
                "can_write_files": False,
                "provider_api_key_involved": False,
                "strict_blocked": False,
                "default_action": "allow",
                "strict_action": "block",
                "warnings": list(self.warnings) + [f"Unknown command '{command_type}'"],
                "reason": "unknown command",
            }

        risk_level = self._metadata_attr(metadata, "risk_level")
        if hasattr(risk_level, "value"):
            risk_level = risk_level.value
        strict_blocked = bool(self._metadata_attr(metadata, "strict_blocked"))
        blocked = self.mode == SAFETY_MODE_STRICT and (strict_blocked or risk_level in {RiskLevel.HIGH, RiskLevel.DESTRUCTIVE, "HIGH", "DESTRUCTIVE"})
        if blocked:
            return self._build_decision(command_type, metadata, False, "command blocked by strict safety policy")

        if self.mode == SAFETY_MODE_AUDIT:
            return self._build_decision(command_type, metadata, True, "command allowed in audit mode")

        return self._build_decision(command_type, metadata, True, "command allowed in compatibility mode")

    def get_safety_status(self):
        high_risk_commands = []
        network_commands = []
        strict_blocked_commands = []

        for command_type, metadata in self.command_safety_map.items():
            risk_level = self._metadata_attr(metadata, "risk_level")
            if hasattr(risk_level, "value"):
                risk_level = risk_level.value
            if risk_level in {RiskLevel.HIGH, RiskLevel.DESTRUCTIVE, "HIGH", "DESTRUCTIVE"}:
                high_risk_commands.append(command_type)
            if bool(self._metadata_attr(metadata, "can_call_network")):
                network_commands.append(command_type)
            if bool(self._metadata_attr(metadata, "strict_blocked")):
                strict_blocked_commands.append(command_type)

        return {
            "mode": self.mode,
            "available_modes": list(AVAILABLE_SAFETY_MODES),
            "default_mode": DEFAULT_SAFETY_MODE,
            "policy_version": SAFETY_POLICY_VERSION,
            "command_count": len(self.command_safety_map),
            "high_risk_commands": sorted(high_risk_commands),
            "network_commands": sorted(network_commands),
            "strict_blocked_commands": sorted(strict_blocked_commands),
            "warnings": list(self.warnings),
        }


class RawCodeExecutionService:
    def __init__(self, server):
        self.server = server

    def execute_code(self, code):
        """Execute arbitrary Blender Python code with shared context"""
        try:
            namespace = {
                "bpy": bpy,
                "shared": self.server.shared_context['variables'],
                "get_object": lambda handle: self.server.shared_context['objects'].get(handle),
                "get_material": lambda handle: self.server.shared_context['materials'].get(handle),
                "get_operation": lambda op_id: self.server.shared_context['operations'].get(op_id),
                "store_object": self.server._store_object_handle,
                "store_material": self.server._store_material_handle,
                "store_operation": self.server._store_operation_result,
            }

            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)

            captured_output = capture_buffer.getvalue()
            self.server._add_to_history("execute_code", code[:100] + "..." if len(code) > 100 else code, captured_output)
            return {"executed": True, "result": captured_output, "shared_variables": list(self.server.shared_context['variables'].keys())}
        except Exception as e:
            error_msg = f"Code execution error: {str(e)}"
            self.server._add_to_history("execute_code", code[:100] + "..." if len(code) > 100 else code, f"ERROR: {error_msg}")
            raise Exception(error_msg)


