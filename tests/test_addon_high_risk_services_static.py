from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


def test_addon_defines_high_risk_service_classes() -> None:
    for name in [
        "class SafetyPolicyService",
        "class RawCodeExecutionService",
        "class GeometryNodesService",
    ]:
        assert name in ADDON_TEXT


def test_addon_initializes_high_risk_service_instances() -> None:
    for name in [
        "self.safety_policy_service = SafetyPolicyService(self)",
        "self.raw_code_execution_service = RawCodeExecutionService(self)",
        "self.geometry_nodes_service = GeometryNodesService(self)",
    ]:
        assert name in ADDON_TEXT


def test_addon_binds_high_risk_service_methods() -> None:
    for name in [
        "self.get_safety_status = self.safety_policy_service.get_safety_status",
        "self.execute_code = self.raw_code_execution_service.execute_code",
        "self.complete_geometry_node = self.geometry_nodes_service.complete_geometry_node",
        "self.get_geometry_nodes_status = self.geometry_nodes_service.get_geometry_nodes_status",
    ]:
        assert name in ADDON_TEXT


def test_addon_high_risk_source_methods_delegate_to_services() -> None:
    for name in [
        "return self.safety_policy_service.get_safety_status()",
        "return self.raw_code_execution_service.execute_code(code)",
        "return self.geometry_nodes_service.complete_geometry_node(object_name, nodes, links, input_sockets)",
        "return self.geometry_nodes_service._create_geometry_nodes_object(object_name)",
        "return self.geometry_nodes_service._setup_node_group_interface(node_group, input_sockets)",
        "return self.geometry_nodes_service.get_geometry_nodes_status()",
    ]:
        assert name in ADDON_TEXT


def test_addon_high_risk_commands_remain_available() -> None:
    for name in [
        "execute_code",
        "complete_geometry_node",
        "get_geometry_nodes_status",
    ]:
        assert f'"{name}":' in ADDON_TEXT or f"'{name}':" in ADDON_TEXT
