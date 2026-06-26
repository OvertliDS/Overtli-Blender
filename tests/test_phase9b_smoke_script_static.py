from pathlib import Path


SMOKE_TEXT = Path("scripts/smoke_blender_addon_socket.py").read_text(encoding="utf-8")


def test_phase9b_smoke_flags_exist():
    for flag in [
        "--include-preferences-status", "--include-tool-profile-ux", "--include-bundled-skills",
        "--include-addon-interop-readonly", "--include-error-catalog", "--include-runtime-dashboard",
        "--include-onboarding-checklist", "--include-product-polish-batch", "--phase9b-full",
    ]:
        assert flag in SMOKE_TEXT


def test_phase9b_smoke_is_non_destructive():
    assert "execute_approved_addon_operator" not in SMOKE_TEXT
    assert "plan_addon_operator_invocation" in SMOKE_TEXT
    assert "third-party execution" in SMOKE_TEXT
