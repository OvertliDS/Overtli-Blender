# Packaged Addon Migration

Phase 10A makes `overtli_blender_addon/` the canonical Blender-side runtime.

The root `addon.py` is intentionally small and delegates to the package entrypoint. Runtime code is organized under:

- `overtli_blender_addon/core.py` for shared Blender-side imports, fallbacks, constants, and pure helpers.
- `overtli_blender_addon/runtime/` for socket server, dispatcher, command context, response, logging, approval, operation, and registry bridges.
- `overtli_blender_addon/services/` for domain services such as scene, materials, assets, geometry nodes, baking, modeling, animation, workspace, diagnostics, addon management, and product UX.
- `overtli_blender_addon/ui/`, `preferences.py`, `operators.py`, and `registration.py` for Blender UI and lifecycle.
- `overtli_blender_addon/adapters/` and `shared/` for compatibility and addon-local contracts.

The addon zip is built from an allowlist and has one install root: `overtli_blender_addon/`. It must not include repository-private docs, tests, scripts, Memory Bank files, generated artifacts, AI review tooling, `.env`, or API mirrors.
