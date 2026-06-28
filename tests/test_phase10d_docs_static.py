from __future__ import annotations


def test_phase10d_docs_explain_browser_mutation_and_approval_modes() -> None:
    docs = "\n".join(
        open(path, encoding="utf-8").read()
        for path in [
            "README.md",
            "docs/chatgpt_browser_connector.md",
            "docs/chatgpt_connector_prompts.md",
            "docs/mcp_setup.md",
            "docs/runtime_smoke.md",
            "docs/known_limitations.md",
            "docs/preferences.md",
            "CHANGELOG.md",
        ]
    )
    for marker in [
        "browser_full_standard",
        "browser_standard",
        "safe structured writes",
        "approval mode",
        "approve_and_execute_operation",
        "execute_approved_operation",
        "full_standard",
        "Refresh",
        "object_count remains 0",
    ]:
        assert marker in docs
