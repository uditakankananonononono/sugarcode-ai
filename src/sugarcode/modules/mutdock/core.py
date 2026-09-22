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
                    drug_name: str = "drug", resnums: list[int] | None = None) -> dict:
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
    true_num = resnums[position] if resnums else pocket_start + position + 1
    return {
        "mutation": f"{wt_aa}{true_num}{mutant_aa}",
        "drug": drug_name,
        "wt_dg": wt["binding_dg_kcal_mol"], "mutant_dg": mt["binding_dg_kcal_mol"],
        "ddg_kcal_mol": ddg,
        "affinity_change_fold": round(2.718 ** (ddg / 0.593), 2),
        "resistance_risk": resistance,
        "hotspot": ddg > 1.0,
    }


def resistance_scan(pocket_residues: str, drugs: dict[str, str],
                    pocket_start: int = 1, resnums: list[int] | None = None) -> dict:
    """resnums: true structure numbering per pocket index (non-contiguous
    pockets MUST pass this - pocket_start assumes contiguity)."""
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
                r = mutation_effect(pocket_residues, smi, pos, aa, pocket_start, name,
                                    resnums=resnums)
                if r["ddg_kcal_mol"] > best_gain:
                    best_gain = r["ddg_kcal_mol"]
                    best_mut = r["mutation"]
            if best_gain > 1.0:
                hotspot_counts[pos] = hotspot_counts.get(pos, 0) + 1
            true_num = resnums[pos] if resnums else pocket_start + pos + 1
            worst.append({"position": true_num,
                          "max_ddg": round(best_gain, 3), "mutation": best_mut})
        per_drug[name] = {"positions": worst,
                          "most_vulnerable": max(worst, key=lambda w: w["max_ddg"])}
    hotspots = [{"position": resnums[p] if resnums else pocket_start + p + 1,
                 "drugs_affected": c}
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
                              ligand_resname: str | None = None,
                              offline: bool = False) -> dict:
    """Cross-drug resistance forecast on a REAL structure pocket.

    Fetches the structure live (RCSB/AlphaFold), extracts the geometry pocket's
    lining sequence, runs the full resistance scan (all positions x 20 AAs x
    drugs) on the real lining. Provenance per result.
    """
    from ..alpha_fold_ui.core import _real_pockets
    from ..docking_studio.core import AA3_TO_1 as _A3
    from ...bio.structures import fetch_pdb, fetch_alphafold, ligand_pocket
    is_pdb = len(identifier) == 4 and identifier[0].isdigit()
    pocket_source = "geometry"
    if ligand_resname and is_pdb:
        # co-crystal ligand pocket: the experimentally observed binding site
        lp = ligand_pocket(identifier, ligand_resname, chain=chain, offline=offline)
        s = fetch_pdb(identifier, offline=offline)
        residues = s["residues"]
        if chain is None and lp["lining"]:
            chain = lp["lining"][0].get("chain") or None  # avoid two-chain duplicates
        if chain:
            residues = [r for r in residues if r["chain"] == chain]
            lp_lining = [r for r in lp["lining"] if r.get("chain") in (None, chain)]
        else:
            lp_lining = lp["lining"]
        lining = lp_lining
        chosen = {r["resnum"] for r in lining}
        pockets = [{"residues": sorted(chosen)}]
        pocket_source = f"co-crystal ligand {lp['ligand']} ({lp['n_lining']} residues within {lp['radius_A']} A)"
    else:
        if ligand_resname and not is_pdb:
            pocket_source = "geometry (ligand_resname ignored - needs a PDB co-structure)"
        s = fetch_pdb(identifier, offline=offline) if is_pdb else fetch_alphafold(identifier, offline=offline)
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
    # binding-site validation (drop 18): for the UniProt/AlphaFold path, compare
    # the geometry pocket against UniProt-annotated BINDING features.
    binding_validation = None
    if not (len(identifier) == 4 and identifier[0].isdigit()):
        try:
            # direct record fetch by accession
            from ...bio.uniprot import _get as _upget, BASE as _UPBASE
            import json as _json
            data = _json.loads(_upget(f"{_UPBASE}/{identifier}.json", offline=offline))
            feats = data.get("features", [])
            sites = [f for f in feats if f.get("type") == "Binding site"]
            site_res = set()
            for f in sites:
                loc = f.get("location", {})
                b, e = (loc.get("start") or {}).get("value"), (loc.get("end") or {}).get("value")
                if b and e:
                    site_res.update(range(int(b), int(e) + 1))
            if site_res:
                overlap = len(chosen & site_res)
                binding_validation = {
                    "annotated_binding_residues": len(site_res),
                    "pocket_residues_in_annotated_sites": overlap,
                    "overlap_fraction": round(overlap / max(len(chosen), 1), 3),
                    "verdict": ("geometry pocket overlaps annotated binding sites"
                                if overlap > 0 else
                                "geometry pocket does NOT overlap any annotated binding site - "
                                "may be an unannotated/allosteric pocket or a false positive"),
                    "source": f"UniProt {identifier} BINDING features (live)" if not offline
                              else f"UniProt {identifier} BINDING features (cache)",
                }
            else:
                binding_validation = {"status": "no annotated BINDING features for this protein"}
            # UniProt feature awareness (drop 20): natural variants at lining
            # residues - a "resistance hotspot" that is a known tolerated
            # natural variant should be flagged, not overcalled.
            if isinstance(binding_validation, dict):
                nvar = [f for f in feats if f.get("type") == "Natural variant"]
                lining_nums = {r["resnum"] for r in lining}
                hits = []
                for f in nvar:
                    loc = f.get("location", {})
                    b = (loc.get("start") or {}).get("value")
                    if b is not None and int(b) in lining_nums:
                        hits.append({"resnum": int(b),
                                     "description": (f.get("description") or "")[:100]})
                binding_validation["natural_variants_in_pocket"] = hits[:10]
                if hits:
                    binding_validation["caveat"] = (
                        f"{len(hits)} pocket residue(s) have annotated natural variants - "
                        "variation at these positions may be tolerated; weigh resistance "
                        "calls accordingly")
        except Exception as e:
            binding_validation = {"status": f"validation lookup failed: {type(e).__name__}: {e}"}
    else:
        binding_validation = {"status": "PDB input - UniProt mapping not available (SIFTS not wired); skipped"}
    seen = set()
    lining = [r for r in lining if not ((r.get("chain"), r["resnum"]) in seen
                                        or seen.add((r.get("chain"), r["resnum"])))]
    pocket_seq = "".join(_A3.get(r["resname"], "G") for r in lining)
    true_resnums = [r["resnum"] for r in lining]
    start = lining[0]["resnum"] - 1
    scan = resistance_scan(pocket_seq, drugs, pocket_start=start, resnums=true_resnums)
    # Vina-form WT baseline affinity on the real pocket coordinates (drop 16).
    # Mutant ddG still comes from the feature scorer - the vina baseline is a
    # real-coordinate WT anchor, labeled as such, not a fake re-dock.
    from ..docking_studio.vina import dock_vina_grid
    pocket_atoms = [{"element": "C", "xyz": r["ca"]} for r in lining]
    vina_wt = {}
    for name, smi in drugs.items():
        try:
            v = dock_vina_grid(pocket_atoms, smi)
            vina_wt[name] = {"vina_score": v["vina_score"],
                             "estimated_dg_kcal_mol": v["estimated_dg_kcal_mol"]}
        except Exception as e:
            vina_wt[name] = {"status": f"vina scoring failed: {type(e).__name__}"}
    scan.update({
        "structure": {"identifier": identifier, "source": s["source"],
                      "chain": chain, "pocket_index": pocket_index,
                      "pocket_source": pocket_source,
                      "n_pockets_found": len(pockets),
                      "lining": [f"{r['resname']}{r['resnum']}" for r in lining]},
        "binding_site_validation": binding_validation,
        "wt_vina_baseline": vina_wt,
        "wt_vina_note": ("Vina-form WT affinity on real pocket CA coordinates "
                         "(Trott & Olson 2010 terms); mutant ddG comes from the "
                         "feature scorer - mutants are NOT re-docked"),
        "note": "hotspot positions use real structure residue numbering",
    })
    return scan

