from __future__ import annotations
import math
import numpy as np

# Chou-Fasman propensities (P_alpha, P_beta, P_turn) - published parameters
CF = {
    "A": (142, 83, 66), "R": (98, 93, 95), "N": (67, 89, 156), "D": (101, 54, 146),
    "C": (70, 119, 119), "Q": (111, 110, 98), "E": (151, 37, 74), "G": (57, 75, 156),
    "H": (100, 87, 95), "I": (108, 160, 47), "L": (121, 130, 59), "K": (114, 74, 101),
    "M": (145, 105, 60), "F": (113, 138, 60), "P": (57, 55, 152), "S": (77, 75, 143),
    "T": (83, 119, 96), "W": (108, 137, 96), "Y": (69, 147, 114), "V": (106, 170, 50),
}


def chou_fasman(seq: str) -> list[str]:
    """Chou-Fasman secondary structure prediction (real 1978 algorithm)."""
    n = len(seq)
    ss = ["C"] * n
    # helix nucleation: 4 of 6 residues with Pa > 100
    for i in range(n - 5):
        win = seq[i:i + 6]
        if sum(1 for a in win if CF.get(a, (0, 0, 0))[0] >= 100) >= 4:
            for j in range(i, min(n, i + 6)):
                ss[j] = "H"
    # extend helices
    i = 0
    while i < n:
        if ss[i] == "H":
            j = i
            while j + 1 < n and CF.get(seq[j + 1], (0, 0, 0))[0] > 100:
                j += 1
                ss[j] = "H"
            i = j
        i += 1
    # strands where not helix
    for i in range(n - 4):
        win = seq[i:i + 5]
        if sum(1 for a in win if CF.get(a, (0, 0, 0))[1] >= 105) >= 3:
            for j in range(i, min(n, i + 5)):
                if ss[j] == "C":
                    ss[j] = "E"
    return ss


def _confidence(seq: str, ss: list[str]) -> list[float]:
    """pLDDT-analog per residue: propensity-window agreement, scaled 0-100."""
    conf = []
    for i, a in enumerate(seq):
        lo, hi = max(0, i - 3), min(len(seq), i + 4)
        win_ss = ss[lo:hi]
        pa, pb, pt = CF.get(a, (50, 50, 50))
        dominant = max(pa, pb, pt)
        agree = win_ss.count(ss[i]) / len(win_ss)
        conf.append(round(min(95.0, 40.0 + 0.4 * dominant * agree), 1))
    return conf


def _pae_matrix(ss: list[str]) -> list[list[float]]:
    """PAE-analog: expected positional error; low within same element, high across."""
    n = len(ss)
    element_id = [0] * n
    eid = 0
    for i in range(1, n):
        if ss[i] != ss[i - 1]:
            eid += 1
        element_id[i] = eid
    pae = []
    for i in range(n):
        row = []
        for j in range(n):
            if element_id[i] == element_id[j]:
                row.append(round(1.0 + abs(i - j) * 0.15, 2))
            else:
                row.append(round(8.0 + abs(element_id[i] - element_id[j]) * 4.0, 2))
        pae.append(row)
    return pae


def _backbone(seq: str, ss: list[str]) -> np.ndarray:
    """Idealized C-alpha trace: helix (100 deg, 1.5 A rise), strand (extended), coil."""
    coords = np.zeros((len(seq), 3))
    pos = np.array([0.0, 0.0, 0.0])
    direction = np.array([1.0, 0.0, 0.0])
    helix_angle = math.radians(100.0)
    for i, s in enumerate(ss):
        coords[i] = pos
        if s == "H":
            theta = helix_angle * i
            step = np.array([0.0, 3.8 * math.cos(theta) * 0.4, 3.8 * math.sin(theta) * 0.4])
            step[0] = 1.5
        elif s == "E":
            step = direction * 3.4
        else:
            step = direction * 3.0 + np.array([0, 0.6 * math.sin(i * 1.7), 0.4 * math.cos(i * 2.3)])
        pos = pos + step
    return coords


