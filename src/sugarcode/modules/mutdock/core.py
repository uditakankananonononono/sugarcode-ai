from __future__ import annotations
from ..docking_studio.core import dock, _pocket_profile, RES_PROPS

# Miyazawa-Jernigan-style contact class deltas (simplified class-level ddG)
_CLASS = {"hydrophobic": set("AILMFWVPG"), "positive": set("KRH"),
          "negative": set("DE"), "polar": set("STNQCY")}
DDG_CLASS_CHANGE = {
    ("hydrophobic", "polar"): 1.2, ("hydrophobic", "negative"): 1.6,
    ("hydrophobic", "positive"): 1.4, ("polar", "hydrophobic"): 0.9,
    ("positive", "negative"): 0.4, ("negative", "positive"): 0.4,
    ("positive", "hydrophobic"): 1.1, ("negative", "hydrophobic"): 1.1,
    ("polar", "polar"): 0.2, ("hydrophobic", "hydrophobic"): 0.3,
}


def _cls(aa: str) -> str:
    for k, v in _CLASS.items():
        if aa in v:
            return k
    return "polar"


def mutation_effect(pocket_residues: str, smiles: str, position: int,
                    mutant_aa: str, pocket_start: int = 1,
                    drug_name: str = "drug") -> dict:
    """Delta-delta-G of a point mutation on drug binding.

    Combines class-change contact penalty with pocket-complementarity shift
    recomputed through the docking scorer.
    """
    if not 0 <= position < len(pocket_residues):
        raise ValueError("position outside pocket")
    wt_aa = pocket_residues[position]
    mutant = pocket_residues[:position] + mutant_aa + pocket_residues[position + 1:]
    wt = dock(pocket_residues, smiles, pocket_start)
    mt = dock(mutant, smiles, pocket_start)
    ddg_score = mt["binding_dg_kcal_mol"] - wt["binding_dg_kcal_mol"]
    class_pen = DDG_CLASS_CHANGE.get((_cls(wt_aa), _cls(mutant_aa)), 0.5)
    ddg = round(0.6 * ddg_score + 0.4 * class_pen, 3)
    resistance = ("high" if ddg > 1.5 else "moderate" if ddg > 0.5 else "low")
    return {
        "mutation": f"{wt_aa}{pocket_start + position + 1}{mutant_aa}",
        "drug": drug_name,
        "wt_dg": wt["binding_dg_kcal_mol"], "mutant_dg": mt["binding_dg_kcal_mol"],
        "ddg_kcal_mol": ddg,
        "affinity_change_fold": round(2.718 ** (ddg / 0.593), 2),
        "resistance_risk": resistance,
        "hotspot": ddg > 1.0,
    }


def resistance_scan(pocket_residues: str, drugs: dict[str, str],
                    pocket_start: int = 1) -> dict:
    """Forecast cross-drug resistance: scan all pocket positions x 20 AAs.

    Returns resistance hotspots (positions where many mutations hurt binding
    across several drugs) and a per-drug vulnerability profile.
    """
    per_drug: dict[str, dict] = {}
    hotspot_counts: dict[int, int] = {}
    for name, smi in drugs.items():
        worst = []
        for pos in range(len(pocket_residues)):
            best_gain = -1e9
            best_mut = None
            for aa in "ACDEFGHIKLMNPQRSTVWY":
                if aa == pocket_residues[pos]:
                    continue
                r = mutation_effect(pocket_residues, smi, pos, aa, pocket_start, name)
                if r["ddg_kcal_mol"] > best_gain:
                    best_gain = r["ddg_kcal_mol"]
                    best_mut = r["mutation"]
            if best_gain > 1.0:
                hotspot_counts[pos] = hotspot_counts.get(pos, 0) + 1
            worst.append({"position": pocket_start + pos + 1,
                          "max_ddg": round(best_gain, 3), "mutation": best_mut})
        per_drug[name] = {"positions": worst,
                          "most_vulnerable": max(worst, key=lambda w: w["max_ddg"])}
    hotspots = [{"position": pocket_start + p + 1, "drugs_affected": c}
                for p, c in sorted(hotspot_counts.items(), key=lambda kv: -kv[1])]
    return {
        "drugs": list(drugs),
        "per_drug": per_drug,
        "resistance_hotspots": hotspots,
        "cross_resistance_forecast": (f"{len([h for h in hotspots if h['drugs_affected'] > 1])} "
                                      "positions threaten multiple drugs - prioritize for "
                                      "next-generation analog design."),
    }


