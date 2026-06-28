# Browser MCP Lessons Learned

[VERIFIED: 2026-06-28]

ChatGPT browser testing exposed several behavior gaps that are now part of the connector contract.

## Cleanup And Destructive Intent

Destructive user language such as "delete", "clear", "reset", "purge", "cleanup", and "remove" must not route to unrelated creation tools. Browser-visible discovery should prefer `scene_cleanup_plan`, `clear_scene`, `delete_objects`, or approval/governance tools.

`clear_scene` is intentionally scoped and conservative:

- default scope is generated `OVERTLI_*` assets
- default mode is `dry_run=true`
- confirmed execution requires `confirm=true`
- batch execution also requires `batch_allow_destructive=true`

Use `scene_cleanup_plan` before resetting a scene in ChatGPT.

## Unsaved Blend Artifacts

Unsaved `.blend` sessions should not write workspace, verification, screenshot, or manifest artifacts under the addon install folder or source checkout. The runtime now resolves unsaved artifacts to:

```text
%LOCALAPPDATA%\Overtli-Blender\temp_workspaces\<session-id>\
```

Use `promote_temp_workspace_to_project(confirm=true, project_root=...)` after the user picks a real project folder.

## Scene Planning And Verification

For multi-step ChatGPT browser prompts, create a workspace plan before mutation and mark items verified only after evidence exists. Useful commands:

- `create_scene_plan`
- `list_scene_plan`
- `complete_workspace_task`
- `create_scene_snapshot`
- `create_verification_snapshot`
- `validate_ground_contact`
- `validate_scene_composition`

Verification snapshots include workspace tasks/todos so browser review loops can see both scene state and task state.

## Dimensions And Contact

For primitives where dimensions matter, prefer final-dimension commands instead of scale-only transforms:

- `create_box`
- `create_primitive_object(..., dimensions=..., anchor=...)`
- `transform_object_dimensions`

Use `anchor="bottom_center"` when the object is meant to rest on the ground or another surface. Use `align_object_to_surface` and `validate_ground_contact` to avoid floating or sunken assets.

## Verified Batch Schema

New prompts should use the preferred batch operation shape:

```json
{
  "command_name": "create_box",
  "params": {
    "name": "OVERTLI_Box",
    "dimensions": [2.0, 1.0, 0.5],
    "anchor": "bottom_center"
  }
}
```

Legacy `type` and `command` fields remain supported for compatibility. Use `prevalidate_only=true` to check a batch before mutation.

## Blender 5.1 Color Management

Blender color-management enum values can vary by version. Browser prompts should call `get_supported_color_management` before setting render color management, or pass `auto_compatible=true` to `set_render_settings` for known Filmic/AgX-style aliases.
