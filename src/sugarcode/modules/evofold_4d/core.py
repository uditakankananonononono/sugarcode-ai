from __future__ import annotations
import numpy as np


def _kirchhoff(coords: np.ndarray, cutoff: float = 10.0,
               stiffness_map: dict[int, float] | None = None) -> np.ndarray:
    """Kirchhoff/contact matrix for a C-alpha elastic network."""
    n = len(coords)
    K = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = np.linalg.norm(coords[i] - coords[j])
            if d < cutoff:
                w = 1.0
                if stiffness_map:
                    w = stiffness_map.get(i, 1.0) * stiffness_map.get(j, 1.0)
                K[i, j] = K[j, i] = -w
                K[i, i] += w
                K[j, j] += w
    return K


def anm_modes(coords: list[list[float]], n_modes: int = 6, cutoff: float = 10.0) -> dict:
    """Anisotropic network model: low-frequency normal modes of a structure.

    Builds the 3N x 3N Hessian from the contact graph, eigen-solves, returns
    mode frequencies and per-residue fluctuation profiles (B-factor analog).
    """
    C = np.asarray(coords, dtype=float)
    n = len(C)
    K = _kirchhoff(C, cutoff)
    H = np.zeros((3 * n, 3 * n))
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            kij = K[i, j]
            if kij == 0:
                continue
            rij = C[j] - C[i]
            dist = np.linalg.norm(rij)
            if dist == 0:
                continue
            e = rij / dist
            block = kij * np.outer(e, e)  # kij < 0: correct ANM off-diagonal
            H[3 * i:3 * i + 3, 3 * j:3 * j + 3] = block
            H[3 * i:3 * i + 3, 3 * i:3 * i + 3] -= block
            H[3 * j:3 * j + 3, 3 * j:3 * j + 3] -= block
    vals, vecs = np.linalg.eigh(H)
    order = np.argsort(vals)
    vals, vecs = vals[order], vecs[:, order]
    nz = [i for i, v in enumerate(vals) if v > 1e-6][:n_modes]
    modes = []
    fluct = np.zeros(n)
    for idx in nz:
        mode = vecs[:, idx].reshape(n, 3)
        sq = (mode ** 2).sum(axis=1)
        fluct += sq / vals[idx]
        modes.append({"index": int(idx), "frequency": round(float(np.sqrt(vals[idx])), 4),
                      "mean_square": round(float(sq.mean()), 6)})
    return {
        "n_residues": n,
        "modes": modes,
        "fluctuation_profile": [round(float(f), 6) for f in fluct / max(len(nz), 1)],
        "hinge_residues": _hinges(fluct),
    }


def _hinges(fluct: np.ndarray) -> list[int]:
    if len(fluct) < 5 or fluct.max() == 0:
        return []
    norm = fluct / fluct.max()
    return [int(i) for i in range(2, len(norm) - 2)
            if norm[i] < 0.2 and norm[i - 1] >= norm[i] and norm[i + 1] >= norm[i]][:5]


