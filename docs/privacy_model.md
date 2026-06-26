# Privacy Model

The Blender addon zip is public-runtime-only. It excludes private planning, local diagnostics, generated release artifacts, Memory Bank files, API mirrors, AI review tooling, environment files, logs, caches, and tests.

The MCP Python package and Blender addon zip are separate artifacts. Shared runtime code included in the addon zip is limited to selected pure Python modules under `overtli_blender_addon/_shared_runtime/`.
