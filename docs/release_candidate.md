# Release Candidate

Run:

```powershell
.\.venv\Scripts\python scripts\release_candidate_check.py --json
```

The check writes:

```text
.overtli_blender/release_candidate/phase10a_release_candidate_manifest.json
```

The manifest records migration audit, package zip verification, compatibility, performance, security, fault-injection, docs lockdown, failed checks, and ship decision.

Live release-candidate smoke requires Blender with the packaged addon enabled and the socket server started:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --release-candidate-full
```

For MCP client setup, including `.venv` creation and AI model access through stdio registration, see [mcp_setup.md](mcp_setup.md).
