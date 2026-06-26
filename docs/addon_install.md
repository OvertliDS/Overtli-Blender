# Blender Addon Install

The Python MCP package is `overtli-blender`; the Blender addon package is installed separately from the addon zip.

The primary Blender addon zip is the clean package zip built by:

```powershell
.\.venv\Scripts\python scripts\build_addon_zip.py --mode package --verify
```

Install the generated zip from:

```text
.overtli_blender/release/addon_zip/overtli_blender_addon_0.1.0.zip
```

In Blender, open `Edit > Preferences > Add-ons > Install`, select the zip, enable `Overtli-Blender`, then start the socket server from the Overtli-Blender sidebar panel.

After the socket server is running, verify the bridge from the repository root:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status
```

The repository-root `addon.py` is only the Blender entrypoint that imports `overtli_blender_addon`; it is not the addon runtime and should not be copied by itself.

If the addon installs but does not appear in Blender's Add-ons list, rebuild the zip and reinstall the generated package zip. The installed addon folder should contain `overtli_blender_addon/__init__.py` with a top-level `bl_info` entry; Blender uses that package metadata for addon discovery.
