from __future__ import annotations
import math
import random

# fragment library: (smiles, heavy_atoms, logp_contrib, hbd, hba, rotatable)
FRAGMENTS = {
    "benzene": ("c1ccccc1", 6, 1.7, 0, 0, 0),
    "pyridine": ("c1ccncc1", 6, 0.9, 0, 1, 0),
    "hydroxyl": ("O", 1, -1.0, 1, 1, 1),
    "amine": ("N", 1, -0.6, 1, 1, 1),
    "carboxyl": ("C(=O)O", 3, -0.3, 1, 2, 1),
    "amide": ("C(=O)N", 3, -0.8, 1, 2, 1),
    "methyl": ("C", 1, 0.5, 0, 0, 0),
    "ethyl_link": ("CC", 2, 1.0, 0, 0, 1),
    "fluorine": ("F", 1, 0.3, 0, 0, 0),
    "sulfonamide": ("S(=O)(=O)N", 5, -0.5, 1, 3, 1),
    "imidazole": ("c1c[nH]cn1", 5, 0.1, 1, 2, 0),
    "piperazine": ("C1CNCCN1", 6, -0.2, 2, 2, 0),
}
CYP_RISK_FRAGMENTS = {"aniline": 0.4, "benzene": 0.2, "imidazole": 0.5}
HERG_RISK = lambda logp, hbd: min(1.0, max(0.0, 0.15 * logp - 0.1 * hbd))  # lipophilic bases


def score_molecule(fragments: list[str]) -> dict:
    """ADMET profile from fragment composition (Crippen-style additivity)."""
    for f in fragments:
        if f not in FRAGMENTS:
            raise KeyError(f"unknown fragment {f!r}; have {sorted(FRAGMENTS)}")
    atoms = sum(FRAGMENTS[f][1] for f in fragments)
    logp = round(sum(FRAGMENTS[f][2] for f in fragments), 2)
    hbd = sum(FRAGMENTS[f][3] for f in fragments)
    hba = sum(FRAGMENTS[f][4] for f in fragments)
    rot = sum(FRAGMENTS[f][5] for f in fragments)
    mw = round(atoms * 13.5 + hbd * 8, 1)
    # aqueous solubility logS (Yalkowsky-style general solubility estimate)
    logS = round(0.5 - logp * 1.0 - 0.01 * (mw - 200) / 50, 2)
    lipinski = sum([mw <= 500, logp <= 5, hbd <= 5, hba <= 10])
    sa = round(max(1.0, 10.0 - rot * 0.4 - len(set(fragments)) * 0.5), 1)  # synthetic accessibility proxy
    return {
        "fragments": fragments, "mw": mw, "logP": logp, "logS": logS,
        "hbd": hbd, "hba": hba, "rotatable": rot,
        "lipinski_violations": 4 - lipinski,
        "cyp_risk": round(sum(CYP_RISK_FRAGMENTS.get(f, 0.05) for f in fragments) / len(fragments), 2),
        "herg_risk": round(HERG_RISK(logp, hbd), 2),
        "synthetic_accessibility": sa,
        "potency_prior": round(max(0.0, 0.5 + 0.1 * (hba - rot)), 2),
    }


def _objectives(m: dict, target_logp: float) -> dict:
    return {
        "potency": m["potency_prior"],
        "solubility": max(0.0, 1.0 + m["logS"] / 4),
        "safety": 1.0 - max(m["cyp_risk"], m["herg_risk"]),
        "logp_fit": max(0.0, 1.0 - abs(m["logP"] - target_logp) / 4),
        "feasibility": max(0.0, 1.0 - (m["synthetic_accessibility"] - 1) / 9),
    }


def pareto_front(candidates: list[dict]) -> list[dict]:
    """Non-dominated subset across objective vectors."""
    def dominates(a, b):
        oa, ob = a["objectives"], b["objectives"]
        return (all(oa[k] >= ob[k] for k in oa) and any(oa[k] > ob[k] for k in oa))
    return [c for c in candidates if not any(dominates(o, c) for o in candidates if o is not c)]


def generate(n: int = 12, target_logp: float = 2.5, seed: int = 42) -> dict:
    """Assemble candidate molecules from fragments, score ADMET, keep Pareto front."""
    rng = random.Random(seed)
    rings = [f for f in FRAGMENTS if FRAGMENTS[f][5] == 0 and FRAGMENTS[f][1] >= 5]
    groups = [f for f in FRAGMENTS if f not in rings]
    cands = []
    for _ in range(n):
        frag = [rng.choice(rings)] + [rng.choice(groups) for _ in range(rng.randint(1, 3))]
        m = score_molecule(frag)
        m["objectives"] = _objectives(m, target_logp)
        m["composite"] = round(sum(m["objectives"].values()) / 5, 3)
        cands.append(m)
    front = pareto_front(cands)
    for c in front:
        c["retrosynthesis"] = _retro(c["fragments"])
    return {
        "generated": n, "pareto_size": len(front),
        "pareto_front": sorted(front, key=lambda c: -c["composite"]),
        "target_logp": target_logp,
        "note": ("fragment-additive ADMET (Crippen-style LogP, Yalkowsky logS); "
                 "objective vector Pareto-filtered - trade-offs explicit, not blended"),
    }


def _retro(fragments: list[str]) -> list[dict]:
    steps = []
    for i, f in enumerate(fragments[1:], 1):
        steps.append({"step": i, "disconnection": f"remove {f}",
                      "reaction": "amide coupling" if f in ("amide", "carboxyl", "amine")
                      else "cross-coupling" if f in ("benzene", "pyridine", "imidazole")
                      else "alkylation"})
    return steps


def similarity_check(smiles: str, cutoff: int = 80, limit: int = 10,
                     offline: bool = False) -> dict:
    """Check a designed molecule against live ChEMBL: nearest known compounds
    (server-side Tanimoto), closest approved drug, and an honest novelty call.
    Failures are reported, never hidden."""
    from ...bio import chembl
    try:
        hits = chembl.similarity_search(smiles, cutoff=cutoff, limit=limit, offline=offline)
    except Exception as e:
        return {"smiles": smiles, "status": f"lookup failed: {type(e).__name__}: {e}",
                "neighbors": [], "novelty": "unknown"}
    if not hits:
        return {"smiles": smiles, "status": "ok", "neighbors": [],
                "novelty": f"no known molecule >= {cutoff}% similar in ChEMBL (novel scaffold space)",
                "closest": None}
    closest = hits[0]
    approved = [h for h in hits if (h.get("max_phase") or 0) and h["max_phase"] >= 3]
    novelty = ("close analog of known compounds" if closest["similarity"] >= 90
               else "related to known chemotypes" if closest["similarity"] >= 80
               else "novel at cutoff")
    return {"smiles": smiles, "status": "ok", "cutoff": cutoff, "neighbors": hits,
            "closest": {"chembl_id": closest["chembl_id"], "pref_name": closest["pref_name"],
                        "similarity": closest["similarity"], "max_phase": closest["max_phase"]},
            "approved_neighbors": [{"chembl_id": h["chembl_id"], "pref_name": h["pref_name"],
                                    "similarity": h["similarity"], "max_phase": h["max_phase"]}
                                   for h in approved],
            "novelty": novelty}
