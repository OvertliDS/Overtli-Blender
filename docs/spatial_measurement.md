# Spatial Measurement

Phase 7C adds spatial measurement and rename-planning foundations.

Measurement commands use explicit object names or explicit points. Results include Blender-unit values, scene unit-system context, confidence, and method notes where applicable. Expensive scene queries are bounded by command parameters.

Supported surfaces include distance, angle, area scaffold, volume estimate, curve length scaffold, clearance, alignment, unit conversion, scale ratio, measurement comparison, oriented bounds, raycast, nearest objects, intersection scaffold, and object-to-reference measurement.

Safe rename commands are plan-first. Plans detect collisions and return approval ids. Execution is approval-gated; Phase 7C enables object datablock rename execution only for exact approved plans, while project folder and arbitrary file rename remain blocked or plan-only.
