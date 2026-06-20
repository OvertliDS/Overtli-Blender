from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")


def test_addon_defines_internal_shared_context_service() -> None:
    for name in [
        "class SharedContextService",
        "def add_to_history(",
        "def clear_shared_context(",
        "self.shared_context_service = SharedContextService(self.shared_context)",
    ]:
        assert name in ADDON_TEXT


def test_addon_defines_internal_script_registry_service() -> None:
    for name in [
        "class ScriptRegistryService",
        "def _get_script_directory(",
        "def register_context_script(",
        "def execute_context_script(",
        "def list_context_scripts(",
        "def clear_context_scripts(",
        "self.script_registry_service = ScriptRegistryService()",
    ]:
        assert name in ADDON_TEXT


def test_addon_wrapper_methods_delegate_to_services() -> None:
    for name in [
        "return self.shared_context_service.store_object_handle(handle, obj_name)",
        "return self.shared_context_service.store_material_handle(handle, mat_name)",
        "return self.shared_context_service.store_operation_result(op_id, result)",
        "self.shared_context_service.add_to_history(operation, input_data, result)",
        "return self.shared_context_service.get_shared_context()",
        "return self.shared_context_service.clear_shared_context(section)",
        "return self.script_registry_service.register_context_script(script_name, script_content, category, permanent)",
        "return self.script_registry_service.execute_context_script(script_name, category)",
        "return self.script_registry_service.list_context_scripts(category)",
        "return self.script_registry_service.clear_context_scripts(category, script_name, clear_permanent)",
    ]:
        assert name in ADDON_TEXT


def test_addon_keeps_command_and_history_contracts() -> None:
    for name in [
        '"execute_code": self.execute_code',
        "execute_code",
        "clear_context_scripts",
        "blendermcp_use_polyhaven",
        "blendermcp_use_hyper3d",
        "blendermcp_use_sketchfab",
        "Keep only last 50 operations",
    ]:
        assert name in ADDON_TEXT
