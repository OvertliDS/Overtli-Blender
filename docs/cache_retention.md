# Cache Retention

Phase 7C introduces cache inventory and cleanup planning for managed Overtli artifacts.

Managed cache categories are `temp`, `derived_previews`, `smoke_artifacts`, `verification_snapshots`, `logs`, `diagnostics`, `release_artifacts`, `exports`, `final_renders`, and `knowledge_indexes`.

`get_cache_status` reports category path, file count, bytes, oldest and newest artifact timestamps, pinned count, and cleanup policy. `plan_cache_cleanup` is dry-run by default and never deletes. `execute_cache_cleanup` requires approval and must stay inside managed cache roots. Final renders and pinned artifacts are protected.

Primary commands: `get_cache_status`, `plan_cache_cleanup`, `execute_cache_cleanup`, `pin_artifact`, `unpin_artifact`, `find_orphaned_artifacts`, and `compact_operation_history`.
