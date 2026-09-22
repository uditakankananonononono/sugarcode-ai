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


AA3_TO_1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V",
}


def _geometry_terms(pocket_residues_full: list[dict], lig: dict) -> dict:
    """Geometry-informed terms from REAL coordinates (named as such):
    enclosure bonus (buried pockets bind better) and size-fit penalty
    (ligand much larger than the pocket cannot be accommodated)."""
    import numpy as np
    coords = np.array([r["ca"] for r in pocket_residues_full])
    center = coords.mean(axis=0)
    span = float(np.linalg.norm(coords - center, axis=1).max())
    n = len(coords)
    enclosure = min(1.0, n / 25.0)              # more lining residues -> more enclosed
    enclosure_bonus = round(-0.9 * enclosure, 2)
    # crude pocket "volume" ~ sphere spanning the lining residues; ligand size ~ heavy atoms
    fit_ratio = lig["heavy_atoms"] / max(8.0, n * 1.6)
    size_penalty = round(2.5 * max(0.0, fit_ratio - 1.0), 2)
    return {"enclosure_bonus": enclosure_bonus, "size_fit_penalty": size_penalty,
            "pocket_span_A": round(span, 1), "pocket_residues": n,
            "pocket_center": [round(float(v), 1) for v in center]}


def dock_into_structure(identifier: str, smiles: str, pocket_index: int = 0,
                        chain: str | None = None, offline: bool = False) -> dict:
    """Dock into a REAL structure: live PDB/AlphaFold coordinates, geometry
    pockets (via Alpha Fold UI's real-coordinate detector), composition
    complementarity plus enclosure/size-fit terms. Provenance is explicit."""
    from ..alpha_fold_ui.core import _real_pockets
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
        raise ValueError(f"no geometry pocket found in {identifier}"
                         + (f" chain {chain}" if chain else ""))
    if pocket_index >= len(pockets):
        raise IndexError(f"pocket_index {pocket_index} out of range - {len(pockets)} found")
    chosen = set(pockets[pocket_index]["residues"])
    lining = [r for r in residues if r["resnum"] in chosen]
    pocket_seq = "".join(AA3_TO_1.get(r["resname"], "G") for r in lining)
    base = dock(pocket_seq, smiles, pocket_start=lining[0]["resnum"] - 1)
    geom = _geometry_terms(lining, base["ligand"])
    dg = round(base["binding_dg_kcal_mol"] + geom["enclosure_bonus"]
               + geom["size_fit_penalty"], 2)
    kd_um = round(1e6 * math.exp(dg / 0.593), 3) if dg < 10 else float("inf")
    base.update({
        "structure": {"identifier": identifier, "source": s["source"],
                      "chain": chain, "n_residues": s["n_residues"],
                      **({"resolution_A": s.get("resolution_A"), "method": s.get("method")}
                         if "resolution_A" in s or "method" in s else
                         {"mean_plddt": s.get("mean_plddt")})},
        "pocket": {"index": pocket_index, "n_pockets_found": len(pockets),
                   "center": geom["pocket_center"], "span_A": geom["pocket_span_A"],
                   "lining_residues": [f"{r['resname']}{r['resnum']}{r['chain']}"
                                       for r in lining]},
        "geometry_terms": geom,
        "binding_dg_kcal_mol": dg,
        "estimated_kd_uM": kd_um,
        "scoring_note": ("composition complementarity + real-geometry enclosure/size-fit; "
                         "no force-field minimization - a screening proxy, not a free energy"),
    })
    return base

# Explicit configurational search and thermodynamic extensions; no learned scorer.
import random
import numpy as np

def pose_energy(receptor_xyz,ligand_xyz,receptor_charges=None,ligand_charges=None,hbond_pairs=(),solvation=.0):
    r=np.asarray(receptor_xyz,float); l=np.asarray(ligand_xyz,float); rq=np.asarray(receptor_charges if receptor_charges is not None else np.zeros(len(r))); lq=np.asarray(ligand_charges if ligand_charges is not None else np.zeros(len(l))); vdw=elec=0
    for i,a in enumerate(r):
        for j,b in enumerate(l):
            d=max(.8,float(np.linalg.norm(a-b))); sr=(3.5/d)**6; vdw+=.08*(sr*sr-2*sr); elec+=.2*rq[i]*lq[j]/d
    hb=-sum(max(0,1-abs(float(np.linalg.norm(r[i]-l[j]))-2.8)/1.2) for i,j in hbond_pairs); return {'vdw':vdw,'electrostatic':elec,'hbond':hb,'solvation':float(solvation),'total':vdw+elec+hb+solvation}

