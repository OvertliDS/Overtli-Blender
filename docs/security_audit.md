# Security Audit

Phase 10A security checks focus on package boundaries and private-file exclusion.

Run:

```powershell
.\.venv\Scripts\python scripts\security_audit.py --json
```

The audit checks packaged addon paths and generated addon zip contents for private or generated inputs such as Memory Bank files, `.env`, `AGENTS.md`, and API mirrors.

## Runtime Code Execution Guards

Raw `execute_code` payloads are scanned with the same dangerous-call pattern family used by the verified snippet workflow. Matches such as dynamic import, subprocess/socket/network calls, file open calls, shell execution, recursive deletion, and addon install/remove calls return:

- `status: blocked`
- `executed: false`
- `error_type: DangerousCodePattern`
- `matched_rules`
- `remediation_code: RAW_CODE_STATIC_SCAN_BLOCK`

Execution failures return structured `status: error` responses with `error_type`, `message`, and a bounded `traceback_summary`; full raw-code success is only reported with `executed: true`.

Registered context scripts are stored under user-local Overtli state scoped by process, socket port, and current blend identity instead of a shared `%TEMP%\.blendermcp` folder. Context scripts expose the same shared Overtli helper namespace as raw execution (`shared`, `get_object`, `get_material`, `get_operation`, `store_object`, `store_material`, and `store_operation`).

Context script registration and execution now use the same dangerous-call scanner family as raw execution. Scanner matches return `status: blocked`, `executed: false`, `error_type: DangerousCodePattern`, and `remediation_code: CONTEXT_SCRIPT_STATIC_SCAN_BLOCK`.
