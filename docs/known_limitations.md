# Known Limitations

- Live Blender socket verification is local/manual. CI runs static checks only and does not require Blender GUI.
- `addon.py` is a thin bootstrap, but `overtli_blender_addon/runtime/socket_server.py` remains the largest runtime module.
- Provider downloads, raw Python execution, addon lifecycle changes, destructive cleanup, simulation bake/cache actions, and third-party addon operator execution remain high-risk or approval-gated surfaces.
- Packaged runtime status can be statically verified without Blender. `PACKAGED_RUNTIME_LIVE_VERIFIED` requires the addon zip installed/enabled in Blender and `scripts/smoke_blender_addon_socket.py --timeout 30 --include-addon-package-status`.
- The final handoff script does not publish, tag, push, upload, or sync Drive mirrors.
- Review package and Drive mirror tooling are local/private and ignored. Use them only as a manual handoff step after release gates pass.
- ChatGPT.com browser connector validation is local/tunnel development only. Automated checks verify static readiness and local HTTP health; creating the connector in ChatGPT and running golden prompts remains manual.
