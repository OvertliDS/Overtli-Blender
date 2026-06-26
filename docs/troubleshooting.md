# Troubleshooting

## Blender Does Not Connect

Verify the addon socket is listening:

```powershell
Test-NetConnection -ComputerName localhost -Port 9876
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status
```

If the port is closed, open Blender, enable `Overtli-Blender`, and start the socket server from the sidebar panel. If Blender is running an older installed copy, rebuild and reinstall the addon zip from `.overtli_blender/release/addon_zip/`.

## MCP Client Cannot Find Tools

Re-check the MCP server command:

```powershell
.\.venv\Scripts\python -m overtli_blender.server
```

For Codex, the stanza belongs in `C:\Users\antju\.codex\config.toml`:

```toml
[mcp_servers."overtli-blender"]
command = "D:\\AI\\custom mcp\\Overtli-Blender\\.venv\\Scripts\\python.exe"
args = [ "-m", "overtli_blender.server" ]
```

Restart or reload the MCP client after editing config.

## PATH_NOT_APPROVED

`PATH_NOT_APPROVED` means the operation tried to read or write outside the approved project roots. Use the file access approval or project workspace commands to inspect allowed roots, then retry with a path under an approved root. Do not bypass this by weakening path checks.

## Addon Package Status Fails

Run:

```powershell
.\.venv\Scripts\python scripts\build_addon_zip.py --mode package --verify --json
.\.venv\Scripts\python scripts\addon_modularity_check.py --json
.\.venv\Scripts\python scripts\import_boundary_check.py --json
```

Then reinstall the generated addon zip in Blender and restart the socket server. A valid status smoke reports `PACKAGED_RUNTIME_LIVE_VERIFIED`; without live Blender it should remain `PACKAGED_RUNTIME_STATIC_VERIFIED` or `PACKAGED_RUNTIME_MANUAL_PENDING`.

## Release Gate Fails

Run the failing script directly with `--json` when available. Generated artifacts stay under `.overtli_blender/`, `dist/`, or `build/` and should remain ignored.
