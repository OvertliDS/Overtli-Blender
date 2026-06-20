from __future__ import annotations

from src.blender_mcp.common.permissions import RiskLevel, Reversibility
from src.blender_mcp.common.safety import (
    AVAILABLE_SAFETY_MODES,
    DEFAULT_SAFETY_MODE,
    SAFETY_MODE_AUDIT,
    SAFETY_MODE_COMPAT,
    SAFETY_MODE_STRICT,
    build_command_safety_map,
    get_command_safety,
)


def test_safety_modes_are_stable() -> None:
    assert DEFAULT_SAFETY_MODE == SAFETY_MODE_COMPAT
    assert AVAILABLE_SAFETY_MODES == [SAFETY_MODE_COMPAT, SAFETY_MODE_AUDIT, SAFETY_MODE_STRICT]


def test_command_safety_map_contains_expected_commands() -> None:
    safety_map = build_command_safety_map()
    for name in [
        "get_scene_info",
        "execute_code",
        "complete_geometry_node",
        "download_polyhaven_asset",
        "download_sketchfab_model",
        "create_rodin_job",
        "get_safety_status",
    ]:
        assert name in safety_map


def test_high_risk_commands_are_flagged_for_strict_mode() -> None:
    safety_map = build_command_safety_map()
    for name in [
        "execute_code",
        "execute_context_script",
        "download_polyhaven_asset",
        "download_sketchfab_model",
        "create_rodin_job",
        "import_generated_asset",
        "complete_geometry_node",
        "clear_context_scripts",
    ]:
        assert safety_map[name].strict_blocked


def test_safety_metadata_uses_core_enums() -> None:
    safety_map = build_command_safety_map()
    execute_code = safety_map["execute_code"]
    assert execute_code.risk_level == RiskLevel.HIGH
    assert execute_code.reversibility == Reversibility.UNKNOWN


def test_get_command_safety_returns_expected_spec() -> None:
    spec = get_command_safety("get_scene_info")
    assert spec is not None
    assert spec.risk_level == RiskLevel.LOW
