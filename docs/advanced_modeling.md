# Advanced Modeling

Phase 8B adds structured construction workflows for custom geometry. The default method hierarchy is reference-guided planning, validated mesh schemas, curves/profiles, non-destructive modifiers, Geometry Nodes where appropriate, shape-key sculpt variants, cloth pattern setup, and only gated destructive operations.

## Mesh Schemas

`validate_mesh_schema` checks vertex/edge/face types, index ranges, duplicate vertices, degenerate faces, boundary/non-manifold risk markers, bounds, and estimated memory. `create_mesh_from_schema` validates first, creates a named mesh with `from_pydata`, links it to an optional collection, and returns a construction manifest summary.

## Profiles and Curves

Profile workflows expose `create_profile_curve`, `extrude_profile`, `lathe_profile`, `loft_profiles`, `bridge_profile_loops`, `create_curve_path_object`, and `create_beveled_curve_object`. Extrude and lathe prefer curve data or non-destructive Screw modifiers. Loft and bridge refuse destructive guessing when explicit loop/profile mapping is missing.

## Modifier Construction

`create_modifier_stack` accepts an allowlisted non-destructive stack: Bevel, Array, Mirror, Solidify, Weighted Normal, Boolean, Shrinkwrap, Simple Deform, Curve, Skin, Wireframe, Lattice, and Displace. `create_hard_surface_panel`, `create_pipe_or_rail`, and `create_modular_assembly` build reusable construction assets without applying destructive modifiers by default.

## Limits

Schema creation is bounded by vertex and face limits. Modifier application is not part of this phase. Destructive cleanup and sculpt/cloth execution paths require approval.
