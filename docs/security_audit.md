# Security Audit

Phase 10A security checks focus on package boundaries and private-file exclusion.

Run:

```powershell
.\.venv\Scripts\python scripts\security_audit.py --json
```

The audit checks packaged addon paths and generated addon zip contents for private or generated inputs such as Memory Bank files, `.env`, `AGENTS.md`, and API mirrors.
