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


# Virtual C-alpha geometry (Oldfield & Hubbard 1994; Levitt 1976): consecutive
# trans CA-CA = 3.80 A; virtual bond angle / dihedral per secondary state.
CA_CA = 3.80
_CA_GEOM = {"H": (91.0, 50.0), "E": (123.0, -170.0), "C": (110.0, -120.0)}
_DIHEDRAL_FALLBACK = (-120.0, 60.0, -60.0, 180.0, 120.0, -170.0, 0.0, 90.0, -90.0)
MIN_NONBONDED_CA = 4.0


def _place(a, b, c, bond, angle_deg, torsion_deg):
    """NeRF: place atom d with |cd|=bond, angle(b,c,d)=angle, dihedral(a,b,c,d)=torsion."""
    ang, tor = math.radians(angle_deg), math.radians(torsion_deg)
    bc = c - b; bc /= np.linalg.norm(bc)
    n = np.cross(b - a, bc); n /= np.linalg.norm(n)
    m = np.cross(n, bc)
    d2 = np.array([-bond * math.cos(ang), bond * math.sin(ang) * math.cos(tor), bond * math.sin(ang) * math.sin(tor)])
    return c + d2[0] * bc + d2[1] * m + d2[2] * n


def _backbone(seq: str, ss: list[str]) -> np.ndarray:
    """Physically consistent C-alpha trace built by NeRF from ideal virtual geometry.

    Every consecutive CA-CA distance is 3.80 A; angles/dihedrals follow the
    predicted state (helix 91/50, strand 123/-170, coil 110/-120). Coil and
    junction residues try fallback dihedrals greedily so no non-adjacent pair
    (|i-j|>=3) sits closer than 4.0 A when avoidable. Idealized, not a fold prediction.
    """
    n = len(seq)
    coords = np.zeros((n, 3))
    if n == 0:
        return coords
    first = _CA_GEOM[ss[0]][0]
    seeds = [np.zeros(3), np.array([CA_CA, 0.0, 0.0])]
    t = math.radians(180.0 - first)
    seeds.append(seeds[1] + CA_CA * np.array([math.cos(t), math.sin(t), 0.0]))
    for i in range(min(n, 3)):
        coords[i] = seeds[i]
    for i in range(3, n):
        angle, pref = _CA_GEOM[ss[i - 1]]
        options = [pref] + [pref + d for d in (15, -15, 30, -30)] + list(_DIHEDRAL_FALLBACK)
        best, best_gap = None, -1.0
        for tor in options:
            x = _place(coords[i - 3], coords[i - 2], coords[i - 1], CA_CA, angle, tor)
            gap = float(np.min(np.linalg.norm(coords[: i - 2] - x, axis=1))) if i >= 3 else 99.0
            if gap >= MIN_NONBONDED_CA:
                best = x
                break
            if gap > best_gap:
                best, best_gap = x, gap
        coords[i] = best
    return coords


def backbone_geometry(coords) -> dict:
    """Geometry audit for a CA trace: bond lengths, virtual angles, clashes."""
    c = np.asarray(coords, float)
    if len(c) < 2:
        return {"n": len(c), "ca_ca_min": 0.0, "ca_ca_max": 0.0, "ca_ca_mean": 0.0, "min_nonadjacent": 0.0, "clash_count": 0, "angles_deg": []}
    bonds = np.linalg.norm(np.diff(c, axis=0), axis=1)
    ang = []
    for i in range(1, len(c) - 1):
        u, v = c[i - 1] - c[i], c[i + 1] - c[i]
        ang.append(math.degrees(math.acos(max(-1, min(1, float(u @ v / (np.linalg.norm(u) * np.linalg.norm(v))))))))
    d = np.linalg.norm(c[:, None] - c[None], axis=2)
    iu = np.triu_indices(len(c), 3)
    nb = d[iu] if len(iu[0]) else np.array([99.0])
    return {"n": len(c), "ca_ca_min": float(bonds.min()), "ca_ca_max": float(bonds.max()), "ca_ca_mean": float(bonds.mean()),
            "min_nonadjacent": float(nb.min()), "clash_count": int(np.sum(nb < 3.5)), "angles_deg": ang}


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

