from __future__ import annotations
from ..crispr_cargo.core import VEHICLES, pk_model

PROMOTERS = {
    "liver": ["TBG", "LP1"], "muscle": ["CK8", "MCK"], "cns": ["Syn1", "hGFAP"],
    "retina": ["RPE65", "CAG"], "heart": ["cTnT"], "ubiquitous": ["CAG", "EF1a"],
}


def optimize_gene_therapy(tissue: str, transgene_kb: float,
                          route: str = "iv") -> dict:
    """Vector + promoter + route optimization for a gene-therapy program."""
    prom = PROMOTERS.get(tissue.lower(), PROMOTERS["ubiquitous"])
    cands = []
    for name, v in VEHICLES.items():
        if not name.startswith("AAV"):
            continue
        trop = v["tissues"].get(tissue.lower(), 0.05)
        fit = 1.0 if transgene_kb <= v["cargo_kb"] else 0.0
        score = 0.6 * trop + 0.4 * fit
        cands.append({"vector": name, "score": round(score, 3), "tropism": trop,
                      "fits_transgene": bool(fit)})
    cands.sort(key=lambda c: -c["score"])
    best = cands[0] if cands and cands[0]["fits_transgene"] else None
    immune = _immune_model(best["vector"] if best else "AAV8", route)
    pk = pk_model(best["vector"], dose_ug=1e13 / 1e9, hours=24 * 7) if best else None
    return {
        "tissue": tissue, "transgene_kb": transgene_kb,
        "promoter_options": prom, "promoter_recommended": prom[0],
        "vector_ranking": cands, "selected": best,
        "delivery_route": route,
        "immune_response": immune,
        "pk": pk,
        "visualization": {"type": "route_map",
                          "stages": ["injection", "circulation", "tissue uptake",
                                     "endosomal escape", "nuclear entry", "expression"]},
        "efficiency_estimate": round(0.3 + 0.5 * (best["tropism"] if best else 0), 2),
    }


def _immune_model(vector: str, route: str) -> dict:
    preexisting = {"AAV2": 0.5, "AAV8": 0.25, "AAV9": 0.3}.get(vector, 0.3)
    route_risk = {"iv": 0.3, "intrathecal": 0.15, "subretinal": 0.05,
                  "intramuscular": 0.25}.get(route, 0.25)
    return {
        "preexisting_nab_prevalence": preexisting,
        "route_immunogenicity": route_risk,
        "mitigation": ["screen for neutralizing antibodies",
                       "transient immunosuppression (steroids/rituximab)",
                       "capsid engineering to escape NAbs (see Vector Opt)"],
        "combined_risk": round(1 - (1 - preexisting) * (1 - route_risk), 3),
    }
