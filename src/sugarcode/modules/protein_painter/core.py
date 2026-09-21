from __future__ import annotations
import random
from ..alpha_fold_ui.core import chou_fasman, _confidence
from ...bio.sequence import molecular_weight, hydrophobicity_profile

FOLD_TEMPLATES = {
    "enzyme": {"pattern": "HHHHHCCEEEEECCHHHHHCCEEEECCHHHHH", "active": "HDE",
               "keywords": ["catalyze", "enzyme", "redox", "hydrolyze", "synthase"]},
    "binder": {"pattern": "HHHHHHHHHHCCHHHHHHHHHCCHHHHHHHHH", "active": "DERY",
               "keywords": ["bind", "antigen", "receptor", "antibody", "affibody"]},
    "structural": {"pattern": "EEEEECCEEEEECCEEEEECCEEEEE", "active": "",
                   "keywords": ["scaffold", "structural", "fiber", "matrix"]},
    "transporter": {"pattern": "HHHHHHHHHHHHCCHHHHHHHHHHHH", "active": "NKR",
                    "keywords": ["transport", "channel", "pump", "pore"]},
}
# propensity-guided amino acid choice per secondary class
AA_FOR = {
    "H": "ALMEQKRHF", "E": "VILTFYW", "C": "GSTNPDAG",
}


def _pick_template(description: str) -> str:
    d = description.lower()
    for name, t in FOLD_TEMPLATES.items():
        if any(k in d for k in t["keywords"]):
            return name
    return "enzyme"


def _design_sequence(pattern: str, active_residues: str, rng: random.Random) -> tuple[str, list[int]]:
    coils = [i for i, ss in enumerate(pattern) if ss == "C"]
    mid = len(pattern) // 2
    active_sites = []
    if active_residues and coils:
        start = min(coils, key=lambda c: abs(c - mid))
        tail = sorted(i for i in coils if i >= start)
        active_sites = tail[:len(active_residues)]
    seq = []
    ai = 0
    for i, ss in enumerate(pattern):
        if i in active_sites:
            seq.append(active_residues[ai])
            ai += 1
        else:
            seq.append(rng.choice(AA_FOR[ss]))
    return "".join(seq), active_sites


def _stability(seq: str, ss_pred: list[str]) -> dict:
    """Stability estimate: helix/strand content, hydrophobic-core fraction,
    and a pseudo-ddG from composition (real computation, heuristic model)."""
    hfrac = ss_pred.count("H") / len(ss_pred)
    efrac = ss_pred.count("E") / len(ss_pred)
    hydro = hydrophobicity_profile(seq, 7)
    core = sum(1 for v in hydro if v > 1.0) / max(1, len(hydro))
    score = 0.4 * hfrac + 0.3 * efrac + 0.3 * core
    ddg = round(-8.0 * score, 2)  # more negative = more stable
    return {"helix_fraction": round(hfrac, 3), "strand_fraction": round(efrac, 3),
            "hydrophobic_core_fraction": round(core, 3),
            "folding_dg_estimate": ddg,
            "stability_class": "high" if score > 0.55 else "moderate" if score > 0.4 else "low"}


def design_protein(description: str, length: int | None = None, seed: int = 0,
                   candidates: int = 8) -> dict:
    """Design amino-acid sequences from a functional description.

    Pipeline: intent -> fold template -> propensity-guided sequence sampling
    with active-site placement -> Chou-Fasman fold verification -> stability
    ranking. Returns the best candidate plus alternates.
    """
    rng = random.Random(seed)
    fold = _pick_template(description)
    template = FOLD_TEMPLATES[fold]
    pattern = template["pattern"]
    if length:
        reps = (length // len(pattern)) + 1
        pattern = (pattern * reps)[:length]
    results = []
    for c in range(candidates):
        seq, active = _design_sequence(pattern, template["active"], rng)
        ss_pred = chou_fasman(seq)
        match = sum(1 for want, got in zip(pattern, ss_pred) if want == got) / len(pattern)
        stab = _stability(seq, ss_pred)
        score = 0.6 * match + 0.4 * min(1.0, -stab["folding_dg_estimate"] / 8.0)
        results.append({
            "sequence": seq, "fold_match": round(match, 3),
            "predicted_ss": "".join(ss_pred),
            "active_site_residues": [f"{seq[i]}{i + 1}" for i in active],
            "active_site_positions": active,
            "stability": stab, "design_score": round(score, 4),
            "molecular_weight_da": round(molecular_weight(seq), 1),
        })
    results.sort(key=lambda r: -r["design_score"])
    best = results[0]
    return {
        "description": description,
        "fold_class": fold,
        "target_pattern": pattern,
        "best": best,
        "alternates": results[1:4],
        "verification": {
            "fold_verified": best["fold_match"] > 0.5,
            "method": "chou-fasman pattern agreement + stability model",
            "next_step": "submit best sequence to structure prediction for 3D check",
        },
        "applications": ("industrial biocatalyst" if fold == "enzyme" else
                         "therapeutic binder" if fold == "binder" else
                         "biomaterial" if fold == "structural" else "membrane transport"),
    }
