# Runtime Smoke

## Phase 9B Product UX Smoke

Phase 9B adds a non-destructive product UX smoke:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase9b-full
```

The scenario checks preferences, tool profiles, visible tool budget, bundled skill packs, read-only addon interop boundaries, error catalog remediation, runtime dashboard, approval queue, recent operations, onboarding, and product polish batch.

Individual flags are also available:

```text
--include-preferences-status
--include-tool-profile-ux
--include-bundled-skills
--include-addon-interop-readonly
--include-error-catalog
--include-runtime-dashboard
--include-onboarding-checklist
--include-product-polish-batch
```

The Phase 9B smoke does not expand permissions, execute third-party addon code, run raw Python, delete files, or write outside approved generated workspace locations.

## Phase 9A

Run the contained Phase 9A animation, rigging, driver, pose, shot, and simulation smoke after refreshing or reloading the Blender addon:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase9a-full
```

Phase 9A smoke flags:

- `--include-animation-system`
- `--include-action-library`
- `--include-fcurve-editing`
- `--include-nla-workflow`
- `--include-driver-dsl`
- `--include-rig-template`
- `--include-pose-library`
- `--include-shot-workflow`
- `--include-simulation-workflow`
- `--include-motion-validation`
- `--phase9a-full`

`--phase9a-full` creates only `OVERTLI_PHASE9A_*` smoke data and checks safe action, keyframe, F-Curve, driver DSL validation, rig, pose, shot, simulation, and motion validation paths. Driver creation, pose application, simulation preview, and cache clearing are verified as approval-gated by default.

## Phase 8A

Run the contained Phase 8A texture baking smoke after refreshing or reloading the Blender addon:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase8a-full
```

Phase 8A smoke flags:

- `--include-bake-capabilities`
- `--include-bake-preflight`
- `--include-bake-target-images`
- `--include-native-bake`
- `--include-derived-bake`
- `--include-selected-to-active-bake`
- `--include-channel-packing`
- `--include-baked-material`
- `--include-bake-cleanup-plan`
- `--include-verified-bake-workflow`
- `--phase8a-full`

`--phase8a-full` creates smoke-scoped objects, materials, image targets, project-local texture folders, and cleanup plans under ignored `.overtli_blender/phase8a_smoke/`. Native bake execution is runtime-dependent and reports unsupported/error states honestly instead of claiming fake success.

## Phase 8B

Run the contained Phase 8B advanced modeling smoke after refreshing or reloading the Blender addon:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase8b-full
```

Phase 8B smoke flags:

- `--include-modeling-capabilities`
- `--include-mesh-schema`
- `--include-profile-modeling`
- `--include-curve-construction`
- `--include-modifier-construction`
- `--include-reference-construction`
- `--include-sculpt-workflow`
- `--include-cloth-patterns`
- `--include-construction-validation`
- `--include-construction-cleanup-plan`
- `--phase8b-full`

`--phase8b-full` creates only `OVERTLI_PHASE8B_*` smoke data and checks modeling capabilities, mesh schema validation/creation, profile extrusion/lathe, beveled curves, hard-surface panels, modifier stacks, reference construction planning, shape-key sculpt setup, cloth panels/pins/collision setup, construction validation, and cleanup planning. Sculpt stroke playback and cloth preview/cache commands are verified as approval-gated by default.

## Phase 7C

Run the contained Phase 7C project-runtime smoke after refreshing or reloading the Blender addon:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase7c-full
```

The scenario creates an ignored project-local workspace under `.overtli_blender/phase7c_smoke/`, initializes the standard project layout, checks file policy, writes and reads a project text file, creates and links a task, records a scene revision marker, imports a generated tiny reference PNG, calibrates reference landmarks, measures simple object geometry, plans a rename, and plans cache/file cleanup without destructive filesystem execution.

Use this checklist after starting Blender with the Overtli-Blender addon enabled.
The Python package and console command are `overtli-blender`.

Prerequisite:
- Open Blender.
- Enable the addon in `Edit > Preferences > Add-ons`.
- Start the addon socket server from the Overtli-Blender UI.

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py
```

Fast non-Blender release gate:

```powershell
.\.venv\Scripts\python scripts\release_check.py --fast
```

Optional checks:

