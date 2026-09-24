from __future__ import annotations
from ...bio.sequence import clean_dna, find_motif, gc_content

# m6A installs at DRACH motifs (D=A/G/T, R=A/G, H=A/C/T); the central A is modified.
DRACH = "DRACH"
# trained-prior positional weights: sites near stop codons / 3' UTR enrich
REGION_PRIORS = {"5utr": 0.35, "cds": 0.55, "near_stop": 0.85, "3utr": 0.75}


def _fold_exposure(seq: str, pos: int, flank: int = 15) -> float:
    """Crude single-strandedness proxy: local GC in a flank around the site.
    m6A prefers exposed (AU-rich) loops."""
    s = seq[max(0, pos - flank):pos + flank + 1]
    return 1.0 - gc_content(s) if s else 0.5


def predict_m6a(rna: str, cds_start: int = 0, cds_end: int | None = None,
                threshold: float = 0.5) -> list[dict]:
    """Predict m6A sites in an RNA sequence (as DNA alphabet, T for U)."""
    s = clean_dna(rna.replace("U", "T"))
    cds_end = cds_end if cds_end is not None else len(s)
    sites = []
    for pos in find_motif(s, DRACH):
        center = pos + 2  # the A in DRACH
        if center >= len(s):
            continue
        if pos < cds_start:
            prior = REGION_PRIORS["5utr"]
        elif pos > cds_end:
            prior = REGION_PRIORS["3utr"]
        elif cds_end - pos < 100:
            prior = REGION_PRIORS["near_stop"]
        else:
            prior = REGION_PRIORS["cds"]
        exposure = _fold_exposure(s, center)
        score = 0.55 * prior + 0.45 * exposure
        if score >= threshold:
            sites.append({
                "position": center, "motif": s[pos:pos + 5],
                "region": ("5'UTR" if pos < cds_start else
                           "3'UTR" if pos > cds_end else
                           "near-stop CDS" if cds_end - pos < 100 else "CDS"),
                "exposure": round(exposure, 3),
                "m6a_probability": round(score, 3),
            })
    return sorted(sites, key=lambda x: -x["m6a_probability"])


def modification_map(rna: str, cds_start: int = 0, cds_end: int | None = None) -> dict:
    s = clean_dna(rna.replace("U", "T"))
    sites = predict_m6a(s, cds_start, cds_end, threshold=0.0)
    return {
        "length": len(s),
        "drach_motifs": len(find_motif(s, DRACH)),
        "predicted_sites": [x for x in sites if x["m6a_probability"] >= 0.5],
        "track": [{"position": x["position"], "score": x["m6a_probability"]} for x in sites],
        "writer_eraser_reader": {
            "writers": ["METTL3", "METTL14", "WTAP"],
            "erasers": ["FTO", "ALKBH5"],
            "readers": ["YTHDF1", "YTHDF2", "YTHDC1"],
        },
    }


def optimize_mrna(rna: str, cds_start: int = 0, cds_end: int | None = None) -> dict:
    """Suggest an mRNA redesign for stability + expression.

    Actions: add m6A at 3'UTR stability sites, remove CDS m6A that slows
    decoding, raise GC moderately, report per-edit rationale.
    """
    s = clean_dna(rna.replace("U", "T"))
    cds_end = cds_end if cds_end is not None else len(s)
    sites = predict_m6a(s, cds_start, cds_end, threshold=0.0)
    edits = []
    for x in sites:
        if x["region"] == "CDS" and x["m6a_probability"] >= 0.6:
            edits.append({"action": "deoptimize_motif", "position": x["position"],
                          "rationale": "CDS m6A can slow ribosome transit; synonymously break DRACH motif"})
        elif x["region"] == "3'UTR" and 0.4 <= x["m6a_probability"] < 0.6:
            edits.append({"action": "retain_site", "position": x["position"],
                          "rationale": "moderate 3'UTR m6A supports YTHDF-mediated stability"})
    gc = gc_content(s[cds_start:cds_end])
    if gc < 0.45:
        edits.append({"action": "raise_cds_gc", "rationale": f"CDS GC {gc:.1%} low; target 50-60% for stability"})
    return {
        "current": modification_map(s, cds_start, cds_end),
        "proposed_edits": edits,
        "predicted_effect": {
            "translation_efficiency": "+10-25% (CDS de-m6A, GC lift)" if edits else "baseline retained",
            "half_life": "extended via 3'UTR reader recruitment",
        },
    }

