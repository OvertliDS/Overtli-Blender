# Spatial Measurement

Phase 7C adds spatial measurement and rename-planning foundations. The 2026-06-28 audit remediation pass replaced the highest-risk scaffold measurements with bounded real calculations.

Measurement commands use explicit object names or explicit points. Results include Blender-unit values, scene unit-system context, confidence, and method notes where applicable. Expensive scene queries are bounded by command parameters.

Supported surfaces include distance, angle, evaluated mesh surface area, evaluated mesh volume with a bounds fallback when exact volume is unavailable, sampled curve length, world-bounding-box clearance, world-bounding-box intersection detection, center-alignment offsets, unit conversion, scale ratio, measurement comparison, oriented bounds, raycast, nearest objects, and object-to-reference measurement.

Area and volume operate on evaluated mesh data. Volume returns `partial` with a warning for non-watertight or fallback cases instead of pretending a bounds product is exact. Clearance and intersections are currently world-bounding-box methods; responses include the method used so clients do not confuse them with mesh-level BVH refinement.

Safe rename commands are plan-first. Plans detect collisions and return approval ids. Execution is approval-gated; Phase 7C enables object datablock rename execution only for exact approved plans, while project folder and arbitrary file rename remain blocked or plan-only.
