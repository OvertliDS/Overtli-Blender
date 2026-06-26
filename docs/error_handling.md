# Error Handling

Phase 9B adds a user-facing error catalog with plain-language summaries and remediation steps.

Commands:

- `get_error_catalog`
- `explain_error`
- `get_remediation_steps`

Covered errors include Blender connection failures, unloaded addon state, uninitialized projects, unsaved blends, path approval failures, approval expiry, disabled tool packs, strict-mode blocks, missing objects/materials/UVs, unsupported bake/sculpt/simulation requests, invalid driver DSL, untrusted addon source roots, and cache cleanup that requires a plan.

The catalog is designed to help users recover without hiding technical diagnostics.
