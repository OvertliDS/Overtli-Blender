# Install

This project has two local install surfaces: the Python MCP package and the packaged Blender addon zip.

For complete MCP client setup, including virtual environment creation and MCP client registration, see [mcp_setup.md](mcp_setup.md).

## Virtual Environment

From the repository root:

```powershell
cd "D:\AI\custom mcp\Overtli-Blender"
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
```

If the Python launcher is not available, create `.venv` with any installed Python 3.10+ interpreter:

```powershell
"C:\Path\To\Python312\python.exe" -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
```

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

For MCP clients, register the venv Python module command:

```powershell
.\.venv\Scripts\python -m overtli_blender.server
```

Codex TOML example:

```toml
[mcp_servers."overtli-blender"]
command = "D:\\AI\\custom mcp\\Overtli-Blender\\.venv\\Scripts\\python.exe"
args = [ "-m", "overtli_blender.server" ]

[mcp_servers."overtli-blender".env]
BLENDER_HOST = "localhost"
BLENDER_PORT = "9876"
```

Quick checks:

```powershell
.\.venv\Scripts\python -c "import overtli_blender; print(overtli_blender.__name__)"
.\.venv\Scripts\python -m compileall addon.py main.py src scripts tests overtli_blender_addon
.\.venv\Scripts\python -m pytest
```

## Blender Addon

Use [addon_install.md](addon_install.md) for Blender UI steps. Build and install the package zip; do not copy the repository-root entrypoint by itself.

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
