"""Mechanistic, hermetic support-routing engine for the Omega OS module network."""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Iterable, Mapping

from omega.registry import REGISTRY

SUBNETWORK_OWNERS: dict[str, list[str]] = {}
for _slug, _spec in REGISTRY.items():
    SUBNETWORK_OWNERS.setdefault(_spec.subnetwork, []).append(_slug)
for _modules in SUBNETWORK_OWNERS.values():
    _modules.sort()
MODULE_TO_NET = {m: net for net, mods in SUBNETWORK_OWNERS.items() for m in mods}
SLA_HOURS = {"security": 2, "bug": 8, "feature": 72, "custom_build": 240,
             "question": 24, "integration": 48}
VALID_TIERS = {"startup", "academic", "enterprise"}

KEYWORDS = {
    "security": ("security", "breach", "leak", "credential", "vulnerability"),
    "bug": ("error", "crash", "wrong", "fail", "bug", "broken", "traceback", "exception"),
    "custom_build": ("custom", "bespoke", "build", "tailor", "white-label"),
    "integration": ("integrate", "integration", "api", "pipeline", "connect", "deploy", "webhook"),
    "feature": ("add", "support", "feature", "would like", "request"),
}
URGENCY = {"blocked": 3, "production": 3, "urgent": 3, "deadline": 2,
           "today": 2, "soon": 1}
EXPERTISE = {
    "genomics": ("variant", "genome", "dna", "rna", "crispr", "sequence"),
    "therapeutics": ("therapy", "therapeutic", "drug", "dose", "patient", "clinical"),
    "bioinformatics": ("pipeline", "workflow", "vcf", "fastq", "bam", "analysis"),
    "platform": ("api", "deploy", "webhook", "authentication", "sdk", "container"),
    "data_governance": ("privacy", "consent", "phi", "hipaa", "gdpr", "security"),
}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[_-][a-z0-9]+)*", text.lower())


_SUFFIX = r"(?:s|es|ed|d|ing|ure|ures)?"


def _kw_hits(q: str, words) -> list[str]:
    """Whole-word keyword hits with simple inflections.  Plain substring tests
    matched "add" in "address", "api" in "rapid" and "build" in "rebuild"."""
    return [w for w in words if re.search(rf"(?<![a-z0-9]){re.escape(w)}{_SUFFIX}(?![a-z0-9])", q)]


def classify_inquiry(inquiry: str) -> dict:
    """Rule-based multi-label classification with auditable evidence."""
    if not isinstance(inquiry, str) or not inquiry.strip():
        raise ValueError("inquiry must be non-empty text")
    q = inquiry.lower()
    hits = {kind: _kw_hits(q, words) for kind, words in KEYWORDS.items()}
    hits = {k: v for k, v in hits.items() if v}
    precedence = ("security", "bug", "custom_build", "integration", "feature")
    primary = next((k for k in precedence if k in hits), "question")
    if primary == "feature" and "custom" in q:
        primary = "custom_build"
    urgency_hits = _kw_hits(q, URGENCY)
    return {"primary": primary, "labels": sorted(hits), "keyword_evidence": hits,
            "urgency_score": min(5, sum(URGENCY[w] for w in urgency_hits)),
            "urgency_evidence": urgency_hits}


def detect_modules(inquiry: str, module: str | None = None) -> list[dict]:
    """Resolve explicit and textual references against the live Omega registry."""
    if module is not None and module not in MODULE_TO_NET:
        raise KeyError(f"unknown module {module!r}")
    q = inquiry.lower().replace("-", "_").replace(" ", "_")
    found = {module} if module else set()
    flat = q.replace("_", "")
    # Longest slugs first; a matched span is blanked so "neuro_hub_dashboard"
    # no longer also reports its prefix "neuro_hub" (same for cellpainter_4d).
    # Slugs that share a key (syn_bio_studio / synbio_studio) stay reported
    # together - that name collision is genuinely ambiguous.
    keys: dict[str, list[str]] = {}
    for slug in MODULE_TO_NET:
        keys.setdefault(slug.replace("_", ""), []).append(slug)
    for key in sorted(keys, key=lambda k: (-len(k), k)):
        if key in flat:
            found.update(keys[key])
            flat = flat.replace(key, " " * len(key))
    return [{"module": slug, "sub_network": MODULE_TO_NET[slug]} for slug in sorted(found)]


