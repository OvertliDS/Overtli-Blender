# Fault Injection

Run:

```powershell
.\.venv\Scripts\python scripts\fault_injection_check.py --json
```

Phase 10A probes unknown command handling and missing-package install guidance. Unknown commands return `COMMAND_NOT_AVAILABLE` with remediation to use tool discovery.
