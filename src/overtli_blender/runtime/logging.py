"""Structured runtime logging helpers."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


LOG_DIR = Path(".overtli_blender") / "logs"
JSONL_LOG = LOG_DIR / "runtime_events.jsonl"
HUMAN_LOG = LOG_DIR / "runtime.log"
REDACTION_KEYS = ("api_key", "token", "secret", "password", "credential", "auth")
_REDACTION_RE = re.compile("|".join(re.escape(key) for key in REDACTION_KEYS), re.IGNORECASE)


def redact_value(key: str, value: Any) -> Any:
    if _REDACTION_RE.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {child_key: redact_value(child_key, child_value) for child_key, child_value in value.items()}
    if isinstance(value, list):
        return [redact_value(key, item) for item in value]
    return value


def redact_event(event: dict[str, Any]) -> dict[str, Any]:
    return {key: redact_value(key, value) for key, value in event.items()}


def write_event(event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    event = redact_event({"ts": time.time(), "event_type": event_type, "payload": payload or {}})
    with JSONL_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    with HUMAN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{event['ts']:.3f} {event_type}\n")
    return event


def get_log_status() -> dict[str, Any]:
    return {
        "status": "success",
        "log_dir": str(LOG_DIR),
        "jsonl_log": str(JSONL_LOG),
        "human_log": str(HUMAN_LOG),
        "jsonl_exists": JSONL_LOG.exists(),
        "human_exists": HUMAN_LOG.exists(),
        "redaction_keys": list(REDACTION_KEYS),
    }


def export_operation_log(operation_id: str | None = None) -> dict[str, Any]:
    if not JSONL_LOG.exists():
        return {"status": "success", "events": [], "operation_id": operation_id}
    events = []
    for line in JSONL_LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if operation_id and event.get("payload", {}).get("operation_id") != operation_id:
            continue
        events.append(event)
    return {"status": "success", "events": events, "operation_id": operation_id}
