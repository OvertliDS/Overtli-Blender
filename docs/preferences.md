# Runtime Preferences

Phase 9B adds a structured runtime preference model for Overtli-Blender product UX.

Preferences cover project behavior, approved filesystem roots, security toggles, artifacts, MCP socket defaults, knowledge roots, tool profiles, providers, and diagnostics. Runtime commands expose schema, current values, validation, updates, and reset previews:

- `get_preferences_schema`
- `get_runtime_preferences`
- `validate_runtime_preferences`
- `update_runtime_preferences`
- `reset_runtime_preferences`

Permission expansion is approval-gated. Adding approved roots, enabling raw Python, enabling addon interoperability, enabling provider downloads, or increasing the permission profile returns an approval-required response unless `confirm=true` is supplied through the MCP approval workflow.

Default local development persistence is `.overtli_blender/config/runtime_preferences.json`. Project-specific persistence may use `.overtli/config.json`.

Sensitive values are not stored in scene data and sensitive preference keys are redacted from command output.
