# MCP Setup

Overtli-Blender has two pieces that must both be running for AI models to use Blender tools:

1. The Blender addon package, installed from the addon zip, starts the local socket server inside Blender.
2. The Python MCP package, installed in the repository virtual environment, exposes stdio tools to MCP clients and forwards tool calls to the Blender socket.

Do not copy the repository root into Blender. Do not install the root `addon.py` by itself.

## 1. Create The Virtual Environment

From the repository root:

```powershell
cd "D:\AI\custom mcp\Overtli-Blender"
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
```

If `py -3.12` is not available, use the Python 3.10+ interpreter installed on the machine:

```powershell
"C:\Path\To\Python312\python.exe" -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
```

## 2. Install The MCP Package

For normal local use:

```powershell
.\.venv\Scripts\python -m pip install -e .
```

For development, tests, and package builds:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Verify the MCP package imports without importing Blender-only modules:

```powershell
.\.venv\Scripts\python -c "import overtli_blender; import overtli_blender.server; print('ok')"
```

The MCP server command is:

```powershell
.\.venv\Scripts\python -m overtli_blender.server
```

The installed console script is:

```powershell
.\.venv\Scripts\overtli-blender.exe
```

MCP clients usually launch the server themselves through stdio, so you normally register the command instead of keeping a separate terminal open.

## 3. Build And Install The Blender Addon

Build the package zip:

```powershell
.\.venv\Scripts\python scripts\build_addon_zip.py --mode package --verify
```

Install this zip in Blender:

```text
.overtli_blender/release/addon_zip/overtli_blender_addon_0.1.0.zip
```

In Blender:

1. Open `Edit > Preferences > Add-ons > Install`.
2. Select the zip above.
3. Enable `Overtli-Blender`.
4. Open the `Overtli-Blender` sidebar panel.
5. Start the socket server.

The default socket is:

```text
localhost:9876
```

## 4. Register With Codex

Add this stanza to `C:\Users\antju\.codex\config.toml`:

```toml
[mcp_servers."overtli-blender"]
command = "D:\\AI\\custom mcp\\Overtli-Blender\\.venv\\Scripts\\python.exe"
args = [ "-m", "overtli_blender.server" ]

[mcp_servers."overtli-blender".env]
BLENDER_HOST = "localhost"
BLENDER_PORT = "9876"
```

After changing `config.toml`, restart or reload Codex so the MCP tool list refreshes. Registration alone does not guarantee the current session sees the new server.

## 5. Generic MCP Client JSON

For MCP clients that use JSON server configuration:

```json
{
  "mcpServers": {
    "overtli-blender": {
      "command": "D:\\AI\\custom mcp\\Overtli-Blender\\.venv\\Scripts\\python.exe",
      "args": ["-m", "overtli_blender.server"],
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

Use the same command for Claude Desktop, Cursor, or other MCP-compatible clients, adjusted to that client's config file format.

## 6. Verify End To End

With Blender open, the addon enabled, and the socket server started:

```powershell
Test-NetConnection -ComputerName localhost -Port 9876
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --release-candidate-full
```

Expected result:

```text
PASS smoke harness completed
```

## Troubleshooting

- If `Test-NetConnection` fails, start the Overtli-Blender socket server from the Blender sidebar.
- If the MCP client cannot find tools, restart or reload the MCP client after editing its config.
- If `overtli_blender` cannot import, run `.\.venv\Scripts\python -m pip install -e .` again.
- If Blender cannot see the addon, rebuild and reinstall the addon zip; the installed package must contain `overtli_blender_addon/__init__.py` with a top-level `bl_info` entry.
- If a tool call reports connection refused, the MCP server started but the Blender addon socket is not running.
- If path approval blocks an operation with `PATH_NOT_APPROVED`, move the target under an approved project/workspace root or use the project workspace/file access tools to inspect approved roots.
- If package status fails, rebuild/reinstall the addon zip and run `.\.venv\Scripts\python scripts\addon_modularity_check.py --json`, `.\.venv\Scripts\python scripts\import_boundary_check.py --json`, and `.\.venv\Scripts\python scripts\final_release_handoff.py --json`.
