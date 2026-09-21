from __future__ import annotations
from ..virtual_cell.core import MetabolicModel, demo_model, gene_knockout

# M. genitalium-style essentiality priors by functional category
CATEGORY_ESSENTIALITY = {
    "replication": 0.85, "transcription": 0.80, "translation": 0.90,
    "glycolysis": 0.60, "membrane_transport": 0.65, "cell_envelope": 0.55,
    "cofactor_biosynthesis": 0.50, "lipid_metabolism": 0.45,
    "nucleotide_metabolism": 0.55, "stress_response": 0.20,
    "motility": 0.05, "secondary_metabolism": 0.05, "unknown": 0.30,
}


def essentiality_scan(model: MetabolicModel | None = None) -> dict:
    """Knock every reaction; classify lethal/impaired/dispensable via FBA."""
    model = model or demo_model()
    results = []
    for rxn in model.reactions:
        ko = gene_knockout(model, rxn)
        results.append({"reaction": rxn, "growth_ratio": ko["growth_ratio"],
                        "class": ko["lethality"]})
    essential = [r for r in results if r["class"] == "lethal"]
    return {"model_reactions": len(results), "scan": results,
            "essential_reactions": [r["reaction"] for r in essential],
            "essential_fraction": round(len(essential) / len(results), 3)}


def design_minimal_genome(genes: list[dict] | None = None) -> dict:
    """Score a gene catalog by essentiality priors and propose the minimal set.

    genes: [{"name": str, "category": str, "size_bp": int}]
    Default: a 450-gene M. genitalium-flavored synthetic catalog.
    """
    if genes is None:
        genes = _default_catalog()
    scored = []
    for g in genes:
        prior = CATEGORY_ESSENTIALITY.get(g["category"], 0.3)
        scored.append({**g, "essentiality_prior": prior,
                       "keep": prior >= 0.45})
    kept = [g for g in scored if g["keep"]]
    dropped = [g for g in scored if not g["keep"]]
    genome_bp = sum(g.get("size_bp", 1000) for g in kept)
    original_bp = sum(g.get("size_bp", 1000) for g in genes)
    return {
        "input_genes": len(genes),
        "minimal_set_size": len(kept),
        "genome_size_bp": genome_bp,
        "reduction_fraction": round(1 - genome_bp / original_bp, 3),
        "kept_by_category": _count_by(kept, "category"),
        "dropped_by_category": _count_by(dropped, "category"),
        "metabolic_support": essentiality_scan(),
        "chassis_protocol": ["compile minimal set into 50-100 kb segments",
                             "assemble via yeast homologous recombination",
                             "genome transplantation into recipient cell",
                             "selection for replication-competent clones"],
    }


def _count_by(genes: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for g in genes:
        out[g[key]] = out.get(g[key], 0) + 1
    return out


def _default_catalog() -> list[dict]:
    import random
    rng = random.Random(7)
    cats = list(CATEGORY_ESSENTIALITY)
    weights = [8, 8, 10, 12, 10, 8, 6, 8, 8, 6, 4, 4, 8]
    genes = []
    for i in range(450):
        cat = rng.choices(cats, weights)[0]
        genes.append({"name": f"MG_{i + 1:03d}", "category": cat,
                      "size_bp": rng.randint(300, 3000)})
    return genes