```powershell
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-safety-status
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-scene-index
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-selection-info
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-scene-health
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-object-deep-info
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-screenshot-pack
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-verification-snapshot
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --phase2-full
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-edit-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-material-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-modifier-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-collection-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-verified-edit-batch
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-workspace-safety-diff
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --phase3-full
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-material-intelligence
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-material-channel-schema
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-material-templates
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-procedural-material
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-custom-material
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-texture-map-slots
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-shader-graph
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-material-preview
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-material-workflow-batch
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --phase4a-full
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-selection-deep-info
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-vertex-group-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-shape-key-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-lattice-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-deformation-modifier-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-region-deformation
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-deformation-workflow-batch
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --phase4b-full
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-timeline-info
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-animation-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-camera-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-lighting-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-render-settings
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-render-still
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-contact-sheet
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-turntable
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-preview-animation
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-compositor-ops
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-presentation-batch
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --phase5a-full
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-asset-formats
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-asset-scan
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-scene-assets
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-dependency-report
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-asset-manifest
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-import-export
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-scene-kit
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-asset-preview
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-asset-workflow-batch
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --phase5b-full
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-geometry-nodes-capabilities
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-geometry-nodes-intelligence
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-geometry-node-templates
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-geometry-node-recipe
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-procedural-assets
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-scatter-system
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-curve-generator
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-radial-array-system
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-panel-generator
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-geometry-nodes-preview
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-geometry-nodes-workflow-batch
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --phase6a-full
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-addon-status
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-addon-list
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-api-docs-inspect
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-api-docs-index
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-api-docs-search
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-snippet-library
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-skill-pack
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-review-package
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-advanced-knowledge-batch
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --phase6b-full
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-screenshot
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-script-registry
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-provider-status
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-geometry-nodes-status
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-code-execution
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-safety-status --expect-strict-blocks
```

This smoke talks directly to the addon socket and does not require MCP client setup.