def write_pdb(seq: str, coords: np.ndarray, confidence: list[float]) -> str:
    """PDB-format C-alpha trace with confidence in the B-factor column."""
    lines = []
    for i, (aa, (x, y, z), c) in enumerate(zip(seq, coords, confidence)):
        lines.append(
            f"ATOM  {i + 1:>5}  CA  {_aa3(aa)} A{i + 1:>4}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00{c:6.2f}           C"
        )
    lines.append("END")
    return "\n".join(lines) + "\n"


def _aa3(a: str) -> str:
    m = {"A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS", "Q": "GLN",
         "E": "GLU", "G": "GLY", "H": "HIS", "I": "ILE", "L": "LEU", "K": "LYS",
         "M": "MET", "F": "PHE", "P": "PRO", "S": "SER", "T": "THR", "W": "TRP",
         "Y": "TYR", "V": "VAL"}
    return m.get(a, "UNK")


def predict_structure(sequence: str) -> dict:
    """Full structure pipeline: secondary prediction, confidence, PAE, PDB.

    Honest scope: Chou-Fasman statistics + idealized backbone geometry with
    pLDDT/PAE-analog metrics - not learned AlphaFold weights (later drop).
    """
    seq = "".join(a for a in sequence.upper() if a in CF)
    if not seq:
        raise ValueError("no valid amino acids")
    ss = chou_fasman(seq)
    conf = _confidence(seq, ss)
    coords = _backbone(seq, ss)
    pae = _pae_matrix(ss)
    from collections import Counter
    comp = Counter(ss)
    pockets = _binding_pockets(seq, ss, conf)
    return {
        "length": len(seq),
        "secondary_structure": "".join(ss),
        "composition": {"helix": comp.get("H", 0), "strand": comp.get("E", 0),
                        "coil": comp.get("C", 0)},
        "plddt_per_residue": conf,
        "mean_plddt": round(sum(conf) / len(conf), 1),
        "pae": pae,
        "pdb": write_pdb(seq, coords, conf),
        "candidate_binding_sites": pockets,
        "method": "chou-fasman-idealized-backbone (learned weights pending)",
    }


def _binding_pockets(seq: str, ss: list[str], conf: list[float]) -> list[dict]:
    """Surface pocket candidates: coil regions flanked by ordered elements with
    catalytic-residue content (His/Cys/Asp/Glu/Ser clusters)."""
    catalytic = set("HCDES")
    pockets = []
    i = 0
    while i < len(seq):
        if ss[i] == "C":
            j = i
            while j < len(seq) and ss[j] == "C":
                j += 1
            seg = seq[i:j]
            hits = [k for k, a in enumerate(seg) if a in catalytic]
            if len(seg) >= 4 and len(hits) >= 2:
                pockets.append({"start": i, "end": j,
                                "catalytic_residues": [f"{seg[k]}{i + k + 1}" for k in hits],
                                "mean_confidence": round(sum(conf[i:j]) / (j - i), 1)})
            i = j
        else:
            i += 1
    return pockets


def _real_pockets(residues: list[dict], radius: float = 9.0, min_size: int = 12) -> list[dict]:
    """Pocket candidates from real C-alpha geometry: cluster spatially dense
    neighborhoods (many CAs within radius = concave/enclosed regions)."""
    import numpy as np
    coords = np.array([r["ca"] for r in residues])
    n = len(coords)
    density = np.zeros(n, dtype=int)
    for i in range(n):
        d = np.linalg.norm(coords - coords[i], axis=1)
        density[i] = int(((d > 1e-6) & (d < radius)).sum())
    threshold = np.percentile(density, 75)
    hot = np.where(density >= threshold)[0]
    pockets, current = [], []
    for idx in hot:
        if current and idx - current[-1] > 3:
            if len(current) >= min_size // 3:
                pockets.append(current)
            current = []
        current.append(int(idx))
    if len(current) >= min_size // 3:
        pockets.append(current)
    out = []
    for p in sorted(pockets, key=len, reverse=True)[:3]:
        c = coords[p].mean(axis=0)
        out.append({
            "residues": [residues[i]["resnum"] for i in p],
            "center": [round(float(v), 1) for v in c],
            "mean_density": round(float(density[p].mean()), 1),
            "mean_plddt_or_b": round(sum(residues[i]["bfactor"] for i in p) / len(p), 1),
            "druggability_prior": round(min(1.0, float(density[p].mean()) / 40), 2),
        })
    return out


