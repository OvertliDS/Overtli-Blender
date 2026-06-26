"""Addon-local redaction helpers."""

from __future__ import annotations


REDACTION_KEYS = ("api_key", "secret", "token", "password", "credential")


def redact_mapping(values: dict) -> dict:
    redacted = {}
    for key, value in values.items():
        redacted[key] = "***REDACTED***" if any(marker in key.lower() for marker in REDACTION_KEYS) else value
    return redacted
