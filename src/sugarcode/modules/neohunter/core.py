from __future__ import annotations

# HLA supertype anchor preferences (positions 2 and C-terminus for 9-mers)
HLA_SUPERTYPES = {
    "A*02:01": {"anchors": {1: "LMIV", 8: "VLAI"}, "weight": 1.0},
    "A*03:01": {"anchors": {1: "LIVM", 8: "KR"}, "weight": 0.9},
    "A*24:02": {"anchors": {1: "YF", 8: "FLIW"}, "weight": 0.9},
    "B*07:02": {"anchors": {1: "P", 8: "LFVIM"}, "weight": 0.85},
    "B*44:03": {"anchors": {1: "E", 8: "FWYL"}, "weight": 0.85},
}
HYDROPHOBIC = set("AILMFWVY")


def hla_binding(peptide: str, hla: str) -> dict:
    """Anchor-residue + hydrophobicity binding score (netMHC-style heuristic).

    Returns predicted affinity class (strong/weak/non-binder) and 0-1 score.
    """
    if hla not in HLA_SUPERTYPES:
        raise KeyError(f"unknown HLA {hla!r}; have {sorted(HLA_SUPERTYPES)}")
    if len(peptide) not in (8, 9, 10, 11):
        raise ValueError("peptide must be 8-11 aa")
    spec = HLA_SUPERTYPES[hla]
    p = peptide.upper()
    score = 0.2
    for pos, allowed in spec["anchors"].items():
        if pos < len(p) and p[pos] in allowed:
            score += 0.35
    hydro_frac = sum(1 for a in p if a in HYDROPHOBIC) / len(p)
    score += 0.2 * min(hydro_frac / 0.5, 1.0)
    # proline mid-peptide disrupts binding groove
    if "P" in p[2:-2]:
        score -= 0.15
    score = max(0.0, min(1.0, score))
    cls = "strong binder" if score >= 0.7 else "weak binder" if score >= 0.45 else "non-binder"
    return {"peptide": p, "hla": hla, "score": round(score, 3), "class": cls}


def _peptides_around(protein: str, pos: int, lengths=(9,)) -> list[str]:
    out = []
    for L in lengths:
        start = pos - L + 1
        for s in range(max(0, start), min(pos + 1, len(protein) - L + 1)):
            if s <= pos < s + L:
                out.append(protein[s:s + L])
    return sorted(set(out))


def find_neoantigens(tumor_protein: str, normal_protein: str, mutation_pos: int,
                     hlas: list[str] | None = None) -> dict:
    """Rank neoantigen candidates from a tumor-specific mutation.

    Peptides spanning the mutation are scored for HLA binding, immunogenicity
    (foreignness: difference from the normal peptide) and expression priors.
    """
    hlas = hlas or ["A*02:01", "B*07:02"]
    mut_aa = tumor_protein[mutation_pos] if 0 <= mutation_pos < len(tumor_protein) else None
    norm_aa = normal_protein[mutation_pos] if 0 <= mutation_pos < len(normal_protein) else None
    if mut_aa is None or norm_aa is None:
        raise ValueError("mutation_pos out of range for one of the sequences")
    if mut_aa == norm_aa:
        raise ValueError("no amino-acid difference at mutation_pos - not a neoantigen mutation")
    cands = []
    for pep in _peptides_around(tumor_protein, mutation_pos):
        idx = tumor_protein.find(pep)
        norm_pep = normal_protein[idx:idx + len(pep)] if idx + len(pep) <= len(normal_protein) else None
        foreignness = sum(1 for a, b in zip(pep, norm_pep or pep) if a != b) / len(pep)
        best = None
        for hla in hlas:
            b = hla_binding(pep, hla)
            if best is None or b["score"] > best["score"]:
                best = b
        immunogenicity = round(0.6 * best["score"] + 0.4 * min(foreignness * 3, 1.0), 3)
        cands.append({"peptide": pep, "normal_peptide": norm_pep,
                      "best_hla": best["hla"], "binding": best["class"],
                      "binding_score": best["score"],
                      "foreignness": round(foreignness, 3),
                      "immunogenicity": immunogenicity})
    cands.sort(key=lambda c: -c["immunogenicity"])
    return {
        "mutation": f"{norm_aa}{mutation_pos + 1}{mut_aa}",
        "hlas_typed": hlas,
        "candidates": cands,
        "top_candidate": cands[0] if cands else None,
        "vaccine_design": _vaccine(cands[:5]) if cands else None,
    }


def _vaccine(top: list[dict]) -> dict:
    return {"format": "synthetic long peptide (SLP) tandem construct",
            "sequence": "-".join(c["peptide"] for c in top),
            "adjuvant": "poly-ICLC",
            "note": "rank order preserved; include both HLA classes where typed"}
