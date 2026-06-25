# Approval Runtime

The Phase 7B approval runtime introduces a two-phase path for high-risk work.
It complements the existing `confirm=True` compatibility gate.

Flow:

1. `prepare_operation` records the command name, canonical parameter hash, risk
   level, capabilities, rollback strategy, and expiration.
2. `get_pending_approvals` lists pending approvals.
3. `approve_operation` or `deny_operation` resolves the record.
4. `execute_approved_operation` validates that the command name and parameters
   still match the approved hash before dispatch.

Read-only commands do not require approval. High-risk or destructive commands
require approval in strict governance paths. During Phase 7B, approved execution
is intentionally staged for migrated operations, so compatibility smoke remains
unblocked and destructive commands are not executed by the governance smoke.
