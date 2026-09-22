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

# Transparent physics/biological-constraint extensions; no trained PLM or structure model.
import math
import numpy as np
def clean_protein(seq):
    s="".join(a for a in str(seq).upper() if a in "ACDEFGHIKLMNPQRSTVWY")
    if not s: raise ValueError("sequence contains no valid amino acids")
    return s
CODONS={'ecoli':{a:c for a,c in zip("ACDEFGHIKLMNPQRSTVWY",("GCG","TGC","GAT","GAA","TTT","GGT","CAT","ATT","AAA","CTG","ATG","AAC","CCG","CAA","CGT","AGC","ACC","GTT","TGG","TAT"))},'yeast':{a:c for a,c in zip("ACDEFGHIKLMNPQRSTVWY",("GCT","TGT","GAC","GAG","TTC","GGA","CAC","ATC","AAG","TTG","ATG","AAT","CCA","CAG","AGA","TCT","ACT","GTC","TGG","TAC"))}}
def codon_optimize(seq,host='ecoli'):
    table=CODONS.get(host,CODONS['ecoli']); return "".join(table[a] for a in clean_protein(seq))

CHARGE={'D':-1,'E':-1,'K':1,'R':1,'H':.1}; HYDRO=set('AILMFWVY'); AROM=set('FWY')

def active_site_geometry(seq,positions,substrate_charge=0):
    s=clean_protein(seq); pos=[int(x) for x in positions]; residues=[s[i] for i in pos]; charge=sum(CHARGE.get(a,0) for a in residues); aromatic=sum(a in AROM for a in residues); hydrophobic=sum(a in HYDRO for a in residues)/max(1,len(residues)); electrostatic=math.exp(-abs(charge+substrate_charge)); return {"positions":pos,"residues":residues,"net_charge":charge,"hydrophobic_fraction":hydrophobic,"aromatic_contacts":aromatic,"transition_state_complementarity":electrostatic*(.5+.5*hydrophobic)}

def enzyme_kinetics(seq,active_positions,substrate_charge=0,temperature_c=37):
    g=active_site_geometry(seq,active_positions,substrate_charge); preorg=g['transition_state_complementarity']; kcat=10**(-1+3*preorg)*math.exp(-((temperature_c-37)/35)**2); km=1e-3/(.1+preorg+.1*g['aromatic_contacts']); return {"kcat_s":kcat,"km_m":km,"catalytic_efficiency_m_inv_s":kcat/km,"status":"relative physical-chemistry heuristic"}

def binding_interface(seq,interface_positions,ligand_hydrophobic=.5,ligand_charge=0):
    g=active_site_geometry(seq,interface_positions,-ligand_charge); packing=1-abs(g['hydrophobic_fraction']-ligand_hydrophobic); salt=min(1,abs(g['net_charge']*ligand_charge)); score=.45*packing+.35*g['transition_state_complementarity']+.2*salt; return {**g,"packing_complementarity":packing,"salt_bridge_score":salt,"binding_score":score,"kd_relative":math.exp(-6*score)}

def cellular_compatibility(seq,compartment='cytosol'):
    s=clean_protein(seq); cysteine=s.count('C'); n_term=s[:25]; secretion=n_term.startswith('M') and sum(a in HYDRO for a in n_term)>=10; transmembrane=max((sum(a in HYDRO for a in s[i:i+19])/19 for i in range(max(1,len(s)-18))),default=0); degrons=sum(m in s for m in ('PEST','KEN','DGN')); disulfides=cysteine//2 if compartment in ('ER','secreted') else 0; return {"compartment":compartment,"signal_peptide_proxy":secretion,"transmembrane_propensity":transmembrane,"disulfide_capacity":disulfides,"degron_count":degrons,"folding_risk":min(1,.15*degrons+.3*(cysteine>2 and compartment=='cytosol'))}

def immunogenicity_scan(seq,window=9):
    s=clean_protein(seq); epitopes=[]
    for i in range(len(s)-window+1):
        p=s[i:i+window]; score=(sum(a in AROM for a in p)+sum(a in 'KR' for a in p))/window
        if score>=.33: epitopes.append({"start":i,"peptide":p,"risk":score})
    return {"epitopes":epitopes,"max_risk":max((e['risk'] for e in epitopes),default=0),"burden":sum(e['risk'] for e in epitopes)}

def expression_construct(seq,host='ecoli',tag='His6'):
    s=clean_protein(seq); dna=codon_optimize(s,host=host); gc=(dna.count('G')+dna.count('C'))/max(1,len(dna)); cai_proxy=len(set(dna[i:i+3] for i in range(0,len(dna),3)))/max(1,len(s)); burden=min(1,len(s)/1000+.3*abs(gc-.5)+.1*s.count('C')); return {"protein":s,"host":host,"coding_dna":dna,"gc_fraction":gc,"codon_diversity":cai_proxy,"tag":tag,"expression_burden":burden,"regulatory_elements":"host-compatible promoter/RBS selection required"}

def mutational_scan(seq,active_positions=()):
    s=clean_protein(seq); rows=[]
    for i,a in enumerate(s):
        local=sum(x in HYDRO for x in s[max(0,i-3):i+4])/max(1,len(s[max(0,i-3):i+4])); sensitivity=.45*local+.4*(i in active_positions)+.15*(a in 'GP'); rows.append({"position":i,"residue":a,"functional_sensitivity":sensitivity,"suggested_class":"conservative" if sensitivity>.5 else "diversifying"})
    return {"positions":rows,"high_sensitivity":[r['position'] for r in rows if r['functional_sensitivity']>.6]}

def engineering_blueprint(description,host='ecoli',seed=0):
    design=design_protein(description,seed=seed); best=design['best']; seq=best['sequence']; active=best['active_site_positions']; return {**design,"active_site_model":active_site_geometry(seq,active),"kinetics":enzyme_kinetics(seq,active) if active else None,"cellular":cellular_compatibility(seq,'cytosol'),"immunogenicity":immunogenicity_scan(seq),"construct":expression_construct(seq,host),"mutational_scan":mutational_scan(seq,active),"validation":["orthogonal structure prediction","thermal stability assay","activity or binding kinetics","expression and aggregation panel"],"model_status":"Transparent sequence/biophysical heuristics; no trained protein language model or 3D predictor and not clinically validated."}

def painter_diagnostics(description,host='ecoli',seed=0):
    r=engineering_blueprint(description,host,seed); b=r['best']; c=r['construct']; x=r['cellular']; i=r['immunogenicity']; return {"length":float(len(b['sequence'])),"molecular_weight_da":b['molecular_weight_da'],"fold_match":b['fold_match'],"design_score":b['design_score'],"folding_dg":b['stability']['folding_dg_estimate'],"helix_fraction":b['stability']['helix_fraction'],"strand_fraction":b['stability']['strand_fraction'],"hydrophobic_core_fraction":b['stability']['hydrophobic_core_fraction'],"active_site_count":float(len(b['active_site_positions'])),"gc_fraction":c['gc_fraction'],"codon_diversity":c['codon_diversity'],"expression_burden":c['expression_burden'],"transmembrane_propensity":x['transmembrane_propensity'],"immunogenicity_burden":i['burden']}
