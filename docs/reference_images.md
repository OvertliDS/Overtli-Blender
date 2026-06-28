# Reference Images

Phase 7C adds reference image workflow foundations.

Reference images are copied into `references/images/` by default. External links require approved read roots. Reference records track source path, project copy path, hash-ready identity, dimensions, reference type, view, scale calibration, opacity, depth, lock state, landmarks, and confidence.

When a reference has been placed as an Empty Image object, opacity, depth, lock state, and visibility setters update the actual Blender object as well as the stored reference record. The response includes `viewport_state` when an object was updated. If a reference has only been imported and not placed, setters update metadata until `place_reference_view` creates the viewport object.

Geometric accuracy is not claimed until calibration is recorded. Landmarks can be added and measured, but uncalibrated measurements are reported with lower confidence.

Primary commands: `import_reference_image`, `create_reference_set`, `place_reference_view`, `calibrate_reference_scale`, `set_reference_opacity`, `set_reference_depth`, `lock_reference`, `set_reference_view_visibility`, `add_reference_landmark`, `measure_reference_landmarks`, `capture_reference_overlay`, `list_reference_images`, `relink_reference_image`, and `remove_reference_image`.
