# Sculpt Workflows

Phase 8B adds safe sculpt setup commands without enabling blind base-mesh sculpting.

`configure_sculpt_session` records brush/session settings and prepares a shape-key-first workflow. `create_sculpt_mask` creates a vertex-group-backed mask. `create_face_set` stores bounded face-set metadata. `create_shape_key_sculpt_variant` creates a new shape key while preserving the Basis key. `validate_sculpt_result` reports shape-key state.

`apply_sculpt_stroke_batch` is high risk and approval-gated. The default implementation does not fake stroke playback support; without an approval ID it returns `requires_approval`, and unsupported runtime stroke execution is reported honestly.
