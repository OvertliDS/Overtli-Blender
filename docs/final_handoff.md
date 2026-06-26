# Final Handoff

Phase 10B is the release-candidate closure path for Overtli-Blender v0.1.0. The Python distribution is `overtli-blender`. This phase does not add new Blender creative tools. It proves the modular addon package, clean artifacts, MCP setup, docs, and local release gates.

## Required Local Gates

Run from the repository root:

```powershell
.\.venv\Scripts\python -m compileall addon.py main.py src scripts tests overtli_blender_addon
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python scripts\release_check.py --fast
.\.venv\Scripts\python scripts\release_candidate_check.py --json
.\.venv\Scripts\python scripts\addon_modularity_check.py --json
.\.venv\Scripts\python scripts\build_addon_zip.py --mode package --verify --json
.\.venv\Scripts\python scripts\import_boundary_check.py --json
.\.venv\Scripts\python scripts\docs_lockdown_check.py --json
.\.venv\Scripts\python scripts\security_audit.py --json
.\.venv\Scripts\python scripts\compatibility_check.py --json
.\.venv\Scripts\python scripts\performance_check.py --fast --json
.\.venv\Scripts\python scripts\fault_injection_check.py --json
.\.venv\Scripts\python scripts\chatgpt_connector_check.py --static --json
.\.venv\Scripts\python scripts\export_diagnostic_bundle.py
.\.venv\Scripts\python scripts\final_release_handoff.py --json
```

The final handoff writes ignored artifacts under:

```text
.overtli_blender/final_handoff/
```

Do not commit generated handoff folders, diagnostic bundles, release candidate manifests, addon zips, wheels, sdists, review packages, or Drive mirrors.

## Live Blender Checks

With Blender open, the packaged addon enabled, and the socket server running:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --release-candidate-full
```

The package-status smoke prints `runtime_mode`, `addon_package_path`, `addon_version`, `server_command_count`, `tool_registry_count`, `packaged_runtime_status`, and `single_file_shim_status`.

## AI Review Package And Drive Mirror

The local review package workflow is private/ignored. If configured locally, run it only after the test and release gates pass:

```powershell
.\Create_AI_Review_Zip.bat
```

Then sync the generated `Overtli-Blender_AIReview_Drive/` mirror through the local workflow. Do not edit the Drive mirror directly. Do not commit `AIReview.config.json`, review packager state files, generated zips, or the Drive mirror.

## Ship Decision

`scripts/final_release_handoff.py --json` writes `ship_decision.json` with one of:

- `ship_candidate`: all required local gates passed.
- `needs_fixes`: non-blocking gaps remain and must be fixed before release.
- `blocked`: package, import-boundary, security, or privacy gates failed.

Do not create a GitHub tag, GitHub release, PyPI upload, or public release artifact until the user explicitly approves v0.1.0 release handoff.

## ChatGPT Browser Connector

Phase 10C adds local/tunnel developer-mode connector prep for ChatGPT.com:

```powershell
.\.venv\Scripts\python -m overtli_blender.server --transport http --host 127.0.0.1 --port 2091 --profile chatgpt_browser_default --remote-safety remote_browser_safe
.\.venv\Scripts\python scripts\chatgpt_connector_check.py --static --json
```

Manual ChatGPT browser validation requires an HTTPS tunnel URL ending in `/mcp`; see [chatgpt_browser_connector.md](chatgpt_browser_connector.md). Keep browser permissions approval-heavy.
