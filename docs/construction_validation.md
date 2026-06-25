# Construction Validation

Phase 8B construction validation checks created objects for existence, type, dimensions, transforms, modifier count, and mesh health summaries. Reference alignment can be included by passing a Phase 7C reference set ID.

`plan_construction_cleanup` is read-only and returns exact smoke/temp targets plus an approval ID. `execute_construction_cleanup` is approval-gated and refuses final-object deletion. The smoke harness uses smoke-created names and ordinary `delete_objects` cleanup for temporary runtime data.

Known limitations: exact mesh self-intersection and full non-manifold repair remain future work. Current validation surfaces report conservative geometry health and confidence instead of overstating production mesh QA.
