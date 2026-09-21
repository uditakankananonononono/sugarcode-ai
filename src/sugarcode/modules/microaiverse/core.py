from __future__ import annotations

GROWTH_FACTORS = {
    "oligotroph": {"media": "dilute R2A / filtered environmental water",
                   "tricks": ["extended incubation (weeks)", "low nutrient"],
                   "partners": []},
    "syntroph": {"media": "defined medium + cross-feeding coculture",
                 "tricks": ["diffusion chamber with partner"],
                 "partners": ["Bacteroides (acetate donor)"]},
    "anaerobe_strict": {"media": "reduced medium + cysteine/resazurin",
                        "tricks": ["anaerobic chamber", "roll tubes"],
                        "partners": []},
    "auxotroph": {"media": "rich medium + specific growth factors",
                  "tricks": ["supplement predicted auxotrophies"],
                  "partners": []},
    "host_dependent": {"media": "cell culture / amoeba coculture",
                       "tricks": ["intra-amoebal enrichment"],
                       "partners": ["Acanthamoeba host"]},
}


def cultivation_plan(target: str, lifestyle: str = "syntroph",
                     genome_gaps: list[str] | None = None) -> dict:
    """Media recipe + co-culture strategy for a previously uncultured microbe.

    Uses metabolic gaps (missing biosynthesis pathways) to compute required
    supplements or cross-feeding partners.
    """
    if lifestyle not in GROWTH_FACTORS:
        raise KeyError(f"unknown lifestyle; have {sorted(GROWTH_FACTORS)}")
    spec = GROWTH_FACTORS[lifestyle]
    gaps = genome_gaps or []
    supplements = _supplements(gaps)
    partners = list(spec["partners"])
    for g in gaps:
        if g in ("amino_acid_biosynthesis", "vitamin_B12"):
            partners.append("Bacteroides (B12/amino acid donor)")
    return {
        "target": target, "lifestyle": lifestyle,
        "media_recipe": {"base": spec["media"], "supplements": supplements},
        "techniques": spec["tricks"],
        "coculture_partners": sorted(set(partners)),
        "predicted_success": round(0.3 + 0.2 * len(supplements) + 0.2 * bool(partners), 2),
        "natural_product_potential": ("uncultured taxa are enriched for novel biosynthetic "
                                      "gene clusters - genome-mine for NRPS/PKS after isolation"),
        "validation": ["colony formation on predicted medium",
                       "16S confirmation vs environmental sequence",
                       "growth curve in defined conditions"],
    }


def _supplements(gaps: list[str]) -> list[str]:
    table = {"amino_acid_biosynthesis": "casamino acids 0.1%",
             "vitamin_B12": "cobalamin 1 ug/L",
             "fatty_acid_synthesis": "tween-80 0.05%",
             "heme_synthesis": "hemin 5 mg/L",
             "purine_synthesis": "adenine 20 mg/L"}
    return [table[g] for g in gaps if g in table]
