"""Vina-form empirical scoring (Trott & Olson 2010 weights) on real pocket
coordinates. Rigid ligand: atoms typed from SMILES, laid on a 1.5 A chain;
best of a coarse translation grid around the pocket centroid. Honest limits:
no torsional sampling, no rotamer search - the torsion penalty is counted but
not optimized."""
from __future__ import annotations
import math

# Trott & Olson 2010 (AutoDock Vina) weights
W = {"gauss1": -0.0356, "gauss2": -0.00516, "repulsion": 0.840,
     "hydrophobic": -0.0351, "hbond": -0.587, "torsion": 0.0585}
VINA_RADII = {"C": 1.9, "N": 1.8, "O": 1.7, "S": 2.0, "F": 1.5, "P": 2.1}
HBOND = {"N", "O", "F"}
HYDROPHOBIC = {"C", "S"}


def vina_pair_terms(r: float, el_lig: str, el_prot: str) -> dict:
    """Vina interaction terms for one atom pair at distance r (Angstrom)."""
    ri = VINA_RADII.get(el_lig, 1.9) + VINA_RADII.get(el_prot, 1.9)
    d = r - ri  # surface distance
    g1 = math.exp(-((d / 0.5) ** 2)) if d < 8 else 0.0
    g2 = math.exp(-(((d - 3.0) / 2.0) ** 2)) if d < 8 else 0.0
    rep = (d ** 2) if d < 0 else 0.0
    # Vina ramps: 1 in the good zone, linear to 0 at the cutoff
    hydro = (1.0 if d < 0.5 else (1.5 - d) if d < 1.5 else 0.0) \
        if (el_lig in HYDROPHOBIC and el_prot in HYDROPHOBIC) else 0.0
    hb = (1.0 if d < -0.7 else (-d / 0.7) if d < 0.0 else 0.0) \
        if (el_lig in HBOND and el_prot in HBOND) else 0.0
    return {"gauss1": g1, "gauss2": g2, "repulsion": rep, "hydrophobic": hydro, "hbond": hb}


def vina_score_pose(ligand_atoms: list[dict], pocket_atoms: list[dict]) -> dict:
    """Weighted sum over all ligand x pocket atom pairs (cutoff 8 A surface)."""
    totals = {k: 0.0 for k in ("gauss1", "gauss2", "repulsion", "hydrophobic", "hbond")}
    for la in ligand_atoms:
        for pa in pocket_atoms:
            r = math.dist(la["xyz"], pa["xyz"])
            if r > 12:  # beyond any surface-distance cutoff
                continue
            t = vina_pair_terms(r, la["element"], pa["element"])
            for k in totals:
                totals[k] += t[k]
    return totals


def _ligand_from_smiles(smiles: str) -> list[dict]:
    """Typed ligand atoms on a straight 1.5 A chain (no conformer generator
    available - labeled limit)."""
    from .core import parse_smiles_features
    feats = parse_smiles_features(smiles)
    atoms = []
    x = 0.0
    for el, n in sorted(feats["atom_counts"].items()):
        for _ in range(n):
            atoms.append({"element": el, "xyz": (x, 0.0, 0.0)})
            x += 1.5
    return atoms


