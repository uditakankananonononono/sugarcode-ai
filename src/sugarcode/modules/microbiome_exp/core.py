from __future__ import annotations
import math
from collections import Counter

FUNCTIONAL_POTENTIAL = {
    "Faecalibacterium": ["butyrate production", "anti-inflammatory"],
    "Bacteroides": ["polysaccharide degradation", "bile acid metabolism"],
    "Lactobacillus": ["lactate production", "pathogen exclusion"],
    "Akkermansia": ["mucin degradation", "barrier support"],
    "Escherichia": ["pro-inflammatory potential", "vitamin K"],
    "Bifidobacterium": ["acetate production", "infant gut health"],
    "Clostridium": ["butyrate production (cluster IV)", "spore formation"],
    "Prevotella": ["fiber fermentation", "propionate production"],
}
DISEASE_ASSOCIATIONS = {
    "low_diversity": ["IBD", "obesity", "c.diff risk"],
    "Faecalibacterium_depleted": ["Crohn's disease"],
    "Escherichia_blooms": ["inflammation", "dysbiosis"],
    "Akkermansia_depleted": ["metabolic syndrome"],
}


def analyze_16s(counts: dict[str, int], metadata: dict | None = None) -> dict:
    """Taxonomic profile from genus-level read counts.

    Computes alpha diversity (Shannon, Simpson, richness), distributions,
    functional potential summary and disease-state correlations.
    """
    if not counts or sum(counts.values()) <= 0:
        raise ValueError("empty count table")
    total = sum(counts.values())
    rel = {g: c / total for g, c in counts.items()}
    shannon = -sum(p * math.log(p) for p in rel.values() if p > 0)
    simpson = 1 - sum(p ** 2 for p in rel.values())
    richness = len(counts)
    dominant = sorted(rel, key=rel.get, reverse=True)[:5]
    functions = {}
    for g, p in rel.items():
        if g in FUNCTIONAL_POTENTIAL and p > 0.01:
            for f in FUNCTIONAL_POTENTIAL[g]:
                functions[f] = functions.get(f, 0) + p
    flags = []
    if shannon < 1.5:
        flags.append({"flag": "low_diversity", "associations": DISEASE_ASSOCIATIONS["low_diversity"]})
    if rel.get("Faecalibacterium", 0) < 0.01:
        flags.append({"flag": "Faecalibacterium_depleted",
                      "associations": DISEASE_ASSOCIATIONS["Faecalibacterium_depleted"]})
    if rel.get("Escherichia", 0) > 0.2:
        flags.append({"flag": "Escherichia_blooms",
                      "associations": DISEASE_ASSOCIATIONS["Escherichia_blooms"]})
    if rel.get("Akkermansia", 0) < 0.005:
        flags.append({"flag": "Akkermansia_depleted",
                      "associations": DISEASE_ASSOCIATIONS["Akkermansia_depleted"]})
    return {
        "total_reads": total,
        "alpha_diversity": {"shannon": round(shannon, 3), "simpson": round(simpson, 3),
                            "richness": richness},
        "relative_abundance": {g: round(p, 4) for g, p in
                               sorted(rel.items(), key=lambda kv: -kv[1])},
        "dominant_genera": dominant,
        "functional_potential": {f: round(v, 3) for f, v in
                                 sorted(functions.items(), key=lambda kv: -kv[1])},
        "disease_correlations": flags,
        "publication_trend_link": "profile comparable against published cohort studies",
        "metadata": metadata or {},
    }
