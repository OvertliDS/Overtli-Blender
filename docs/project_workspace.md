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
.overtli/tasks/
.overtli/manifests/
blend/
screenshots/
verification/
logs/
tasks/
manifests/
```

`initialize_project_workspace` creates this layout and writes `.overtli/project.json`. `repair_project_layout` is the safe path for an existing project folder that does not already follow the Overtli layout: it creates missing standard folders and updates the manifest without requiring the user to move their existing assets first.

Primary commands: `get_project_status`, `get_loaded_project_folder`, `resolve_project_workspace`, `initialize_project_workspace`, `initialize_temp_workspace`, `promote_temp_workspace_to_project`, `validate_project_layout`, `repair_project_layout`, `register_blend_file`, `save_project_as`, `resave_project_folder`, `plan_project_folder_move`, `move_project_folder`, `create_project_backup`, `restore_project_backup`, and `collect_project_dependencies`.

## Storage Model

Project metadata is stored as JSON files, not SQLite. The project manifest lives at `.overtli/project.json`; task and manifest resources live under `.overtli/tasks/` and `.overtli/manifests/`; runtime event logs use JSONL under the ignored runtime log area. The manifest records `storage_backend: "json_files"` and `persistence.sqlite: false` so clients do not need to guess.

## Saved Blend Project Folder

For a saved `.blend`, `get_loaded_project_folder` reports the current project folder as the parent directory of the loaded file, plus the layout status. This is the preferred first check before writing generated assets, references, textures, renders, exports, or task metadata.

`resave_project_folder` saves the current `.blend` into a chosen project folder and repairs the standard layout/manifest in the same operation. Use it when a scene was opened from a loose folder or when an unsaved scene needs a real project home. By default, confirmed resaves collect external image textures into `textures/source/`, relink them as paths relative to the saved `.blend`, and save again so Blender can reload the project portably.

`collect_project_dependencies` can also run as a separate preflight. Without confirmation it reports image dependencies, packed images, missing files, and raw paths. With `copy_external_images=true` and `confirm=true`, it copies external image files into `textures/source/` and relinks them relatively.

## Unsaved Scene Temporary Workspace

Unsaved `.blend` sessions no longer write task, screenshot, verification, or manifest artifacts under the addon install folder or source repository by default. `resolve_project_workspace` and artifact-writing services route unsaved sessions to a user-local temporary workspace:

```text
%LOCALAPPDATA%\Overtli-Blender\temp_workspaces\<session-id>\
```

The fallback order is `%LOCALAPPDATA%`, then `%TEMP%`/`%TMP%`, then the user home directory. `initialize_temp_workspace` creates the standard layout there and returns `temporary: true` metadata so clients can tell that the scene has not yet been promoted to a real project.

Use `promote_temp_workspace_to_project(project_root=..., confirm=true)` when the user chooses a durable project folder. Without confirmation it returns an approval-shaped response and does not copy files or save the `.blend`.

Artifact-writing tools such as workspace tasks, scene snapshots, and verification manifests should use the saved project root when available, explicit `artifact_root` when supplied, or this temporary workspace for unsaved scenes. They should not infer the addon folder as the scene workspace.

## Moving Or Copying Projects

`plan_project_folder_move` is read-only and returns the source project folder, target project folder, target `.blend` path, conflicts, and the exact steps that would run.

`move_project_folder` requires confirmation. By default it copies the project folder, saves the current `.blend` to the target, collects/relinks external image textures into the target `textures/source/`, repairs the target manifest, approves the target as the active project root, and keeps the original folder. Deleting the original is only attempted when `copy_mode="move"` and `delete_original=True` are both explicitly supplied.

## Drive Roots

`detect_drive_roots` reports common local drive roots such as `C:\` and `D:\` when present. `approve_drive_roots` requires confirmation because it grants broad local filesystem access. Use it for local desktop workflows where assets may move between drives, but keep project writes under the active project folder whenever possible.

## Public Zips

The Blender install zip and the public source/GitHub handoff zip are separate artifacts:

- `scripts/build_addon_zip.py` creates the installable addon package zip rooted at `overtli_blender_addon/`.
- `scripts/build_public_repo_zip.py` creates a public-safe source zip with the addon package, MCP source package, public docs, scripts, tests, config, launchers, and packaging metadata while excluding Memory Bank, `.overtli_blender/`, local tools, generated release outputs, review mirrors, caches, and private agent instructions.
