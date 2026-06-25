# Install

This project has two local install surfaces: the Python MCP package and the Blender addon entrypoint.

## Python Package

From the repository root:

```powershell
.\.venv\Scripts\python -m pip install -e .
```

For development and package builds:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

The package name is `overtli-blender`, the import package is `src/overtli_blender`, and the console command is:

```powershell
overtli-blender
```

Quick checks:

```powershell
.\.venv\Scripts\python -c "import overtli_blender; print(overtli_blender.__name__)"
.\.venv\Scripts\python -m compileall addon.py main.py src scripts tests
.\.venv\Scripts\python -m pytest
```

## Blender Addon

Use [addon_install.md](addon_install.md) for Blender UI steps. `addon.py` remains the single-file Blender entrypoint.

## Socket Smoke

After the addon socket server is running in Blender on `localhost:9876`:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --phase6b-full
```

The full Phase 2 through Phase 6B smoke flags are documented in [runtime_smoke.md](runtime_smoke.md).

## Release Checks

Fast local gate:

```powershell
.\.venv\Scripts\python scripts\release_check.py --fast
```

Full local gate when build dependencies are installed:

```powershell
.\.venv\Scripts\python scripts\release_check.py --full
```

## Troubleshooting

- If `python -m build` is missing, install dev dependencies with `.\.venv\Scripts\python -m pip install -e ".[dev]"`.
- If socket smoke cannot connect, confirm the addon is enabled and the socket server is started in Blender.
- CI does not run live Blender smoke. Run live smoke manually with Blender open.
- Generated files under `.overtli_blender/`, `dist/`, `build/`, caches, Memory Bank files, and private planning docs are not release inputs.
