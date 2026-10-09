"""Gap telemetry for Sugarcode module self-improvement.

Modules report capability gaps (unhandled intents, repeated errors, feature
requests) as structured events. Events are append-only JSONL so detection
survives restarts and can be audited.
"""
from __future__ import annotations

import json
import math
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from .json_values import InvalidTelemetryValue, snapshot_json

GAP_KINDS = ("capability_miss", "unhandled_intent", "repeated_error", "feature_request")


@dataclass(frozen=True)
class GapEvent:
    module_slug: str
    signature: str
    kind: str = "capability_miss"
    detail: str = ""
    exemplar: Any = None
    event_id: str = field(default_factory=lambda: uuid4().hex)
    at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        for text in (self.module_slug, self.signature, self.kind, self.detail, self.event_id):
            if type(text) is not str:
                raise InvalidTelemetryValue("event text fields must be strings")
        if (type(self.at) not in (int, float)
                or (type(self.at) is float and not math.isfinite(self.at))
                or abs(self.at) > 1_000_000_000_000):
            raise InvalidTelemetryValue("event timestamp must be finite and within supported range")
        if self.kind not in GAP_KINDS:
            raise ValueError(f"unknown gap kind {self.kind!r}")
        if not self.signature.strip():
            raise ValueError("signature must not be empty")


class GapEventStore:
    """Append-only JSONL store, one file per module slug."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, module_slug: str) -> Path:
        safe = "".join(c for c in module_slug if c.isalnum() or c in "-_")
        if safe != module_slug or not safe:
            raise ValueError(f"unsafe module slug {module_slug!r}")
        return self._root / f"{safe}.gap-events.jsonl"

    def append(self, event: GapEvent) -> None:
        raw = {name: getattr(event, name) for name in (
            "module_slug", "signature", "kind", "detail", "exemplar", "event_id", "at")}
        line = json.dumps(snapshot_json(raw), sort_keys=True, allow_nan=False)
        with self._lock, self._path(event.module_slug).open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def all(self, module_slug: str) -> list[GapEvent]:
        path = self._path(module_slug)
        if not path.exists():
            return []
        events: list[GapEvent] = []
        with self._lock:
            lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = snapshot_json(json.loads(line))
                if type(raw) is not dict or raw.get("module_slug") != module_slug:
                    raise InvalidTelemetryValue("invalid event module")
                event = GapEvent(
                    module_slug=raw["module_slug"], signature=raw["signature"],
                    kind=raw.get("kind", "capability_miss"), detail=raw.get("detail", ""),
                    exemplar=raw.get("exemplar"), event_id=raw.get("event_id", uuid4().hex),
                    at=raw.get("at", 0.0),
                )
            except (ValueError, TypeError, KeyError, RecursionError) as exc:
                raise InvalidTelemetryValue(
                    f"invalid historical telemetry row {line_number}; repair required") from exc
            events.append(event)
        return events
