# Development

## Setup

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

The package identity is:

- distribution: `overtli-blender`
- import package: `src/overtli_blender`
- console command: `overtli-blender`
- addon entrypoint: `addon.py`

## Static Validation

```powershell
.\.venv\Scripts\python -m compileall addon.py main.py src scripts tests
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python scripts\release_check.py --fast
```

## Package Builds

```powershell
.\.venv\Scripts\python scripts\build_python_package.py
.\.venv\Scripts\python scripts\build_addon_zip.py
```

`scripts/build_python_package.py` writes standard Python artifacts under `dist/`. `scripts/build_addon_zip.py` writes ignored addon zip artifacts under `.overtli_blender/release/addon_zip/`.

## Diagnostic Bundles

```powershell
.\.venv\Scripts\python scripts\export_diagnostic_bundle.py
```

Diagnostic bundles are public-safe summaries under `.overtli_blender/diagnostics/`. They do not include Memory Bank content, private docs mirrors, `.env` files, review zips, caches, or `AGENTS.md`.

## Runtime Smoke

Runtime smoke requires Blender with the Overtli-Blender addon enabled and its socket server running on `localhost:9876`.

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase6b-full
```

The smoke harness preserves prior Phase 2 through Phase 6B flags and does not run provider downloads or raw code unless those optional flags are explicitly supplied.
