from __future__ import annotations
import math
from collections import Counter
from ...bio.sequence import clean_dna


def find_strs(seq: str, min_unit: int = 1, max_unit: int = 6, min_repeats: int = 4) -> list[dict]:
    """Exact tandem-repeat detection over 1-6 bp units (suffix-comparison scan)."""
    s = clean_dna(seq)
    n = len(s)
    hits = []
    i = 0
    while i < n:
        best = None
        for u in range(min_unit, max_unit + 1):
            if i + 2 * u > n:
                continue
            unit = s[i:i + u]
            reps = 1
            while s[i + reps * u:i + (reps + 1) * u] == unit:
                reps += 1
            if reps >= min_repeats:
                cand = {"start": i, "unit": unit, "unit_len": u,
                        "repeats": reps, "length": reps * u}
                if best is None or cand["length"] > best["length"]:
                    best = cand
        if best:
            hits.append(best)
            i = best["start"] + best["length"]
        else:
            i += 1
    return hits


def expansion_call(sample_repeats: int, reference_repeats: int, unit: str = "") -> dict:
    """Classify an STR genotype vs reference (normal/intermediate/expanded)."""
    delta = sample_repeats - reference_repeats
    if delta <= 2:
        cls = "normal range"
    elif delta <= 10:
        cls = "intermediate / premutation range"
    else:
        cls = "expanded - pathogenic-range candidate"
    return {
        "unit": unit,
        "reference_repeats": reference_repeats,
        "sample_repeats": sample_repeats,
        "delta": delta,
        "classification": cls,
        "instability_risk": round(1 - math.exp(-max(delta, 0) / 12.0), 3),
    }


def diagnostic_index(str_loci: list[dict], repair_pathway_links: int = 0) -> dict:
    """Diagnostic potential index across loci.

    Combines expansion burden, motif pathogenicity priors (CAG/CTG/CGG known
    expansion disease motifs) and DNA-repair-pathway disruption links.
    """
    hot = {"CAG", "CTG", "CGG", "GCC", "GAA", "CAGG", "CCTG"}
    score = 0.0
    annotated = []
    for locus in str_loci:
        unit = locus["unit"].upper()
        delta = locus.get("delta", 0)
        w = 1.5 if unit in hot or unit[::-1] in hot else 1.0
        contrib = w * min(max(delta, 0) / 10.0, 3.0)
        score += contrib
        annotated.append({**locus, "hot_motif": unit in hot, "contribution": round(contrib, 3)})
    score += 0.5 * repair_pathway_links
    index = round(1 - math.exp(-score / 5.0), 3)
    return {
        "diagnostic_potential_index": index,
        "loci": annotated,
        "repair_pathway_links": repair_pathway_links,
        "interpretation": ("high" if index > 0.6 else "moderate" if index > 0.3 else "low")
        + " diagnostic potential for repeat-instability disease",
    }

# Transparent single-molecule, stochastic repair and pathway models; no trained GNN.
import numpy as np

def reconstruct_repeat_reads(reads,motif):
    motif=clean_dna(motif); rows=[]
    for rid,read in enumerate(reads):
        s=clean_dna(read); best={'repeat_count':0,'start':None,'interruptions':[]}
        for frame in range(len(motif)):
            chunks=[s[i:i+len(motif)] for i in range(frame,len(s)-len(motif)+1,len(motif))]; runs=[]; start=0
            for i,c in enumerate(chunks+['END']):
                if c==motif or (len(c)==len(motif) and sum(a!=b for a,b in zip(c,motif))<=1): continue
                if i>start: runs.append((start,i,chunks[start:i]))
                start=i+1
            if runs:
                a,b,cs=max(runs,key=lambda x:x[1]-x[0]); ints=[{'repeat_index':j,'observed':c} for j,c in enumerate(cs) if c!=motif]
                if b-a>best['repeat_count']: best={'repeat_count':b-a,'start':frame+a*len(motif),'interruptions':ints}
        rows.append({'read_id':rid,**best,'purity':1-len(best['interruptions'])/max(1,best['repeat_count'])})
    counts=np.array([r['repeat_count'] for r in rows],float); return {'reads':rows,'molecule_count':len(rows),'median_repeats':float(np.median(counts)) if len(counts) else 0,'mosaicism_std':float(counts.std()) if len(counts) else 0}

def locus_architecture(sequence,motif,flank=20):
    hits=find_strs(sequence,min_unit=len(motif),max_unit=len(motif),min_repeats=2); candidates=[h for h in hits if h['unit']==motif];
    if not candidates: return {'motif':motif,'repeat_count':0,'interruptions':[],'left_flank':'','right_flank':''}
    h=max(candidates,key=lambda x:x['length']); s=clean_dna(sequence); return {**h,'motif':motif,'repeat_count':h['repeats'],'purity':1.0,'interruptions':[],'left_flank':s[max(0,h['start']-flank):h['start']],'right_flank':s[h['start']+h['length']:h['start']+h['length']+flank]}

