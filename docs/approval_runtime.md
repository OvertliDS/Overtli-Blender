# Approval Runtime

The Phase 7B approval runtime introduces a two-phase path for high-risk work.
It complements the existing `confirm=True` compatibility gate.

Flow:

1. `prepare_operation` records the command name, canonical parameter hash, risk
   level, capabilities, rollback strategy, and expiration.
2. `get_pending_approvals` lists pending approvals.
3. `approve_operation` or `deny_operation` resolves the record. Browser MCP
   `approve_operation` defaults to executing immediately after approval because
   some connector sessions do not reliably choose a separate executor tool.
4. `execute_approved_operation` validates that the command name and parameters
   still match the approved hash before dispatch. It can load the stored command
   and params from `approval_id` when callers only pass the approval id.

Read-only commands do not require approval. High-risk or destructive commands
require approval in strict governance paths. Approved execution now dispatches
the exact approved structured command after the command name and canonical
parameters are validated. Browser Full Standard does not hide raw Python, addon
operator execution, or cleanup tools; those paths are governed by the active
approval mode, exact confirmation fields, approval ids, command allowlists, and
addon-side safety scanners.
