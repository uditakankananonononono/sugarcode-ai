"""ClinicalTrials.gov API v2 client and structured study normalizer."""
from __future__ import annotations
from pathlib import Path
from .client import CachedHTTPClient, EvidenceAPIError
from .models import EvidenceRecord, MISSING

_BASE = "https://clinicaltrials.gov/api/v2/studies"


class ClinicalTrialsClient:
    def __init__(self, cache_dir: str | Path, *, http: CachedHTTPClient | None = None):
        self.http = http or CachedHTTPClient(cache_dir, min_interval=0.25)

    def search(self, query: str, *, limit: int = 20, offline: bool = False) -> list[EvidenceRecord]:
        if not query.strip():
            raise ValueError("query must not be blank")
        data = self.http.json(_BASE, {"query.term": query, "pageSize": max(1, min(int(limit), 100)),
                                     "format": "json"}, offline=offline)
        studies = data.get("studies")
        if not isinstance(studies, list):
            raise EvidenceAPIError("malformed ClinicalTrials.gov response")
        return [_study(x) for x in studies if isinstance(x, dict)]


def _study(s: dict) -> EvidenceRecord:
    p = s.get("protocolSection") or {}
    ident = p.get("identificationModule") or {}
    design = p.get("designModule") or {}
    status = p.get("statusModule") or {}
    arms = p.get("armsInterventionsModule") or {}
    outcomes = p.get("outcomesModule") or {}
    nct = ident.get("nctId") or MISSING
    enroll = design.get("enrollmentInfo") or {}
    interventions = [x.get("name") for x in arms.get("interventions", []) if x.get("name")]
    endpoint_names = [x.get("measure") for kind in ("primaryOutcomes", "secondaryOutcomes")
                      for x in outcomes.get(kind, []) if x.get("measure")]
    result = s.get("resultsSection") or {}
    effect_text = MISSING
    effect_direction = MISSING
    analyses = ((result.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or [])
    if analyses:
        effect_text = "Results posted; inspect structured outcome analyses"
        effect_direction = "reported_not_inferred"
    contacts = (p.get("contactsLocationsModule") or {}).get("centralContacts") or []
    population = contacts[0].get("role", MISSING) if contacts else MISSING
    return EvidenceRecord(source="ClinicalTrials.gov", source_id=nct,
        title=ident.get("briefTitle") or ident.get("officialTitle") or MISSING,
        url=f"https://clinicaltrials.gov/study/{nct}" if nct != MISSING else MISSING,
        publication_date=(status.get("studyFirstPostDateStruct") or {}).get("date", MISSING),
        study_type=design.get("studyType", MISSING), sample_size=enroll.get("count", MISSING),
        population=population,
        intervention="; ".join(interventions) or MISSING, endpoints=endpoint_names,
        effect_direction=effect_direction, effect_text=effect_text,
        status=status.get("overallStatus", MISSING), raw=s)
