from __future__ import annotations
from omega.search import UnifiedSearch


def cross_domain_diagnosis(case: str, limit: int = 8) -> dict:
    """Mine the platform's full module corpus for non-standard angles on a case.

    Clusters search hits by sub-network to surface hidden diagnostic angles,
    then composes an experimental roadmap.
    """
    engine = UnifiedSearch()
    hits = engine.search(case, limit=limit * 2)
    clusters: dict[str, list[dict]] = {}
    for h in hits:
        clusters.setdefault(h["subnetwork"], []).append(h)
    perspectives = []
    for sn, mods in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        perspectives.append({
            "angle": sn,
            "relevant_modules": [m["name"] for m in mods[:3]],
            "diagnostic_hook": _hook(sn),
        })
    roadmap = _roadmap(case, perspectives)
    return {
        "case": case,
        "hidden_clusters": perspectives,
        "biomarker_candidates": _biomarkers(hits),
        "experimental_roadmap": roadmap,
        "novelty_note": ("cross-domain links assembled from platform-wide corpus; "
                         "each angle names the module that can execute it"),
    }


def _hook(subnetwork: str) -> str:
    return {
        "genome-editing": "search for causal variants / splice defects",
        "therapeutics": "match against known drug-response and disease models",
        "microbiome-phage": "check microbial contribution to phenotype",
        "cellular-systems": "test on patient-cell digital twin or organoid",
        "protein-engineering": "check for structural destabilization by variants",
        "synthetic-biology": "build a reporter of the disease pathway",
        "fabrication-evolution": "repurpose/evolve molecules against the target",
        "core-intelligence": "mine literature for analogous solved cases",
        "platform": "track metrics of the diagnostic program itself",
    }.get(subnetwork, "exploratory angle")


def _roadmap(case: str, perspectives: list[dict]) -> list[dict]:
    steps = []
    for i, p in enumerate(perspectives[:4]):
        steps.append({"phase": i + 1, "angle": p["angle"],
                      "action": p["diagnostic_hook"],
                      "modules": p["relevant_modules"]})
    steps.append({"phase": len(steps) + 1, "angle": "synthesis",
                  "action": "integrate findings into a ranked diagnostic hypothesis list",
                  "modules": ["Bio-Copilot"]})
    return steps


def _biomarkers(hits: list[dict]) -> list[str]:
    out = []
    for h in hits[:5]:
        out.append(f"{h['name']}-derived candidate marker panel")
    return out
