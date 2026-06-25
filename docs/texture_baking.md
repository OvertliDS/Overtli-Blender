# Texture Baking

Phase 8A adds a project-scoped texture baking pipeline for AI clients. Outputs are classified honestly:

- `native`: produced through a Blender-supported native bake pass such as `NORMAL`, `AO`, `DIFFUSE`, `EMIT`, or `ROUGHNESS` when the runtime reports support.
- `derived`: produced by assembling or routing material data, such as metallic/roughness workflow outputs or channel-packed maps.
- `approximated`: produced by an approximation workflow, especially curvature and thickness.
- `unsupported`: not produced because the current runtime or workflow cannot do it safely.

The main commands are `get_bake_capabilities`, `validate_bake_setup`, `estimate_bake_cost`, `create_bake_target_images`, `assign_bake_targets`, `bake_material_maps`, `bake_selected_to_active`, `bake_procedural_material`, `bake_derived_map`, `bake_curvature_map`, `bake_thickness_map`, `save_baked_textures`, `validate_baked_textures`, `relink_baked_textures`, `create_baked_material`, `plan_bake_cleanup`, `execute_bake_cleanup`, and `run_verified_bake_workflow`.

## Workspace Rules

Bake outputs default to the Phase 7C project workspace under `textures/baked/`. Packed outputs default to `textures/packed/`. Writes use the project file access policy and existing files require overwrite approval.

## Preflight

`validate_bake_setup` checks object existence, mesh compatibility, UV layers, selected-to-active source/target rules, render engine suitability, bake operator availability, output collisions, resolution bounds, cage object existence, normal-space support, target node plans, and estimated cost.

## Temporary Nodes

Bake target image nodes are tagged as Overtli temporary bake nodes. Cleanup is plan/execute and approval-gated. Cleanup only removes tracked temporary nodes/images and never deletes final baked textures by default.

## Limitations

Curvature and thickness are not claimed as native outputs. They are reported as approximated workflows with confidence and limitations. Native bake execution depends on Blender runtime support and typically requires Cycles.
