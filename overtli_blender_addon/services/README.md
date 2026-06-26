# Addon Services

This directory owns Blender-side service implementations grouped by domain.

Examples:

- `scene.py`: scene observation, intelligence, and scene edits.
- `materials.py`: material, shader graph, texture, preview, and workflow services.
- `geometry_nodes.py`: Geometry Nodes templates, recipes, modifiers, validation, preview, and workflow services.
- `workspace.py`: workspace, scene diff, task, reference, and file/project services.
- `product_ux.py`: preferences, profiles, onboarding, error catalog, dashboard, and product-polish services.

New Blender-side behavior should be added to the relevant service module and wired through `runtime/socket_server.py` without moving implementation back into `addon.py`.
