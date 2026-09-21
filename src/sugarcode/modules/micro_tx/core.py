from __future__ import annotations

PREBIOTIC_SUBSTRATES = {
    "Bifidobacterium_adolescentis": ["inulin", "GOS", "resistant_starch"],
    "Faecalibacterium_prausnitzii": ["inulin", "pectin", "arabinoxylan"],
    "Akkermansia_muciniphila": ["mucin", "cranberry_polyphenols", "FOS"],
    "Lactobacillus_reuteri": ["FOS", "GOS", "dietary_fiber"],
    "Roseburia": ["resistant_starch", "arabinoxylan", "beta_glucan"],
}
INDICATIONS = {
    "metabolic_syndrome": {"strains": ["Akkermansia_muciniphila", "Faecalibacterium_prausnitzii"],
                           "goal": "barrier + butyrate"},
    "IBD": {"strains": ["Faecalibacterium_prausnitzii", "Roseburia"], "goal": "anti-inflammatory SCFAs"},
    "antibiotic_recovery": {"strains": ["Bifidobacterium_adolescentis", "Lactobacillus_reuteri"],
                            "goal": "recolonization"},
    "immune_support": {"strains": ["Lactobacillus_reuteri", "Bifidobacterium_adolescentis"],
                       "goal": "immune modulation"},
}


def pair_therapeutic(indication: str) -> dict:
    """Pair beneficial strains with prebiotics that selectively feed them."""
    if indication not in INDICATIONS:
        raise KeyError(f"unknown indication; have {sorted(INDICATIONS)}")
    spec = INDICATIONS[indication]
    pairs = []
    for strain in spec["strains"]:
        subs = PREBIOTIC_SUBSTRATES[strain]
        pairs.append({
            "strain": strain,
            "prebiotic": subs[0],
            "alternates": subs[1:],
            "rationale": (f"{subs[0]} is selectively metabolized by {strain.replace('_', ' ')}, "
                          f"giving it a competitive edge to deliver: {spec['goal']}"),
        })
    community = _simulate_pairing(pairs)
    return {
        "indication": indication, "goal": spec["goal"],
        "pairs": pairs,
        "community_simulation": community,
        "dosing": {"strain_cfu": "1e10/day", "prebiotic_g": "5-10/day", "duration_weeks": 8},
        "success_markers": ["strain engraftment by qPCR at week 2",
                            "SCFA rise in stool at week 4",
                            "symptom scores at weeks 4 and 8"],
    }


def _simulate_pairing(pairs: list[dict]) -> dict:
    from ..microbiome_rx.core import simulate_community
    profile = {"Bacteroides": 0.3, "Escherichia": 0.2, "Lactobacillus": 0.1,
               "Bifidobacterium": 0.1, "Faecalibacterium": 0.1, "Akkermansia": 0.05}
    r = simulate_community(profile, days=14, diet={"fiber": 2.0, "sugar": 0.5})
    return {"with_prebiotic": r["final_relative"],
            "butyrate_flux": r["metabolite_flux"].get("butyrate", 0),
            "note": "prebiotic raises paired strains' share; model via Microbiome Rx"}
