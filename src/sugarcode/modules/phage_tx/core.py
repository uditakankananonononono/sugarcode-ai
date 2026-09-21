from __future__ import annotations
import random

PHAGE_LIBRARY = {
    "phiKZ": {"targets": ["Pseudomonas_aeruginosa"], "receptor": "LPS",
              "burst": 180, "latent_min": 50},
    "T4": {"targets": ["Escherichia_coli"], "receptor": "LPS/OmpC", "burst": 150, "latent_min": 25},
    "K": {"targets": ["Staphylococcus_aureus"], "receptor": "wall_teichoic", "burst": 90, "latent_min": 40},
    "phiAB6": {"targets": ["Acinetobacter_baumannii"], "receptor": "capsule", "burst": 120, "latent_min": 35},
    "vB_EfaS": {"targets": ["Enterococcus_faecalis"], "receptor": "Epa", "burst": 60, "latent_min": 45},
    "M13": {"targets": ["Escherichia_coli"], "receptor": "F_pilus", "burst": 0, "latent_min": 0},
}
RESISTANCE_MECHANISMS = {
    "LPS": "LPS modification (waaL mutation)",
    "LPS/OmpC": "OmpC loss (porin down-regulation)",
    "wall_teichoic": "WTA glycosylation change (tarM)",
    "capsule": "capsule overproduction",
    "Epa": "epa locus phase variation",
    "F_pilus": "plasmid loss",
}
RECEPTOR_REDUNDANCY = {"LPS": ["capsule", "Epa"], "OmpC": ["capsule"],
                       "capsule": ["LPS", "wall_teichoic"], "Epa": ["LPS"],
                       "wall_teichoic": ["capsule"], "F_pilus": ["LPS/OmpC"]}


def match_phages(pathogen: str) -> dict:
    """Match a pathogen to phages in the library; flag receptor-based resistance
    routes and suggest complementary pairings."""
    hits = {name: spec for name, spec in PHAGE_LIBRARY.items() if pathogen in spec["targets"]}
    if not hits:
        raise KeyError(f"no phage for {pathogen}; library covers "
                       f"{sorted({t for s in PHAGE_LIBRARY.values() for t in s['targets']})}")
    entries = []
    for name, spec in hits.items():
        rec = spec["receptor"]
        entries.append({
            "phage": name, "receptor": rec, "burst_size": spec["burst"],
            "latent_min": spec["latent_min"],
            "lytic": spec["burst"] > 0,
            "resistance_risk": RESISTANCE_MECHANISMS[rec],
            "complementary_receptors": RECEPTOR_REDUNDANCY.get(rec.split("/")[0], []),
        })
    entries.sort(key=lambda e: -e["burst_size"])
    return {
        "pathogen": pathogen,
        "matches": entries,
        "best": entries[0],
        "monitoring": ["qPCR bacterial load 0/6/24/48h",
                       "plaque assay on therapy-sample isolates (resistance emergence)",
                       "receptor gene sequencing of breakthrough isolates"],
    }


def evolve_cocktail(pathogen: str, rounds: int = 3, seed: int = 42) -> dict:
    """Model cocktail composition to suppress resistance: pair phages with
    non-overlapping receptors, iterate against simulated escape mutants."""
    rng = random.Random(seed)
    matched = match_phages(pathogen)["matches"]
    lytic = [m for m in matched if m["lytic"]]
    cocktail, receptors = [], set()
    for m in lytic:
        rec = m["receptor"].split("/")[0]
        if rec not in receptors:
            cocktail.append(m["phage"])
            receptors.add(rec)
    if len(cocktail) < 2 and len(lytic) > 1:
        cocktail = [m["phage"] for m in lytic[:2]]
    history = []
    kill = 0.85
    for r in range(rounds):
        escape_rate = round(0.3 ** len(cocktail) * (0.8 + 0.4 * rng.random()), 4)
        kill = round(min(0.999, kill + 0.05 * len(cocktail)), 4)
        history.append({"round": r + 1, "kill_fraction": kill,
                        "escape_mutant_rate": escape_rate})
    return {
        "pathogen": pathogen, "cocktail": cocktail,
        "receptor_coverage": sorted(receptors),
        "evolution_history": history,
        "final_escape_rate": history[-1]["escape_mutant_rate"],
        "strategy": ("non-overlapping receptor targets force simultaneous multi-locus "
                     "mutations for escape - escape rate falls exponentially with cocktail size"),
        "personalized_match": "re-screen patient isolate against cocktail before dosing",
    }
