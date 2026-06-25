# Project Workspace

Phase 7C adds project-aware runtime commands that distinguish a saved `.blend` from an unsaved scene.

Saved `.blend` files resolve the project root from the blend file parent directory. Unsaved files return structured options and do not silently use the repo root for user scene artifacts unless an explicit preferred root or fallback is provided.

The standard project layout is:

```text
.overtli/
assets/
textures/source/
textures/working/
textures/baked/
textures/packed/
references/images/
imports/
exports/
renders/previews/
renders/finals/
backups/
```

`initialize_project_workspace` creates this layout and writes `.overtli/project.json`. Saving an unsaved `.blend`, overwriting a manifest, restoring a backup, and saving a project under a new file name require confirmation or approval.

Primary commands: `get_project_status`, `resolve_project_workspace`, `initialize_project_workspace`, `validate_project_layout`, `repair_project_layout`, `register_blend_file`, `save_project_as`, `create_project_backup`, `restore_project_backup`, and `collect_project_dependencies`.
