from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")
SMOKE_TEXT = (ROOT / "scripts" / "smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_phase6a_procedural_asset_generators_are_present() -> None:
    for method in [
        "def create_procedural_asset",
        "def create_scatter_system",
        "def create_curve_generator",
        "def create_radial_array_system",
        "def create_panel_generator",
        "def create_cable_or_rope_generator",
        "def create_terrain_noise_system",
    ]:
        assert method in ADDON_TEXT


def test_phase6a_preview_scene_kit_and_cleanup_are_present() -> None:
    for text in [
        "create_geometry_nodes_preview",
        "create_geometry_nodes_scene_kit",
        "delete_geometry_node_groups requires confirm=True",
        "remove_geometry_nodes_modifiers requires confirm=True",
        "does-not-apply-modifier-destructively",
    ]:
        assert text in ADDON_TEXT or text in (ROOT / "src" / "overtli_blender" / "common" / "safety.py").read_text(encoding="utf-8")


def test_phase6a_smoke_uses_exact_prefix_and_forbids_raw_or_provider_commands() -> None:
    start = SMOKE_TEXT.index("def run_phase6a_full_smoke")
    end = SMOKE_TEXT.index("def build_parser")
    block = SMOKE_TEXT[start:end]
    for text in [
        "OVERTLI_PHASE6A_",
        "remove_geometry_nodes_modifiers",
        "delete_geometry_node_groups",
        "cleanup_asset_artifacts",
        "_assert_phase6a_workspace_ignored",
    ]:
        assert text in block
    for forbidden in ["execute_code", "download_polyhaven_asset", "download_sketchfab_model", "create_rodin_job"]:
        assert forbidden not in block
