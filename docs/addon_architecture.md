# Addon Architecture

`overtli_blender_addon/` is the Blender addon runtime. The MCP server package under `src/overtli_blender/` remains a separate Python package for stdio tools and client-side wrappers.

Architecture boundaries:

- `addon.py`: thin Blender entrypoint only.
- `overtli_blender_addon/registration.py`: class registration, scene properties, and shutdown cleanup.
- `overtli_blender_addon/runtime/socket_server.py`: socket lifecycle and command execution.
- `overtli_blender_addon/runtime/dispatcher.py`: command dispatch envelope and unknown-command errors.
- `overtli_blender_addon/services/`: Blender-side domain behavior.
- `overtli_blender_addon/adapters/`: version and API compatibility helpers.
- `overtli_blender_addon/shared/`: addon-local constants, schemas, and redaction helpers.

MCP server imports must not import `bpy` or `overtli_blender_addon` at startup.
