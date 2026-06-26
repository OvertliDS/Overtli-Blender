"""Fault-injection probes for packaged addon release checks."""

from __future__ import annotations


def unknown_command_probe(dispatcher) -> dict:
    response = dispatcher.dispatch("__phase10a_missing_command__")
    ok = response.get("status") == "error" and response.get("errors", [{}])[0].get("code") == "COMMAND_NOT_AVAILABLE"
    return {"status": "passed" if ok else "failed", "response": response}


def missing_package_probe(message: str) -> dict:
    expected = "addon zip built by scripts/build_addon_zip.py"
    return {"status": "passed" if expected in message else "failed", "message": message}
