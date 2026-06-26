from overtli_blender.runtime.error_catalog import ERROR_CATALOG, explain_error, get_remediation_steps


def test_phase9b_error_catalog_contains_required_codes():
    for code in ["BLENDER_NOT_CONNECTED", "PATH_NOT_APPROVED", "STRICT_MODE_BLOCKED", "ADDON_SOURCE_UNTRUSTED", "CACHE_CLEANUP_REQUIRES_PLAN"]:
        assert code in ERROR_CATALOG
        assert ERROR_CATALOG[code].user_actions


def test_phase9b_error_explain_and_remediation():
    assert explain_error("PATH_NOT_APPROVED")["status"] == "success"
    assert get_remediation_steps("PATH_NOT_APPROVED")["steps"]
