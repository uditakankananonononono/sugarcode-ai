"""Cross-source evidence mining facade for downstream SugarCode modules."""
from __future__ import annotations
from pathlib import Path
from .client import EvidenceAPIError
from .pubmed import PubMedClient
from .trials import ClinicalTrialsClient
from .table import build_evidence_table


class EvidenceMiner:
    """Query PubMed and ClinicalTrials.gov into one stable evidence table.

    ``strict=True`` is fail-closed: either source failing aborts the result. A
    caller may explicitly choose partial results with ``strict=False``; source
    errors are then returned in-band and are never silently discarded.
    """
    def __init__(self, cache_dir: str | Path, *, pubmed_email: str | None = None,
                 pubmed_api_key: str | None = None):
        root = Path(cache_dir)
        self.pubmed = PubMedClient(root / "pubmed", email=pubmed_email, api_key=pubmed_api_key)
        self.trials = ClinicalTrialsClient(root / "clinicaltrials")

    def mine(self, query: str, *, pubmed_limit: int = 20, trial_limit: int = 20,
             offline: bool = False, strict: bool = True, include_raw: bool = False) -> dict:
        records, errors = [], {}
        for name, call in (
            ("PubMed", lambda: self.pubmed.query(query, limit=pubmed_limit, offline=offline)),
            ("ClinicalTrials.gov", lambda: self.trials.search(query, limit=trial_limit, offline=offline)),
        ):
            try:
                records.extend(call())
            except (EvidenceAPIError, ValueError) as exc:
                if strict:
                    raise
                errors[name] = f"{type(exc).__name__}: {exc}"
        table = build_evidence_table(records, include_raw=include_raw)
        return {"query": query, "offline": offline, "records": table,
                "record_count": len(table), "source_errors": errors}
