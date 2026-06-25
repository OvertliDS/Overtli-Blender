# Image Resource Pipeline

Phase 8A creates and manages image resources for bake workflows without writing outside approved project roots.

## Texture Folders

- `textures/source/`: user or imported source textures.
- `textures/working/`: intermediate texture work.
- `textures/baked/`: baked texture maps.
- `textures/packed/`: ORM/RMA/MRA/glTF packed maps.

## Image Targets

`create_bake_target_images` creates Blender image datablocks, assigns file paths, sets color-space intent, and optionally creates active image texture nodes on materials.

Color-space intent:

- Color/albedo/emission/combined preview maps use `sRGB`.
- Normal, AO, roughness, metallic, height, curvature, thickness, UV, packed maps, and other data maps use `Non-Color`.

## Save and Validate

`save_baked_textures` saves named Blender images under approved project texture folders and returns file hashes. `validate_baked_textures` checks image presence, dimensions, file existence, non-empty state where available, and color-space metadata.

## Resource Inventory

Optional Phase 8A image resource commands include `list_project_images`, `get_image_resource_info`, and `rename_image_resource`. Datablock rename is direct; file rename remains approval-gated and should use the existing project rename workflow for filesystem moves.
