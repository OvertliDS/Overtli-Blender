from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = [
    "docs/addon_architecture.md",
    "docs/addon_packaging.md",
    "docs/compatibility_matrix.md",
    "docs/performance_budgets.md",
    "docs/security_audit.md",
    "docs/privacy_model.md",
    "docs/threat_model.md",
    "docs/fault_injection.md",
    "docs/release_candidate.md",
    "docs/migration_audit.md",
    "docs/mcp_setup.md",
    "docs/final_handoff.md",
    "docs/release_artifacts.md",
    "docs/known_limitations.md",
    "docs/troubleshooting.md",
    "docs/chatgpt_browser_connector.md",
    "docs/chatgpt_connector_prompts.md",
]
STALE_PUBLIC_PHRASES = [
    "single-file Blender addon entrypoint",
    "Install `addon.py`",
    "experimental_package_layout",
]


def run_check() -> dict:
    missing = [rel for rel in REQUIRED_DOCS if not (ROOT / rel).is_file()]
    stale = []
    for rel in [
        "README.md",
        "docs/addon_install.md",
        "docs/install.md",
        "docs/mcp_setup.md",
        "docs/packaged_addon_migration.md",
        "docs/final_handoff.md",
        "docs/release_artifacts.md",
        "docs/known_limitations.md",
        "docs/troubleshooting.md",
    ]:
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in STALE_PUBLIC_PHRASES:
            if phrase in text:
                stale.append({"path": rel, "phrase": phrase})
        if rel in {"docs/install.md", "docs/mcp_setup.md"} and "overtli_blender.server" not in text:
            stale.append({"path": rel, "phrase": "missing MCP server command"})
        if rel in {"docs/final_handoff.md", "docs/release_artifacts.md"} and "final_release_handoff.py" not in text:
            stale.append({"path": rel, "phrase": "missing final handoff command"})
        if rel == "docs/troubleshooting.md" and "PATH_NOT_APPROVED" not in text:
            stale.append({"path": rel, "phrase": "missing path approval troubleshooting"})
        if rel == "docs/mcp_setup.md" and "chatgpt_browser_connector.md" not in text:
            stale.append({"path": rel, "phrase": "missing ChatGPT browser connector link"})
        if rel == "docs/chatgpt_browser_connector.md":
            for required in ["Developer mode", "Settings -> Connectors -> Create", "/mcp", "MCP Inspector", "local/tunnel development"]:
                if required not in text:
                    stale.append({"path": rel, "phrase": f"missing {required}"})
    return {"status": "passed" if not missing and not stale else "failed", "missing": missing, "stale": stale}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 10A docs lockdown checks.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run_check()
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"status: {report['status']}")
        for item in report["missing"]:
            print(f"missing: {item}")
        for item in report["stale"]:
            print(f"stale: {item['path']}: {item['phrase']}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
