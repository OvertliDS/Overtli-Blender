# Reference Construction

Phase 8B adds reference-driven modeling planning on top of the Phase 7C reference image and spatial measurement surfaces.

`plan_reference_construction` records the reference set, target description, optional measurement IDs, selected method, and construction steps. `run_reference_construction_step` is intentionally plan-first unless a calibrated reference set is provided. `validate_reference_alignment` checks named objects against the supplied reference context and reports measurement confidence.

Reference construction should use calibrated Phase 7C references and spatial measurements for scale, proportion, landmarks, and alignment. When calibration is absent, commands report lower confidence instead of claiming verified alignment.