# Explicit structural/ensemble/epistasis extensions; no learned GNN potential.
import math
import numpy as np

def local_repack(coords,mutation_index,size_delta=0,steps=25):
    x=np.asarray(coords,float).copy(); center=x[mutation_index].copy(); trace=[]
    for _ in range(steps):
        e=0; grad=np.zeros_like(x)
        for i in range(len(x)):
            if i==mutation_index: continue
            d=x[i]-center; r=max(.5,np.linalg.norm(d)); target=3.8+.4*size_delta; diff=r-target; e+=.5*diff*diff; grad[i]+=diff*d/r
        x-=.02*np.clip(grad,-2,2); trace.append(float(e))
    return {'coordinates':x.tolist(),'energy_trace':trace,'converged':trace[-1]<=trace[0]}

def interaction_graph(pocket,smiles):
    d=dock(pocket,smiles); nodes=[{'id':i,'residue':a,'type':'residue'} for i,a in enumerate(pocket)]+[{'id':'ligand','type':'ligand'}]; edges=[]
    polar=d['ligand']['hbond_capacity']>0
    for i,a in enumerate(pocket):
        if a in 'HDESTNQCY' and polar: edges.append({'source':i,'target':'ligand','interaction':'hbond','strength':1})
        if a in 'AILMFWVY' and d['ligand']['heavy_atoms']>1: edges.append({'source':i,'target':'ligand','interaction':'hydrophobic','strength':.7})
    return {'nodes':nodes,'edges':edges,'fingerprint':{k:sum(e['interaction']==k for e in edges) for k in ('hbond','hydrophobic')}}