def transform_pose(coords,translation=(0,0,0),axis=(0,0,1),angle=0):
    c=np.asarray(coords,float); a=np.asarray(axis,float); a=a/(np.linalg.norm(a)+1e-12); K=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]]); R=np.eye(3)+math.sin(angle)*K+(1-math.cos(angle))*(K@K); return (c@R.T+np.asarray(translation)).tolist()

def monte_carlo_dock(receptor_xyz,ligand_xyz,steps=100,temperature=.6,seed=0):
    rng=random.Random(seed); current=np.asarray(ligand_xyz,float); e=pose_energy(receptor_xyz,current)['total']; best=(e,current.copy()); trace=[]
    for step in range(steps):
        proposal=np.asarray(transform_pose(current,[rng.gauss(0,.3) for _ in range(3)],[rng.random() for _ in range(3)],rng.gauss(0,.15))); pe=pose_energy(receptor_xyz,proposal)['total']; accepted=pe<e or rng.random()<math.exp(min(0,(e-pe)/temperature));
        if accepted: current,e=proposal,pe
        if e<best[0]: best=(e,current.copy())
        trace.append({'step':step,'energy':e,'accepted':accepted})
    return {'best_energy':best[0],'best_pose':best[1].tolist(),'trajectory':trace,'acceptance_rate':sum(x['accepted'] for x in trace)/max(1,steps)}

def ensemble_docking(pocket_ensembles,smiles):
    poses=[{**dock(p,smiles),'conformation':i} for i,p in enumerate(pocket_ensembles)]; poses.sort(key=lambda x:x['binding_dg_kcal_mol']); dg=np.array([p['binding_dg_kcal_mol'] for p in poses]); w=np.exp(-(dg-dg.min())/.593); w=w/w.sum(); return {'poses':poses,'conformational_weights':w.tolist(),'ensemble_dg':float(-.593*math.log(np.exp(-dg/.593).mean())),'best':poses[0]}

def binding_thermodynamics(dg,rotatable_bonds,displaced_waters=0,temperature_k=298):
    entropy_penalty=.003*temperature_k*rotatable_bonds; solvent_gain=.35*displaced_waters; enthalpy=dg-entropy_penalty+solvent_gain; return {'delta_h_kcal_mol':enthalpy,'minus_t_delta_s_kcal_mol':entropy_penalty-solvent_gain,'delta_g_kcal_mol':dg,'temperature_k':temperature_k}

def competitive_binding(ligands,concentrations_uM):
    if len(ligands)!=len(concentrations_uM): raise ValueError('length mismatch')
    terms=[c/max(1e-12,l['estimated_kd_uM']) for l,c in zip(ligands,concentrations_uM)]; z=1+sum(terms); return {'unbound_fraction':1/z,'occupancies':[x/z for x in terms]}

def interaction_fingerprint(pocket,smiles):
    d=dock(pocket,smiles); terms=d['energy_terms']; return {'hydrogen_bond':int(terms['hbond']<0),'hydrophobic':int(terms['vdw']<0),'electrostatic':int(terms['electrostatic']<-.1),'aromatic':int(terms['aromatic']<0),'key_residues':d['key_residues']}

def relative_free_energy(pocket,reference_smiles,analogs):
    ref=dock(pocket,reference_smiles)['binding_dg_kcal_mol']; return {'reference':reference_smiles,'analogs':[{'smiles':s,'delta_delta_g':dock(pocket,s)['binding_dg_kcal_mol']-ref} for s in analogs]}

def docking_report(pocket,library,ensembles=None):
    screen=virtual_screen(pocket,library); detailed=[{**dock(pocket,s),'fingerprint':interaction_fingerprint(pocket,s)} for s in library]; return {'screen':screen,'detailed':detailed,'ensemble':ensemble_docking(ensembles,library[0]) if ensembles and library else None,'model_status':'Transparent composition/physics scoring and stochastic search; no trained GNN and values are screening proxies, not experimental free energies.'}

def docking_diagnostics(pocket,smiles):
    d=dock(pocket,smiles); f=d['ligand']; e=d['energy_terms']; return {'pocket_length':float(len(pocket)),'heavy_atoms':float(f['heavy_atoms']),'rings':float(f['rings']),'logp':f['logp_estimate'],'molecular_weight':f['mol_weight'],'hbond_capacity':float(f['hbond_capacity']),'vdw':e['vdw'],'hbond':e['hbond'],'electrostatic':e['electrostatic'],'desolvation':e['desolvation'],'aromatic':e['aromatic'],'binding_dg':d['binding_dg_kcal_mol'],'estimated_kd_uM':d['estimated_kd_uM'],'key_residue_count':float(len(d['key_residues']))}
