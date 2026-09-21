from __future__ import annotations
import re
from collections.abc import Iterable
from .models import EvidenceRecord, MISSING


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def deduplicate(records: Iterable[EvidenceRecord]) -> list[EvidenceRecord]:
    """Deduplicate by source ID, DOI, then normalized title, preserving order."""
    seen: set[tuple[str, str]] = set()
    out = []
    for r in records:
        keys = []
        if r.source_id != MISSING:
            keys.append((r.source.casefold(), r.source_id.casefold()))
        if r.doi != MISSING:
            keys.append(("doi", r.doi.casefold().removeprefix("https://doi.org/")))
        if r.title != MISSING:
            keys.append(("title", _norm(r.title)))
        if keys and any(k in seen for k in keys):
            continue
        seen.update(keys)
        out.append(r)
    return out


def build_evidence_table(records: Iterable[EvidenceRecord], *, include_raw: bool = False) -> list[dict]:
    """Return a stable, JSON-serializable evidence table for other modules."""
    return [r.to_dict(include_raw=include_raw) for r in deduplicate(records)]
