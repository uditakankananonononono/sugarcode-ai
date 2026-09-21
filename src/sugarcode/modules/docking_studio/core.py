from __future__ import annotations
import math
import re

# residue physicochemical classes for pocket-ligand complementarity
RES_PROPS = {
    "hydrophobic": set("AILMFWVPG"), "positive": set("KRH"), "negative": set("DE"),
    "polar": set("STNQCY"), "aromatic": set("FWYH"),
}
ATOM_PROPS = {
    "C": {"hydrophobic": 1.0, "charge": 0.0, "hbond": 0.0, "aromatic": 0.0},
    "N": {"hydrophobic": 0.0, "charge": 0.5, "hbond": 1.0, "aromatic": 0.0},
    "O": {"hydrophobic": 0.0, "charge": -0.5, "hbond": 1.0, "aromatic": 0.0},
    "S": {"hydrophobic": 0.5, "charge": 0.0, "hbond": 0.3, "aromatic": 0.0},
    "F": {"hydrophobic": 0.2, "charge": 0.0, "hbond": 0.2, "aromatic": 0.0},
    "P": {"hydrophobic": 0.0, "charge": -1.0, "hbond": 0.5, "aromatic": 0.0},
}


def parse_smiles_features(smiles: str) -> dict:
    """Feature extraction from a SMILES string: atom counts, ring/aromatic flags,
    rough LogP (fragment heuristic), H-bond capacity, rotatable bonds."""
    atoms = re.findall(r"Cl|Br|[A-Z][a-z]?|[cnops]", smiles)
    counts: dict[str, int] = {}
    aromatic_c = smiles.count("c")
    for a in atoms:
        a0 = a if a in ("Cl", "Br") else a[0].upper()
        counts[a0] = counts.get(a0, 0) + 1
    n_c = counts.get("C", 0) + aromatic_c
    n_hetero = sum(v for k, v in counts.items() if k not in ("C", "H"))
    rings = sum(smiles.count(d) for d in "123456789")
    rotatable = max(0, smiles.count("-") + len(re.findall(r"(?<![=\#])[A-Z] [A-Z]", smiles)))
    logp = 0.54 * n_c + 0.28 * aromatic_c - 1.0 * n_hetero  # fragment-style heuristic
    mw = (12.01 * n_c + 14.01 * counts.get("N", 0) + 16.0 * counts.get("O", 0)
          + 32.07 * counts.get("S", 0) + 19.0 * counts.get("F", 0)
          + 30.97 * counts.get("P", 0) + 35.45 * smiles.count("Cl") + 79.9 * smiles.count("Br")
          + 1.008 * max(0, 2 * n_c + 2 + n_hetero - rings))
    return {
        "smiles": smiles, "atom_counts": counts, "heavy_atoms": len(atoms),
        "aromatic_carbons": aromatic_c, "rings": rings,
        "logp_estimate": round(logp, 2), "mol_weight": round(mw, 1),
        "hbond_capacity": counts.get("N", 0) + counts.get("O", 0),
        "lipinski_ro5": {
            "mw_ok": mw < 500, "logp_ok": logp < 5,
            "hbd_ok": counts.get("N", 0) + counts.get("O", 0) <= 5,
        },
    }


def _pocket_profile(pocket_residues: str) -> dict:
    total = len(pocket_residues) or 1
    return {k: sum(1 for r in pocket_residues if r in v) / total
            for k, v in RES_PROPS.items()}


def _score(pocket: dict, lig: dict) -> dict:
    """Complementarity scoring: vdw-ish (hydrophobic match), electrostatic
    (charge balance), H-bond (polar/donor-acceptor overlap), desolvation penalty."""
    counts = lig["atom_counts"]
    heavy = max(1, lig["heavy_atoms"])
    lig_hyd = counts.get("C", 0) / heavy
    lig_pol = (counts.get("N", 0) + counts.get("O", 0)) / heavy
    vdw = 2.2 * min(pocket["hydrophobic"], lig_hyd) * math.sqrt(heavy)
    elec = -3.0 * abs((pocket["positive"] - pocket["negative"])
                      - (counts.get("N", 0) - counts.get("O", 0)) / heavy) * 0.2
    hbond = 1.4 * min(pocket["polar"] + pocket["negative"], lig_pol) * lig["hbond_capacity"]
    desolv = -0.6 * lig["logp_estimate"] * (1 - pocket["hydrophobic"])
    aromatic_bonus = 0.8 * min(pocket["aromatic"], lig["aromatic_carbons"] / heavy)
    dg = -(vdw + hbond + aromatic_bonus) + elec + desolv
    return {"vdw": round(-vdw, 2), "hbond": round(-hbond, 2),
            "electrostatic": round(elec, 2), "desolvation": round(desolv, 2),
            "aromatic": round(-aromatic_bonus, 2), "dg_kcal_mol": round(dg, 2)}


def dock(pocket_residues: str, smiles: str, pocket_start: int = 1) -> dict:
    """Dock one ligand into a pocket defined by its residue sequence."""
    pocket = _pocket_profile(pocket_residues)
    lig = parse_smiles_features(smiles)
    terms = _score(pocket, lig)
    dg = terms["dg_kcal_mol"]
    kd_um = round(1e6 * math.exp(dg / 0.593), 3) if dg < 10 else float("inf")  # RT at 298K
    key = [f"{r}{pocket_start + i + 1}" for i, r in enumerate(pocket_residues)
           if r in "STNQCYHDEKR" ][:6]
    return {
        "ligand": lig, "pocket_profile": {k: round(v, 3) for k, v in pocket.items()},
        "energy_terms": terms, "binding_dg_kcal_mol": dg,
        "estimated_kd_uM": kd_um,
        "key_residues": key,
        "suggested_mutations": _mutations(pocket_residues, lig, pocket_start),
        "visualization": _pose_summary(pocket_residues, terms),
    }


def _mutations(pocket: str, lig: dict, start: int) -> list[dict]:
    out = []
    counts = lig["atom_counts"]
    for i, r in enumerate(pocket):
        if r in "AGILV" and (counts.get("N", 0) + counts.get("O", 0)) >= 3:
            out.append({"mutation": f"{r}{start + i + 1}S",
                        "rationale": "add H-bond donor/acceptor for polar ligand"})
        elif r in "DE" and counts.get("N", 0) > counts.get("O", 0):
            out.append({"mutation": f"{r}{start + i + 1}K",
                        "rationale": "reverse charge to favor basic ligand"})
    return out[:4]


def _pose_summary(pocket: str, terms: dict) -> dict:
    return {"type": "3d_pose_payload",
            "interactions": [{"kind": k, "energy": v} for k, v in terms.items()
                             if k != "dg_kcal_mol" and v != 0],
            "pocket_length": len(pocket)}


def virtual_screen(pocket_residues: str, library: list[str], top_n: int = 10) -> dict:
    """Rank a chemical library against one pocket."""
    scored = []
    for smi in library:
        try:
            d = dock(pocket_residues, smi)
            scored.append({"smiles": smi, "dg": d["binding_dg_kcal_mol"],
                           "kd_uM": d["estimated_kd_uM"]})
        except Exception:
            continue
    scored.sort(key=lambda x: x["dg"])
    return {"pocket_length": len(pocket_residues), "screened": len(scored),
            "hits": scored[:top_n],
            "best": scored[0] if scored else None}