def _bond_energy(x,bond_length=CA_CA,k_bond=10.0):
    b=np.linalg.norm(np.diff(x,axis=0),axis=1) if len(x)>1 else np.zeros(0); return float(k_bond*np.sum((b-bond_length)**2))


def _project_bonds(x,bond_length=CA_CA):
    """SHAKE-style chain projection: keep each bond direction, reset its length."""
    y=x.copy()
    for i in range(1,len(y)):
        v=x[i]-x[i-1]; nv=np.linalg.norm(v)
        v=v/nv if nv>1e-9 else np.array([1.0,0.0,0.0])
        y[i]=y[i-1]+bond_length*v
    return y


def refine_coordinates(coords,charges=None,steps=20,learning_rate=.002,restrain_bonds=True,bond_length=CA_CA,k_bond=10.0):
    """Gradient descent over LJ + electrostatics with CA-CA bond restraint.

    With restrain_bonds (default) the objective adds k_bond*(r-3.80)^2 per
    consecutive pair and every step is projected back onto exact 3.80 A
    bonds, so refinement cannot distort the backbone. restrain_bonds=False
    restores the unrestrained nonbonded-only descent.
    """
    x=np.asarray(coords,float).copy()
    def total(y): return physical_energy(y,charges)['total']+(_bond_energy(y,bond_length,k_bond) if restrain_bonds else 0.0)
    trajectory=[]
    for _ in range(steps):
        e=total(x); trajectory.append(e); grad=np.zeros_like(x); h=1e-4
        for i in range(len(x)):
            for j in range(3):
                x[i,j]+=h; ep=total(x); x[i,j]-=h; grad[i,j]=(ep-e)/h
        x-=learning_rate*np.clip(grad,-10,10)
        if restrain_bonds: x=_project_bonds(x,bond_length)
    trajectory.append(total(x)); b=np.linalg.norm(np.diff(x,axis=0),axis=1) if len(x)>1 else np.zeros(1)
    return {'coordinates':x.tolist(),'energy_trajectory':trajectory,'converged':trajectory[-1]<=trajectory[0],
            'bond_restraint':bool(restrain_bonds),'max_bond_deviation_A':float(np.max(np.abs(b-bond_length))) if len(x)>1 else 0.0}

def mutation_stability(sequence,position,mutant):
    seq=''.join(a for a in sequence.upper() if a in CF); position=int(position); wild=seq[position]; p0=CF[wild]; p1=CF[mutant]; hyd=set('AILMFWVY'); propensity_shift=(max(p1)-max(p0))/100; hydro_shift=float((mutant in hyd)-(wild in hyd)); ddg=.8*propensity_shift-1.2*hydro_shift; return {'position':position,'wild_type':wild,'mutant':mutant,'ddg_relative':ddg,'destabilizing':ddg>0,'terms':{'propensity':.8*propensity_shift,'hydrophobicity':-1.2*hydro_shift},'scope':'composition/propensity heuristic; adjacent bonded pairs are excluded from nonbonded physical_energy'}

def folding_workspace(sequence,msa=None):
    base=predict_structure(sequence); seq=''.join(a for a in sequence.upper() if a in CF); ss=list(base['secondary_structure']); coords=_backbone(seq,ss); charge=[1 if a in 'KR' else -1 if a in 'DE' else 0 for a in seq]; graph=residue_graph(coords); energy=physical_energy(coords,charge); couplings=msa_couplings(msa) if msa else None; return {**base,'coordinates':coords.tolist(),'residue_graph':graph,'energy':energy,'msa':couplings,'pair_representation':couplings['mutual_information'] if couplings else None,'model_status':'Chou-Fasman, MSA mutual information and explicit geometry/energy; no AlphaFold neural weights and pLDDT/PAE are analogs, not calibrated predictions.'}

