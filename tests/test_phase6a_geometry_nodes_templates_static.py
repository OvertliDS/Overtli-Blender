from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
from tests._addon_source import ADDON_PACKAGE_SOURCE as ADDON_TEXT


REQUIRED_TEMPLATES = [
    "scatter_on_surface",
    "curve_rope",
    "curve_cable",
    "radial_array",
    "linear_array",
    "grid_array",
    "panel_grid",
    "sci_fi_panel",
    "fence_generator",
    "railing_generator",
    "pipe_generator",
    "beaded_chain",
    "terrain_noise",
    "rock_field_scatter",
    "grass_clump_scatter",
    "point_instance_scatter",
    "label_plate",
    "beveled_curve_path",
    "procedural_stairs",
    "simple_building_blocks",
]


def test_phase6a_required_template_names_exist() -> None:
    for template in REQUIRED_TEMPLATES:
        assert f'"{template}"' in ADDON_TEXT


def test_phase6a_templates_are_schema_and_manifest_aware() -> None:
    for text in [
        "supported_parameters",
        "default_parameters",
        "input_schema",
        "node_plan",
        "required_node_types",
        "version_requirements",
        "known_limitations",
        '".overtli_blender"',
        '"geometry_nodes"',
        '"recipes"',
    ]:
        assert text in ADDON_TEXT


def test_phase6a_custom_recipe_is_allowlisted() -> None:
    assert "ALLOWED_NODE_TYPES" in ADDON_TEXT
    assert "ALLOWED_SOCKET_TYPES" in ADDON_TEXT
    assert "Recipe validation failed" in ADDON_TEXT
    assert "arbitrary" not in ADDON_TEXT[ADDON_TEXT.index("class GeometryNodesRecipeService"):ADDON_TEXT.index("class GeometryNodesModifierService")].lower()