def match_expertise(inquiry: str, modules: Iterable[Mapping] = ()) -> list[dict]:
    """Rank support expertise from lexical needs and module ownership."""
    words = set(_tokens(inquiry)); scores = Counter()
    reasons: dict[str, list[str]] = {k: [] for k in EXPERTISE}
    for domain, terms in EXPERTISE.items():
        for term in terms:
            if term in words:
                scores[domain] += 2; reasons[domain].append(term)
    for item in modules:
        net = str(item["sub_network"])
        scores[net] += 3
        reasons.setdefault(net, []).append(f"owns:{item['module']}")
    if not scores:
        scores["platform"] = 1; reasons["platform"].append("default intake")
    return [{"expertise": k, "score": int(v), "reasons": reasons.get(k, [])}
            for k, v in sorted(scores.items(), key=lambda x: (-x[1], x[0]))]


def knowledge_base_matches(inquiry: str, kind: str, modules: Iterable[Mapping]) -> list[dict]:
    """Return deterministic topic matches, rather than claiming external retrieval."""
    topics = {
        "crispr_opt": ("Guide scoring", ("guide", "pam", "off-target", "crispr")),
        "virtual_cell": ("Flux balance models", ("flux", "stoichiometry", "fba")),
        "docking_studio": ("Docking workflow", ("pocket", "dock", "ligand")),
        "platform": ("API integration", ("api", "webhook", "sdk", "integrate")),
    }
    q = inquiry.lower(); names = {m["module"] for m in modules}
    out = []
    for key, (title, terms) in topics.items():
        overlap = [t for t in terms if t in q]
        if overlap or key in names:
            out.append({"article_key": key, "title": title, "score": len(overlap) + 2*(key in names),
                        "matched_terms": overlap})
    return sorted(out, key=lambda x: (-x["score"], x["article_key"]))


def _sla(kind: str, tier: str, urgency: int) -> float:
    if tier not in VALID_TIERS:
        raise ValueError(f"tier must be one of {sorted(VALID_TIERS)}")
    factor = {"startup": 1.0, "academic": 1.0, "enterprise": .5}[tier]
    return max(1.0, SLA_HOURS[kind] * factor / (1 + .25*urgency))


def triage(inquiry: str, module: str | None = None, tier: str = "startup",
           submitted_at: datetime | None = None) -> dict:
    """Classify, route, prioritise, estimate SLA, and match knowledge resources."""
    cls = classify_inquiry(inquiry); modules = detect_modules(inquiry, module)
    experts = match_expertise(inquiry, modules)
    kind, urgency = cls["primary"], cls["urgency_score"]
    sla = _sla(kind, tier, urgency)
    submitted = submitted_at or datetime.now(timezone.utc)
    if submitted.tzinfo is None:
        submitted = submitted.replace(tzinfo=timezone.utc)
    priority_score = {"security": 5, "bug": 4, "integration": 3,
                      "custom_build": 3, "feature": 2, "question": 1}[kind] + urgency
    kb = knowledge_base_matches(inquiry, kind, modules)
    target = modules[0] if modules else {"module": None,
              "sub_network": experts[0]["expertise"] if experts else "platform"}
    digest = hashlib.sha256((inquiry.strip()+"|"+str(submitted.isoformat())).encode()).hexdigest()[:12]
    return {
        "ticket_id": f"NXS-{digest.upper()}", "classification": kind,
        "labels": cls["labels"], "keyword_evidence": cls["keyword_evidence"],
        "priority": "critical" if priority_score >= 7 else "high" if (kind == "bug" or priority_score >= 5) else
                    "medium" if priority_score >= 3 else "low",
        "priority_score": priority_score, "routed_to": target, "candidate_modules": modules,
        "expertise_matches": experts, "sla_hours": round(sla, 2),
        "response_due_at": (submitted + timedelta(hours=sla)).isoformat(),
        "tier_applied": tier, "kb_matches": kb, "kb_match": kb[0]["title"] if kb else None,
        "auto_resolvable": bool(kb) and kind == "question",
        "escalation": "security and domain lead" if kind == "security" else
                      "domain specialist on first response" if kind in {"bug", "custom_build"} else
                      "support engineer; specialist on follow-up",
        "model_status": "mechanistic hermetic routing; no trained or clinical claims",
    }


