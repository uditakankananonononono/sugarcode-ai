from __future__ import annotations
from ...bio.sequence import (
    clean_dna, transcribe, translate, gc_content, molecular_weight,
    hydrophobicity_profile, AA_NAMES, orfs,
)


def _segments(dna: str, n: int = 6) -> list[dict]:
    """Split the gene into n labelled sequence segments for UI display."""
    dna = clean_dna(dna)
    n = max(1, min(n, len(dna)))
    size = len(dna) // n
    segs = []
    for i in range(n):
        start = i * size
        end = len(dna) if i == n - 1 else (i + 1) * size
        segs.append({"index": i, "start": start, "end": end,
                     "sequence": dna[start:end], "gc": round(gc_content(dna[start:end]), 4)})
    return segs


def explore(dna: str, gene_name: str = "gene", reading_frame: int = 0) -> dict:
    """Full central-dogma trace for a DNA sequence.

    Returns DNA stats, the mRNA transcript, the translated protein with
    annotations, detected ORFs and display segments.
    """
    dna = clean_dna(dna)
    mrna = transcribe(dna)
    protein = translate(dna, reading_frame=reading_frame)
    mature = protein.split("*")[0]
    found_orfs = orfs(dna, min_aa=10)
    longest = max(found_orfs, key=lambda o: o["aa_length"], default=None)
    return {
        "gene": gene_name,
        "dna": {
            "length": len(dna),
            "gc_content": round(gc_content(dna), 4),
            "sequence": dna,
            "segments": _segments(dna),
        },
        "mrna": {
            "length": len(mrna),
            "sequence": mrna,
            "codon_count": len(mrna) // 3,
        },
        "protein": {
            "length": len(mature),
            "sequence": mature,
            "molecular_weight_da": round(molecular_weight(mature), 2),
            "hydrophobicity": [round(v, 3) for v in hydrophobicity_profile(mature)],
            "composition": {aa: mature.count(aa) for aa in sorted(set(mature)) if aa in AA_NAMES},
            "truncated_by_stop": "*" in protein,
        },
        "orfs": [
            {"strand": o["strand"], "frame": o["frame"], "start": o["start"],
             "end": o["end"], "aa_length": o["aa_length"]}
            for o in found_orfs
        ],
        "longest_orf": ({k: longest[k] for k in ("strand", "frame", "start", "end", "aa_length")}
                        if longest else None),
        "animation_script": _animation_steps(dna, mrna, mature),
    }


def _animation_steps(dna: str, mrna: str, protein: str) -> list[dict]:
    """Keyframe descriptions for a 3D central-dogma animation."""
    return [
        {"step": 1, "scene": "unwind", "detail": f"DNA double helix ({len(dna)} bp) unwinds; strands separate."},
        {"step": 2, "scene": "transcribe", "detail": f"RNA polymerase builds {len(mrna)} nt pre-mRNA 5'->3'."},
        {"step": 3, "scene": "process", "detail": "5' cap added, poly-A tail appended, introns spliced out."},
        {"step": 4, "scene": "translate", "detail": f"Ribosome scans to AUG; tRNAs elongate a {len(protein)} aa chain."},
        {"step": 5, "scene": "fold", "detail": "Chain folds into secondary/tertiary structure; chaperones assist."},
    ]


def central_dogma_report(dna: str, gene_name: str = "gene") -> str:
    r = explore(dna, gene_name)
    lines = [
        f"Gene Explorer report: {gene_name}",
        f"DNA: {r['dna']['length']} bp, GC {r['dna']['gc_content']:.1%}",
        f"mRNA: {r['mrna']['length']} nt, {r['mrna']['codon_count']} codons",
        f"Protein: {r['protein']['length']} aa, {r['protein']['molecular_weight_da']} Da",
    ]
    if r["protein"]["truncated_by_stop"]:
        lines.append("Note: internal stop codon - protein shown up to first stop.")
    if r["longest_orf"]:
        o = r["longest_orf"]
        lines.append(f"Longest ORF: strand {o['strand']} frame {o['frame']} "
                     f"({o['aa_length']} aa) at {o['start']}..{o['end']}")
    return "\n".join(lines)

# Mechanistic digital-gene exploration. No trained model and not clinically validated.
import math,json
import numpy as np
from scipy.integrate import solve_ivp

def information_graph(dna,isoforms=None,variants=None,interactions=None):
    trace=explore(dna); nodes=[{"id":"DNA","type":"allele"},{"id":"pre_mRNA","type":"transcript"},{"id":"protein","type":"conformer"}]; edges=[{"source":"DNA","target":"pre_mRNA","relation":"transcription"},{"source":"pre_mRNA","target":"protein","relation":"translation"}]
    for i,x in enumerate(isoforms or []): nodes.append({"id":x,"type":"isoform"}); edges.append({"source":"pre_mRNA","target":x,"relation":"splicing"})
    for v in variants or []: nodes.append({"id":v,"type":"allele"}); edges.append({"source":v,"target":"DNA","relation":"perturbs"})
    for x in interactions or []: nodes.append({"id":x,"type":"protein"}); edges.append({"source":"protein","target":x,"relation":"interacts"})
    return {"nodes":nodes,"edges":edges,"central_dogma":trace['animation_script']}

def transcript_processing(exons,introns=None,cap_efficiency=.98,poly_a_length=200):
    if not exons or not 0<=cap_efficiency<=1 or poly_a_length<0: raise ValueError("invalid transcript processing inputs")
    exons=[clean_dna(x) for x in exons]; mature=''.join(exons); return {"pre_mrna_length":len(mature)+sum(len(clean_dna(x)) for x in (introns or [])),"mature_mrna":mature.replace('T','U'),"exon_count":len(exons),"intron_count":len(introns or []),"cap_probability":cap_efficiency,"poly_a_length":poly_a_length,"export_probability":cap_efficiency*(1-math.exp(-poly_a_length/50))}

