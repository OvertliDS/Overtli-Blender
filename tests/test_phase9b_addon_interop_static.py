from pathlib import Path

from overtli_blender.runtime.addon_interop import plan_operator_invocation, scan_addon_sources


def test_phase9b_addon_interop_scans_without_importing(tmp_path: Path):
    addon_file = tmp_path / "sample.py"
    addon_file.write_text(
        "bl_info = {'name': 'Sample', 'version': (1, 0, 0)}\n"
        "class TEST_OT_sample(Operator):\n"
        "    bl_idname = 'test.sample'\n"
        "    bl_label = 'Sample'\n",
        encoding="utf-8",
    )
    result = scan_addon_sources(str(tmp_path), [str(tmp_path)])
    assert result["status"] == "success"
    assert result["operators"][0]["bl_idname"] == "test.sample"


def test_phase9b_addon_operator_plan_requires_approval():
    result = plan_operator_invocation("object.select_all")
    assert result["status"] == "requires_approval"
    assert result["approval_required"] is True
