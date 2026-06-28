# MCP Setup

Overtli-Blender has two pieces that must both be running for AI models to use Blender tools:

1. The Blender addon package, installed from the addon zip, starts the local socket server inside Blender.
2. The Python MCP package, installed in the repository virtual environment, exposes stdio tools to MCP clients and forwards tool calls to the Blender socket.

For ChatGPT.com browser developer-mode connectors, use the HTTP bridge guide instead: [chatgpt_browser_connector.md](chatgpt_browser_connector.md). Browser connectors cannot launch the local stdio command directly; use the local HTTP MCP bridge plus either OpenAI Secure MCP Tunnel or a public HTTPS tunnel ending in `/mcp`.

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

## 2A. Optional ChatGPT.com Browser Connector HTTP Bridge

Local stdio setup above remains the default for Codex and local MCP clients. For ChatGPT.com browser testing, start the additional Streamable HTTP bridge with the root launcher:

```powershell
.\Start_ChatGPT_MCP_Server.bat
```

Keep that BAT window open while ChatGPT.com is using the connector. Press `Ctrl+C` or close the window to stop the attached server process.

Equivalent manual command:

```powershell
.\.venv\Scripts\python -m overtli_blender.server --transport http --host 127.0.0.1 --port 2091 --profile browser_full_standard --remote-safety browser_standard
```

Documented connector endpoint:

```text
http://127.0.0.1:2091/mcp
```

Use a local-development tunnel to provide an HTTPS URL for ChatGPT:

```text
https://<your-tunnel-host>/mcp
```

Fast Server URL mode:

```powershell
.\Start_ChatGPT_Server_URL.bat
```

This starts/reuses the local HTTP bridge with public tunnel Host headers allowed for this mode, starts a Cloudflare quick tunnel, and prints the exact public HTTPS `/mcp` URL to paste into ChatGPT with `Connection: Server URL` and `Authentication: No Auth`. Browser defaults are `browser_full_standard`, `browser_standard`, and approval mode `ask_for_destructive_only`, so trusted local structured writes work without raw Python while high-risk tools remain gated. If `cloudflared` is missing, the launcher downloads a local copy to ignored `tools\cloudflared.exe`; it does not install a global tool. If ChatGPT previously triggered `Invalid Host header` or `421 Misdirected Request`, close old launcher windows and rerun this BAT so the bridge starts with the current Server URL mode.

Server URL mode is intentionally disposable. Cloudflare quick-tunnel hostnames usually change every time the launcher starts, and ChatGPT may not let you edit an existing connector's Server URL. If the URL changes, delete/recreate that test connector. The launcher stops stale quick-tunnel processes for this repo/port before creating a new URL so old Server URL connectors do not keep working by accident. For a stable connector that does not require changing a public URL, use `.\Start_ChatGPT_Connector.bat` with OpenAI Secure MCP Tunnel and configure ChatGPT with the stable `tunnel_...` ID instead.

For OpenAI Secure MCP Tunnel, run the tunnel client in a second terminal:

```powershell
$env:CONTROL_PLANE_API_KEY = "<runtime-api-key>"
$env:OVERTLI_TUNNEL_ID = "tunnel_0123456789abcdef0123456789abcdef"
.\Start_OpenAI_MCP_Tunnel.bat
```

Or use the combined ChatGPT launcher, which prompts for missing tunnel credentials, remembers them locally, starts the local HTTP bridge when needed, and then runs OpenAI `tunnel-client`:

```powershell
$env:CONTROL_PLANE_API_KEY = "<runtime-api-key>"
$env:OVERTLI_TUNNEL_ID = "tunnel_0123456789abcdef0123456789abcdef"
.\Start_ChatGPT_Connector.bat
```

In that mode, configure ChatGPT with the tunnel ID from OpenAI Platform. The ID starts with `tunnel_`; it is not the connector name. For ngrok, Cloudflare Tunnel, or hosted HTTPS, configure ChatGPT with the public HTTPS `/mcp` URL.

Stable Server URL mode with ngrok:

```powershell
$env:OVERTLI_NGROK_URL = "https://your-domain.ngrok-free.dev"
.\Start_ChatGPT_Ngrok_URL.bat
```

Use this when OpenAI Secure MCP Tunnel is failing but you still need one consistent ChatGPT `Server URL`. The launcher starts/reuses the local HTTP bridge, runs `ngrok http --url <your-stable-domain> http://127.0.0.1:2091`, saves the stable URL under `.overtli_blender/local/chatgpt_ngrok_url/server_url.txt`, and keeps the tunnel alive while the window remains open. It requires an ngrok account, local ngrok sign-in already configured, and an assigned static/dev domain. Set `OVERTLI_NGROK_EXE` if `ngrok.exe` is not on `PATH` or copied to `tools\ngrok.exe`.

The launcher normalizes copied values, so `OVERTLI_NGROK_URL` may be a bare domain, a quoted URL, or the full ChatGPT Server URL ending in `/mcp`; it passes only the base ngrok domain to `ngrok --url`. It also cleans up stale local ngrok tunnels for the same stable domain before launching and retries once if ngrok reports the endpoint is already online.

The combined launcher stores the runtime API key using Windows DPAPI under `.overtli_blender/local/chatgpt_connector/` and stores the tunnel ID in ignored local config. To clear local launcher state:

```powershell
.\Reset_ChatGPT_Connector_Credentials.bat
```

See [chatgpt_browser_connector.md](chatgpt_browser_connector.md) for tunnel setup, ChatGPT developer-mode steps, MCP Inspector validation, and browser smoke prompts.

After changing tool visibility or profile defaults, refresh connector metadata in ChatGPT settings. If prepare/approve works but nothing changes or `object_count remains 0`, verify `execute_approved_operation` and `approve_and_execute_operation` are visible, reload the Blender addon, and run the browser mutation smoke.

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