import math
import numpy as np
MOD_MOTIFS={'m6A':'DRACH','m5C':'CG','psi':'TT','m1A':'GATC'}
def nanopore_modification(signal,expected,noise_sd=.2):
 a=np.asarray(signal,float); e=np.asarray(expected,float); z=(a-e)/(noise_sd+1e-9); p=1/(1+np.exp(-(np.abs(z)-2))); return {'z_scores':z.tolist(),'modification_probability':p.tolist(),'mean_probability':float(p.mean()),'status':'signal-deviation heuristic, not a trained nanopore basecaller'}
def multi_modification_map(rna):
 s=clean_dna(rna.replace('U','T')); out={}
 for name,motif in MOD_MOTIFS.items():
  if name=='m6A': out[name]=[{'position':x['position'],'motif':x['motif'],'m6a_probability':x['m6a_probability']} for x in sorted(predict_m6a(s),key=lambda x:x['position'])]; continue  # same sites/positions as predict_m6a (modified A, thresholded)
  out[name]=[{'position':p,'motif':s[p:p+len(motif)]} for p in find_motif(s,motif)]
 return {'length':len(s),'modifications':out,'site_count':sum(map(len,out.values()))}
def structure_ensemble(rna,window=20):
 s=clean_dna(rna.replace('U','T')); rows=[]
 for i in range(0,len(s),window):
  w=s[i:i+window]; pair=sum(a==b for a,b in zip(w,w[::-1]))/max(1,len(w)); dg=-2*(w.count('G')+w.count('C'))-.5*(w.count('A')+w.count('T')); rows.append({'start':i,'pairing_probability':pair,'folding_dg_proxy':dg})
 return {'windows':rows,'mean_pairing':sum(x['pairing_probability'] for x in rows)/len(rows),'total_dg_proxy':sum(x['folding_dg_proxy'] for x in rows)}
def modification_kinetics(initial=.1,writer=1,eraser=.2,hours=24):
 t=np.linspace(0,hours,121); equilibrium=writer/(writer+eraser); occ=equilibrium+(initial-equilibrium)*np.exp(-(writer+eraser)*t); return {'time_h':t.tolist(),'occupancy':occ.tolist(),'equilibrium':equilibrium}
def functional_impact(rna,modifications):
 struct=structure_ensemble(rna); burden=sum(len(v) for v in modifications.values()); translation=max(0,1+.03*len(modifications.get('psi',[]))-.02*len(modifications.get('m6A',[]))); immune=max(0,.5-.04*len(modifications.get('psi',[]))+.02*len(modifications.get('m1A',[]))); return {'translation_efficiency_relative':translation,'immune_activation_relative':immune,'stability_relative':1+.01*burden-.2*struct['mean_pairing'],'structure':struct}
def design_rna(rna,delivery='LNP'):
 base=optimize_mrna(rna); mods=multi_modification_map(rna); impact=functional_impact(rna,mods['modifications']); encapsulation=max(0,min(1,.8-.3*abs(gc_content(rna.replace('U','T'))-.5))) if delivery=='LNP' else .5; return {**base,'multi_modification_map':mods,'functional_impact':impact,'delivery':{'vehicle':delivery,'encapsulation_proxy':encapsulation},'validation':['direct RNA nanopore with matched control','miCLIP/MeRIP confirmation','ribosome profiling','innate immune panel'],'model_status':'Sequence motifs, folding proxies and explicit kinetics; no trained nanopore/transformer/GNN model and not clinically validated.'}
def rna_diagnostics(r):
 m=r['multi_modification_map']; i=r['functional_impact']; s=i['structure']; return {'length':float(m['length']),'site_count':float(m['site_count']),'m6a_count':float(len(m['modifications']['m6A'])),'m5c_count':float(len(m['modifications']['m5C'])),'psi_count':float(len(m['modifications']['psi'])),'m1a_count':float(len(m['modifications']['m1A'])),'translation_efficiency':i['translation_efficiency_relative'],'immune_activation':i['immune_activation_relative'],'stability':i['stability_relative'],'mean_pairing':s['mean_pairing'],'folding_dg':s['total_dg_proxy'],'encapsulation':r['delivery']['encapsulation_proxy']}
