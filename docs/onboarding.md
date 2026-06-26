# Onboarding

The onboarding checklist reports whether the runtime is ready for common Overtli-Blender workflows.

Checks include package availability, MCP entrypoint, addon/socket live status, version metadata, project workspace, approved roots, active tool profile, writable logs/cache, docs index, and diagnostic bundle tooling.

Commands:

- `get_setup_status`
- `run_onboarding_checklist`

The checklist is read-only by default. `fix_safe_defaults=true` requires confirmation before any preference writes and does not expand broad permissions.