def custom_build_plan(request: str, constraints: Mapping | None = None) -> dict:
    """Turn a custom-build request into traceable work packages and acceptance gates."""
    constraints = dict(constraints or {}); q = request.lower()
    modules = detect_modules(request)
    formats = ("fastq", "bam", "vcf", "csv", "json", "fasta")
    # Contextual clauses prevent an output such as "returning JSON" from being
    # misreported as an input. Bare format mentions remain outputs only.
    inputs = [x for x in formats if re.search(rf"(?:ingest(?:ing)?|input|from|read(?:ing)?)\s+(?:an?\s+)?{x}\b", q)]
    outputs = [x for x in ("report", "api", "dashboard", "json", "csv", "model") if
               re.search(rf"(?:return(?:ing)?|output|export|produce|as)\s+(?:an?\s+)?{x}\b", q) or
               (x in {"report", "api", "dashboard", "model"} and x in q)]
    compliance = [x.upper() for x in ("hipaa", "gdpr", "gxp") if x in q]
    work = [
        {"phase": "discovery", "deliverable": "scope and data contract", "depends_on": []},
        {"phase": "prototype", "deliverable": "hermetic reference workflow", "depends_on": ["discovery"]},
        {"phase": "validation", "deliverable": "acceptance-test evidence", "depends_on": ["prototype"]},
        {"phase": "integration", "deliverable": "versioned deployment package", "depends_on": ["validation"]},
    ]
    risks = []
    if not inputs: risks.append("input format unspecified")
    if not outputs: risks.append("output contract unspecified")
    if "deadline" not in constraints: risks.append("delivery deadline unspecified")
    if not modules: risks.append("Omega module boundary unspecified")
    return {"request_type": "custom_build", "modules": modules, "input_formats": inputs,
            "output_formats": outputs, "compliance_mentions": compliance,
            "constraints": constraints, "work_packages": work, "open_risks": risks,
            "acceptance_gates": ["schema validation", "deterministic regression suite",
                                 "performance budget", "security review", "owner sign-off"],
            "model_status": "mechanistic hermetic planning; estimates require expert review"}


def integration_plan(source: str, destination: str, *, data_types: Iterable[str] = (),
                     requirements: Mapping | None = None) -> dict:
    """Build an executable systems-integration checklist with dependency ordering."""
    if not source.strip() or not destination.strip():
        raise ValueError("source and destination are required")
    types = sorted(set(map(str, data_types))); req = dict(requirements or {})
    steps = [
        {"id": "contract", "action": "define versioned schemas", "depends_on": []},
        {"id": "auth", "action": "configure least-privilege authentication", "depends_on": []},
        {"id": "ingest", "action": f"connect {source} to Omega OS", "depends_on": ["contract", "auth"]},
        {"id": "validate", "action": "validate and quarantine malformed records", "depends_on": ["ingest"]},
        {"id": "deliver", "action": f"write validated results to {destination}", "depends_on": ["validate"]},
        {"id": "observe", "action": "record latency, failures, and lineage", "depends_on": ["deliver"]},
    ]
    return {"source": source, "destination": destination, "data_types": types,
            "requirements": req, "steps": steps, "rollback": ["stop ingestion", "revoke credential",
            "restore last compatible schema", "replay idempotent records"],
            "tests": ["contract", "authentication", "idempotency", "failure recovery", "lineage"],
            "model_status": "mechanistic hermetic integration design"}


def schedule_queue(tickets: Iterable[Mapping], capacity_hours: float) -> dict:
    """Select support work under a capacity budget using exact 0/1 enumeration.

    The objective maximises priority-weighted SLA risk; deterministic tie-breaking
    prefers more tickets and then lexical ticket IDs. This is an exact solver for
    modest support batches rather than a greedy placeholder.
    """
    rows = [dict(t) for t in tickets]
    if capacity_hours < 0 or len(rows) > 22:
        raise ValueError("capacity must be non-negative and queue limited to 22 tickets")
    # Selection is tracked by row index.  The old code keyed rows by
    # ticket_id, defaulting to the position inside the chosen subset, so
    # tickets without IDs returned the wrong row and duplicate IDs returned
    # every row sharing the ID (over capacity).
    best = (-1.0, -1, (), 0.0, ())
    for mask in range(1 << len(rows)):
        idx = [i for i in range(len(rows)) if mask >> i & 1]
        hours = sum(float(rows[i].get("estimated_hours", 1)) for i in idx)
        if hours <= capacity_hours + 1e-12:
            value = sum(float(rows[i].get("priority_score", 1)) * float(rows[i].get("sla_risk", 1)) for i in idx)
            ids = tuple(sorted(str(rows[i].get("ticket_id", i)) for i in idx))
            candidate = (value, len(idx), tuple(reversed(ids)), hours, tuple(idx))
            if candidate[:3] > best[:3]: best = candidate
    chosen_idx = set(best[4])
    selected = [r for i, r in enumerate(rows) if i in chosen_idx]
    return {"selected": selected, "deferred": [r for i, r in enumerate(rows) if i not in chosen_idx],
            "used_hours": round(best[3], 6), "capacity_hours": capacity_hours,
            "objective_value": round(best[0], 6), "solver": "exact_binary_enumeration",
            "optimal": True}


