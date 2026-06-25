# Phase 9A Animation, Rigging, Drivers, Pose, Shot, and Simulation Workflows

Phase 9A adds a bounded animation workflow layer on top of the existing timeline,
driver, rigging, and simulation basics. The command surface favors inspection,
manifest-backed planning, explicit target names, and approval gates for operations
that can alter motion, rigs, drivers, caches, or poses in hard-to-reverse ways.

## Command Areas

- Animation intelligence: capability detection and scene animation inspection.
- Action library: list, inspect, create, duplicate, rename, assign, and delete actions.
- Keyframes and F-Curves: batch keyframe insertion, retiming, interpolation, F-Curve modifier planning, and validation.
- NLA workflows: create tracks, add actions as strips, edit/mute/delete tracks, and validate overlap.
- Driver DSL: allowlisted driver expressions compiled from structured input instead of arbitrary Python.
- Rig templates: create simple template rigs, add control metadata, IK chains, constraints, custom properties, and rig validation.
- Pose library: snapshot, apply, compare, manifest-backed pose assets, and exact delete.
- Shot workflows: shot ranges, camera cuts, timeline markers, shot plans, and validation.
- Simulation workflows: inspect and configure rigid body, cloth, soft body, hair-curve intent, cache status, preview plan, bake plan, and clear plan.
- Motion validation: aggregate checks for drivers, NLA overlap, rig naming/targets, simulation state, and motion bounds.

## Safety Model

These Phase 9A commands are high-risk and approval-gated by default:

- `delete_actions`
- `edit_keyframes`
- `retime_action`
- `remove_fcurve_modifier`
- `delete_nla_tracks`
- `remove_drivers`
- `remove_rig_constraints`
- `apply_pose_snapshot`
- `delete_pose_assets`
- `simulate_preview_range`
- `bake_simulation_cache`
- `clear_simulation_cache`

Driver creation is also confirmation-gated and uses the structured driver DSL.
Simulation preview, bake, and cache clearing report approval-required or unsupported
instead of claiming unverified cache execution.

## Smoke

After refreshing or reloading the Blender addon, run:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase9a-full
```

The Phase 9A smoke creates only `OVERTLI_PHASE9A_*` data, checks safe action,
keyframe, rig, pose, shot, simulation, and validation paths, and verifies that
driver creation, pose application, simulation preview, and cache clearing require
approval by default.
