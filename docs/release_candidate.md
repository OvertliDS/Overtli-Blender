# Release Candidate

Run:

```powershell
.\.venv\Scripts\python scripts\release_candidate_check.py --json
```

The check writes:

```text
.overtli_blender/release_candidate/phase10b_release_candidate_manifest.json
```

The manifest records migration audit, addon modularity evidence, package zip verification, import boundary evidence, compatibility, performance, security, fault-injection, docs lockdown, packaged runtime status fields, failed checks, and ship decision.

For the final aggregate handoff, run:

```powershell
.\.venv\Scripts\python scripts\final_release_handoff.py --json
```

That writes `handoff_manifest.json`, `ship_decision.json`, artifact pointers, smoke summary, limitations, and next steps under `.overtli_blender/final_handoff/`.

Live release-candidate smoke requires Blender with the packaged addon enabled and the socket server started:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --release-candidate-full
```

For MCP client setup, including `.venv` creation and AI model access through stdio registration, see [mcp_setup.md](mcp_setup.md).

For ChatGPT.com browser connector readiness, run:

```powershell
.\.venv\Scripts\python scripts\chatgpt_connector_check.py --static --json
```

The browser connector setup is documented in [chatgpt_browser_connector.md](chatgpt_browser_connector.md). Its connector URL must end in `/mcp`, and live ChatGPT testing remains manual through a local-development HTTPS tunnel.
