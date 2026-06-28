# Command Registry

`src/overtli_blender/runtime/command_registry.py` owns the Phase 7B
`CommandSpec` registry.

Each spec records command identity, handler mapping, category, tool pack,
operation type, risk, approval requirements, progress/cancel support,
capabilities, filesystem/network access, schema references, and smoke flags.

The registry is built from the shared safety map plus governance commands. This
keeps existing socket command names stable while making command metadata
discoverable and testable.

`get_command_registry_report` reports coverage and response-envelope migration
state. In Phase 7B, governance commands use the new envelope while legacy
commands remain compatibility responses.

## Browser Cleanup And Batch Contracts

The browser-facing profile includes explicit planning and verification commands
for destructive or geometry-sensitive scene work:

- `scene_cleanup_plan` is the preferred first step for reset/cleanup requests.
- `clear_scene` defaults to `dry_run=true`, generated `OVERTLI_*` scope, and
  `confirm=false`. Confirmed cleanup must be explicit and scoped.
- `create_box`, `create_primitive_object(dimensions=...)`, and
  `transform_object_dimensions` use final dimensions instead of requiring the
  client to reason from Blender scale values.
- `validate_ground_contact`, `align_object_to_surface`, and
  `validate_scene_composition` provide lightweight geometry checks that can be
  run before and after a verified batch.

`run_verified_edit_batch` accepts the preferred operation shape:

```json
{
  "command_name": "create_box",
  "params": {
    "name": "OVERTLI_Box",
    "dimensions": [2.0, 1.0, 0.5],
    "location": [0.0, 0.0, 0.0],
    "anchor": "bottom_center"
  }
}
```

Legacy `{ "type": "...", "params": {...} }` and `{ "command": "...", ... }`
forms remain accepted for compatibility. Clients should prefer `command_name`
because schema errors can then report the expected operation shape and supported
commands more clearly. Use `prevalidate_only=true` to validate a whole batch
without mutating the Blender scene.

Destructive batch operations require both a confirmed destructive operation
parameter such as `confirm=true` and top-level
`batch_allow_destructive=true`. Tool discovery also treats destructive intent
(`delete`, `clear`, `reset`, `purge`, `cleanup`, `remove`) specially so unrelated
creation tools are not recommended as substitutes for cleanup commands.
