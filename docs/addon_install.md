# Blender Addon Install

`addon.py` is the single-file Overtli-Blender addon entrypoint for the `overtli-blender` package. You can install that file directly or install the zip produced by `scripts/build_addon_zip.py`.

## Install `addon.py`

1. Open Blender.
2. Go to `Edit > Preferences > Add-ons`.
3. Choose `Install from Disk` or `Install`.
4. Select `addon.py` from the repository root.
5. Enable `Overtli-Blender`.
6. In the Overtli-Blender panel, start the socket server.
7. Leave the default host and port as `localhost:9876` unless you intentionally changed them.

## Install Addon Zip

Build the zip:

```powershell
.\.venv\Scripts\python scripts\build_addon_zip.py
```

Then use the same Blender add-on install UI and select the generated zip under `.overtli_blender/release/addon_zip/`.

## Smoke Check

With Blender open and the socket server started:

```powershell
.\.venv\Scripts\python scripts\smoke_blender_addon_socket.py
```

Full manual smoke commands are documented in [runtime_smoke.md](runtime_smoke.md). Do not run provider downloads or raw code smoke unless you explicitly intend to test those optional flows.
