# Reference Images

Phase 7C adds reference image workflow foundations.

Reference images are copied into `references/images/` by default. External links require approved read roots. Reference records track source path, project copy path, hash-ready identity, dimensions, reference type, view, scale calibration, opacity, depth, lock state, landmarks, and confidence.

Geometric accuracy is not claimed until calibration is recorded. Landmarks can be added and measured, but uncalibrated measurements are reported with lower confidence.

Primary commands: `import_reference_image`, `create_reference_set`, `place_reference_view`, `calibrate_reference_scale`, `set_reference_opacity`, `set_reference_depth`, `lock_reference`, `set_reference_view_visibility`, `add_reference_landmark`, `measure_reference_landmarks`, `capture_reference_overlay`, `list_reference_images`, `relink_reference_image`, and `remove_reference_image`.
