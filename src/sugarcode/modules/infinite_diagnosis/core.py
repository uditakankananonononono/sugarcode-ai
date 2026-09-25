from __future__ import annotations
from omega.search import UnifiedSearch
from ...bio.entrez import pubmed_ids, pubmed_abstracts, EntrezError


def cross_domain_diagnosis(case: str, limit: int = 8, offline: bool = False) -> dict:
    """Mine the platform's full module corpus for non-standard angles on a case.

    Clusters search hits by sub-network to surface hidden diagnostic angles,
    then composes an experimental roadmap.
    """
    engine = UnifiedSearch()
    # Real-case finding (module sweep 102): the raw case went straight to the
    # catalog ranker, so "and"/"with" produced every angle for real clinical
    # phrasings ("tall stature and lens dislocation" -> SynDroid, Micro-Tx...).
    # Rank on content words only.
    hits = engine.search(_content_query(case), limit=limit * 2)
    # Real-case finding (module sweep 102): module specs never name diseases,
    # symptoms or genes, so a case like "cystic fibrosis" matched zero modules
    # even though RareNet AI holds a curated record for it. Bridge the case
    # terms to rarenet's structured disease records and add that module.
    curated = _curated_disease_matches(case)
    if curated and not any(h["slug"] == "rarenet_ai" for h in hits):
        from omega.search import REGISTRY
        spec = REGISTRY.get("rarenet_ai")
        if spec is not None:
            hits.append({"slug": "rarenet_ai", "name": spec.name,
                         "subnetwork": spec.subnetwork, "summary": spec.summary,
                         "score": 0.0})
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
    leads, lit_status = _literature_leads(case, limit, offline)
    return {
        "case": case,
        "hidden_clusters": perspectives,
        "biomarker_candidates": leads,
        "experimental_roadmap": roadmap,
        "curated_disease_matches": curated,
        "catalog_status": (f"{len(hits)} module hits" if hits else
                           "no module in the catalog matched the case terms"),
        "novelty_note": ("angles come from a keyword match against Sugarcode's own module "
                         "catalog; biomarker candidates are PubMed records (live NCBI "
                         f"E-utilities) for the case terms - {lit_status}"),
    }


_FUNCTION_WORDS = {"and", "or", "with", "without", "of", "the", "a", "an", "in", "on",
                   "for", "to", "is", "are", "was", "were", "be", "has", "have", "had",
                   "who", "which", "that", "this", "from", "by", "at", "as", "but",
                   "not", "no", "his", "her", "their", "its", "into", "than"}


def _content_query(case: str) -> str:
    """Case text minus English function words (catalog ranking input)."""
    import re
    return " ".join(t for t in re.findall(r"[a-z0-9]+", case.lower())
                    if t not in _FUNCTION_WORDS)


def _curated_disease_matches(case: str) -> list[dict]:
    """Rarenet curated diseases whose name, symptom or gene appears in the case.

    Whole-phrase, case-insensitive matching on the structured record fields
    (disease key and symptoms with underscores read as spaces; gene symbols as
    whole words). Returns [] when nothing matches - nothing is inferred."""
    import re
    from ..rarenet_ai.core import RARE_DISEASES
    text = " " + re.sub(r"[^a-z0-9]+", " ", case.lower()) + " "
    out = []
    for disease, d in RARE_DISEASES.items():
        via = []
        name = disease.replace("_", " ")
        if f" {name} " in text or (name.endswith("s") and f" {name[:-1]} " in text):
            via.append(f"disease:{disease}")
        via += [f"symptom:{s}" for s in sorted(d["symptoms"])
                if f" {s.replace('_', ' ')} " in text]
        via += [f"gene:{g}" for g in d["genes"] if f" {g.lower()} " in text]
        if via:
            out.append({"disease": disease, "genes": list(d["genes"]), "matched_via": via})
    return out


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


_STOP = {"with", "and", "or", "of", "the", "a", "an", "in", "on", "for", "to",
         "patient", "child", "poor"}


def _literature_leads(case: str, limit: int, offline: bool) -> tuple[list[str], str]:
    """PubMed biomarker/diagnosis records for the case terms. Empty on no hits or
    lookup failure - the status string says which; nothing is invented."""
    import re
    terms = [t for t in re.findall(r"[A-Za-z0-9\-]+", case.lower()) if t not in _STOP]
    if not terms:
        return [], "no searchable case terms"
    query = " ".join(terms) + " AND (biomarker[tiab] OR diagnosis[tiab])"
    try:
        ids = pubmed_ids(query, retmax=limit, offline=offline)
        recs = pubmed_abstracts(ids, offline=offline) if ids else []
    except (EntrezError, ValueError, KeyError) as e:
        return [], f"literature lookup failed: {type(e).__name__}: {e}"
    if not recs:
        return [], f"PubMed returned no records for: {query}"
    return ([f"PMID {r['pmid']} ({r['year']}): {r['title']}" for r in recs],
            f"{len(recs)} PubMed records for: {query}")


# --- drop 20: joint symptom x variant view -------------------------------------
def joint_case_view(symptoms: list[str], variants: list[dict],
                    offline: bool = False) -> dict:
    """Joint view: rarenet symptom matching + the live variant evidence panel.

    Symptoms and variants are scored independently and then crossed: a variant
    with strong molecular support in a gene whose disease matches the symptom
    cluster is the lead hypothesis. Named sources per component; the joint
    call is a ranking for a clinician, never a diagnosis."""
    from ..rarenet_ai.core import diagnose, variant_evidence_panel
    sym = diagnose(symptoms)
    panel = variant_evidence_panel(variants, offline=offline)
    sym_diseases = {d["disease"]: d for d in sym.get("candidates", [])}
    # gene membership from the differential's own disease records (structured,
    # not text overlap)
    diff_genes = {g.upper() for d in sym_diseases.values() for g in d.get("genes", [])}
    joint = []
    for v in panel["panel"]:
        gene = (v.get("gene") or "").upper()
        # a 0.0 from failed lookups is "not assessed", not "no support"
        failed = [k for k in ("clinvar", "gnomad", "gene_constraint")
                  if "failed" in str((v.get(k) or {}).get("status", ""))]
        if failed and not v.get("score_components"):
            v = {**v, "evidence_class": "not assessed - lookups failed: " + ", ".join(failed)}
        gene_in_diff = gene in diff_genes
        lead = v["support_score"] >= 0.75 and (gene_in_diff or not sym_diseases)
        joint.append({
            "gene": gene, "hgvs": v.get("hgvs") or v.get("change"),
            "support_score": v["support_score"],
            "evidence_class": v["evidence_class"],
            "gene_named_in_symptom_differential": gene_in_diff,
            "lead_hypothesis": lead,
        })
    return {
        "symptom_differential": sym.get("candidates"),
        "variant_panel_summary": joint,
        "top_hypothesis": next((j for j in joint if j["lead_hypothesis"]), None),
        "limits": ["gene-disease membership comes from rarenet's curated rare-disease "
                   "records (small set); a gene absent there is not evidence against",
                   "symptom frequencies are heuristic"],
        "disclaimer": panel["disclaimer"],
    }
