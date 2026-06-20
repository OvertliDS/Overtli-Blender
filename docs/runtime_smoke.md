# Runtime Smoke

Use this checklist after starting Blender with the Blender MCP addon enabled.

Prerequisite:
- Open Blender.
- Enable the addon in `Edit > Preferences > Add-ons`.
- Start the addon socket server from the existing Blender MCP UI.

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py
```

Optional checks:

```powershell
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-screenshot
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-script-registry
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-provider-status
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-safety-status
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-geometry-nodes-status
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-code-execution
.\.venv\Scripts\python scripts/smoke_blender_addon_socket.py --include-safety-status --expect-strict-blocks
```

Success criteria:
- The default smoke prints `PASS` lines for `get_scene_info`, `get_shared_context`, `get_operation_history`, `list_object_handles`, `list_material_handles`, and `list_context_scripts`.
- Optional screenshot smoke passes only when a visible viewport is available.
- Optional script registry smoke registers, lists, executes, and clears a harmless temporary script.
- Optional provider status smoke returns status-only responses without downloading assets.
- Optional safety status smoke reports the current compatibility/audit/strict mode and policy summary.
- Optional Geometry Nodes status smoke reports status only and does not create or modify geometry.
- Optional code execution smoke uses a harmless print-only payload and should not mutate scene data, files, or network state.
- Optional strict-mode smoke only applies when Blender was started in strict mode and verifies that a harmless code execution request is blocked.

If something fails, paste the full console output back into the task so the runtime issue can be isolated quickly.
