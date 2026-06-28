# Runtime Preferences

Phase 9B adds a structured runtime preference model for Overtli-Blender product UX. Phase 10D extends it with approval-mode defaults for browser and local usage.

Preferences cover project behavior, approved filesystem roots, security toggles, artifacts, MCP socket defaults, knowledge roots, tool profiles, providers, and diagnostics. Runtime commands expose schema, current values, validation, updates, and reset previews:

- `get_preferences_schema`
- `get_runtime_preferences`
- `validate_runtime_preferences`
- `update_runtime_preferences`
- `reset_runtime_preferences`

Permission expansion is approval-gated. Adding approved roots, enabling raw Python, enabling addon interoperability, enabling provider downloads, or increasing the permission profile returns an approval-required response unless `confirm=true` is supplied through the MCP approval workflow.

Phase 10D separates tool profile, permission profile, and approval mode:

- local default tool profile: `full_standard`
- local default permission profile: `standard`
- local default approval mode: `ask_for_high_destructive`
- browser default tool profile: `browser_full_standard`
- browser default permission profile: `browser_standard`
- browser default approval mode: `ask_for_destructive_only`
- approval timeout: `900` seconds

Supported approval modes are `always_ask`, `ask_for_medium_high`, `ask_for_high_destructive`, `ask_for_destructive_only`, `full_access_developer`, and `read_only`. Changing approval mode to a less restrictive value requires confirmation. Browser safe structured writes are enabled by `browser_connector_write_policy = safe_structured_writes_enabled`; raw Python, provider downloads, file delete, external writes, and addon lifecycle changes retain explicit approval requirements.

Default local development persistence is `.overtli_blender/config/runtime_preferences.json`. Project-specific persistence may use `.overtli/config.json`.

Sensitive values are not stored in scene data and sensitive preference keys are redacted from command output.
