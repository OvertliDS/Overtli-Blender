from __future__ import annotations

from ..core import *

class BlenderApiKnowledgeService:
    def __init__(self, server):
        self.server = server

    def inspect_blender_api_docs(self, docs_root=None, max_files=50000):
        root = os.path.abspath(docs_root or PHASE6B_DOCS_ROOT)
        files = []
        if os.path.isdir(root):
            for d, _, names in os.walk(root):
                for n in names:
                    if n.lower().endswith(".md"):
                        files.append(os.path.join(d, n))
                        if len(files) >= int(max_files): break
                if len(files) >= int(max_files): break
        topics = sorted({t for t in ["bpy.ops", "bpy.types", "bpy.utils", "bpy.app.handlers", "bpy.path", "bpy.props", "AddonPreferences", "Operator", "Panel"] if any(t.lower() in os.path.basename(p).lower() for p in files)})
        return {"status": "success", "docs_root": root, "exists": os.path.isdir(root), "file_count": len(files), "top_level_files": [os.path.basename(p) for p in files[:25]], "detected_topics": topics, "warnings": []}

    def build_blender_api_index(self, docs_root=None, include_patterns=None, max_files=50000, max_chars_per_file=20000, write_index=True, artifact_root=None):
        root = os.path.abspath(docs_root or PHASE6B_DOCS_ROOT)
        if not os.path.isdir(root):
            return {"status": "error", "message": f"Docs root missing: {root}"}
        records = []
        for d, _, names in os.walk(root):
            for n in names:
                if not n.lower().endswith(".md"): continue
                text = open(os.path.join(d, n), "r", encoding="utf-8", errors="replace").read(int(max_chars_per_file))
                headings = [line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")][:12]
                symbols = sorted(set(re.findall(r"\bbpy\.[A-Za-z0-9_\.]+|register_class|unregister_class|addon_install|addon_enable|addon_disable|addon_remove|AddonPreferences|Operator|Panel", text)))[:80]
                records.append({"path": os.path.relpath(os.path.join(d, n), root).replace("\\", "/"), "title": headings[0] if headings else os.path.splitext(n)[0], "headings": headings, "symbols": symbols, "summary": " ".join(headings[:3])[:300], "keywords": sorted(set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b", text.lower())))[:120]})
                if len(records) >= int(max_files): break
            if len(records) >= int(max_files): break
        out_dir = _phase6b_workspace_path("knowledge", "api_index", artifact_root=artifact_root)
        if write_index:
            _phase6b_write_json(os.path.join(out_dir, "api_index.json"), {"records": records, "docs_root": root, "record_count": len(records)})
            _phase6b_write_json(os.path.join(out_dir, "source_manifest.json"), {"docs_root": root, "file_count": len(records), "private_source": True})
            _phase6b_write_json(os.path.join(out_dir, "build_report.json"), {"status": "success", "record_count": len(records)})
        return {"status": "success", "docs_root": root, "record_count": len(records), "index_path": os.path.join(out_dir, "api_index.json") if write_index else None}

    def _load_index(self, artifact_root=None):
        path = _phase6b_workspace_path("knowledge", "api_index", "api_index.json", artifact_root=artifact_root)
        if not os.path.exists(path):
            self.build_blender_api_index(artifact_root=artifact_root)
        return _phase6b_read_json(path, {"records": []}), path

    def search_blender_api_docs(self, query, max_results=20, artifact_root=None):
        index, path = self._load_index(artifact_root); terms = [t.lower() for t in re.findall(r"\w+", str(query))]; results = []
        for rec in index.get("records", []):
            hay = " ".join([rec.get("title", ""), rec.get("summary", ""), " ".join(rec.get("symbols", [])), " ".join(rec.get("keywords", []))]).lower()
            score = sum(hay.count(t) for t in terms)
            if score: results.append({"score": score, "title": rec.get("title"), "path": rec.get("path"), "summary": rec.get("summary"), "symbols": rec.get("symbols", [])[:20]})
        results.sort(key=lambda item: item["score"], reverse=True)
        return {"status": "success", "query": query, "index_path": path, "results": results[:int(max_results)], "warnings": []}

    def get_blender_api_topic(self, topic, include_summary=True, include_symbols=True, artifact_root=None):
        index, path = self._load_index(artifact_root); needle = str(topic).lower()
        for rec in index.get("records", []):
            if needle in rec.get("title", "").lower() or needle in rec.get("path", "").lower() or any(needle in s.lower() for s in rec.get("symbols", [])):
                return {"status": "success", "topic": rec.get("title"), "path": rec.get("path"), "summary": rec.get("summary") if include_summary else None, "symbols": rec.get("symbols", []) if include_symbols else [], "index_path": path}
        return {"status": "error", "message": f"API topic not found: {topic}"}


class VerifiedSnippetLibraryService:
    def __init__(self, server):
        self.server = server
    def _path(self, artifact_root=None): return _phase6b_workspace_path("knowledge", "snippets", "snippets.json", artifact_root=artifact_root)
    def _load(self, artifact_root=None): return _phase6b_read_json(self._path(artifact_root), {"snippets": {}})
    def _save(self, data, artifact_root=None): _phase6b_write_json(self._path(artifact_root), data)
    def create_verified_snippet(self, name, code, description="", tags=None, source_evidence=None, safety_classification="medium", smoke_status="not_run", overwrite=False, artifact_root=None):
        sid = _phase6b_slug(name, "snippet"); data = self._load(artifact_root)
        if sid in data["snippets"] and not overwrite: return {"status": "error", "message": "Snippet exists; pass overwrite=True"}
        dangerous = sorted(set(PHASE6B_BAD_SNIPPET_RE.findall(str(code))))
        entry = {"id": sid, "name": name, "description": description, "tags": tags or [], "source_evidence": source_evidence or [], "safety_classification": safety_classification, "smoke_status": smoke_status, "dangerous_calls": dangerous, "code": str(code)}
        data["snippets"][sid] = entry; self._save(data, artifact_root)
        return {"status": "success", "snippet": {k: v for k, v in entry.items() if k != "code"}, "store_path": self._path(artifact_root), "warnings": ["dangerous-call-detected"] if dangerous else []}
    def validate_verified_snippet(self, snippet_id=None, code=None, artifact_root=None):
        entry = self._load(artifact_root).get("snippets", {}).get(str(snippet_id)) if snippet_id else None
        if snippet_id and not entry: return {"status": "error", "message": "Snippet not found"}
        dangerous = sorted(set(PHASE6B_BAD_SNIPPET_RE.findall(str(code if code is not None else entry.get("code", "")))))
        return {"status": "success", "valid": not dangerous, "dangerous_calls": dangerous, "snippet_id": snippet_id}
    def list_verified_snippets(self, include_code=False, artifact_root=None):
        items = list(self._load(artifact_root).get("snippets", {}).values())
        if not include_code: items = [{k: v for k, v in item.items() if k != "code"} for item in items]
        return {"status": "success", "snippets": items, "count": len(items)}
    def search_verified_snippets(self, query, max_results=20, artifact_root=None):
        needle = str(query).lower(); return {"status": "success", "query": query, "snippets": [i for i in self.list_verified_snippets(False, artifact_root)["snippets"] if needle in json.dumps(i).lower()][:int(max_results)]}
    def get_verified_snippet(self, snippet_id, include_code=False, artifact_root=None):
        item = self._load(artifact_root).get("snippets", {}).get(str(snippet_id))
        if not item: return {"status": "error", "message": "Snippet not found"}
        return {"status": "success", "snippet": item if include_code else {k: v for k, v in item.items() if k != "code"}}
    def run_verified_snippet_smoke(self, snippet_id, confirm=False, artifact_root=None):
        if not confirm: return {"status": "error", "message": "run_verified_snippet_smoke requires confirm=True"}
        validation = self.validate_verified_snippet(snippet_id=snippet_id, artifact_root=artifact_root)
        if not validation.get("valid"): return {"status": "error", "message": "Snippet failed static validation", "validation": validation}
        report = {"snippet_id": snippet_id, "smoke_status": "static_validated_only", "executed": False}; _phase6b_write_json(_phase6b_workspace_path("knowledge", "snippets", "smoke", f"{snippet_id}.json", artifact_root=artifact_root), report); return {"status": "success", "report": report}
    def delete_verified_snippets(self, snippet_ids, confirm=False, artifact_root=None):
        if not confirm: return {"status": "error", "message": "delete_verified_snippets requires confirm=True"}
        data = self._load(artifact_root); removed = [sid for sid in (snippet_ids or []) if data["snippets"].pop(str(sid), None) is not None]; self._save(data, artifact_root); return {"status": "success", "removed": removed}


class SkillPackService:
    def __init__(self, server): self.server = server
    def _root(self, artifact_root=None): return _phase6b_workspace_path("knowledge", "skill_packs", artifact_root=artifact_root)
    def create_skill_pack(self, name, description="", operations=None, snippet_ids=None, docs_topics=None, overwrite=False, artifact_root=None):
        pid = _phase6b_slug(name, "skill_pack"); pdir = os.path.join(self._root(artifact_root), pid)
        if os.path.exists(pdir) and not overwrite: return {"status": "error", "message": "Skill pack exists; pass overwrite=True"}
        os.makedirs(pdir, exist_ok=True); manifest = {"id": pid, "name": name, "description": description, "operations": operations or [], "snippet_ids": snippet_ids or [], "docs_topics": docs_topics or [], "run_requires_confirm": True}
        _phase6b_write_json(os.path.join(pdir, "skill_pack.json"), manifest); open(os.path.join(pdir, "README.md"), "w", encoding="utf-8").write(f"# {name}\n\n{description}\n")
        return {"status": "success", "skill_pack": manifest, "pack_dir": pdir}
    def validate_skill_pack(self, pack_id, artifact_root=None):
        path = os.path.join(self._root(artifact_root), _phase6b_slug(pack_id, "skill_pack"), "skill_pack.json")
        if not os.path.isfile(path): return {"status": "error", "message": "Skill pack manifest not found"}
        manifest = _phase6b_read_json(path, {}); issues = [] if manifest.get("id") and isinstance(manifest.get("operations", []), list) else ["invalid manifest shape"]
        return {"status": "success", "valid": not issues, "issues": issues, "skill_pack": manifest}
    def list_skill_packs(self, artifact_root=None):
        root = self._root(artifact_root); packs = [_phase6b_read_json(os.path.join(root, n, "skill_pack.json"), {}) for n in os.listdir(root) if os.path.isfile(os.path.join(root, n, "skill_pack.json"))] if os.path.isdir(root) else []
        return {"status": "success", "skill_packs": packs, "count": len(packs)}
    def get_skill_pack(self, pack_id, artifact_root=None): return self.validate_skill_pack(pack_id, artifact_root)
    def run_skill_pack(self, pack_id, confirm=False, max_operations=20, artifact_root=None):
        if not confirm: return {"status": "error", "message": "run_skill_pack requires confirm=True"}
        pack = self.validate_skill_pack(pack_id, artifact_root)
        if pack.get("status") != "success": return pack
        handlers = self.server._build_command_handlers(); results = []
        for op in pack["skill_pack"].get("operations", [])[:int(max_operations)]:
            cmd = op.get("command"); results.append({"command": cmd, "result": handlers[cmd](**op.get("params", {})) if cmd in handlers and cmd != "execute_code" else {"status": "blocked", "message": "blocked or unknown command"}})
        return {"status": "success", "pack_id": pack_id, "results": results}
    def delete_skill_packs(self, pack_ids, confirm=False, artifact_root=None):
        if not confirm: return {"status": "error", "message": "delete_skill_packs requires confirm=True"}
        root = os.path.abspath(self._root(artifact_root)); removed = []
        for pid in pack_ids or []:
            path = os.path.abspath(os.path.join(root, _phase6b_slug(pid, "skill_pack")))
            if path.startswith(root + os.sep) and os.path.isdir(path): shutil.rmtree(path); removed.append(pid)
        return {"status": "success", "removed": removed}


class ReviewPackageExportService:
    def __init__(self, server): self.server = server
    def export_project_review_package(self, package_id=None, include_memory_bank=False, include_private_docs=False, include_generated_artifacts_summary=True, max_files=2000, artifact_root=None):
        pid = _phase6b_slug(package_id or f"review_{int(time.time()*1000)}", "review"); pdir = _phase6b_workspace_path("review_packages", pid, artifact_root=artifact_root)
        excluded_names = {".git", ".venv", "__pycache__", ".pytest_cache", ".overtli_blender", "tools"} | (set() if include_memory_bank else {"memory_bank"})
        files, excluded = [], []
        for d, dirs, names in os.walk(ADDON_ROOT):
            rel_dir = os.path.relpath(d, ADDON_ROOT); parts = set([] if rel_dir == "." else rel_dir.split(os.sep))
            if parts & excluded_names or (not include_private_docs and "blender_python_reference_5_1_md" in rel_dir):
                excluded.append(rel_dir); dirs[:] = []; continue
            for n in names:
                rel = os.path.normpath(os.path.join(rel_dir, n)).replace("\\", "/")
                if n.endswith((".pyc", ".env", ".zip")) or PHASE6B_SECRET_RE.search(n): excluded.append(rel); continue
                files.append(rel)
                if len(files) >= int(max_files): break
            if len(files) >= int(max_files): break
        try:
            import subprocess
            git_status = subprocess.run(["git", "status", "--short", "--untracked-files=all", "--ignored=matching"], cwd=ADDON_ROOT, text=True, capture_output=True, timeout=10).stdout
        except Exception as exc:
            git_status = f"git status unavailable: {exc}"
        _phase6b_write_json(os.path.join(pdir, "manifest.json"), {"package_id": pid, "files_included_count": len(files), "include_memory_bank": include_memory_bank, "include_private_docs": include_private_docs})
        _phase6b_write_json(os.path.join(pdir, "file_manifest.json"), {"files": files})
        _phase6b_write_json(os.path.join(pdir, "exclusion_report.json"), {"excluded": sorted(set(excluded)), "memory_bank_excluded": not include_memory_bank, "docs_mirror_excluded": not include_private_docs, "env_excluded": True})
        _phase6b_write_json(os.path.join(pdir, "docs_summary.json"), {"public_safe": True, "private_docs_copied": False})
        _phase6b_write_json(os.path.join(pdir, "test_summary.json"), {"tests_executed_by_export": False})
        _phase6b_write_json(os.path.join(pdir, "smoke_summary.json"), {"smoke_executed_by_export": False})
        open(os.path.join(pdir, "repo_status.txt"), "w", encoding="utf-8").write(git_status)
        return {"status": "success", "package_id": pid, "package_dir": pdir, "warnings": []}
    def validate_review_package(self, package_path):
        pdir = os.path.abspath(str(package_path)); issues = [f"missing {n}" for n in ["manifest.json", "file_manifest.json", "exclusion_report.json"] if not os.path.isfile(os.path.join(pdir, n))]
        files = _phase6b_read_json(os.path.join(pdir, "file_manifest.json"), {"files": []}).get("files", []); joined = "\n".join(files).lower()
        for forbidden in ["memory_bank", "blender_python_reference_5_1_md", ".env"]:
            if forbidden in joined: issues.append(f"forbidden path included: {forbidden}")
        if len(files) > 5000: issues.append("file count exceeds review package bound")
        return {"status": "success", "valid": not issues, "issues": issues, "file_count": len(files)}


class AdvancedKnowledgeWorkflowBatchService:
    def __init__(self, server): self.server = server
    def run_advanced_knowledge_workflow_batch(self, label=None, operations=None, stop_on_error=True, max_operations=40, batch_allow_destructive=False, artifact_root=None):
        allowed = {"inspect_blender_api_docs", "build_blender_api_index", "search_blender_api_docs", "get_blender_api_topic", "create_verified_snippet", "validate_verified_snippet", "list_verified_snippets", "search_verified_snippets", "get_verified_snippet", "create_skill_pack", "validate_skill_pack", "list_skill_packs", "get_skill_pack", "export_project_review_package", "validate_review_package"}
        destructive = {"install_local_addon", "enable_blender_addon", "disable_blender_addon", "remove_blender_addon", "run_verified_snippet_smoke", "delete_verified_snippets", "run_skill_pack", "delete_skill_packs"}
        handlers = self.server._build_command_handlers(); results = []
        for op in (operations or [])[:int(max_operations)]:
            cmd, params = op.get("command") or op.get("type"), op.get("params", {})
            if cmd in destructive and not (batch_allow_destructive and params.get("confirm") is True): result = {"status": "blocked", "message": "destructive operation requires batch_allow_destructive=True and operation confirm=True"}
            elif cmd not in allowed and cmd not in destructive: result = {"status": "error", "message": f"operation not allowed in advanced knowledge batch: {cmd}"}
            else: result = handlers[cmd](**params) if cmd in handlers else {"status": "error", "message": f"unknown command: {cmd}"}
            results.append({"command": cmd, "result": result})
            if stop_on_error and result.get("status") != "success": break
        manifest_path = _phase6b_workspace_path("knowledge", "workflow_batches", f"{_phase6b_slug(label or 'phase6b_batch', 'batch')}.json", artifact_root=artifact_root)
        _phase6b_write_json(manifest_path, {"label": label, "results": results})
        return {"status": "success", "label": label, "results": results, "manifest_path": manifest_path}


