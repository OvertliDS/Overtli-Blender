# Performance Budgets

Phase 10A adds static release-candidate budgets in `config/performance_budgets.json`.

Current budgets:

- `addon_py_max_lines`: 300.
- `package_zip_max_bytes`: 10485760.
- `dispatcher_unknown_command_max_ms`: 5.
- `release_check_fast_max_seconds`: 120.

Run:

```powershell
.\.venv\Scripts\python scripts\performance_check.py --fast --json
```
