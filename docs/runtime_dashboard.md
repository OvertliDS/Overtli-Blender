# Runtime Dashboard

The Phase 9B dashboard summarizes the current user-facing runtime state.

It reports:

- permission mode
- active tool profile
- enabled tool packs
- active bundled skill packs
- approved root count
- approval queue summary
- recent operation summary
- setup blockers
- warnings
- next recommended actions

Commands:

- `get_runtime_dashboard`
- `get_approval_queue_summary`
- `get_recent_operation_summary`
- `run_product_polish_workflow_batch`

The product polish batch runs non-destructive checks for preferences, setup, active profile, dashboard, and error catalog coverage.
