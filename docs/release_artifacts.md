# Release Artifacts

Generated `overtli-blender` release artifacts are local outputs and are ignored by git.

## Addon ZIP

Build the clean Blender addon package:

```powershell
.\.venv\Scripts\python scripts\build_addon_zip.py --mode package --verify --json
.\.venv\Scripts\python scripts\build_addon_zip.py --mode package --verify --list
```

Expected root entry:

```text
overtli_blender_addon/
```

Allowed contents are the addon package modules, selected bundled shared runtime modules under `overtli_blender_addon/_shared_runtime/`, optional addon manifest/resources, and the generated zip manifest. The zip must exclude `memory_bank/`, `.overtli_blender/`, `tests/`, bulk `docs/`, `scripts/`, root `tools/`, review tooling, generated release artifacts, API mirrors, caches, logs, `.env`, and `AGENTS.md`.

## Python Package

Build wheel and source distribution:

```powershell
.\.venv\Scripts\python scripts\build_python_package.py
```

Outputs are written under `dist/` and are ignored. This script never publishes.

## Diagnostics And Handoff

Export public-safe diagnostics:

```powershell
.\.venv\Scripts\python scripts\export_diagnostic_bundle.py
```

Generate the final handoff:

```powershell
.\.venv\Scripts\python scripts\final_release_handoff.py --json
```

Live runtime smoke remains a separate Blender-dependent check:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status
```

Handoff outputs include `handoff_manifest.json`, `ship_decision.json`, `artifact_manifest.json`, addon zip pointers, diagnostic bundle pointers, `test_summary.json`, `smoke_summary.json`, `known_limitations.md`, and `next_steps.md`.

## Safe To Commit

Commit source, tests, scripts, docs, README, CHANGELOG, and CI changes. Do not commit generated artifacts, private Memory Bank files, review packager state, Drive mirrors, local diagnostics, release candidate output, addon zips, wheel/sdist files, caches, or local `AGENTS.md`.
