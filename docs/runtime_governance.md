# Runtime Governance

Phase 7B adds a governance layer over the existing Blender socket command
surface. It does not rename existing commands or remove atomic tools.

The governance layer provides:

- `CommandSpec` metadata for command discovery, risk, approval, capabilities,
  progress/cancel support, and migration state.
- Tool pack discovery and keyword search.
- Two-phase approval records for high-risk or destructive commands.
- Capability profiles for read-only, standard, trusted project, developer, and
  custom workflows.
- Operation status/cancel/progress skeletons for migrated long-running work.
- Structured log status and redaction metadata.

Existing command responses remain compatible. New governance commands use the
standard operation response envelope. The registry report lists older commands
that still need envelope migration in a future phase.
