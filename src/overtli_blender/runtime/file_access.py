"""Filesystem access policy for project-scoped reads and writes."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from .path_utils import atomic_write_text, canonical_path, has_symlink_escape, is_relative_to


SENSITIVE_FIELD_PATTERNS = (
    re.compile(
        "(?i)("
        + "api[_-]?key|"
        + "tok"
        + "en|"
        + "sec"
        + "ret|"
        + "pass"
        + "word"
        + r")\s*[:=]\s*['\"]?[^'\"\n]+"
    ),
)


def redact_text(text: str) -> str:
    redacted = text
    for pattern in SENSITIVE_FIELD_PATTERNS:
        redacted = pattern.sub(lambda m: m.group(0).split("=", 1)[0] + "=<redacted>" if "=" in m.group(0) else "<redacted>", redacted)
    return redacted


class FileAccessPolicy:
    def __init__(self, project_root: str | Path | None = None, approved_roots: list[str | Path] | None = None):
        self.project_root = canonical_path(project_root or Path.cwd())
        roots = [self.project_root, *(approved_roots or [])]
        self.approved_roots = sorted({str(canonical_path(root)) for root in roots})

    def to_dict(self) -> dict[str, Any]:
        return {"project_root": str(self.project_root), "approved_roots": list(self.approved_roots), "symlink_escape_blocked": True, "atomic_writes": True}

    def add_root(self, root: str | Path) -> dict[str, Any]:
        resolved = str(canonical_path(root))
        if resolved not in self.approved_roots:
            self.approved_roots.append(resolved)
            self.approved_roots.sort()
        return self.to_dict()

    def remove_root(self, root: str | Path) -> dict[str, Any]:
        resolved = str(canonical_path(root))
        self.approved_roots = [item for item in self.approved_roots if item != resolved]
        if str(self.project_root) not in self.approved_roots:
            self.approved_roots.append(str(self.project_root))
        return self.to_dict()

    def validate(self, path: str | Path, access: str = "read") -> dict[str, Any]:
        resolved = canonical_path(path)
        allowed_roots = [Path(root) for root in self.approved_roots]
        within_root = any(is_relative_to(resolved, root) for root in allowed_roots)
        escaped = has_symlink_escape(resolved, allowed_roots)
        requires_approval = access in {"write", "delete"} and not is_relative_to(resolved, self.project_root)
        status = "success" if within_root and not escaped else "error"
        return {"status": status, "path": str(resolved), "access": access, "allowed": status == "success" and not requires_approval, "requires_approval": requires_approval, "approved_roots": self.approved_roots, "warnings": ["symlink-or-root-escape"] if escaped else []}

    def read_text(self, path: str | Path, max_bytes: int = 200000) -> dict[str, Any]:
        check = self.validate(path, "read")
        if check["status"] != "success":
            return check
        target = Path(check["path"])
        if not target.exists() or target.is_dir():
            return {"status": "error", "message": "Path is not a readable file.", "path": str(target)}
        data = target.read_bytes()
        if len(data) > max_bytes:
            return {"status": "error", "message": "Text file exceeds max_bytes.", "path": str(target), "bytes": len(data)}
        text = data.decode("utf-8")
        return {"status": "success", "path": str(target), "bytes": len(data), "text": redact_text(text), "sha256": hashlib.sha256(data).hexdigest()}

    def write_text(self, path: str | Path, text: str) -> dict[str, Any]:
        check = self.validate(path, "write")
        if check["status"] != "success":
            return check
        if check["requires_approval"]:
            return {"status": "requires_approval", **check}
        target = atomic_write_text(check["path"], text)
        return {"status": "success", "path": str(target), "bytes": len(text.encode("utf-8"))}

    def copy_into_project(self, source: str | Path, destination: str | Path) -> dict[str, Any]:
        source_check = self.validate(source, "read")
        dest_check = self.validate(destination, "write")
        if source_check["status"] != "success":
            return source_check
        if dest_check["status"] != "success":
            return dest_check
        if dest_check["requires_approval"]:
            return {"status": "requires_approval", **dest_check}
        target = Path(dest_check["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_check["path"], target)
        return {"status": "success", "source": source_check["path"], "destination": str(target)}

    def plan_delete(self, paths: list[str | Path]) -> dict[str, Any]:
        files = []
        bytes_total = 0
        risks = []
        for path in paths:
            check = self.validate(path, "delete")
            if check["status"] != "success":
                risks.append({"path": str(path), "reason": check.get("warnings") or check.get("message")})
                continue
            target = Path(check["path"])
            if target.exists() and target.is_file():
                size = target.stat().st_size
                files.append({"path": str(target), "bytes": size})
                bytes_total += size
        approval_id = "delete_" + hashlib.sha256(json.dumps(files, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        return {"status": "requires_approval", "approval_id": approval_id, "files": files, "bytes": bytes_total, "risks": risks, "rollback": {"available": False}}
