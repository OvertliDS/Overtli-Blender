# Migration Audit

Phase 10A migration audit verifies:

- `addon.py` is under the line budget.
- No `legacy_runtime.py` monolith exists.
- Required package modules exist.
- The packaged socket server owns `BlenderMCPServer` and `_build_command_handlers`.
- Service classes are distributed under domain modules.

Run through:

```powershell
.\.venv\Scripts\python scripts\release_candidate_check.py --json
```
