"""Session time and scene revision tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TimeRevisionTracker:
    session_start_monotonic: float = field(default_factory=time.monotonic)
    session_start_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scene_revision: int = 0
    operations: list[dict[str, Any]] = field(default_factory=list)

    def time_info(self) -> dict[str, Any]:
        return {"status": "success", "utc": datetime.now(timezone.utc).isoformat(), "local": datetime.now().astimezone().isoformat(), "session_start_utc": self.session_start_utc, "monotonic_elapsed": time.monotonic() - self.session_start_monotonic}

    def marker(self, label: str | None = None, source: str = "overtli") -> dict[str, Any]:
        self.scene_revision += 1
        entry = {"revision": self.scene_revision, "label": label, "source": source, "utc": datetime.now(timezone.utc).isoformat()}
        self.operations.append(entry)
        return {"status": "success", "marker": entry}

    def recent(self, limit: int = 20) -> dict[str, Any]:
        return {"status": "success", "operations": self.operations[-limit:]}
