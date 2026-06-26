from __future__ import annotations

import ast
from pathlib import Path

from overtli_blender.runtime.command_registry import CommandSpec, build_command_registry, command_registry_report


ROOT = Path(__file__).resolve().parents[1]


def _addon_command_names() -> set[str]:
    tree = ast.parse((ROOT / "overtli_blender_addon" / "runtime" / "socket_server.py").read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_build_command_handlers":
            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and isinstance(child.value, str) and "_" in child.value:
                    names.add(child.value)
    return {name for name in names if name.islower()}


def _mcp_tool_names() -> set[str]:
    names: set[str] = set()
    for path in (ROOT / "src" / "overtli_blender" / "tools").glob("*_tools.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            is_mcp_tool = any(
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "tool"
                for decorator in node.decorator_list
            )
            if is_mcp_tool:
                names.add(node.name)
    return names


def test_command_spec_registry_covers_addon_and_mcp_commands() -> None:
    registry = build_command_registry()
    assert CommandSpec
    assert not (_addon_command_names() - set(registry))
    assert not (_mcp_tool_names() - set(registry))


def test_command_specs_have_governance_metadata() -> None:
    registry = build_command_registry()
    for name, spec in registry.items():
        assert spec.name == name
        assert spec.category
        assert spec.tool_pack
        assert spec.risk_level in {"LOW", "MEDIUM", "HIGH", "DESTRUCTIVE"}
        if spec.risk_level == "HIGH":
            assert spec.requires_approval or spec.requires_confirmation
        if spec.destructive:
            assert spec.requires_approval or spec.requires_confirmation


def test_command_registry_report_lists_envelope_migration_pending() -> None:
    report = command_registry_report()
    assert report["status"] == "success"
    assert report["command_count"] >= 100
    assert "response_envelope_migration" in report
    assert "delete_objects" in report["response_envelope_migration"]["migration_pending"]
    stale_alias = "blender-mcp" + "-enhanced"
    assert stale_alias not in (ROOT / "src" / "overtli_blender" / "runtime" / "command_registry.py").read_text(encoding="utf-8")
