from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "README.md",
    ROOT / "docs" / "install.md",
    ROOT / "docs" / "mcp_setup.md",
    ROOT / "docs" / "addon_install.md",
    ROOT / "docs" / "runtime_smoke.md",
    ROOT / "docs" / "final_handoff.md",
    ROOT / "docs" / "release_artifacts.md",
    ROOT / "docs" / "troubleshooting.md",
]


def main() -> int:
    failures: list[str] = []
    for path in DOCS:
        if not path.is_file():
            failures.append(f"missing {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        if "overtli-blender" not in text:
            failures.append(f"{path.relative_to(ROOT)} missing overtli-blender")
        if path.name in {"README.md", "install.md"} and "src/overtli_blender" not in text:
            failures.append(f"{path.relative_to(ROOT)} missing src/overtli_blender")
        if "smoke_blender_addon_socket.py" not in text:
            failures.append(f"{path.relative_to(ROOT)} missing runtime smoke command")
        if path.name in {"install.md", "mcp_setup.md"} and "py -3.12 -m venv .venv" not in text:
            failures.append(f"{path.relative_to(ROOT)} missing venv creation command")
        if path.name == "mcp_setup.md" and "[mcp_servers.\"overtli-blender\"]" not in text:
            failures.append(f"{path.relative_to(ROOT)} missing Codex MCP stanza")
        if path.name in {"final_handoff.md", "release_artifacts.md"} and "final_release_handoff.py" not in text:
            failures.append(f"{path.relative_to(ROOT)} missing final handoff command")
        if path.name == "troubleshooting.md" and "PATH_NOT_APPROVED" not in text:
            failures.append(f"{path.relative_to(ROOT)} missing path approval troubleshooting")
        if path.name != "README.md" and "blender-mcp-enhanced" in text:
            failures.append(f"{path.relative_to(ROOT)} contains stale blender-mcp-enhanced")
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print("PASS install docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