def live_mutation_context(gene: str, position: int, mutant_aa: str, smiles: str,
                          window: int = 12, offline: bool = False) -> dict:
    """Mutation effect grounded in a LIVE UniProt record: real sequence window
    around the mutated position, real feature annotations (domains, binding
    sites, active sites) deciding whether the change hits functional real estate.

    position is 1-based. Falls back with a named warning, never silently.
    """
    from ...bio import uniprot
    rec = uniprot.search(gene, offline=offline)
    if not rec or not rec.get("sequence"):
        return {"gene": gene, "source": "unavailable",
                "warning": "no reviewed UniProt entry with sequence",
                "fallback": "use mutation_effect with a manually supplied pocket"}
    seq = rec["sequence"]
    if not (1 <= position <= len(seq)):
        raise ValueError(f"{gene} is {len(seq)} aa; position {position} out of range")
    wt_aa = seq[position - 1]
    lo = max(0, position - 1 - window // 2)
    hi = min(len(seq), position + window // 2)
    pocket = seq[lo:hi]
    idx = position - 1 - lo
    base = mutation_effect(pocket, smiles, idx, mutant_aa, pocket_start=lo,
                           drug_name=f"{gene}-ligand")
    feats = [f for f in rec["features"]
             if f.get("begin") and f.get("end")
             and f["begin"] <= position <= f["end"]
             and f["type"] in ("Domain", "Binding site", "Active site", "Site", "Region")]
    base.update({
        "gene": gene, "source": "UniProt (live)",
        "accession": rec["accession"], "protein_name": rec["protein_name"],
        "wt_residue": wt_aa,
        "window": {"start": lo + 1, "end": hi, "sequence": pocket},
        "functional_features_at_position": feats,
        "in_functional_site": bool(feats),
        "interpretation": ("mutation lands in annotated functional real estate - "
                           "resistance call carries extra weight" if feats else
                           "no annotated feature at this position; treat ddG as screening-level"),
    })
    return base


def structure_resistance_scan(identifier: str, drugs: dict[str, str],
                              pocket_index: int = 0, chain: str | None = None,
                              offline: bool = False) -> dict:
    """Cross-drug resistance forecast on a REAL structure pocket.

    Fetches the structure live (RCSB/AlphaFold), extracts the geometry pocket's
    lining sequence, runs the full resistance scan (all positions x 20 AAs x
    drugs) on the real lining. Provenance per result.
    """
    from ..alpha_fold_ui.core import _real_pockets
    from ..docking_studio.core import AA3_TO_1 as _A3
    from ...bio.structures import fetch_pdb, fetch_alphafold
    if len(identifier) == 4 and identifier[0].isdigit():
        s = fetch_pdb(identifier, offline=offline)
    else:
        s = fetch_alphafold(identifier, offline=offline)
    residues = s["residues"]
    if chain:
        residues = [r for r in residues if r["chain"] == chain]
    pockets = _real_pockets(residues)
    if not pockets:
        raise ValueError(f"no geometry pocket in {identifier}")
    if pocket_index >= len(pockets):
        raise IndexError(f"pocket_index {pocket_index} out of range - {len(pockets)} found")
    chosen = set(pockets[pocket_index]["residues"])
    lining = [r for r in residues if r["resnum"] in chosen]
    pocket_seq = "".join(_A3.get(r["resname"], "G") for r in lining)
    start = lining[0]["resnum"] - 1
    scan = resistance_scan(pocket_seq, drugs, pocket_start=start)
    scan.update({
        "structure": {"identifier": identifier, "source": s["source"],
                      "chain": chain, "pocket_index": pocket_index,
                      "n_pockets_found": len(pockets),
                      "lining": [f"{r['resname']}{r['resnum']}" for r in lining]},
        "note": "hotspot positions use real structure residue numbering",
    })
    return scan
