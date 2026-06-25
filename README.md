# Overtli-Blender

Overtli-Blender is a local-first Blender MCP addon/server for AI-assisted Blender workflows.
It connects Blender to MCP clients through a socket bridge, with shared context, inspection tools, scripting helpers, provider status checks, Geometry Nodes helpers, raw code execution, and a built-in safety policy.

## What It Does

- Scene and object inspection
- Rich Phase 2 scene index, object deep inspection, selection inspection, and scene health diagnostics
- Viewport screenshots
- Multi-view screenshot packs and verification snapshot manifests under `.overtli_blender/verification/`
- Verified Phase 3 scene editing: primitive creation, transforms, duplication, bounded deletion, visibility, materials, modifiers, collections, and verified edit batches
- Phase 3 workspace, todo, operation journal, scene snapshot, scene diff, user-change detection, and rollback tools under `.overtli_blender/workspace/`
- Phase 4A production material workflows: channel schema, material templates, deep material inspection, shader graph inspection, texture/map slot binding, procedural material generation, material previews, material workflow batches, and confirmed material cleanup
- Phase 4B method, asset, region, deformation, and sculpt workflows: method plans, playbooks, tricks knowledge, anti-pattern rules, modifier recipes, confidence scoring, asset scans/previews, style/PBR material helpers, texture-folder import, paintable texture setup, UV map inspection, measurements, vertex groups, Basis-preserving shape keys, lattice deformers, proportional-style deformation, sculpt mask intent, shape-key sculpt workflows, and deformation workflow batches
- Phase 5A presentation workflows: timeline and animation inspection, transform/material/light/shape-key animation, camera creation/framing, active camera control, light and studio setup tools, render settings, still/contact-sheet/preview artifacts, turntable setup, compositor/pass presets, presentation workflow batches, and exact-prefix cleanup
- Shared context, object handles, and material handles
- Script registry management
- Provider status checks for Poly Haven, Sketchfab, and Hyper3D
- Geometry Nodes helpers
- Raw Blender Python execution with safety policy controls
- Safety status inspection
- A local socket smoke harness for runtime verification

## Safety

Raw code execution can run Blender Python inside the current session, so treat it as powerful and potentially destructive.

- Default mode is `compatibility`
- `audit` keeps behavior but adds safety metadata
- `strict` blocks the high-risk command set
- Provider and asset download tools may involve network access or API keys

## Install

Use an editable install during development:

```powershell
python -m pip install -e .
```

The primary console command is:

```powershell
overtli-blender
```

## Blender Addon Setup

1. Open Blender.
2. Install or enable `addon.py` in `Edit > Preferences > Add-ons`.
3. Start the addon socket server from the Blender MCP UI.
4. Leave the socket on `localhost:9876` unless you intentionally changed it.

## Runtime Smoke

The addon socket smoke runs directly against Blender and does not require MCP client setup.

See [docs/runtime_smoke.md](docs/runtime_smoke.md).

Phase 2 verification smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase2-full
```

Phase 3 verified edit smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase3-full
```

The Phase 3 smoke creates temporary `OVERTLI_PHASE3_*` objects, materials, and collections, uses only structured edit/workspace commands, captures verification artifacts under `.overtli_blender/verification/`, writes workspace evidence under `.overtli_blender/workspace/`, checks scene diff/change detection/rollback, and cleans up only the object and collection names created by that run. It does not run raw code, download assets, or target arbitrary user objects.

Phase 4A production material smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase4a-full
```

The Phase 4A smoke creates temporary `OVERTLI_PHASE4A_*` objects, materials, and a collection; exercises material channel schema, templates, procedural/custom materials, shader graph inspection, texture slot validation, preview artifacts, material workflow batches, and confirmed material deletion; then verifies no smoke-created objects, collections, or materials remain. It may write ignored preview and verification artifacts under `.overtli_blender/`, and it may reference ignored placeholder texture paths under `.overtli_blender/material_test_textures/`. It does not download assets, run raw code, bake textures, or touch arbitrary user data.

Phase 4B selection and deformation smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase4b-full
```

The Phase 4B smoke creates temporary `OVERTLI_PHASE4B_*` objects, materials, an image, a collection, a vertex group, shape keys, a lattice, and a deformation modifier. It exercises method planning, playbooks, tricks, anti-patterns, modifier recipes, asset scan/preview, style material creation, paintable texture setup, selection intelligence, UV inspection, measurement, confidence scoring, vertex group masks, shape key offsets, lattice updates, proportional deformation, sculpt mask intent, shape-key sculpt workflow, region deformation, and workflow batches; then verifies no smoke-created objects, collections, materials, images, lattices, vertex groups, or shape keys remain. It writes ignored verification artifacts under `.overtli_blender/`, does not run raw code, does not download assets, does not apply modifiers destructively, and does not touch arbitrary user data.

Phase 5A presentation smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase5a-full
```

The Phase 5A smoke creates temporary `OVERTLI_PHASE5A_*` scene data, exercises timeline, animation, camera, lighting, render settings, still render, contact sheet, turntable, bounded preview animation, compositor/pass, and presentation batch workflows, then removes exact smoke-created scene data. It writes ignored render, preview, presentation, and verification artifacts under `.overtli_blender/`. It does not download assets, run raw code, render high-cost full animations, or touch arbitrary user objects.

Generated verification and workspace artifacts are written under `.overtli_blender/` and are ignored by git.

## Upstream Credit

This project builds on the original BlenderMCP work by Siddharth Ahuja and the BlenderMCP community.
Historical names are retained only where they are part of upstream attribution or repository history.
