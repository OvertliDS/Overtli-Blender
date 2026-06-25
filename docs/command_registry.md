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
