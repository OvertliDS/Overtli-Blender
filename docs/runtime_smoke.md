# Runtime Smoke

Use this checklist after starting Blender with the Overtli-Blender addon enabled.

Prerequisite:
- Open Blender.
- Enable the addon in `Edit > Preferences > Add-ons`.
- Start the addon socket server from the Overtli-Blender UI.

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py
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
- Optional screenshot smoke passes only when a visible viewport is available.
- Optional script registry smoke registers, lists, executes, and clears a harmless temporary script.
- Optional provider status smoke returns status-only responses without downloading assets.
- Optional Geometry Nodes status smoke reports status only and does not create or modify geometry.
- Optional code execution smoke uses a harmless print-only payload and should not mutate scene data, files, or network state.
- Optional strict-mode smoke only applies when Blender was started in strict mode and verifies that a harmless code execution request is blocked.

If something fails, paste the full console output back into the task so the runtime issue can be isolated quickly.

Generated Phase 2, Phase 3, Phase 4A, and Phase 4B artifacts are local evidence only. The smoke harness passes the repository root as `artifact_root`, so live smoke artifacts are written under `.overtli_blender/` in this checkout even when Blender loaded the addon from the user add-ons directory. They are ignored by git via `.overtli_blender/` and should not be committed.
