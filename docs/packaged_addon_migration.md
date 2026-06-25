# Packaged Addon Migration

Phase 7B creates an experimental packaged addon scaffold:

```text
overtli_blender_addon/
  __init__.py
  registration.py
  preferences.py
  runtime/
  services/
```

`addon.py` remains the stable addon entrypoint and install target. The packaged
layout exists to make future migration smaller and safer.

`scripts/build_addon_zip.py` now supports:

- `--layout legacy`: current single-file addon zip.
- `--layout packaged`: experimental package-layout zip.
- `--layout both`: build both outputs. This is the default.

The packaged zip is labeled `experimental_package_layout`. Future phases should
move services gradually and keep smoke compatibility with `addon.py` until the
packaged runtime is equivalent.
