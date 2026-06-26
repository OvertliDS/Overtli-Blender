"""Static security audit helpers for release-candidate checks."""

from __future__ import annotations

from pathlib import Path


FORBIDDEN_PUBLIC_PATTERNS = ("AGENTS.md", ".env", "memory_bank", "blender_python_reference_5_1_md")


def audit_paths(paths: list[str]) -> dict:
    findings = []
    for name in paths:
        parts = Path(name).parts
        if any(pattern in name or pattern in parts for pattern in FORBIDDEN_PUBLIC_PATTERNS):
            findings.append({"path": name, "severity": "high", "message": "private or generated path included"})
    return {"status": "passed" if not findings else "failed", "findings": findings}