def repeat_instability(initial_repeats,divisions=50,slippage=.05,mmr=.8,ber=.5,seed=0,trajectories=500):
    if not 0<=min(slippage,mmr,ber)<=max(slippage,mmr,ber)<=1: raise ValueError('rates must be in [0,1]')
    rng=np.random.default_rng(seed); lengths=np.full(trajectories,int(initial_repeats)); history=[lengths.copy()]
    for _ in range(divisions):
        event=rng.random(trajectories)<slippage*(1+.01*np.maximum(lengths-20,0)); repair=rng.random(trajectories)<(.7*mmr+.3*ber); direction=np.where(rng.random(trajectories)<.65,1,-1); lengths=np.maximum(1,lengths+event*(~repair)*direction); history.append(lengths.copy())
    H=np.asarray(history); return {'mean_trajectory':H.mean(1).tolist(),'variance_trajectory':H.var(1).tolist(),'final_distribution':lengths.tolist(),'expansion_probability':float(np.mean(lengths>initial_repeats)),'contraction_probability':float(np.mean(lengths<initial_repeats))}

def molecular_consequence(motif,repeats,region='coding',accessibility=.5):
    if region=='coding': aggregation=min(1,max(0,repeats-20)/60) if motif in ('CAG','CAA') else .1*min(1,repeats/50); disorder=min(1,.3+repeats/100); return {'region':region,'poly_amino_acid_length':repeats,'aggregation_risk':aggregation,'phase_separation_risk':aggregation*disorder,'structural_disorder':disorder}
    gc=(motif.count('G')+motif.count('C'))/len(motif); stall=min(1,repeats/80*(.5+gc)); return {'region':region,'polymerase_stalling':stall,'chromatin_closure':min(1,stall*(1-accessibility+.5)),'rna_toxicity':min(1,repeats/100*(1+gc)),'splice_disruption':min(1,stall*.7)}

def repair_network(repeats,mmr=.8,ber=.5,hr=.7,checkpoint=.7):
    stress=min(1,max(0,repeats-20)/80); nodes={'repeat_stress':stress,'MMR':mmr,'BER':ber,'HR':hr,'checkpoint':checkpoint,'chromatin':1-stress*.4}; edges=[('repeat_stress','MMR'),('MMR','checkpoint'),('BER','HR'),('checkpoint','chromatin')]; instability=stress*(1-.35*mmr-.2*ber-.25*hr-.2*checkpoint); return {'nodes':nodes,'edges':[{'source':a,'target':b} for a,b in edges],'genomic_instability_index':max(0,instability),'intervention_points':sorted(('MMR','BER','HR','checkpoint'),key=lambda x:nodes[x])[:2]}

def intervention_assessment(repeats,strategy,offtarget_risk=.1):
    efficacy={'repeat_interruption':.45,'rna_targeting':.55,'repair_modulation':.3,'contraction_editing':.65}.get(strategy,.2); expected=max(0,repeats*(1-efficacy)); return {'strategy':strategy,'baseline_repeats':repeats,'expected_repeats_or_burden':expected,'efficacy_proxy':efficacy,'offtarget_risk':offtarget_risk,'net_benefit':efficacy-offtarget_risk,'status':'non-procedural comparative concept, not therapeutic guidance'}

def str_report(sequence,motif,reads=None,region='coding'):
    arch=locus_architecture(sequence,motif); n=arch['repeat_count']; return {'architecture':arch,'single_molecule':reconstruct_repeat_reads(reads,motif) if reads else None,'instability':repeat_instability(n or 1,divisions=20),'molecular_consequence':molecular_consequence(motif,n,region),'repair_network':repair_network(n),'interventions':[intervention_assessment(n,s) for s in ('repeat_interruption','rna_targeting','repair_modulation')],'model_status':'Transparent repeat parsing, stochastic repair and pathway equations; no trained transformer/GNN and not clinical guidance.'}

def str_diagnostics(report):
    a=report['architecture']; i=report['instability']; c=report['molecular_consequence']; n=report['repair_network']; sm=report['single_molecule']; return {'repeat_count':float(a['repeat_count']),'unit_length':float(a.get('unit_len',len(a['motif']))),'repeat_length':float(a.get('length',0)),'purity':float(a.get('purity',0)),'interruption_count':float(len(a['interruptions'])),'molecule_count':float(sm['molecule_count'] if sm else 0),'mosaicism_std':float(sm['mosaicism_std'] if sm else 0),'expansion_probability':i['expansion_probability'],'contraction_probability':i['contraction_probability'],'final_variance':i['variance_trajectory'][-1],'consequence_burden':float(max(v for k,v in c.items() if k!='region')),'instability_index':n['genomic_instability_index']}
