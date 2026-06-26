# Addon Packaging

Build the installable Blender addon zip with:

```powershell
.\.venv\Scripts\python scripts\build_addon_zip.py --mode package --verify --json
```

The zip root is:

```text
overtli_blender_addon/
```

The builder uses explicit package/runtime allowlists and rejects repository bloat, including `memory_bank/`, `.overtli_blender/`, `tests/`, bulk `docs/`, `scripts/`, AI review artifacts, `.env`, `AGENTS.md`, generated build output, caches, and API mirrors.

Each build writes a manifest next to the zip with included files, hashes, excluded patterns, root entries, layout, total bytes, commit, and validation status.
