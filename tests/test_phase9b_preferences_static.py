from overtli_blender.runtime.preferences_schema import default_preferences, permission_expands, preferences_schema, validate_preferences


def test_phase9b_preferences_schema_sections_exist():
    schema = preferences_schema()
    assert schema["status"] == "success"
    for section in ["Project", "Filesystem", "Security", "Artifacts", "MCP", "Knowledge", "Tool Profiles", "Providers", "Diagnostics"]:
        assert section in schema["sections"]


def test_phase9b_preferences_validation_and_expansion_detection():
    prefs = default_preferences()
    assert validate_preferences(prefs)["valid"] is True
    requested = default_preferences()
    requested["filesystem"]["approved_roots"] = ["D:/AI/custom mcp/Overtli-Blender"]
    assert permission_expands(prefs, requested) is True
