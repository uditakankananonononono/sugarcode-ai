from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

MISSING = "Missing"


@dataclass
class EvidenceRecord:
    source: str
    source_id: str
    title: str
    url: str
    publication_date: str = MISSING
    study_type: str = MISSING
    sample_size: int | str = MISSING
    population: str = MISSING
    intervention: str = MISSING
    comparator: str = MISSING
    endpoints: list[str] = field(default_factory=list)
    effect_direction: str = MISSING
    effect_text: str = MISSING
    doi: str = MISSING
    status: str = MISSING
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self, *, include_raw: bool = False) -> dict[str, Any]:
        result = asdict(self)
        if not include_raw:
            result.pop("raw", None)
        return result
