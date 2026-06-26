# Threat Model

Primary Phase 10A risks:

- Accidentally packaging private repository files.
- Importing Blender-only modules from MCP server startup.
- Copying a partial addon entrypoint without its package.
- Allowing unknown commands to fail without actionable remediation.
- Expanding permissions through preferences or third-party addon interop without approval.

Mitigations are enforced through allowlist packaging, import-boundary tests, dispatcher fault-injection probes, release checks, and docs lockdown.
