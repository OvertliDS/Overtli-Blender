# Cloth Patterns

Phase 8B adds cloth pattern setup surfaces for panel-based fabric workflows.

`create_cloth_pattern_panel` creates a bounded mesh panel and optional Solidify thickness. `define_cloth_seam_pair` records explicit seam metadata. `create_cloth_pin_group` creates a vertex group for pinned vertices. `create_cloth_setup` adds a Cloth modifier with bounded quality, mass, pressure, and optional pin group. `create_cloth_collision_setup` adds collision settings to an exact object.

Simulation and cache actions are high risk. `simulate_cloth_preview`, `bake_cloth_cache`, `clear_cloth_cache`, and `convert_cloth_result` require approval and are not run by default smoke.
