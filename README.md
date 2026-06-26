# Overtli-Blender

## Phase 9B Product UX

Phase 9B adds user-facing runtime UX over the existing command library:

- runtime preferences schema and validation
- safe permission/profile persistence
- built-in tool profiles and visible tool budgets
- bundled skill pack library and readiness checks
- read-only third-party addon source inspection
- approval-gated third-party operator planning
- user-friendly error catalog and remediation hints
- onboarding/setup checks
- runtime dashboard, approval queue, and recent operation summaries

See `docs/preferences.md`, `docs/tool_profiles.md`, `docs/bundled_skill_packs.md`, `docs/addon_interoperability.md`, `docs/error_handling.md`, `docs/onboarding.md`, and `docs/runtime_dashboard.md`.

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
- Phase 5B asset workflows: runtime import/export format detection, bounded local folder scans, scene asset inventory, asset file inspection, dependency reports, asset manifests, `.blend` append/link, local model import/export, asset previews/contact sheets, reusable scene kits, external dependency validation/collection, and asset workflow batches
- Phase 8 basics: driver add/remove, armature creation/inspection, mesh-to-armature parenting with vertex groups, pose-bone transforms, and basic cloth/hair/soft-body/rigid-body/collision setup
- Phase 7B runtime governance: command registry, tool packs, approval records, capability profiles, operation status/cancel skeletons, structured log status, and packaged addon migration scaffold
- Phase 7C project runtime foundation: saved/unsaved `.blend` workspace resolution, approved-root file access, cache retention planning, task graph and scene revision tracking, reference image calibration, spatial measurement, and safe rename planning
- Phase 8A texture baking and image resource pipeline: bake capability detection, preflight, bake target images, native/derived/approximated map classification, channel packing, baked texture validation, baked material variants, and approval-gated cleanup planning
- Phase 8B advanced modeling workflows: validated mesh schemas, profile/extrude/lathe/loft surfaces, curve/path pipe construction, non-destructive modifier stacks, reference construction planning, shape-key-first sculpt setup, cloth pattern panels, construction validation, and gated cleanup/cache actions
- Phase 9A animation and rigging workflows: action library tools, keyframe/F-Curve editing, NLA track/strip workflows, allowlisted driver DSL, rig templates, IK/constraint/custom-property helpers, pose snapshots/assets, shot plans, simulation inspection/configuration, cache approval gates, and motion validation
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

Runtime governance adds command discovery, tool specs, permission profiles, and
two-phase approval metadata on top of the existing safety policy. Existing
socket command names remain stable.

## Install

Create a local virtual environment and install the MCP package:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e .
```

The Python distribution is `overtli-blender`, the import package lives at `src/overtli_blender`, and the Blender addon runtime lives in `overtli_blender_addon/`.

The primary console command is:

```powershell
overtli-blender
```

See [docs/install.md](docs/install.md), [docs/mcp_setup.md](docs/mcp_setup.md), and [docs/addon_install.md](docs/addon_install.md) for repeatable install and MCP client setup steps.

For MCP clients, register the venv Python module command:

```powershell
.\.venv\Scripts\python -m overtli_blender.server
```

## Blender Addon Setup

1. Build the addon zip with `.\.venv\Scripts\python scripts\build_addon_zip.py --mode package --verify`.
2. Open Blender and install `.overtli_blender/release/addon_zip/overtli_blender_addon_0.1.0.zip`.
3. Enable Overtli-Blender and start the addon socket server from the sidebar UI.
4. Leave the socket on `localhost:9876` unless you intentionally changed it.

## Runtime Smoke

The addon socket smoke runs directly against Blender and does not require MCP client setup.

See [docs/runtime_smoke.md](docs/runtime_smoke.md).

Fast local release readiness check:

```powershell
.\.venv\Scripts\python scripts\release_check.py --fast
```

Package and release helper docs:

- [docs/release_check.md](docs/release_check.md)
- [docs/development.md](docs/development.md)
- [docs/runtime_governance.md](docs/runtime_governance.md)
- [docs/command_registry.md](docs/command_registry.md)
- [docs/tool_packs.md](docs/tool_packs.md)
- [docs/approval_runtime.md](docs/approval_runtime.md)
- [docs/packaged_addon_migration.md](docs/packaged_addon_migration.md)
- [docs/project_workspace.md](docs/project_workspace.md)
- [docs/file_access_policy.md](docs/file_access_policy.md)
- [docs/cache_retention.md](docs/cache_retention.md)
- [docs/task_graph.md](docs/task_graph.md)
- [docs/reference_images.md](docs/reference_images.md)
- [docs/spatial_measurement.md](docs/spatial_measurement.md)
- [docs/advanced_modeling.md](docs/advanced_modeling.md)
- [docs/reference_construction.md](docs/reference_construction.md)
- [docs/sculpt_workflows.md](docs/sculpt_workflows.md)
- [docs/cloth_patterns.md](docs/cloth_patterns.md)
- [docs/construction_validation.md](docs/construction_validation.md)

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

Phase 5B asset workflow smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase5b-full
```

The Phase 5B smoke creates temporary `OVERTLI_PHASE5B_*` scene data, exports only its smoke-created object under `.overtli_blender/exports/`, imports only that exported local file into a smoke collection, writes asset scan/manifests/dependency reports/previews/scene kits under `.overtli_blender/`, runs an allowlisted asset workflow batch, and removes exact smoke-created scene data. It does not download provider assets, run raw code, import arbitrary user files, overwrite by default, or delete arbitrary files.

Phase 6A Geometry Nodes procedural workflow smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase6a-full
```

The Phase 6A smoke creates temporary `OVERTLI_PHASE6A_*` objects, materials, collections, node groups, and Geometry Nodes modifiers; exercises capability detection, node group and modifier inspection, template discovery, safe template group creation, allowlisted recipe creation, modifier input setting, procedural rope/scatter/curve/radial/panel/cable/terrain generators, validation, previews, scene kits, and workflow batches; then removes exact smoke-created scene data. It writes ignored Geometry Nodes recipes, previews, workflow manifests, scene kit data, and verification snapshots under `.overtli_blender/`. It does not run raw code, download provider assets, apply modifiers destructively, create arbitrary node graphs, or touch arbitrary user objects.

Phase 6B addon and knowledge workflow smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase6b-full
```

The Phase 6B smoke exercises addon status/list/info, local Blender Python API docs inspection/index/search, verified snippet metadata, local skill pack manifests, review package export/validation, and a non-destructive advanced knowledge workflow batch. It uses the local docs mirror at `memory_bank/research/blender_python_reference_5_1_md` when present and writes ignored knowledge, snippet, skill pack, addon-dev, and review artifacts under `.overtli_blender/`. It does not install addons by default, does not enable/disable/remove addons, does not execute snippets by default, does not publish private docs, does not run raw code, and does not run provider downloads.

Generated verification and workspace artifacts are written under `.overtli_blender/` and are ignored by git.

Phase 9A animation, rigging, and simulation smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase9a-full
```

The Phase 9A smoke creates temporary `OVERTLI_PHASE9A_*` scene data, exercises action, keyframe, F-Curve, driver DSL validation, rig, pose, shot, simulation, and motion validation paths, and verifies that driver creation, pose application, simulation preview, and cache clearing require approval by default.

## Upstream Credit

This project builds on the original BlenderMCP work by Siddharth Ahuja and the BlenderMCP community.
Historical names are retained only where they are part of upstream attribution or repository history.
