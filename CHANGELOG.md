# Changelog

## Phase 10C - ChatGPT Browser Connector and Remote MCP Bridge

- Added Streamable HTTP MCP bridge startup flags while preserving stdio as the default local MCP transport.
- Added `chatgpt_browser_default` and `remote_browser_safe` profiles for compact browser connector discovery and approval-heavy remote use.
- Added ChatGPT browser connector docs, prompt checklist, metadata JSON, static/live connector check script, and release/docs gate coverage.
- Added `/health`, `/metadata`, and documented `/mcp` endpoint behavior for local tunnel development.

## Phase 10B - Final RC Closure and v0.1.0 Handoff Prep

- Added final addon modularity, import boundary, and handoff aggregate scripts.
- Extended release-candidate checks with Phase 10B package, import, docs, security, compatibility, performance, and fault gates.
- Added final handoff, release artifact, known limitation, and troubleshooting docs.
- Added static tests for Phase 10B scripts, docs, clean addon zip boundaries, CI readiness, and MCP setup docs.
- Kept Phase 10B feature-frozen: no new Blender creative capability breadth, no publishing, no tagging.

## Phase 10A - Modular Addon Package and Release-Candidate Hardening

- Moved the Blender addon runtime out of the root entrypoint and into `overtli_blender_addon/`.
- Split addon code into core, runtime, registration, preferences, UI, operators, adapters, shared helpers, and domain service modules.
- Made `scripts/build_addon_zip.py` package-first with allowlist contents, manifest hashes, JSON/list output, and zip verification.
- Added compatibility, performance, security, fault-injection, docs-lockdown, migration-audit, and release-candidate check surfaces.
- Updated static tests to inspect the packaged addon runtime as the source of truth.

## Phase 9B - Product UX, Preferences, Skill Packs, and Addon Interoperability

- Added runtime preferences schema, persistence, validation, and approval-gated permission expansion.
- Added built-in tool profiles, tool-pack visibility controls, visible tool budgets, and profile recommendations.
- Added bundled skill pack library, search, recommendations, activation, and readiness checks.
- Added read-only third-party addon source inspection with AST parsing and no source execution.
- Added approval-required addon operator invocation planning boundary.
- Added user-facing error catalog, remediation steps, onboarding checks, runtime dashboard, approval queue summary, recent operation summary, and product polish batch.
- Added Phase 9B smoke flags and public docs for the new UX surfaces.

## Unreleased

- Added Phase 9A advanced animation, rigging, drivers, simulation, pose/action library, and shot workflow command surfaces.
- Added action inspection/management, batch keyframe insertion, F-Curve editing, NLA track/strip workflows, allowlisted driver DSL, rig templates, IK/constraint/custom-property helpers, pose snapshots/assets, shot plans, simulation inspection/configuration, cache approval gates, and motion validation.
- Added Phase 9A MCP wrappers, command registry metadata, tool packs, smoke flags, docs, and static tests.
- Added Phase 8B advanced modeling, sculpt setup, cloth pattern, reference construction, and construction validation command surfaces.
- Added validated mesh schema creation, profile/curve workflows, non-destructive modifier construction, hard-surface panel and pipe helpers, and approval-gated sculpt/cloth/cache cleanup paths.
- Added Phase 8A texture baking and image resource pipeline command surface.
- Added bake preflight, target image creation, native/derived/approximated classification, channel packing metadata, baked texture validation, baked material variants, and approval-gated bake cleanup planning.
- Added Phase 8A smoke flags and public docs for texture baking, image resources, and channel packing.
- Added Phase 7C project runtime foundations: project workspace resolution, approved-root file access policy, cache retention planning, task graph and scene revision tracking, reference image workflow scaffolding, spatial measurement commands, and safe rename planning.
- Added Phase 7C MCP wrapper modules, command registry metadata, tool packs, smoke flags, and static tests.

All notable public Overtli-Blender changes are summarized here. Private planning files, generated review packages, Memory Bank content, and local diagnostics are intentionally excluded from release artifacts.

## Unreleased / Current Development

### Phase 7B - Runtime Governance, Tool Packs, and Packaged Addon Foundation
- Added a source-owned `CommandSpec` registry for existing socket commands and governance commands.
- Added tool pack discovery/search, permission profiles, two-phase approval records, operation response envelopes, operation runtime skeletons, and structured log helpers.
- Added governance MCP wrappers and socket command support without renaming existing tools.
- Added Phase 7B smoke flags, release-check gates, public governance docs, and initial packaged addon build layout.

### Phase 7A - Release Hardening and Distribution Readiness
- Added local release readiness checks through `scripts/release_check.py`.
- Added public-safe addon zip packaging through `scripts/build_addon_zip.py`.
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
