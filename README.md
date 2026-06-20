# Overtli-Blender

Overtli-Blender is a local-first Blender MCP addon/server for AI-assisted Blender workflows.
It connects Blender to MCP clients through a socket bridge, with shared context, inspection tools, scripting helpers, provider status checks, Geometry Nodes helpers, raw code execution, and a built-in safety policy.

## What It Does

- Scene and object inspection
- Viewport screenshots
- Shared context, object handles, and material handles
- Script registry management
- Provider status checks for Poly Haven, Sketchfab, and Hyper3D
- Geometry Nodes helpers
- Raw Blender Python execution with safety policy controls
- Safety status inspection
- A local socket smoke harness for runtime verification

## Safety

Raw code execution can run Blender Python inside the current session, so treat it as powerful and potentially destructive.

- Default mode is `compatibility`
- `audit` keeps behavior but adds safety metadata
- `strict` blocks the high-risk command set
- Provider and asset download tools may involve network access or API keys

## Install

Use an editable install during development:

```powershell
python -m pip install -e .
```

The primary console command is:

```powershell
overtli-blender
```

## Blender Addon Setup

1. Open Blender.
2. Install or enable `addon.py` in `Edit > Preferences > Add-ons`.
3. Start the addon socket server from the Blender MCP UI.
4. Leave the socket on `localhost:9876` unless you intentionally changed it.

## Runtime Smoke

The addon socket smoke runs directly against Blender and does not require MCP client setup.

See [docs/runtime_smoke.md](docs/runtime_smoke.md).

## Upstream Credit

This project builds on the original BlenderMCP work by Siddharth Ahuja and the BlenderMCP community.
Historical names are retained only where they are part of upstream attribution or repository history.