Success criteria:
- The default smoke prints `PASS` lines for `get_scene_info`, `get_shared_context`, `get_operation_history`, `list_object_handles`, `list_material_handles`, and `list_context_scripts`.
- Optional safety status smoke reports the current mode and policy summary.
- Optional Phase 2 scene index, selection info, scene health, and object deep info smokes return structured JSON and do not mutate scene data.
- Optional Phase 2 screenshot pack and verification snapshot smokes write local generated artifacts under `.overtli_blender/verification/`.
- `--phase2-full` runs the default smoke plus safety status, Phase 2 inspection, screenshot pack, and verification snapshot checks. It does not run provider downloads, Geometry Nodes creation, raw code execution, or script execution.
- `--phase3-full` runs a contained Phase 3 scenario: it creates a unique `OVERTLI_PHASE3_SMOKE_<timestamp>` collection, a cube, a material, a bevel modifier, a duplicate, a verified edit batch, before/after verification snapshots, scene/object inspection, task workspace entries, todos, operation journal entries, scene snapshots, scene diff, user-change detection, rollback, and cleanup for only the smoke-created object and collection names.
- `--include-workspace-safety-diff` runs only the master Phase 3 workspace, todo, journal, scene diff, user-change detection, and rollback checks.
- Phase 3 smoke does not run raw code, does not download provider assets, does not import/export files, and does not delete arbitrary user objects.
- Phase 3 generated verification and workspace artifacts are written under `.overtli_blender/` and remain ignored by git.
- `--phase4a-full` runs a contained Phase 4A material workflow: it creates a unique `OVERTLI_PHASE4A_SMOKE_<timestamp>` collection, two primitives, PBR/template/procedural/custom materials, texture-map-slot validation, shader graph inspection and allowlisted node editing, material preview artifacts, material workflow batch snapshots, scene health/index checks, and cleanup for only the smoke-created object, collection, and material names.
- Phase 4A smoke writes material preview manifests under `.overtli_blender/material_previews/` and verification snapshots under `.overtli_blender/verification/`. It may reference ignored placeholder texture paths under `.overtli_blender/material_test_textures/`.
- Phase 4A smoke does not run raw code, does not download assets, does not bake textures, does not run provider generation, and does not delete arbitrary user objects or materials.
- Phase 4A cleanup succeeds only when remaining `OVERTLI_PHASE4A_*` objects, collections, and materials are all empty lists.
- `--phase4b-full` runs a contained Phase 4B method, asset, region, deformation, and sculpt workflow: it creates temporary `OVERTLI_PHASE4B_*` objects, materials, an image, a collection, a vertex group, shape keys, a lattice, and a deformation modifier; exercises method plans, playbooks, tricks knowledge, anti-pattern rules, modifier recipes, asset scan/preview, style material creation, paintable texture setup, deep selection info, UV inspection, measurements, confidence scoring, vertex group operations, shape key offsets, lattice updates, proportional deformation, sculpt mask intent, shape-key sculpt workflow, region deformation, and deformation workflow batches; then cleans up exact smoke-created data.
- Phase 4B smoke writes verification artifacts under `.overtli_blender/verification/`, does not run raw code, does not download assets, does not run provider generation, does not apply modifiers destructively, and does not touch arbitrary user objects.
- Phase 4B cleanup succeeds only when remaining `OVERTLI_PHASE4B_*` objects, collections, materials, images, lattices, vertex groups, and shape keys are all empty lists.
- `--phase5a-full` runs a contained Phase 5A presentation workflow: it creates temporary `OVERTLI_PHASE5A_*` scene data; exercises timeline inspection, bounded timeline updates, camera creation/framing, lighting setup, active camera control, object/camera/light/material animation, animation deep info, render settings, smoke-clamped still render, contact sheet manifest, turntable setup, bounded preview frame artifacts, compositor/pass presets, presentation workflow batch snapshots, and scene health; then cleans up exact smoke-created scene data.
- Phase 5A smoke writes render artifacts under `.overtli_blender/renders/`, presentation batch manifests under `.overtli_blender/presentation/`, and verification snapshots under `.overtli_blender/verification/`.
- Phase 5A smoke does not run raw code, does not download assets, does not run provider generation, does not run high-cost full animations, does not create arbitrary compositor graphs, and does not touch arbitrary user objects.
- Phase 5A cleanup succeeds only when remaining `OVERTLI_PHASE5A_*` objects, collections, and materials are all empty lists.
- `--phase5b-full` runs a contained Phase 5B asset workflow: it creates temporary `OVERTLI_PHASE5B_*` scene data, detects supported import/export formats, scans the local `assets/` folder, inventories scene assets, writes dependency and asset manifests, creates a preview, exports the smoke-created object to `.overtli_blender/exports/`, imports only that exported file into a smoke collection, creates and validates a scene kit under `.overtli_blender/scene_kits/`, runs an allowlisted asset workflow batch, checks scene health, and cleans exact smoke-created scene data.
- Phase 5B smoke writes generated files under `.overtli_blender/assets/`, `.overtli_blender/imports/`, `.overtli_blender/exports/`, `.overtli_blender/scene_kits/`, `.overtli_blender/dependency_reports/`, `.overtli_blender/renders/`, and `.overtli_blender/verification/`.
- Phase 5B smoke does not run raw code, does not download provider assets, does not run provider generation, does not import arbitrary user files, does not write outside `.overtli_blender/` by default, and does not delete arbitrary files.
- Phase 5B cleanup succeeds only when remaining `OVERTLI_PHASE5B_*` objects, collections, materials, images, actions, and libraries are all empty lists. Generated files under `.overtli_blender/` may remain as ignored evidence.
- `--phase6a-full` runs a contained Phase 6A Geometry Nodes workflow: it creates temporary `OVERTLI_PHASE6A_*` objects, collections, materials, node groups, and modifiers; detects Geometry Nodes capabilities; lists node groups/modifiers; discovers templates; creates safe template and allowlisted recipe node groups; applies a non-destructive Geometry Nodes modifier; sets modifier inputs; creates rope, scatter, curve, radial, panel, cable, and terrain procedural assets; validates node groups; writes preview, scene-kit, and workflow batch artifacts; checks scene index/health; and cleans exact smoke-created scene data.
- Phase 6A smoke writes generated files under `.overtli_blender/geometry_nodes/`, `.overtli_blender/scene_kits/`, and `.overtli_blender/verification/`.
- Phase 6A smoke does not run raw code, does not download provider assets, does not apply modifiers destructively, does not create arbitrary node graphs, and does not touch arbitrary user objects.
- Phase 6A cleanup succeeds only when remaining `OVERTLI_PHASE6A_*` objects, collections, materials, node groups, and modifiers are all empty lists. Generated files under `.overtli_blender/` may remain as ignored evidence.
- `--phase6b-full` runs a contained Phase 6B addon and knowledge workflow: it checks addon management status, lists addons, inspects one addon, inspects the local Blender Python API docs mirror, builds a public-safe API index, searches API topics, creates and validates a metadata-only verified snippet, creates and validates a local skill pack, exports and validates a privacy-filtered review package, and runs a non-destructive advanced knowledge batch.
- Phase 6B smoke writes generated files under `.overtli_blender/knowledge/`, `.overtli_blender/addon_dev/`, and `.overtli_blender/review_packages/`.
- Phase 6B smoke uses the local docs mirror if present, does not install addons by default, does not enable/disable/remove addons, does not execute snippets by default, does not publish private docs, does not run raw code, and does not run provider downloads.
- `--phase7b-full` runs Phase 7B governance checks: status, tool pack discovery, keyword tool search, tool spec lookup, permission profile, capability validation, metadata-only approval prepare/approve/deny, pending approvals, operation status/list, log status, and command registry coverage.
- Phase 7B smoke is metadata/status-only. It does not run raw code, provider downloads, or destructive execution, and it does not mutate user data.
- Optional screenshot smoke passes only when a visible viewport is available.
- Optional script registry smoke registers, lists, executes, and clears a harmless temporary script.
- Optional provider status smoke returns status-only responses without downloading assets.
- Optional Geometry Nodes status smoke reports status only and does not create or modify geometry.
- Optional code execution smoke uses a harmless print-only payload and should not mutate scene data, files, or network state.
- Optional strict-mode smoke only applies when Blender was started in strict mode and verifies that a harmless code execution request is blocked.

If something fails, paste the full console output back into the task so the runtime issue can be isolated quickly.

Generated Phase 2, Phase 3, Phase 4A, Phase 4B, Phase 5A, Phase 5B, Phase 6A, and Phase 6B artifacts are local evidence only. The smoke harness writes live smoke artifacts under `.overtli_blender/` in this checkout. They are ignored by git via `.overtli_blender/` and should not be committed.
