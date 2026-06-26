from __future__ import annotations

import ast
from pathlib import Path

from tests._addon_source import ADDON_PACKAGE_SOURCE


ROOT = Path(__file__).resolve().parents[1]


def test_addon_py_is_thin_entrypoint() -> None:
    text = (ROOT / "addon.py").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 300
    assert "importlib.import_module(\"overtli_blender_addon\")" in text
    assert "class BlenderMCPServer" not in text
    assert "class SharedContextService" not in text


def test_no_renamed_monolith_exists() -> None:
    assert not (ROOT / "overtli_blender_addon" / "legacy_runtime.py").exists()


def test_canonical_addon_package_modules_exist() -> None:
    for rel in [
        "overtli_blender_addon/core.py",
        "overtli_blender_addon/bl_info.py",
        "overtli_blender_addon/registration.py",
        "overtli_blender_addon/preferences.py",
        "overtli_blender_addon/operators.py",
        "overtli_blender_addon/ui/panels.py",
        "overtli_blender_addon/runtime/socket_server.py",
        "overtli_blender_addon/runtime/dispatcher.py",
        "overtli_blender_addon/services/context.py",
        "overtli_blender_addon/services/scene.py",
        "overtli_blender_addon/services/materials.py",
        "overtli_blender_addon/services/geometry_nodes.py",
        "overtli_blender_addon/services/product_ux.py",
    ]:
        assert (ROOT / rel).is_file()


def test_packaged_addon_init_has_literal_bl_info_for_blender_discovery() -> None:
    text = (ROOT / "overtli_blender_addon" / "__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    bl_info_assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "bl_info" for target in node.targets)
    ]

    assert bl_info_assignments, "Blender addon discovery needs a literal bl_info in package __init__.py"
    bl_info = ast.literal_eval(bl_info_assignments[0].value)
    assert bl_info["name"] == "Overtli-Blender"
    assert bl_info["category"] == "Interface"


def test_packaged_addon_does_not_require_requests_to_register() -> None:
    text = (ROOT / "overtli_blender_addon" / "core.py").read_text(encoding="utf-8")
    assert "except ModuleNotFoundError:" in text
    assert "Optional dependency 'requests' is not available in Blender Python" in text
    assert "requests = _MissingRequests()" in text


def test_service_implementations_are_in_package_source() -> None:
    for marker in [
        "class SharedContextService",
        "class SceneObservationService",
        "class MaterialAuthoringService",
        "class GeometryNodesService",
        "class PreferencesConfigurationService",
        "class BlenderMCPServer",
        "def _build_command_handlers",
    ]:
        assert marker in ADDON_PACKAGE_SOURCE
