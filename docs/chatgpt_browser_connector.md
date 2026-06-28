# ChatGPT Browser Connector

This guide is for ChatGPT.com developer-mode connector testing. It is different from local stdio MCP setup in [mcp_setup.md](mcp_setup.md).

Local stdio clients can launch:

```powershell
.\.venv\Scripts\python -m overtli_blender.server
```

ChatGPT.com cannot launch that local command. It needs either an OpenAI Secure MCP Tunnel connection or an HTTPS-reachable MCP endpoint:

```text
https://<your-tunnel-host>/mcp
```

Use this only for local/tunnel development. Do not expose local Blender control broadly. For a trusted local project, use ChatGPT's persistent allow option after reviewing the connector; Overtli-Blender still gates destructive, raw-code, delete, provider, file-write, and addon-lifecycle paths internally.

## Official Docs Alignment

This setup follows current OpenAI docs:

- Apps SDK MCP server concepts: <https://developers.openai.com/apps-sdk/concepts/mcp-server>
- Connect from ChatGPT: <https://developers.openai.com/apps-sdk/deploy/connect-chatgpt>
- Apps SDK quickstart: <https://developers.openai.com/apps-sdk/quickstart>
- Developer mode: <https://developers.openai.com/api/docs/guides/developer-mode>
- Secure MCP Tunnel: <https://developers.openai.com/api/docs/guides/secure-mcp-tunnels>
- Testing with MCP Inspector and golden prompts: <https://developers.openai.com/apps-sdk/deploy/testing>

The relevant OpenAI flow is: build an MCP server, expose Streamable HTTP or SSE through a supported connection path, create the connector in ChatGPT settings, then test with MCP Inspector and ChatGPT developer mode. Streamable HTTP is the preferred local bridge path here.

Important distinction:

- `Start_ChatGPT_MCP_Server.bat` starts the local Overtli-Blender HTTP MCP bridge only.
- `Start_OpenAI_MCP_Tunnel.bat` runs OpenAI's Secure MCP Tunnel client and forwards that local MCP bridge to a ChatGPT tunnel.
- `Start_ChatGPT_Connector.bat` is the combined ChatGPT launcher; it starts the local HTTP bridge when needed, then runs OpenAI's `tunnel-client`.
- `Start_ChatGPT_Server_URL.bat` is the combined Server URL launcher; it starts the local HTTP bridge when needed, then runs a Cloudflare quick tunnel and prints the public HTTPS `/mcp` URL.
- `Start_ChatGPT_Ngrok_URL.bat` is the stable Server URL launcher for ngrok static/dev domains; it starts the local HTTP bridge when needed, then runs `ngrok http --url <domain> http://127.0.0.1:2091`.
- ngrok or Cloudflare Tunnel are alternate public-HTTPS tunnel choices and do not use OpenAI's `tunnel-client`.

## Local Prerequisites

From the repository root:

```powershell
cd "D:\AI\custom mcp\Overtli-Blender"
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\python -c "import overtli_blender; import overtli_blender.server; print('ok')"
```

## Blender Side

1. Build and install the addon zip.
2. Enable `Overtli-Blender` in Blender.
3. Start the socket server from the Overtli-Blender sidebar.
4. Confirm the local socket is reachable on `localhost:9876`.

```powershell
Test-NetConnection -ComputerName localhost -Port 9876
```

## Start The HTTP MCP Bridge

Recommended root launcher:

```powershell
.\Start_ChatGPT_MCP_Server.bat
```

The BAT starts the HTTP bridge in the same console window. Keep that window open while ChatGPT.com is using the connector. Press `Ctrl+C` or close the window to stop the attached server process; it intentionally does not spawn a detached background server.

Equivalent manual command from the repository root:

```powershell
.\.venv\Scripts\python -m overtli_blender.server --transport http --host 127.0.0.1 --port 2091 --profile browser_full_standard --remote-safety browser_standard
```

Local endpoints:

```text
http://127.0.0.1:2091/mcp
http://127.0.0.1:2091/health
http://127.0.0.1:2091/metadata
http://127.0.0.1:2091/.well-known/oauth-protected-resource/mcp
http://127.0.0.1:2091/.well-known/oauth-authorization-server
```

The `/mcp` endpoint is the connector URL path. `/health` is only for debugging. The well-known OAuth discovery URLs are present so OpenAI `tunnel-client doctor` and MCP discovery clients can validate the protected-resource metadata shape for the local bridge.

For OpenAI Secure MCP Tunnel, you can skip the separate local-bridge terminal and use the combined launcher in [Option A](#option-a-openai-secure-mcp-tunnel). Keep this separate bridge launcher for local HTTP testing, MCP Inspector checks, ngrok/Cloudflare tunnels, or debugging.

## Test Locally

Check health:

```powershell
curl http://127.0.0.1:2091/health
```

Run the static connector readiness check:

```powershell
.\.venv\Scripts\python scripts\chatgpt_connector_check.py --static --json
```

Use MCP Inspector before ChatGPT browser testing:

```powershell
npx @modelcontextprotocol/inspector@latest
```

Inspector URL:

```text
http://127.0.0.1:2091/mcp
```

Use Inspector to list tools and call low-risk tools such as `search_tools`, `get_tool_spec`, `get_runtime_dashboard`, and scene summary/status tools. If Blender is not connected, the HTTP server can still start, but tool calls that need Blender should return connection guidance rather than pretending success.

## Browser Test Workflow Expectations

For scene-building prompts in ChatGPT, prefer a plan/execute/verify loop:

1. Call `create_scene_plan` or create a workspace task/todo list before mutating the scene.
2. Use `scene_cleanup_plan` before any reset request. Use `clear_scene(confirm=true, dry_run=false, ...)` only after the plan is reviewed and scoped.
3. Use `create_box`, `create_primitive_object(..., dimensions=...)`, and `transform_object_dimensions` when final dimensions matter.
4. Use `validate_ground_contact`, `validate_scene_composition`, and verification snapshots after edits. Mark tasks `verified` only when checks or screenshots support that status.
5. For unsaved `.blend` sessions, let workspace and verification tools write to the user-local temporary workspace. Use `promote_temp_workspace_to_project(confirm=true, project_root=...)` when the user chooses a real project folder.

The preferred `run_verified_edit_batch` operation schema is:

```json
{
  "command_name": "create_box",
  "params": {
    "name": "OVERTLI_Test_Box",
    "dimensions": [2.0, 1.0, 0.5],
    "anchor": "bottom_center"
  }
}
```

Legacy `type` and `command` operation keys remain compatible, but new browser prompts should use `command_name`. To check a batch without changing Blender, pass `prevalidate_only=true`.

For Blender 5.1 color-management differences, call `get_supported_color_management` first or pass `auto_compatible=true` to `set_render_settings` so known names such as Filmic/AgX preferences are mapped to a supported enum when possible.

## Expose To ChatGPT

Use one local-development tunnel option after the local HTTP MCP bridge is running.

### Option A: OpenAI Secure MCP Tunnel

Use this if your OpenAI workspace has Secure MCP Tunnel access. This flow uses a tunnel ID in ChatGPT, not a copied public HTTPS URL.

1. In OpenAI Platform tunnel settings, create or select a tunnel for this connector.
2. Download/install `tunnel-client` and make sure it is on `PATH`.
3. Create a runtime API key for `tunnel-client`.
4. In a new PowerShell window, set the required values, or let `Start_ChatGPT_Connector.bat` prompt for them. The tunnel ID must be the OpenAI-generated ID from Platform tunnel settings, not the connector name. It should look like `tunnel_0123456789abcdef0123456789abcdef`. When prompted, the launcher saves the runtime API key in local Windows DPAPI-encrypted storage and saves the tunnel ID in ignored local config under `.overtli_blender/local/chatgpt_connector/`.

```powershell
$env:CONTROL_PLANE_API_KEY = "<runtime-api-key>"
$env:OVERTLI_TUNNEL_ID = "tunnel_0123456789abcdef0123456789abcdef"
```

5. Run the combined root launcher:

```powershell
.\Start_ChatGPT_Connector.bat
```

The combined launcher starts the local MCP bridge if it is not already healthy, initializes `tunnel-client` with OpenAI's `sample_mcp_remote_no_auth` profile sample, runs `doctor --explain`, and then runs the tunnel in the foreground. If it started the local bridge itself, it stops that bridge when the tunnel exits. The bridge exposes OAuth discovery metadata for tunnel-client readiness, but it does not issue local OAuth login material; the tunnel connection and ChatGPT connector configuration remain the exposure boundary.

To clear the locally remembered runtime API key and tunnel ID:

```powershell
.\Reset_ChatGPT_Connector_Credentials.bat
```

This only removes local launcher state. It does not revoke API keys or delete tunnels in OpenAI Platform.

Alternative two-terminal mode:

```powershell
.\Start_ChatGPT_MCP_Server.bat
.\Start_OpenAI_MCP_Tunnel.bat
```

`Start_OpenAI_MCP_Tunnel.bat` uses the downloaded `tools\tunnel-client.exe` when present, otherwise it falls back to `tunnel-client` on `PATH`. It checks that `http://127.0.0.1:2091/health` is reachable, initializes a `tunnel-client` profile named `overtli-blender-http` with `sample_mcp_remote_no_auth`, runs `tunnel-client doctor --explain`, then runs the tunnel client in the foreground.

Keep both windows open:

```text
Combined mode: .\Start_ChatGPT_Connector.bat
Two-terminal mode, window 1: .\Start_ChatGPT_MCP_Server.bat
Two-terminal mode, window 2: .\Start_OpenAI_MCP_Tunnel.bat
```

In ChatGPT connector setup, choose the Tunnel connection mode if available and use the tunnel ID from OpenAI Platform.

### Option B: Server URL Through Cloudflare Quick Tunnel

Use this path when OpenAI Secure MCP Tunnel is blocked by tunnel ID, workspace, or 401 control-plane issues.

This is a disposable test mode, not the stable daily connector path. Cloudflare quick-tunnel hostnames usually change on each launcher run. If ChatGPT will not let you edit an existing connector's Server URL, delete/recreate that test connector with the new printed URL. The launcher stops stale quick-tunnel processes for this repo/port before starting a new tunnel; if an old Server URL still works, an older `cloudflared` process is still running. For stable repeated use, prefer [Option A](#option-a-openai-secure-mcp-tunnel), where ChatGPT stores the OpenAI tunnel ID instead of a changing public URL.

Recommended root launcher:

```powershell
.\Start_ChatGPT_Server_URL.bat
```

The launcher:

- starts the local HTTP bridge at `http://127.0.0.1:2091/mcp` if it is not already healthy
- starts that bridge with public tunnel Host headers allowed for this mode, because Cloudflare quick tunnels forward a dynamic `*.trycloudflare.com` Host header
- uses `tools\cloudflared.exe`, `cloudflared` on `PATH`, or downloads a local ignored `tools\cloudflared.exe`
- starts `cloudflared tunnel --url http://127.0.0.1:2091`
- prints and saves the exact ChatGPT Server URL, for example `https://example.trycloudflare.com/mcp`
- opens ChatGPT connector settings
- stops the Cloudflare tunnel and any bridge process it started when the window closes

In ChatGPT connector setup, use:

```text
Connection: Server URL
Server URL: https://<your-trycloudflare-domain>/mcp
Authentication: No Auth
```

Keep the launcher window open while creating and testing the connector. Close it when finished; that stops the public tunnel and the printed URL will no longer be usable. The normal local bridge launcher and OpenAI Secure MCP Tunnel launcher keep the MCP package's default localhost Host-header protection. Only this Server URL quick-tunnel launcher uses `--allow-public-tunnel-hosts`.

Advanced: pass `-AllowParallelTunnels` to `scripts\start_chatgpt_server_url.ps1` only when intentionally testing multiple simultaneous Cloudflare quick-tunnel URLs for the same local bridge.

### Option C: Stable Server URL Through Ngrok

Use this when OpenAI Secure MCP Tunnel is blocked but you need one consistent ChatGPT `Server URL`.

Prerequisites:

- an ngrok account
- local ngrok sign-in already configured for `ngrok.exe`
- an assigned static/dev domain in ngrok, for example `https://example.ngrok-free.dev`
- `ngrok.exe` on `PATH`, copied to `tools\ngrok.exe`, or referenced through `OVERTLI_NGROK_EXE`

Recommended root launcher:

```powershell
$env:OVERTLI_NGROK_URL = "https://example.ngrok-free.dev"
.\Start_ChatGPT_Ngrok_URL.bat
```

The launcher accepts a bare domain, a quoted URL copied from PowerShell, or a full ChatGPT Server URL ending in `/mcp`; it normalizes these to the base ngrok domain before starting `ngrok`.

The launcher:

- starts the local HTTP bridge at `http://127.0.0.1:2091/mcp` if it is not already healthy
- starts that bridge with public tunnel Host headers allowed for this mode
- runs `ngrok http --url <your-stable-domain> http://127.0.0.1:2091`
- saves the ChatGPT URL to `.overtli_blender/local/chatgpt_ngrok_url/server_url.txt`
- stops stale local ngrok tunnels for the same domain before starting a new one, using ngrok's local API when available and a process fallback when Windows hides the command line, unless `-AllowParallelTunnels` is supplied
- retries once if ngrok returns `ERR_NGROK_334` because the endpoint is already online

Use these ChatGPT connector settings:

```text
Connection: Server URL
Server URL: https://<your-ngrok-domain>/mcp
Authentication: No Auth
```

Unlike Cloudflare quick-tunnel mode, the hostname should remain the same across launcher restarts as long as the ngrok domain remains assigned to your account.

### Option C: Manual Public HTTPS Tunnel

Use ngrok, Cloudflare Tunnel, or an equivalent user-approved tunnel/hosting option to expose:

```text
http://127.0.0.1:2091
```

Then use a public HTTPS connector URL ending in `/mcp`, for example:

Example placeholder:

```text
https://<your-tunnel-host>/mcp
```

Do not commit tunnel config, local tunnel logs, private tunnel identifiers, or generated diagnostics.

## ChatGPT.com Setup

1. Open ChatGPT.com.
2. Go to `Settings -> Apps & Connectors -> Advanced settings -> Developer mode`.
3. Enable developer mode.
4. Go to `Settings -> Connectors -> Create`.
5. For OpenAI Secure MCP Tunnel, choose the Tunnel connection mode and select or paste the tunnel ID from OpenAI Platform. For Server URL mode, use:

```text
Connector name: Overtli-Blender
Description: Local Blender control and inspection through Overtli-Blender MCP.
Connector URL: https://<your-tunnel-host>/mcp
```

6. Create the connector.
7. Start a new chat.
8. Click `+`.
9. Click `More`.
10. Choose `Overtli-Blender`.

## Permissions

Recommended permission behavior:

```text
Always allow for trusted local projects; destructive operations stay internally gated
```

or the closest available option that asks before making changes.

The default browser profile is `browser_full_standard`. The legacy `chatgpt_browser_default` name remains a backward-compatible alias. Browser mode is mutation-capable for safe structured writes: primitive creation, transforms, collections, materials, cameras, lights, verification snapshots, verified edit batches, and presentation workflow batches are visible without requiring raw Python.

Browser permission profile is `browser_standard`. The legacy `remote_browser_safe` name remains an alias. Browser approval mode defaults to `ask_for_destructive_only`, so normal structured scene creation does not loop on approvals while destructive work remains gated.

Tool profile, permission profile, and approval mode are separate:

- Tool profile controls visible and organized tools.
- Permission profile controls allowed categories.
- Approval mode controls when an allowed operation asks before execution.

Browser MCP `approve_operation` executes after approval by default so ChatGPT does not dead-end when it prepares a structured write and then only calls the approval tool. Call it with `execute_after_approval=false` only when you intentionally want approval metadata without dispatch. `execute_approved_operation(approval_id)` can also load the stored command/params from the approval record, and `approve_and_execute_operation` remains the explicit one-step path. All execution paths refuse expired, denied, already executed, changed, hidden, or capability-blocked operations.

`remote_browser_safe` keeps network-exposed mode approval-heavy:

- raw Python is not visible in the browser profile
- external provider downloads are not visible by default
- file delete execution is hidden
- addon operator execution is hidden
- visible tools are bounded
- path/private-value details should stay redacted in logs and docs

## Manual Browser Smoke

After Inspector passes, test the golden prompts in [chatgpt_connector_prompts.md](chatgpt_connector_prompts.md).

Record:

- whether ChatGPT picked the expected tool
- what arguments were passed
- whether approval prompts appeared for changes
- whether negative prompts were refused or routed to approval

## Troubleshooting

- If `/health` is degraded, start Blender and the addon socket server.
- If the BAT closes immediately, confirm `.venv\Scripts\python.exe` exists and rerun `.\.venv\Scripts\python -m pip install -e .`.
- If `Start_OpenAI_MCP_Tunnel.bat` reports `tunnel-client was not found`, install/download OpenAI `tunnel-client` and add it to `PATH`.
- If `Start_OpenAI_MCP_Tunnel.bat` reports a missing `CONTROL_PLANE_API_KEY` or `OVERTLI_TUNNEL_ID`, create those in OpenAI Platform tunnel settings and set them in the tunnel terminal.
- If it says `invalid tunnel ID`, replace names such as `overtli-blender` with the actual Platform tunnel ID, which starts with `tunnel_`.
- If `tunnel-client doctor` reports `oauth_metadata` failed, rerun `.\Start_ChatGPT_Connector.bat` after this launcher update. The launcher now forces `sample_mcp_remote_no_auth`; older generated profiles may have used the DCR sample and expected OAuth metadata from the local MCP bridge.
- If you saved the wrong key or tunnel ID, run `.\Reset_ChatGPT_Connector_Credentials.bat` and start the connector again.
- If ChatGPT cannot create the connector, verify the public URL is HTTPS and ends in `/mcp`.
- If the terminal shows `Invalid Host header` and `421 Misdirected Request`, close old launcher windows and rerun `.\Start_ChatGPT_Server_URL.bat`; the current Server URL launcher passes `--allow-public-tunnel-hosts`.
- If using Secure MCP Tunnel, verify the ChatGPT connector is configured with the tunnel ID and that `tunnel-client doctor --profile overtli-blender-http --explain` passes.
- If tools are missing, restart the HTTP bridge and refresh the connector in ChatGPT settings.
- If safe write tools are missing in ChatGPT, restart the HTTP bridge with `--profile browser_full_standard --remote-safety browser_standard`, then use `ChatGPT -> Settings -> Connectors -> Overtli-Blender -> Refresh` to refresh connector metadata.
- If prepare/approve works but nothing changes, the browser MCP wrapper or installed addon is stale. Update the server/addon, refresh connector metadata, reload the Blender addon, and run `scripts\chatgpt_connector_check.py --browser-write-profile --json`.
- If `object_count remains 0` after approval, the operation was approved but not executed, or the Blender socket is not running. Run `scripts\smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status`, then `--include-browser-mutation-path`, then `--include-browser-approval-execution-path`.
- If the approval-execution smoke reports `Unknown command type: approve_and_execute_operation`, rebuild and reinstall `.overtli_blender\release\addon_zip\overtli_blender_addon_0.1.0.zip`, restart the addon socket, and rerun the smoke. Refreshing connector metadata alone does not replace Blender's installed addon package.
- If too many tools appear, verify `--profile browser_full_standard` is in the HTTP bridge command and that dangerous tools remain hidden.
- If high-risk actions appear directly, stop the bridge and rerun with `--remote-safety browser_standard`.
