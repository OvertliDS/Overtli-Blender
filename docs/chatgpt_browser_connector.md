# ChatGPT Browser Connector

This guide is for ChatGPT.com developer-mode connector testing. It is different from local stdio MCP setup in [mcp_setup.md](mcp_setup.md).

Local stdio clients can launch:

```powershell
.\.venv\Scripts\python -m overtli_blender.server
```

ChatGPT.com cannot launch that local command. It needs an HTTPS-reachable MCP endpoint:

```text
https://<your-tunnel-host>/mcp
```

Use this only for local/tunnel development. Do not expose local Blender control broadly. Keep ChatGPT permissions on `Always ask` or the closest available "ask before making changes" setting.

## Official Docs Alignment

This setup follows current OpenAI docs:

- Apps SDK MCP server concepts: <https://developers.openai.com/apps-sdk/concepts/mcp-server>
- Connect from ChatGPT: <https://developers.openai.com/apps-sdk/deploy/connect-chatgpt>
- Apps SDK quickstart: <https://developers.openai.com/apps-sdk/quickstart>
- Developer mode: <https://developers.openai.com/api/docs/guides/developer-mode>
- Secure MCP Tunnel: <https://developers.openai.com/api/docs/guides/secure-mcp-tunnels>
- Testing with MCP Inspector and golden prompts: <https://developers.openai.com/apps-sdk/deploy/testing>

The relevant OpenAI flow is: build an MCP server, expose Streamable HTTP or SSE over HTTPS, create the connector in ChatGPT settings, then test with MCP Inspector and ChatGPT developer mode. Streamable HTTP is the preferred local bridge path here.

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

Run the HTTP bridge from the repository root:

```powershell
.\.venv\Scripts\python -m overtli_blender.server --transport http --host 127.0.0.1 --port 2091 --profile chatgpt_browser_default --remote-safety remote_browser_safe
```

Local endpoints:

```text
http://127.0.0.1:2091/mcp
http://127.0.0.1:2091/health
http://127.0.0.1:2091/metadata
```

The `/mcp` endpoint is the connector URL path. `/health` is only for debugging.

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

## Expose To ChatGPT

Use one local-development tunnel option:

- OpenAI Secure MCP Tunnel, if available in your workspace.
- ngrok.
- Cloudflare Tunnel.

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
5. Use:

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
Always ask
```

or the closest available option that asks before making changes.

The default browser profile is `chatgpt_browser_default`. It keeps the visible tool list compact, exposes discovery/workflow/status tools, hides raw Python and destructive operations, and pairs with `remote_browser_safe`.

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
- If ChatGPT cannot create the connector, verify the public URL is HTTPS and ends in `/mcp`.
- If tools are missing, restart the HTTP bridge and refresh the connector in ChatGPT settings.
- If too many tools appear, verify `--profile chatgpt_browser_default` is in the HTTP bridge command.
- If high-risk actions appear directly, stop the bridge and rerun with `--remote-safety remote_browser_safe`.