def isoform_expression(isoforms,condition=None):
    condition=condition or {}; weights={name:max(0,float(value)*float(condition.get(name,1))) for name,value in isoforms.items()}; z=sum(weights.values())
    if z<=0: raise ValueError("isoform weights must sum positive")
    return {"fractions":{k:v/z for k,v in weights.items()},"dominant":max(weights,key=weights.get)}

def variant_cascade(dna,pos,alt,conservation=.5,interface=False,regulatory=.1):
    s=clean_dna(dna)
    if not 0<=pos<len(s): raise ValueError("position outside DNA")
    alt=clean_dna(alt)
    if len(alt)!=1: raise ValueError("alt must be one base")
    mutant=s[:pos]+alt+s[pos+1:]; ref_protein=translate(s); alt_protein=translate(mutant); aa_changes=sum(a!=b for a,b in zip(ref_protein,alt_protein))+abs(len(ref_protein)-len(alt_protein)); ddg=.5+2*conservation+.8*interface+.4*aa_changes; expression_ratio=max(.05,1-regulatory-.1*aa_changes); phenotype=1-expression_ratio*math.exp(-ddg/5)
    return {"ref":s[pos],"alt":alt,"protein_change_count":aa_changes,"ddg_kcal_mol":ddg,"interface_disruption":min(1,.2+.5*interface+.1*aa_changes),"expression_ratio":expression_ratio,"phenotype_effect":phenotype,"mutant_dna":mutant}

def conformational_states(protein,ddg=0):
    p=protein or 'X'; hydrophobic=sum(a in 'AILMFWVY' for a in p)/len(p); energies={"native":0,"open":1+.5*hydrophobic,"misfolded":3-ddg*.3}; w={k:math.exp(-v/.593) for k,v in energies.items()}; z=sum(w.values()); return {"energies":energies,"populations":{k:v/z for k,v in w.items()},"hydrophobic_fraction":hydrophobic}

def pathway_simulation(hours=24,expression=1,feedback=.2,drug=.0):
    if hours<=0 or not 0<=drug<=1: raise ValueError("invalid pathway inputs")
    def rhs(_t,y): protein,signal,phenotype=y; return [expression-.4*protein,.8*protein*(1-drug)-.3*signal-feedback*phenotype,.5*signal-.25*phenotype]
    t=np.linspace(0,hours,121); sol=solve_ivp(rhs,(0,hours),[0,0,0],t_eval=t,rtol=1e-8,atol=1e-9); return {"time_h":sol.t.tolist(),"protein":sol.y[0].tolist(),"signal":sol.y[1].tolist(),"phenotype":sol.y[2].tolist()}

def probabilistic_variant(conservation=.5,ddg=1,regulatory=.1,splicing=.1,functional=.5,n=100):
    components={"conservation":conservation,"structure":1/(1+math.exp(-(ddg-2))),"regulatory":regulatory,"splicing":splicing,"functional":functional}; weights={"conservation":.2,"structure":.25,"regulatory":.2,"splicing":.15,"functional":.2}; raw=sum(weights[k]*components[k] for k in components); p=1/(1+math.exp(-5*(raw-.45))); radius=1.96*math.sqrt(p*(1-p)/n); contributions={k:weights[k]*components[k] for k in components}; total=sum(contributions.values()); return {"pathogenic_probability":p,"attributions":{k:v/total for k,v in contributions.items()},"conformal_interval":[max(0,p-radius),min(1,p+radius)]}

def central_dogma_diagnostics(dna,reading_frame=0):
    r=explore(dna,reading_frame=reading_frame); d={"dna_length":float(r['dna']['length']),"dna_gc":r['dna']['gc_content'],"segment_count":float(len(r['dna']['segments'])),"mrna_length":float(r['mrna']['length']),"codon_count":float(r['mrna']['codon_count']),"protein_length":float(r['protein']['length']),"protein_mw":float(r['protein']['molecular_weight_da']),"protein_hydrophobicity_mean":float(np.mean(r['protein']['hydrophobicity'])) if r['protein']['hydrophobicity'] else 0.,"protein_hydrophobicity_std":float(np.std(r['protein']['hydrophobicity'])) if r['protein']['hydrophobicity'] else 0.,"truncated_by_stop":float(r['protein']['truncated_by_stop']),"orf_count":float(len(r['orfs'])),"longest_orf_aa":float(r['longest_orf']['aa_length'] if r['longest_orf'] else 0),"animation_steps":float(len(r['animation_script']))}; return d

def digital_gene_explorer(dna,gene_name='gene',variants=None,condition=None):
    trace=explore(dna,gene_name); protein=trace['protein']['sequence']; cascades=[variant_cascade(dna,v['position'],v['alt'],v.get('conservation',.5),v.get('interface',False),v.get('regulatory',.1)) for v in (variants or [])]; return {"trace":trace,"information_graph":information_graph(dna,variants=[f"{v['position']}{v['alt']}" for v in (variants or [])]),"transcript_processing":transcript_processing([dna]),"conformational_states":conformational_states(protein,cascades[0]['ddg_kcal_mol'] if cascades else 0),"variant_cascades":cascades,"pathway":pathway_simulation(expression=(condition or {}).get('expression',1),drug=(condition or {}).get('drug',0)),"diagnostics":central_dogma_diagnostics(dna),"model_status":"Transparent sequence/mechanistic models; no trained model and not clinically validated."}
