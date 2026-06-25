from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase7c_spatial_runtime_and_addon_commands_exist() -> None:
    runtime = (ROOT / "src/overtli_blender/runtime/spatial.py").read_text(encoding="utf-8")
    for marker in ["def distance", "def angle_degrees", "def convert_units"]:
        assert marker in runtime
    addon = (ROOT / "addon.py").read_text(encoding="utf-8")
    assert "class SpatialMeasurementService" in addon
    for name in ["calculate_distance", "calculate_angle", "calculate_area", "calculate_volume", "convert_units", "get_oriented_bounds", "raycast_scene", "find_nearest_objects", "detect_object_intersections"]:
        assert f'"{name}":' in addon
