# File Access Policy

Phase 7C adds an approved-root file access policy for project reads, writes, copies, and delete planning.

Paths are canonicalized before access checks. The policy blocks `..` escapes and symlink or junction escapes outside approved roots. Text writes use atomic temporary replacement. Text previews redact common sensitive auth-like fields before display.

Project-local reads and writes are allowed when the path is inside an approved root. Writes outside the project root require approval. Deletes are split into `plan_file_delete` and `execute_approved_file_delete`; planning reports exact files, byte counts, risks, and rollback availability, while execution remains approval-gated.

Primary commands: `get_file_access_policy`, `set_file_access_policy`, `validate_path_access`, `list_approved_roots`, `add_approved_root`, `remove_approved_root`, `scan_project_files`, `read_project_text_file`, `write_project_text_file`, `copy_file_into_project`, `plan_file_delete`, and `execute_approved_file_delete`.