def transition_trace(coords: list[list[float]], mode_index: int = 0,
                     steps: int = 20, amplitude: float = 3.0) -> dict:
    """Temporal morph between open and closed states along a slow mode.

    Returns per-frame coordinates and RMSD-from-start trace (the 4th dimension).
    """
    C = np.asarray(coords, dtype=float)
    res = anm_modes(coords, n_modes=max(1, mode_index + 1))
    C0 = C
    K = _kirchhoff(C)
    # rebuild the chosen mode direction
    n = len(C)
    H = np.zeros((3 * n, 3 * n))
    for i in range(n):
        for j in range(n):
            kij = K[i, j]
            if i == j or kij == 0:
                continue
            rij = C[j] - C[i]
            dist = np.linalg.norm(rij)
            if dist == 0:
                continue
            e = rij / dist
            block = kij * np.outer(e, e)  # kij < 0: correct ANM off-diagonal
            H[3 * i:3 * i + 3, 3 * j:3 * j + 3] = block
            H[3 * i:3 * i + 3, 3 * i:3 * i + 3] -= block
            H[3 * j:3 * j + 3, 3 * j:3 * j + 3] -= block
    vals, vecs = np.linalg.eigh(H)
    nz = [i for i, v in enumerate(vals) if v > 1e-6]
    if not nz:
        raise ValueError("structure has no non-rigid modes")
    mode = vecs[:, nz[min(mode_index, len(nz) - 1)]].reshape(n, 3)
    frames, rmsd = [], []
    for s in range(steps):
        phase = amplitude * np.sin(np.pi * s / (steps - 1))
        frame = C0 + phase * mode
        frames.append([[round(float(x), 3) for x in row] for row in frame])
        rmsd.append(round(float(np.sqrt(((frame - C0) ** 2).sum(axis=1).mean())), 4))
    return {
        "mode": mode_index, "frames": frames, "rmsd_trace": rmsd,
        "max_rmsd": max(rmsd),
        "event_timeline": [{"frame": i, "event": "opening" if i < steps // 2 else "closing"}
                           for i in (0, steps // 2, steps - 1)],
    }


def perturbation_effect(coords: list[list[float]], site: int, kind: str = "phosphorylation") -> dict:
    """Model a PTM/ligand as a local stiffness change; report fluctuation shift."""
    base = anm_modes(coords)
    stiff = {site: 2.5}
    C = np.asarray(coords, dtype=float)
    n = len(C)
    K = _kirchhoff(C, stiffness_map=stiff)
    # recompute fluctuation quickly with modified network
    from numpy.linalg import pinv
    G = pinv(K, rcond=1e-6)
    fluct_ptm = np.diag(G)[:n]
    base_f = np.array(base["fluctuation_profile"])
    f2 = fluct_ptm / fluct_ptm.max() if fluct_ptm.max() > 0 else fluct_ptm
    b = base_f / base_f.max() if base_f.max() > 0 else base_f
    delta = f2 - b
    return {
        "site": site, "perturbation": kind,
        "local_rigidification": round(float(-delta[site]), 4) if site < len(delta) else None,
        "most_affected_residues": sorted(range(len(delta)), key=lambda i: -abs(delta[i]))[:5],
        "interpretation": (f"{kind} at residue {site} stiffens the local network and "
                           "redistributes flexibility - shifting the open/closed equilibrium."),
    }


def structure_dynamics(identifier: str, chain: str | None = None, n_modes: int = 6,
                       offline: bool = False) -> dict:
    """ANM normal modes on REAL structure coordinates (RCSB/AlphaFold), with the
    classic validation: correlation between predicted fluctuations and measured
    B-factors (X-ray) or pLDDT (AlphaFold, inverted)."""
    from ...bio.structures import fetch_pdb, fetch_alphafold
    if len(identifier) == 4 and identifier[0].isdigit():
        s = fetch_pdb(identifier, offline=offline)
        conf_kind = "b_factor"
    else:
        s = fetch_alphafold(identifier, offline=offline)
        conf_kind = "plddt"
    residues = s["residues"]
    if chain:
        residues = [r for r in residues if r["chain"] == chain]
    coords = [list(r["ca"]) for r in residues]
    result = anm_modes(coords, n_modes=n_modes)
    fluct = np.array(result["fluctuation_profile"], dtype=float)
    measured = np.array([r["bfactor"] for r in residues], dtype=float)
    corr = None
    if len(fluct) > 5 and fluct.std() > 0 and measured.std() > 0:
        pred = fluct if conf_kind == "b_factor" else -fluct  # pLDDT is inverse disorder
        corr = round(float(np.corrcoef(pred, measured)[0, 1]), 3)
    result.update({
        "structure": {"identifier": identifier, "source": s["source"],
                      "chain": chain, "n_residues": len(residues)},
        "validation": {
            "kind": f"ANM fluctuation vs {'experimental B-factors' if conf_kind == 'b_factor' else 'pLDDT (inverted)'}",
            "pearson_r": corr,
            "verdict": ("good agreement - modes capture real flexibility" if corr and corr > 0.5
                        else "weak agreement - interpret modes cautiously" if corr is not None
                        else "insufficient variance to validate"),
        },
        "hinge_residues_real": [residues[i]["resnum"] for i in result["hinge_residues"]
                                if i < len(residues)],
        "note": "real C-alpha coordinates; 6 zero modes (rigid body) excluded automatically",
    })
    return result

# Explicit stochastic dynamics, state models and evolutionary conditioning.
def langevin_dynamics(coords,steps=100,dt=.01,temperature=.1,friction=1,seed=0,bonds=None):
    x=np.asarray(coords,float).copy(); rng=np.random.default_rng(seed); v=np.zeros_like(x); bonds=bonds or [(i,i+1,float(np.linalg.norm(x[i+1]-x[i]))) for i in range(len(x)-1)]; frames=[x.copy().tolist()]; energies=[]
    for _ in range(steps):
        force=np.zeros_like(x); energy=0
        for i,j,r0 in bonds:
            d=x[j]-x[i]; r=max(1e-9,np.linalg.norm(d)); extension=r-r0; f=extension*d/r; force[i]+=f; force[j]-=f; energy+=.5*extension**2
        v+=(force-friction*v)*dt+math_sqrt(2*friction*temperature*dt)*rng.normal(size=x.shape); x+=v*dt; frames.append(x.copy().tolist()); energies.append(float(energy))
    return {'frames':frames,'energy':energies,'rmsd':[float(np.sqrt(np.mean((np.asarray(f)-np.asarray(coords))**2))) for f in frames],'temperature':temperature}

def math_sqrt(x): return float(np.sqrt(x))

def state_assignments(trajectory,n_states=3):
    frames=np.asarray(trajectory,float); ref=frames[0]; feature=np.sqrt(np.mean((frames-ref)**2,axis=(1,2))); bins=np.quantile(feature,np.linspace(0,1,n_states+1)); states=np.digitize(feature,bins[1:-1],right=True); return {'states':states.tolist(),'feature_rmsd':feature.tolist(),'boundaries':bins.tolist()}

def markov_state_model(states,lag=1,n_states=None):
    s=np.asarray(states,int); n=n_states or int(s.max()+1); counts=np.zeros((n,n))
    for i in range(len(s)-lag): counts[s[i],s[i+lag]]+=1
    T=np.divide(counts,counts.sum(1,keepdims=True),out=np.eye(n),where=counts.sum(1,keepdims=True)>0); vals=np.linalg.eigvals(T); times=[float(-lag/np.log(abs(v))) for v in vals if 0<abs(v)<.999999]; pi=np.ones(n)/n
    for _ in range(100): pi=pi@T
    return {'transition_counts':counts.tolist(),'transition_matrix':T.tolist(),'stationary_probability':(pi/pi.sum()).tolist(),'implied_timescales':times}

def free_energy_landscape(features,temperature=.593,bins=20):
    hist,edges=np.histogram(np.asarray(features,float),bins=bins,density=True); p=hist/max(1e-12,hist.sum()); free=-temperature*np.log(np.clip(p,1e-12,None)); free-=free.min(); minima=[i for i in range(1,len(free)-1) if free[i]<=free[i-1] and free[i]<=free[i+1]]; return {'bin_edges':edges.tolist(),'probability':p.tolist(),'free_energy_kcal_mol':free.tolist(),'metastable_basins':minima}

def evolutionary_constraints(msa):
    rows=np.array([list(s) for s in msa]); n=rows.shape[1]; conservation=[]
    for i in range(n):
        _,c=np.unique(rows[:,i],return_counts=True); p=c/c.sum(); conservation.append(float(1+np.sum(p*np.log(p))/np.log(max(2,len(c)))))
    return {'depth':len(rows),'conservation':conservation,'constrained_positions':[i for i,x in enumerate(conservation) if x>.8]}

def mutation_dynamics(coords,position,property_delta=1,msa=None):
    base=anm_modes(coords); pert=perturbation_effect(coords,position,'mutation'); conservation=evolutionary_constraints(msa)['conservation'][position] if msa else .5; barrier_shift=property_delta*(.5+conservation); return {'position':position,'property_delta':property_delta,'conservation':conservation,'barrier_shift_relative':barrier_shift,'base_hinges':base['hinge_residues'],'flexibility_effect':pert}

def multi_model_pdb(frames):
    lines=[]
    for m,frame in enumerate(frames,1):
        lines.append(f'MODEL     {m}')
        for i,(x,y,z) in enumerate(frame,1): lines.append(f'ATOM  {i:5d}  CA  GLY A{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C')
        lines.append('ENDMDL')
    return '\n'.join(lines)+'\nEND\n'

def dynamics_report(coords,steps=60,seed=0):
    dyn=langevin_dynamics(coords,steps=steps,seed=seed); assign=state_assignments(dyn['frames']); msm=markov_state_model(assign['states']); landscape=free_energy_landscape(assign['feature_rmsd']); return {'trajectory':dyn,'states':assign,'msm':msm,'landscape':landscape,'multi_model_pdb':multi_model_pdb(dyn['frames'][::max(1,steps//10)]),'model_status':'Explicit elastic-network/Langevin/MSM approximations; no neural SDE, diffusion model or learned force field is bundled.'}

def evofold_diagnostics(coords,steps=30):
    r=dynamics_report(coords,steps); modes=anm_modes(coords); rms=np.asarray(r['trajectory']['rmsd']); energy=np.asarray(r['trajectory']['energy']); T=np.asarray(r['msm']['transition_matrix']); return {'residue_count':float(len(coords)),'mode_count':float(len(modes['modes'])),'hinge_count':float(len(modes['hinge_residues'])),'rmsd_mean':float(rms.mean()),'rmsd_max':float(rms.max()),'energy_mean':float(energy.mean()),'energy_std':float(energy.std()),'state_count':float(len(T)),'transition_nonzero':float(np.count_nonzero(T)),'stationary_entropy':float(-sum(p*np.log(max(p,1e-12)) for p in r['msm']['stationary_probability'])),'basin_count':float(len(r['landscape']['metastable_basins'])),'frame_count':float(len(r['trajectory']['frames']))}
