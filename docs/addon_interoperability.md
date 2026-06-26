# Addon Interoperability

Phase 9B adds safe third-party addon source inspection.

The scanner is read-only and uses Python AST parsing. It does not import third-party addon modules, run `register()`, enable addons, install addons, or rewrite source.

Commands:

- `list_addon_source_roots`
- `scan_addon_sources_readonly`
- `get_addon_source_summary`
- `search_addon_operators`
- `search_addon_panels`
- `search_addon_properties`
- `plan_addon_operator_invocation`
- `execute_approved_addon_operator`

Scanning requires an approved addon-source root. Results summarize `bl_info`, operators, panels, and properties without returning full source dumps.

Third-party operator invocation planning is metadata-only. Execution is high risk, strict-mode blocked, and requires exact operator target plus explicit approval.
