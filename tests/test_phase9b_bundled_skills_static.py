from overtli_blender.runtime.skill_pack_library import BUNDLED_SKILL_PACKS, search_bundled_skill_packs


def test_phase9b_bundled_skill_pack_library_complete():
    expected = {
        "reference_modeling", "hard_surface_modeling", "organic_proportion_editing",
        "procedural_modeling", "geometry_nodes_patterns", "pbr_material_authoring",
        "texture_baking", "texture_painting_preflight", "sculpt_refinement",
        "cloth_pattern_workflow", "character_rigging", "animation_blocking",
        "product_rendering", "cinematic_lighting", "game_asset_export",
        "scene_cleanup", "addon_development", "project_repair", "diagnostics_review",
    }
    assert expected <= set(BUNDLED_SKILL_PACKS)
    for pack in BUNDLED_SKILL_PACKS.values():
        assert pack.intent_patterns
        assert pack.required_inspection
        assert pack.verification_stages


def test_phase9b_bundled_skill_search():
    assert search_bundled_skill_packs("texture baking")["results"][0]["skill_pack_id"] == "texture_baking"