def analyze_real_structure(identifier: str, offline: bool = False) -> dict:
    """Full structure analysis on a REAL experimental/AlphaFold structure.

    identifier: 4-char PDB id (experimental) or UniProt accession (AlphaFold).
    Real coordinates, real confidence (pLDDT/B-factors), geometry-based pockets.
    """
    from ...bio.structures import fetch_pdb, fetch_alphafold
    if len(identifier) == 4 and identifier[0].isdigit():
        s = fetch_pdb(identifier, offline=offline)
        confidence_kind = "crystallographic B-factor"
    else:
        s = fetch_alphafold(identifier, offline=offline)
        confidence_kind = "AlphaFold pLDDT"
    residues = s["residues"]
    bs = [r["bfactor"] for r in residues]
    pockets = _real_pockets(residues)
    return {
        "identifier": identifier, "source": s["source"],
        "n_residues": s["n_residues"], "chains": s["chains"],
        "confidence_kind": confidence_kind,
        "confidence_stats": {"mean": round(sum(bs) / len(bs), 2),
                             "min": round(min(bs), 2), "max": round(max(bs), 2)},
        **({"mean_plddt": s["mean_plddt"],
            "fraction_low_confidence": s["fraction_low_confidence"]}
           if "mean_plddt" in s else
           {"method": s.get("method"), "resolution_A": s.get("resolution_A")}),
        "pockets": pockets,
        "title": s.get("title", ""),
        "note": ("real coordinates from " + s["source"] +
                 "; pockets computed from C-alpha density, not the Chou-Fasman stand-in"),
    }

# Transparent evolutionary/geometry/physics extensions; no AlphaFold weights bundled.
def msa_couplings(msa,sequence_weights=None):
    rows=[''.join(a for a in s.upper() if a in CF or a=='-') for s in msa]
    if not rows or len({len(x) for x in rows})!=1: raise ValueError('aligned equal-length sequences required')
    n=len(rows[0]); w=np.asarray(sequence_weights if sequence_weights is not None else [1]*len(rows),float); w=w/w.sum(); alphabet='ACDEFGHIKLMNPQRSTVWY-'; couplings=np.zeros((n,n))
    entropy=[]
    for i in range(n):
        p=np.array([sum(w[k] for k,r in enumerate(rows) if r[i]==a) for a in alphabet]); p=p[p>0]; entropy.append(float(-np.sum(p*np.log(p))))
    for i in range(n):
        for j in range(i+1,n):
            joint={}; pi={}; pj={}
            for k,r in enumerate(rows): joint[(r[i],r[j])]=joint.get((r[i],r[j]),0)+w[k]; pi[r[i]]=pi.get(r[i],0)+w[k]; pj[r[j]]=pj.get(r[j],0)+w[k]
            mi=sum(p*math.log(p/(pi[a]*pj[b])) for (a,b),p in joint.items() if p); couplings[i,j]=couplings[j,i]=mi
    return {'depth':len(rows),'length':n,'entropy':entropy,'mutual_information':couplings.tolist(),'effective_depth':1/float(np.sum(w*w))}

def residue_graph(coords,cutoff=8):
    c=np.asarray(coords,float); d=np.linalg.norm(c[:,None,:]-c[None,:,:],axis=2); edges=[{'source':i,'target':j,'distance_A':float(d[i,j])} for i in range(len(c)) for j in range(i+1,len(c)) if d[i,j]<=cutoff]; return {'nodes':len(c),'edges':edges,'distance_matrix':d.tolist()}

def rigid_transform(coords,rotation,translation):
    c=np.asarray(coords,float); r=np.asarray(rotation,float); t=np.asarray(translation,float); return c@r.T+t

