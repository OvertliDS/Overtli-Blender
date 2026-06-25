from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase7c_reference_service_tracks_calibration_and_landmarks() -> None:
    addon = (ROOT / "addon.py").read_text(encoding="utf-8")
    assert "class ReferenceImageService" in addon
    for marker in ['"references", "images"', "scale_calibration", "landmarks", "copy_into_project", "empty_display_type"]:
        assert marker in addon
    for name in ["import_reference_image", "create_reference_set", "place_reference_view", "calibrate_reference_scale", "add_reference_landmark", "measure_reference_landmarks", "list_reference_images", "remove_reference_image"]:
        assert f'"{name}":' in addon
