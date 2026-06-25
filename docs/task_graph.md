# Task Graph

Phase 7C adds a project task graph under `.overtli/tasks/`.

Tasks preserve the user goal, status, priority, dependencies, blocked-by links, target handles, acceptance criteria, required approvals, scene revision metadata, linked artifacts, user notes, and model summaries.

Supported statuses are `planned`, `ready`, `in_progress`, `waiting_for_approval`, `waiting_for_user_selection`, `blocked`, `completed_unverified`, `verified`, `failed`, `rolled_back`, `stale`, and `archived`.

Completed and verified are different states. Scene revision markers can make previously completed or verified tasks stale, so downstream work can detect when scene changes require re-verification.

Primary commands: `create_task`, `update_task`, `list_tasks`, `get_task`, `set_task_status`, `link_task_artifact`, `link_task_target`, `mark_task_verified`, `mark_task_stale`, `archive_tasks`, `get_task_graph`, `detect_stale_tasks`, `get_session_time`, `get_scene_revision`, `get_recent_operations`, `get_changes_since_revision`, `get_operation_duration`, and `create_scene_revision_marker`.