def dock_vina_grid(pocket_coords: list[dict], smiles: str, grid_step: float = 2.0,
                   n_steps: int = 4) -> dict:
    """Best Vina score over a translation cube around the pocket centroid.

    pocket_coords: [{element, xyz}] real pocket atoms (CA or full-atom).
    Returns best pose offset, score, and full term breakdown."""
    lig = _ligand_from_smiles(smiles)
    cx = sum(a["xyz"][0] for a in pocket_coords) / len(pocket_coords)
    cy = sum(a["xyz"][1] for a in pocket_coords) / len(pocket_coords)
    cz = sum(a["xyz"][2] for a in pocket_coords) / len(pocket_coords)
    # center the ligand chain on origin
    lx = sum(a["xyz"][0] for a in lig) / len(lig)
    best = None
    for ix in range(-n_steps, n_steps + 1):
        for iy in range(-n_steps, n_steps + 1):
            for iz in range(-n_steps, n_steps + 1):
                off = (cx - lx + ix * grid_step, cy + iy * grid_step, cz + iz * grid_step)
                placed = [{"element": a["element"],
                           "xyz": (a["xyz"][0] + off[0], a["xyz"][1] + off[1], a["xyz"][2] + off[2])}
                          for a in lig]
                terms = vina_score_pose(placed, pocket_coords)
                score = sum(W[k] * v for k, v in terms.items())
                if best is None or score < best["score"]:
                    best = {"score": score, "offset": off, "terms": terms, "placed": placed}
    rotatable = smiles.count("-") + sum(1 for i in range(1, len(smiles) - 1)
                                        if smiles[i].isupper() and smiles[i + 1].isupper())
    n_heavy = len(lig)
    final = best["score"] / (1 + W["torsion"] * rotatable)
    pose = [{"element": a["element"], "xyz": [round(v, 3) for v in a["xyz"]]}
            for a in best["placed"]]
    return {
        "smiles": smiles,
        "ligand_pose": pose,
        "complex_pdb": complex_pdb(pocket_coords, pose, remarks=[
            f"SUGARCODE VINA-FORM SCORE {final:.3f} (Trott & Olson 2010 weights)",
            "TERMS " + " ".join(f"{k}={v:.3f}" for k, v in best["terms"].items()),
            f"LIGAND {smiles}",
            "RIGID LINEAR LIGAND EMBEDDING, TRANSLATION GRID ONLY - SCREENING POSE"]),
        "vina_score": round(final, 3),
        "estimated_dg_kcal_mol": round(final, 3),  # Vina score is already kcal-ish affinity
        "raw_pairwise_sum": round(best["score"], 3),
        "terms": {k: round(v, 3) for k, v in best["terms"].items()},
        "best_offset": [round(o, 1) for o in best["offset"]],
        "rotatable_bonds": rotatable,
        "heavy_atoms": n_heavy,
        "weights": W, "weights_source": "Trott & Olson 2010 (AutoDock Vina)",
        "limits": ["rigid linear ligand embedding - no conformer generation",
                   "translation grid only - no rotational or torsional sampling",
                   "pocket atoms treated as rigid"],
    }


def complex_pdb(pocket_atoms: list[dict], ligand_atoms: list[dict],
                remarks: list[str] | None = None) -> str:
    """Annotated protein-ligand complex as PDB text (opens in PyMOL, Mol*,
    ChimeraX). Pocket atoms -> ATOM records (resname/resnum/chain/atom name
    used when present, else CA/UNK); ligand -> HETATM LIG, chain L; score and
    terms -> REMARK 999 lines."""
    lines = [f"REMARK 999 {r}"[:80] for r in (remarks or [])]
    serial = 1
    for i, a in enumerate(pocket_atoms, 1):
        x, y, z = a["xyz"]
        name = str(a.get("name", "CA"))[:4]
        el = str(a.get("element", "C"))[:2]
        lines.append(f"ATOM  {serial:5d} {name:<4s} {str(a.get('resname', 'UNK'))[:3]:>3s} "
                     f"{str(a.get('chain') or 'A')[:1]}{int(a.get('resnum', i)) % 10000:4d}    "
                     f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {el:>2s}")
        serial += 1
    lines.append("TER")
    for i, a in enumerate(ligand_atoms, 1):
        x, y, z = a["xyz"]
        el = str(a["element"])[:2]
        name = f"{el}{i}"[:4]
        lines.append(f"HETATM{serial:5d} {name:<4s} LIG L   1    "
                     f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {el.upper():>2s}")
        serial += 1
    lines.append("END")
    return "\n".join(lines) + "\n"


def dock_vina_structure(identifier: str, smiles: str, chain: str | None = None,
                        pocket_center_resnum: int | None = None, radius: float = 12.0,
                        offline: bool = False) -> dict:
    """Vina-form scoring against a REAL structure pocket (RCSB/AlphaFold).

    Pocket = residues within `radius` of the given center residue (or the whole
    chain if none given). CA atoms stand in for the protein."""
    from ...bio.structures import fetch_pdb, fetch_alphafold
    if len(identifier) == 4 and identifier[0].isdigit():
        s = fetch_pdb(identifier, offline=offline)
    else:
        s = fetch_alphafold(identifier, offline=offline)
    residues = s["residues"]
    if chain:
        residues = [r for r in residues if r["chain"] == chain]
    if pocket_center_resnum is not None:
        ctr = [r for r in residues if r["resnum"] == pocket_center_resnum]
        if not ctr:
            raise ValueError(f"residue {pocket_center_resnum} not in structure")
        c0 = ctr[0]["ca"]
        residues = [r for r in residues
                    if sum((r["ca"][k] - c0[k]) ** 2 for k in range(3)) <= radius ** 2]
    pocket_atoms = [{"element": "C", "xyz": r["ca"], "resnum": r["resnum"],
                     "resname": r.get("resname", "UNK"), "chain": r.get("chain")}
                    for r in residues]
    out = dock_vina_grid(pocket_atoms, smiles)
    out["structure"] = {"identifier": identifier, "source": s["source"],
                        "chain": chain, "pocket_residues": len(residues)}
    return out
