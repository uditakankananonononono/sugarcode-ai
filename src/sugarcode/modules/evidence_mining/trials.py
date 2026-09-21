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
    endpoint_names = []
    for kind, label in (("primaryOutcomes", "primary"), ("secondaryOutcomes", "secondary")):
        for outcome in outcomes.get(kind, []):
            if not outcome.get("measure"):
                continue
            item = f"{label}: {outcome['measure']}"
            if outcome.get("timeFrame"):
                item += f" ({outcome['timeFrame']})"
            endpoint_names.append(item)
    result = s.get("resultsSection") or {}
    effect_text = MISSING
    effect_direction = MISSING
    outcome_results = ((result.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or [])
    result_fragments = []
    for outcome in outcome_results:
        for analysis in outcome.get("analyses", []) or []:
            parts = [str(x) for x in (analysis.get("paramType"), analysis.get("paramValue")) if x not in (None, "")]
            if analysis.get("pValue") not in (None, ""):
                parts.append(f"p={analysis['pValue']}")
            if analysis.get("statisticalMethod"):
                parts.append(str(analysis["statisticalMethod"]))
            if parts:
                result_fragments.append(f"{outcome.get('title', 'outcome')}: " + "; ".join(parts))
    if result_fragments:
        # Numeric analyses are exposed verbatim. Direction is not inferred
        # without a reliable mapping of groups, estimand, and favorable sign.
        effect_text = " | ".join(result_fragments)
        effect_direction = "reported_not_inferred"
    eligibility = p.get("eligibilityModule") or {}
    population_parts = []
    if eligibility.get("sex"):
        population_parts.append(str(eligibility["sex"]))
    ages = [eligibility.get("minimumAge"), eligibility.get("maximumAge")]
    if any(ages):
        population_parts.append(" to ".join(str(x) for x in ages if x))
    if eligibility.get("healthyVolunteers") is not None:
        population_parts.append("healthy volunteers: " + str(eligibility["healthyVolunteers"]).lower())
    population = "; ".join(population_parts) or MISSING
    return EvidenceRecord(source="ClinicalTrials.gov", source_id=nct,
        title=ident.get("briefTitle") or ident.get("officialTitle") or MISSING,
        url=f"https://clinicaltrials.gov/study/{nct}" if nct != MISSING else MISSING,
        publication_date=(status.get("studyFirstPostDateStruct") or {}).get("date", MISSING),
        study_type=design.get("studyType", MISSING), sample_size=enroll.get("count", MISSING),
        population=population,
        intervention="; ".join(interventions) or MISSING, endpoints=endpoint_names,
        effect_direction=effect_direction, effect_text=effect_text,
        status=status.get("overallStatus", MISSING), raw=s)