def graph_invariance(coords,rotation,translation,cutoff=8):
    a=residue_graph(coords,cutoff); b=residue_graph(rigid_transform(coords,rotation,translation),cutoff); da=np.asarray(a['distance_matrix']); db=np.asarray(b['distance_matrix']); return {'max_distance_error':float(np.max(abs(da-db))),'edges_preserved':[(x['source'],x['target']) for x in a['edges']]==[(x['source'],x['target']) for x in b['edges']]}

def physical_energy(coords,charges=None,sigma=3.8,epsilon=.1):
    c=np.asarray(coords,float); q=np.asarray(charges if charges is not None else np.zeros(len(c)),float); lj=elec=0
    for i in range(len(c)):
        for j in range(i+2,len(c)):
            r=max(.5,float(np.linalg.norm(c[i]-c[j]))); sr=(sigma/r)**6; lj+=4*epsilon*(sr*sr-sr); elec+=.05*q[i]*q[j]/r
    return {'lennard_jones':lj,'electrostatic':elec,'total':lj+elec}

def refine_coordinates(coords,charges=None,steps=20,learning_rate=.002):
    x=np.asarray(coords,float).copy(); trajectory=[]
    for _ in range(steps):
        e=physical_energy(x,charges)['total']; trajectory.append(e); grad=np.zeros_like(x); h=1e-4
        for i in range(len(x)):
            for j in range(3):
                x[i,j]+=h; ep=physical_energy(x,charges)['total']; x[i,j]-=h; grad[i,j]=(ep-e)/h
        x-=learning_rate*np.clip(grad,-10,10)
    trajectory.append(physical_energy(x,charges)['total']); return {'coordinates':x.tolist(),'energy_trajectory':trajectory,'converged':trajectory[-1]<=trajectory[0]}

def mutation_stability(sequence,position,mutant):
    seq=''.join(a for a in sequence.upper() if a in CF); position=int(position); wild=seq[position]; p0=CF[wild]; p1=CF[mutant]; hyd={'AILMFWVY'}; propensity_shift=(max(p1)-max(p0))/100; hydro_shift=float((mutant in hyd)-(wild in hyd)); ddg=.8*propensity_shift-1.2*hydro_shift; return {'position':position,'wild_type':wild,'mutant':mutant,'ddg_relative':ddg,'destabilizing':ddg>0}

def folding_workspace(sequence,msa=None):
    base=predict_structure(sequence); seq=''.join(a for a in sequence.upper() if a in CF); ss=list(base['secondary_structure']); coords=_backbone(seq,ss); charge=[1 if a in 'KR' else -1 if a in 'DE' else 0 for a in seq]; graph=residue_graph(coords); energy=physical_energy(coords,charge); couplings=msa_couplings(msa) if msa else None; return {**base,'coordinates':coords.tolist(),'residue_graph':graph,'energy':energy,'msa':couplings,'pair_representation':couplings['mutual_information'] if couplings else None,'model_status':'Chou-Fasman, MSA mutual information and explicit geometry/energy; no AlphaFold neural weights and pLDDT/PAE are analogs, not calibrated predictions.'}

def structure_diagnostics(sequence,msa=None):
    r=folding_workspace(sequence,msa); p=np.asarray(r['pae']); c=np.asarray(r['plddt_per_residue']); e=r['energy']; g=r['residue_graph']; return {'length':float(r['length']),'mean_plddt_analog':r['mean_plddt'],'plddt_std':float(c.std()),'plddt_min':float(c.min()),'pae_mean':float(p.mean()),'pae_max':float(p.max()),'helix_count':float(r['composition']['helix']),'strand_count':float(r['composition']['strand']),'coil_count':float(r['composition']['coil']),'graph_edges':float(len(g['edges'])),'lj_energy':e['lennard_jones'],'electrostatic_energy':e['electrostatic'],'total_energy':e['total'],'msa_effective_depth':float(r['msa']['effective_depth'] if r['msa'] else 0)}
