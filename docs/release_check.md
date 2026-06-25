# Release Checks

Phase 7A adds local and CI checks for release readiness without publishing packages or requiring Blender GUI in CI.

## Fast Check

```powershell
.\.venv\Scripts\python scripts\release_check.py --fast
```

The fast check runs:

- Python version check.
- Git status command availability.
- `compileall` for `addon.py`, `main.py`, `src`, `scripts`, and `tests`.
- `pytest`.
- `import overtli_blender`.
- `pyproject.toml` package, version, and console-script metadata checks.
- Privacy and stale identity scans.
- `addon.py` syntax/identity check.
- Smoke harness static check.

JSON output:

```powershell
.\.venv\Scripts\python scripts\release_check.py --fast --json
```

## Full Check

```powershell
.\.venv\Scripts\python scripts\release_check.py --full
```

The full check adds:

- `scripts/build_python_package.py` when the `build` package is installed.
- `scripts/build_addon_zip.py`.
- `scripts/export_diagnostic_bundle.py`.

If the `build` package is missing, install dev dependencies:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

## Individual Scripts

```powershell
.\.venv\Scripts\python scripts\build_python_package.py
.\.venv\Scripts\python scripts\build_addon_zip.py
.\.venv\Scripts\python scripts\export_diagnostic_bundle.py
.\.venv\Scripts\python scripts\check_install_docs.py
```

## CI

`.github/workflows/ci.yml` runs:

- Static tests on Python 3.10, 3.11, and 3.12.
- Editable install and package import checks.
- `scripts/release_check.py --fast --json`.
- Local wheel/sdist build validation.
- Privacy/stale identity checks.

CI does not:

- start Blender.
- run live socket smoke.
- publish to PyPI.
- publish GitHub Releases.
- upload private artifacts.
- require secrets.

## Manual Live Smoke

Live Blender smoke remains manual:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase2-full
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase3-full
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase4a-full
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase4b-full
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase5a-full
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase5b-full
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase6a-full
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase6b-full
```

## Privacy Exclusions

Release and diagnostic scripts exclude private/generated areas by default:

- `memory_bank/`
- `.overtli_blender/` except generated release/diagnostic summaries
- `.venv/`
- tests and caches from addon zip payloads
- Blender API docs mirror
- review zips and generated release bundles
- `AGENTS.md` unless intentionally made public later
- `.env` and credential-like paths