def enhancement_features(inquiry: str, module: str | None = None,
                         tier: str = "startup") -> dict:
    """Return 56 independently meaningful support diagnostics/capabilities."""
    r = triage(inquiry, module, tier, submitted_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    tok = _tokens(inquiry); unique = set(tok); q = inquiry.lower()
    modules = r["candidate_modules"]; experts = r["expertise_matches"]
    funcs = {
      "ticket_identifier": r["ticket_id"], "primary_class": r["classification"],
      "secondary_label_count": len(r["labels"]), "priority_band": r["priority"],
      "priority_score": r["priority_score"], "sla_hours": r["sla_hours"],
      "response_deadline": r["response_due_at"], "service_tier": tier,
      "route_network": r["routed_to"]["sub_network"], "route_module": r["routed_to"]["module"] or "unassigned",
      "candidate_module_count": len(modules), "candidate_network_count": len({m["sub_network"] for m in modules}),
      "expertise_match_count": len(experts), "top_expertise": experts[0]["expertise"],
      "top_expertise_score": experts[0]["score"], "knowledge_match_count": len(r["kb_matches"]),
      "auto_resolution_candidate": r["auto_resolvable"], "escalation_path": r["escalation"],
      "token_count": len(tok), "unique_token_count": len(unique),
      "character_count": len(inquiry), "sentence_count": len(re.findall(r"[.!?]+", inquiry)) or 1,
      "question_present": "?" in inquiry, "code_block_present": "```" in inquiry,
      "url_present": bool(re.search(r"https?://", inquiry)), "email_present": bool(re.search(r"\b[^\s@]+@[^\s@]+\b", inquiry)),
      "stack_trace_present": "traceback" in q or "exception" in q, "error_code_present": bool(re.search(r"\b(?:4\d\d|5\d\d)\b", q)),
      "version_present": bool(re.search(r"\bv?\d+\.\d+", q)), "environment_present": any(x in q for x in ("linux","windows","macos","docker","kubernetes")),
      "reproduction_steps_present": any(x in q for x in ("steps to reproduce","repro","first","then")),
      "expected_behavior_present": "expected" in q, "actual_behavior_present": "actual" in q,
      "data_format_count": sum(x in q for x in ("fastq","bam","vcf","csv","json","fasta")),
      "api_mentioned": "api" in unique, "pipeline_mentioned": "pipeline" in unique,
      "deployment_mentioned": any(x in q for x in ("deploy","production","container")),
      "security_mentioned": any(x in q for x in KEYWORDS["security"]),
      "privacy_mentioned": any(x in q for x in ("privacy","phi","consent","hipaa","gdpr")),
      "clinical_context_mentioned": any(x in q for x in ("clinical","patient","therapeutic","therapy")),
      "research_context_mentioned": any(x in q for x in ("research","experiment","assay","study")),
      "customization_mentioned": any(x in q for x in KEYWORDS["custom_build"]),
      "integration_mentioned": any(x in q for x in KEYWORDS["integration"]),
      "feature_request_mentioned": any(x in q for x in KEYWORDS["feature"]),
      "failure_mentioned": any(x in q for x in KEYWORDS["bug"]),
      "urgency_score": classify_inquiry(inquiry)["urgency_score"],
      "urgency_evidence_count": len(classify_inquiry(inquiry)["urgency_evidence"]),
      "attachment_reference_present": any(x in q for x in ("attached","attachment","screenshot","log file")),
      "sample_identifier_present": bool(re.search(r"\b(?:sample|patient)[-_ ]?[a-z0-9]+", q)),
      "deadline_present": any(x in q for x in ("deadline","by monday","by tuesday","by wednesday","by thursday","by friday")),
      "blocking_language_present": any(x in q for x in ("blocked","cannot proceed","stopped")),
      "requested_output_present": any(x in q for x in ("report","dashboard","export","result")),
      "authentication_mentioned": any(x in q for x in ("oauth","token","credential","authentication")),
      "webhook_mentioned": "webhook" in unique, "batch_mode_mentioned": "batch" in unique,
      "real_time_mentioned": "real-time" in q or "realtime" in q,
    }
    assert len(funcs) == 56
    return funcs


def support_case(inquiry: str, *, module: str | None = None, tier: str = "startup",
                 constraints: Mapping | None = None) -> dict:
    """End-to-end Nexus Support case spanning inquiry, build, and integration needs."""
    routed = triage(inquiry, module, tier)
    result = {"triage": routed, "diagnostics": enhancement_features(inquiry, module, tier),
              "diagnostic_count": 56, "model_status": routed["model_status"]}
    if routed["classification"] == "custom_build":
        result["custom_build"] = custom_build_plan(inquiry, constraints)
    if routed["classification"] == "integration" or "integration" in routed["labels"]:
        result["integration_readiness"] = {"plan_required": True,
            "required_inputs": ["source", "destination", "data types", "authentication"]}
    return result