def structure_diagnostics(sequence,msa=None):
    """Flat numeric diagnostic panel (>=50 features) from folding_workspace()."""
    r=folding_workspace(sequence,msa); p=np.asarray(r['pae'],float); c=np.asarray(r['plddt_per_residue'],float); e=r['energy']; g=r['residue_graph']
    seq=''.join(a for a in sequence.upper() if a in CF); X=np.asarray(r['coordinates'],float); geo=backbone_geometry(X); n=len(seq); ss=r['secondary_structure']
    D=np.linalg.norm(X[:,None]-X[None],axis=2); ii,jj=np.triu_indices(n,3); contacts=D[ii,jj]<8.0 if len(ii) else np.zeros(0,bool)
    sep=(jj-ii)[contacts] if len(ii) else np.zeros(0)
    rg=float(np.sqrt(((X-X.mean(0))**2).sum(1).mean())); ang=np.asarray(geo['angles_deg'] or [0.0])
    segs=[]; k=0
    while k<n:
        j=k
        while j<n and ss[j]==ss[k]: j+=1
        segs.append((ss[k],j-k)); k=j
    seg_len=lambda t:[L for s_,L in segs if s_==t]
    hl,el,cl=seg_len('H'),seg_len('E'),seg_len('C')
    same=np.array([[ss[i]==ss[j] for j in range(n)] for i in range(n)])
    hyd=set('AILMFWVC'); pos=set('KR'); neg=set('DE'); arom=set('FWY')
    comp=r['composition']; msa_=r['msa']
    d={'length':float(n),'mean_plddt_analog':float(r['mean_plddt']),'plddt_std':float(c.std()),'plddt_min':float(c.min()),'plddt_max':float(c.max()),
       'plddt_median':float(np.median(c)),'plddt_p10':float(np.percentile(c,10)),'plddt_p90':float(np.percentile(c,90)),
       'frac_plddt_ge_90':float(np.mean(c>=90)),'frac_plddt_ge_70':float(np.mean(c>=70)),'frac_plddt_lt_50':float(np.mean(c<50)),
       'pae_mean':float(p.mean()),'pae_max':float(p.max()),'pae_median':float(np.median(p)),'pae_intra_element_mean':float(p[same].mean()),
       'pae_inter_element_mean':float(p[~same].mean()) if (~same).any() else 0.0,
       'helix_count':float(comp['helix']),'strand_count':float(comp['strand']),'coil_count':float(comp['coil']),
       'helix_fraction':comp['helix']/n,'strand_fraction':comp['strand']/n,'coil_fraction':comp['coil']/n,
       'helix_segments':float(len(hl)),'strand_segments':float(len(el)),'coil_segments':float(len(cl)),
       'mean_helix_length':float(np.mean(hl)) if hl else 0.0,'mean_strand_length':float(np.mean(el)) if el else 0.0,
       'longest_helix':float(max(hl,default=0)),'longest_strand':float(max(el,default=0)),'longest_coil':float(max(cl,default=0)),
       'ca_ca_mean':geo['ca_ca_mean'],'ca_ca_min':geo['ca_ca_min'],'ca_ca_max':geo['ca_ca_max'],
       'virtual_angle_mean':float(ang.mean()),'virtual_angle_std':float(ang.std()),
       'min_nonadjacent_ca':geo['min_nonadjacent'],'clash_count':float(geo['clash_count']),
       'radius_of_gyration':rg,'rg_per_residue_scaling':rg/(n**(1/3)) if n else 0.0,'end_to_end_distance':float(D[0,-1]) if n>1 else 0.0,
       'max_dimension':float(D.max()),'contact_count_8A':float(contacts.sum()),'contacts_per_residue':float(contacts.sum())/n,
       'long_range_contacts':float(np.sum(sep>=12)),'relative_contact_order':float(sep.mean()/n) if len(sep) else 0.0,
       'graph_edges':float(len(g['edges'])),'lj_energy':float(e['lennard_jones']),'electrostatic_energy':float(e['electrostatic']),
       'total_energy':float(e['total']),'energy_per_residue':float(e['total'])/n,
       'hydrophobic_fraction':sum(a in hyd for a in seq)/n,'aromatic_fraction':sum(a in arom for a in seq)/n,
       'net_charge':float(sum(a in pos for a in seq)-sum(a in neg for a in seq)),'glycine_proline_fraction':sum(a in 'GP' for a in seq)/n,
       'candidate_site_count':float(len(r['candidate_binding_sites'])),
       'msa_depth':float(msa_['depth'] if msa_ else 0),'msa_effective_depth':float(msa_['effective_depth'] if msa_ else 0),
       'msa_mean_entropy':float(np.mean(msa_['entropy'])) if msa_ else 0.0,'msa_max_coupling':float(np.max(msa_['mutual_information'])) if msa_ else 0.0}
    return d