def graph_perturbation(pocket,smiles,position,mutant):
    wt=interaction_graph(pocket,smiles); mp=pocket[:position]+mutant+pocket[position+1:]; mt=interaction_graph(mp,smiles); return {'wild_type':wt,'mutant':mt,'lost_contacts':max(0,len(wt['edges'])-len(mt['edges'])),'gained_contacts':max(0,len(mt['edges'])-len(wt['edges']))}

def ensemble_mutation_effect(pocket_ensemble,smiles,position,mutant):
    effects=[mutation_effect(p,smiles,position,mutant) for p in pocket_ensemble]; ddg=np.array([x['ddg_kcal_mol'] for x in effects]); w=np.exp(-np.array([dock(p,smiles)['binding_dg_kcal_mol'] for p in pocket_ensemble])/.593); w/=w.sum(); mean=float(w@ddg); var=float(w@((ddg-mean)**2)); return {'conformations':effects,'weights':w.tolist(),'ddg_mean':mean,'ddg_std':math.sqrt(var),'resistance_probability':float(sum(w*(ddg>.5)))}

def epistasis_effect(pocket,smiles,mutations):
    single=[]
    for pos,aa in mutations: single.append(mutation_effect(pocket,smiles,pos,aa)['ddg_kcal_mol'])
    mutant=list(pocket)
    for pos,aa in mutations: mutant[pos]=aa
    combined=dock(''.join(mutant),smiles)['binding_dg_kcal_mol']-dock(pocket,smiles)['binding_dg_kcal_mol']; additive=sum(single); return {'single_ddg':single,'combined_ddg':combined,'additive_expectation':additive,'epistasis':combined-additive,'classification':'synergistic' if combined-additive>.25 else 'compensatory' if combined-additive<-.25 else 'additive'}

def mutational_fitness_landscape(pocket,smiles,positions=None):
    positions=positions or range(len(pocket)); variants=[]
    for p in positions:
        for aa in 'ACDEFGHIKLMNPQRSTVWY':
            if aa!=pocket[p]:
                r=mutation_effect(pocket,smiles,p,aa); fitness=math.exp(-max(0,r['ddg_kcal_mol'])) ; variants.append({**r,'position':p,'fitness_proxy':fitness})
    return {'variants':variants,'resistance_hotspots':sorted(variants,key=lambda x:-x['ddg_kcal_mol'])[:10]}

def cross_drug_matrix(pocket,drugs,mutations):
    matrix=[]
    for pos,aa in mutations: matrix.append({'mutation':f'{pocket[pos]}{pos+1}{aa}','ddg':{name:mutation_effect(pocket,smi,pos,aa,drug_name=name)['ddg_kcal_mol'] for name,smi in drugs.items()}})
    return {'drugs':list(drugs),'rows':matrix,'broad_resistance':[r['mutation'] for r in matrix if sum(v>.5 for v in r['ddg'].values())>1]}

def evolutionary_forecast(pocket,smiles,generations=20,mutation_rate=.05,population=1000):
    landscape=mutational_fitness_landscape(pocket,smiles); beneficial=[v for v in landscape['variants'] if v['ddg_kcal_mol']>.5]; rate=mutation_rate*len(beneficial)/max(1,len(landscape['variants'])); probability=[1-math.exp(-population*rate*(g+1)/population) for g in range(generations)]; return {'generations':list(range(1,generations+1)),'resistance_emergence_probability':probability,'accessible_resistance_variants':len(beneficial),'status':'population-genetic proxy, not patient prognosis'}

def mutdock_report(pocket,drugs,mutations):
    matrix=cross_drug_matrix(pocket,drugs,mutations); epi=epistasis_effect(pocket,next(iter(drugs.values())),mutations[:2]) if len(mutations)>=2 else None; return {'cross_drug':matrix,'epistasis':epi,'fitness':mutational_fitness_landscape(pocket,next(iter(drugs.values()))),'forecast':evolutionary_forecast(pocket,next(iter(drugs.values()))),'model_status':'Transparent docking-feature, ensemble and epistasis models; no trained GNN and not clinical treatment guidance.'}

def mutdock_diagnostics(pocket,smiles,position,mutant):
    r=mutation_effect(pocket,smiles,position,mutant); g=graph_perturbation(pocket,smiles,position,mutant); f=mutational_fitness_landscape(pocket,smiles,[position]); vals=np.array([x['ddg_kcal_mol'] for x in f['variants']]); return {'pocket_length':float(len(pocket)),'position':float(position),'wt_dg':r['wt_dg'],'mutant_dg':r['mutant_dg'],'ddg':r['ddg_kcal_mol'],'affinity_fold':r['affinity_change_fold'],'hotspot':float(r['hotspot']),'wt_contacts':float(len(g['wild_type']['edges'])),'mutant_contacts':float(len(g['mutant']['edges'])),'lost_contacts':float(g['lost_contacts']),'gained_contacts':float(g['gained_contacts']),'scan_ddg_mean':float(vals.mean()),'scan_ddg_std':float(vals.std()),'scan_ddg_max':float(vals.max())}
