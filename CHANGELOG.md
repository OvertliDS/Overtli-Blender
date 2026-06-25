# Changelog

All notable public Overtli-Blender changes are summarized here. Private planning files, generated review packages, Memory Bank content, and local diagnostics are intentionally excluded from release artifacts.

## Unreleased / Current Development

### Phase 7A - Release Hardening and Distribution Readiness
- Added local release readiness checks through `scripts/release_check.py`.
- Added public-safe single-file addon zip packaging through `scripts/build_addon_zip.py`.
- Added wheel/sdist build validation through `scripts/build_python_package.py`.
- Added public-safe diagnostic bundle export through `scripts/export_diagnostic_bundle.py`.
- Added install documentation checks through `scripts/check_install_docs.py`.
- Added non-publishing GitHub Actions CI for static tests, package/import checks, and privacy checks.
- Documented install, addon install, release checks, and development workflows.

## Phase 6B - Addon, Knowledge, Snippets, Skill Packs, and Review Export
- Added safe addon management status/list/info surfaces and confirmation-gated addon lifecycle command surfaces.
- Added addon development skeleton, static validation, and local addon zip packaging helpers.
- Added local Blender API docs inspection, indexing, search, and topic lookup from a private docs mirror when present.
- Added verified snippet metadata, local skill packs, privacy-filtered review package export/validation, and advanced knowledge workflow batches.
- Verified static tests and live Phase 6B socket smoke after addon refresh.

## Phase 6A - Geometry Nodes and Procedural Workflows
- Added Geometry Nodes capability detection, node group/modifier inspection, template discovery, template-first node group creation, allowlisted recipes, modifier input updates, procedural generators, validation, previews, scene kits, and workflow batches.

## Phase 5B - Assets, Import/Export, Scene Kits, and Rigging Basics
- Added asset format detection, bounded local asset scans, scene asset inventory, dependency reports, asset manifests, `.blend` append/link, local model import/export, previews/contact sheets, reusable scene kits, dependency validation/collection, and asset workflow batches.
- Added static coverage for driver, armature, pose, and basic simulation command surfaces.

## Phase 5A - Animation and Presentation
- Added timeline inspection, animation workflows, camera creation/framing, lighting setup, render settings, still/contact-sheet/preview artifacts, turntables, compositor/pass presets, and presentation workflow batches.

## Phase 4B - Selection, Deformation, and Workflow Intelligence
- Added method planning, operation playbooks, tricks knowledge, anti-pattern rules, modifier recipes, asset scans/previews, style/PBR material helpers, texture-folder import, paintable texture setup, UV map inspection, measurements, vertex groups, shape keys, lattices, proportional deformation, sculpt mask intent, shape-key sculpt workflow, and deformation workflow batches.

## Phase 4A - Materials and Shaders
- Added material channel schemas, templates, deep material inspection, shader graph inspection/editing, texture map slot binding, procedural/custom material creation, previews, material workflow batches, and confirmed material cleanup.

## Phase 3 - Workspace, Safety, and Diff
- Added task workspace, todo system, operation journal, scene snapshots, scene diff, user-change detection, rollback, and verified scene editing workflows.

## Phase 2 - Scene Intelligence and Verification
- Added richer scene/object/selection inspection, scene health diagnostics, screenshot packs, and verification snapshot manifests.

## Phase 1 - Foundation, Refactor, Safety, and Rebrand
- Established the `overtli-blender` package, `overtli_blender` import path, `overtli-blender` console command, modular MCP tool registration, safety metadata framework, and public/private repository boundary.

## Upstream
- Overtli-Blender builds on the original BlenderMCP work by Siddharth Ahuja and the BlenderMCP community. Historical names are retained only for attribution or negative compatibility checks.
