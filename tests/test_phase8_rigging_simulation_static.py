from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
TOOLS_TEXT = (ROOT / "src/overtli_blender/tools/rigging_simulation_tools.py").read_text(encoding="utf-8")
SAFETY_TEXT = (ROOT / "src/overtli_blender/common/safety.py").read_text(encoding="utf-8")
REGISTRY_TEXT = (ROOT / "src/overtli_blender/tools/registry.py").read_text(encoding="utf-8")


def test_phase8_rigging_simulation_service_and_commands_exist() -> None:
    for text in [
        "class RiggingSimulationService",
        "self.rigging_simulation_service = RiggingSimulationService(self)",
        "def inspect_rigging(",
        "def create_armature(",
        "def parent_mesh_to_armature(",
        "def pose_bone_transform(",
        "def add_driver(",
        "def remove_driver(",
        "def add_physics_basic(",
    ]:
        assert text in ADDON_TEXT


def test_phase8_rigging_simulation_mcp_wrappers_are_registered() -> None:
    assert "register_rigging_simulation_tools" in REGISTRY_TEXT
    for command in [
        "inspect_rigging",
        "create_armature",
        "parent_mesh_to_armature",
        "pose_bone_transform",
        "add_driver",
        "remove_driver",
        "add_physics_basic",
    ]:
        assert f"def {command}(" in TOOLS_TEXT
        assert f'"{command}"' in TOOLS_TEXT
        assert f'"{command}": self.{command}' in ADDON_TEXT
        assert f'"{command}": _spec("{command}"' in SAFETY_TEXT


def test_phase8_basics_cover_master_list_terms() -> None:
    for text in ["ARMATURE", "CLOTH", "SOFT_BODY", "rigid_body", "PARTICLE_SYSTEM", "HAIR", "driver_add", "driver_remove"]:
        assert text in ADDON_TEXT
