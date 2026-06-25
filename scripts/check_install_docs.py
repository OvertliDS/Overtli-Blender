from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [ROOT / "README.md", ROOT / "docs" / "install.md", ROOT / "docs" / "addon_install.md", ROOT / "docs" / "runtime_smoke.md"]


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
