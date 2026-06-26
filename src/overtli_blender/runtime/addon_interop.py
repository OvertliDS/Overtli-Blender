"""Read-only addon source inspection helpers for Phase 9B."""

from __future__ import annotations

import ast
import hashlib
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


MAX_FILES_DEFAULT = 80
MAX_BYTES_DEFAULT = 1_000_000


@dataclass
class AddonOperatorSummary:
    class_name: str
    bl_idname: str | None
    bl_label: str | None
    file: str


@dataclass
class AddonSourceSummary:
    root: str
    files_scanned: int
    files_skipped: int
    operators: list[AddonOperatorSummary] = field(default_factory=list)
    panels: list[dict[str, str | None]] = field(default_factory=list)
    properties: list[dict[str, str | None]] = field(default_factory=list)
    bl_info: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["operators"] = [asdict(item) for item in self.operators]
        return data


def redact_path(path: str) -> str:
    home = str(Path.home())
    return path.replace(home, "~") if path.startswith(home) else path


def validate_safe_root(root: str, approved_roots: list[str]) -> dict[str, Any]:
    candidate = Path(root).expanduser().resolve()
    approved = [Path(item).expanduser().resolve() for item in approved_roots]
    if not candidate.exists() or not candidate.is_dir():
        return {"status": "error", "message": f"Addon source root does not exist: {redact_path(str(candidate))}"}
    if not any(candidate == item or item in candidate.parents for item in approved):
        return {"status": "requires_approval", "message": "Addon source root is not approved for read-only inspection.", "root": redact_path(str(candidate))}
    return {"status": "success", "root": str(candidate)}


def discover_python_files(root: str, max_files: int = MAX_FILES_DEFAULT) -> list[Path]:
    base = Path(root).expanduser().resolve()
    files = []
    for path in base.rglob("*.py"):
        if any(part in {"__pycache__", ".git", "node_modules", "venv", ".venv"} for part in path.parts):
            continue
        files.append(path)
        if len(files) >= max_files:
            break
    return files


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _assigned_string(node: ast.ClassDef, name: str) -> str | None:
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    value = _literal(stmt.value)
                    return value if isinstance(value, str) else None
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.target.id == name:
            value = _literal(stmt.value) if stmt.value else None
            return value if isinstance(value, str) else None
    return None


def parse_addon_file(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=str(path))
    rel = str(path.relative_to(root))
    result: dict[str, Any] = {"operators": [], "panels": [], "properties": [], "bl_info": {}}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "bl_info":
                    info = _literal(stmt.value)
                    if isinstance(info, dict):
                        result["bl_info"] = {str(k): v for k, v in info.items() if isinstance(k, str) and k in {"name", "author", "version", "blender", "category", "description"}}
        if isinstance(stmt, ast.ClassDef):
            bases = {getattr(base, "id", None) or getattr(base, "attr", None) for base in stmt.bases}
            item = {"class_name": stmt.name, "bl_idname": _assigned_string(stmt, "bl_idname"), "bl_label": _assigned_string(stmt, "bl_label"), "file": rel}
            if "Operator" in bases or (item["bl_idname"] and "." in item["bl_idname"]):
                result["operators"].append(item)
            if "Panel" in bases or str(item["bl_idname"] or "").startswith(("VIEW3D_PT_", "OBJECT_PT_")):
                result["panels"].append(item)
            for body_stmt in stmt.body:
                if isinstance(body_stmt, (ast.AnnAssign, ast.Assign)):
                    target = body_stmt.target if isinstance(body_stmt, ast.AnnAssign) else (body_stmt.targets[0] if body_stmt.targets else None)
                    target_name = getattr(target, "id", None)
                    call = body_stmt.value if isinstance(body_stmt, ast.AnnAssign) else getattr(body_stmt, "value", None)
                    if target_name and isinstance(call, ast.Call):
                        func_name = getattr(call.func, "id", None) or getattr(call.func, "attr", None)
                        if func_name and func_name.endswith("Property"):
                            result["properties"].append({"class_name": stmt.name, "property_name": target_name, "property_type": func_name, "file": rel})
    return result


def scan_addon_sources(root: str, approved_roots: list[str], max_files: int = MAX_FILES_DEFAULT, max_bytes: int = MAX_BYTES_DEFAULT) -> dict[str, Any]:
    validation = validate_safe_root(root, approved_roots)
    if validation.get("status") != "success":
        return validation
    base = Path(validation["root"])
    summary = AddonSourceSummary(root=redact_path(str(base)), files_scanned=0, files_skipped=0)
    for path in discover_python_files(str(base), max_files=max_files):
        try:
            if path.stat().st_size > max_bytes:
                summary.files_skipped += 1
                summary.warnings.append(f"Skipped large file: {path.name}")
                continue
            parsed = parse_addon_file(path, base)
            summary.files_scanned += 1
            summary.operators.extend(AddonOperatorSummary(**item) for item in parsed["operators"])
            summary.panels.extend(parsed["panels"])
            summary.properties.extend(parsed["properties"])
            summary.bl_info.update(parsed["bl_info"])
        except SyntaxError:
            summary.files_skipped += 1
            summary.warnings.append(f"Skipped unparsable Python file: {path.name}")
    digest = hashlib.sha256(str(summary.to_dict()).encode("utf-8")).hexdigest()
    data = summary.to_dict()
    data["scan_id"] = digest[:16]
    data["status"] = "success"
    return data


def plan_operator_invocation(operator_id: str, addon_module: str | None = None, properties: dict[str, Any] | None = None) -> dict[str, Any]:
    if not operator_id or "." not in operator_id:
        return {"status": "error", "message": "Operator id must be an exact bpy operator id such as object.select_all."}
    return {
        "status": "requires_approval",
        "approval_required": True,
        "operator_id": operator_id,
        "addon_module": addon_module,
        "properties": properties or {},
        "execution_boundary": "No third-party code is executed by planning. Execution requires exact operator id and approval.",
    }
