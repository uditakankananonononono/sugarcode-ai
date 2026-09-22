from __future__ import annotations
from ...bio.sequence import clean_dna, gc_content, translate, molecular_weight, orfs
from ..crispr_opt.core import design_guides
from ..openclinvar.core import interpret_variant
from ..dark_genome.core import decode


def gene_profile(symbol: str, genomic_seq: str, promoter_span: tuple[int, int] | None = None,
                 variants: list[dict] | None = None, publications: list[int] | None = None) -> dict:
    """High-fidelity biological profile of a gene locus.

    Integrates: sequence composition, ORF/protein stats, regulatory landscape,
    variant interpretations, CRISPR target designs and publication trend bins.
    External NCBI/UniProt/ClinVar connectors are a later drop; this computes
    everything derivable from the sequence itself.
    """
    s = clean_dna(genomic_seq)
    found_orfs = orfs(s, min_aa=30)
    longest = max(found_orfs, key=lambda o: o["aa_length"], default=None)
    protein = longest["protein"] if longest else ""
    regulatory = decode(s, coding_spans=[(o["start"], o["end"]) for o in found_orfs])
    crispr = design_guides(s, background=s, top_n=5)
    var_results = []
    for v in (variants or []):
        var_results.append(interpret_variant(symbol, v["variant"],
                                             consequence=v.get("consequence"),
                                             allele_frequency=v.get("allele_frequency"),
                                             functional_score=v.get("functional_score")))
    return {
        "symbol": symbol,
        "locus": {"length": len(s), "gc_content": round(gc_content(s), 4)},
        "protein": ({"aa_length": longest["aa_length"],
                     "molecular_weight_da": round(molecular_weight(protein), 1),
                     "strand": longest["strand"], "span": [longest["start"], longest["end"]]}
                    if longest else None),
        "regulatory_landscape": {
            "enhancer_clusters": regulatory["enhancer_clusters"],
            "cpg_islands": regulatory["cpg_islands"],
            "tf_motif_count": len(regulatory["tf_motif_hits"]),
        },
        "variants": var_results,
        "crispr_targets": crispr["guides"],
        "publication_trend": _pub_trend(publications or []),
        "pathway_links": _pathway_links(symbol),
    }


def _pub_trend(years: list[int]) -> dict:
    if not years:
        return {"note": "no publication data supplied"}
    bins: dict[int, int] = {}
    for y in years:
        bins[y // 5 * 5] = bins.get(y // 5 * 5, 0) + 1
    return {"by_half_decade": dict(sorted(bins.items())), "total": len(years)}


def _pathway_links(symbol: str) -> list[dict]:
    known = {
        "TP53": ["DNA damage response", "apoptosis", "cell-cycle checkpoint"],
        "BRCA1": ["homologous recombination repair", "G2/M checkpoint"],
        "CFTR": ["chloride transport", "epithelial fluid secretion"],
        "HBB": ["oxygen transport", "erythrocyte physiology"],
        "EGFR": ["RTK signaling", "MAPK cascade", "cell proliferation"],
    }
    return [{"pathway": p, "source": "built-in reference"} for p in known.get(symbol.upper(), [])]


def live_gene_profile(symbol: str, organism: str = "human", offline: bool = False) -> dict:
    """Live multi-source gene profile: NCBI Gene + UniProt, merged.

    Falls back per-source: a source that fails is reported as unavailable,
    never silently dropped or invented.
    """
    from ...bio import entrez, uniprot
    out = {"symbol": symbol, "organism": organism, "sources": {}}
    try:
        uid = entrez.gene_id(symbol, organism, offline=offline)
        if uid:
            summ = entrez.esummary("gene", [uid], offline=offline)[uid]
            out["sources"]["ncbi_gene"] = {
                "uid": uid, "name": summ.get("name"),
                "description": summ.get("description"),
                "chromosome": summ.get("chromosome"),
                "map_location": summ.get("maplocation"),
                "aliases": summ.get("otheraliases", ""),
            }
        else:
            out["sources"]["ncbi_gene"] = {"error": "symbol not found"}
    except Exception as e:  # connector failure is reported, not hidden
        out["sources"]["ncbi_gene"] = {"error": f"{type(e).__name__}: {e}"}
    try:
        org_id = 9606 if organism == "human" else 10090
        rec = uniprot.search(symbol, organism_id=org_id, offline=offline)
        out["sources"]["uniprot"] = rec or {"error": "no reviewed entry"}
    except Exception as e:
        out["sources"]["uniprot"] = {"error": f"{type(e).__name__}: {e}"}
    # local analysis still runs on the fetched sequence when available
    seq = (out["sources"].get("uniprot") or {}).get("sequence", "")
    if seq:
        out["protein_stats"] = {
            "length": len(seq),
            "hydrophobic_fraction": round(sum(1 for a in seq if a in "AILMFWVY") / len(seq), 3),
            "charged_fraction": round(sum(1 for a in seq if a in "DEKRH") / len(seq), 3),
        }
    return out


def live_publication_trend(symbol: str, years: int = 5, offline: bool = False) -> dict:
    """Real publication trend: per-year PubMed counts for the gene symbol."""
    from ...bio import entrez
    from datetime import datetime
    now = datetime.now().year
    counts = {}
    for y in range(now - years + 1, now + 1):
        data = entrez._get("esearch.fcgi", {"db": "pubmed",
                                            "term": f"{symbol}[Title/Abstract] AND {y}[dp]",
                                            "retmode": "json", "retmax": 0},
                           offline=offline)
        import json as _j
        counts[y] = int(_j.loads(data)["esearchresult"]["count"])
    vals = list(counts.values())
    trend = ("rising" if len(vals) >= 2 and vals[-1] > vals[0] * 1.2 else
             "falling" if len(vals) >= 2 and vals[-1] < vals[0] * 0.8 else "steady")
    return {"symbol": symbol, "source": "PubMed (live)", "counts_by_year": counts,
            "trend": trend, "note": "Title/Abstract mention counts per publication year"}

# Explicit probabilistic/mechanistic digital-twin models. No trained model is
# bundled and these outputs are not clinically validated.
import math, json
import numpy as np
from scipy.integrate import solve_ivp

def molecular_graph(symbol,variants=None,isoforms=None,interactions=None):
    nodes=[{"id":symbol,"type":"gene"}]; edges=[]
    for i,iso in enumerate(isoforms or []): nodes.append({"id":iso,"type":"isoform"}); edges.append({"source":symbol,"target":iso,"relation":"transcribes"})
    for v in variants or []: nodes.append({"id":v['variant'],"type":"allele"}); edges.append({"source":v['variant'],"target":symbol,"relation":"perturbs"})
    for x in interactions or []: nodes.append({"id":x,"type":"protein"}); edges.append({"source":symbol,"target":x,"relation":"interacts"})
    return {"nodes":nodes,"edges":edges}

def splice_outcome(consequence,position=None,exon_length=150):
    consequence=(consequence or '').lower(); splice='splice' in consequence; stop='stop' in consequence or 'nonsense' in consequence; nmd=stop and (position is None or position<exon_length-50); return {"splice_disruption":.8 if splice else .05,"exon_inclusion":.2 if splice else .95,"nmd_probability":.8 if nmd else .1,"isoform_switch_probability":.65 if splice else .1}

def structure_perturbation(conservation=.5,interface=False,active_site=False,buried=.5):
    for v in (conservation,buried):
        if not 0<=v<=1: raise ValueError("fractions must be in [0,1]")
    ddg=.5+2.5*buried+1.2*conservation+.8*interface+1.0*active_site; return {"ddg_kcal_mol":ddg,"destabilization_probability":1/(1+math.exp(-(ddg-2))),"interface_loss_probability":min(1,.25+.5*interface+.2*conservation),"allosteric_disruption":min(1,.2+.4*active_site+.3*conservation)}

def variant_posterior(conservation=.5,structural=None,regulatory=.1,splicing=.1,functional_prior=.5,calibration_n=100):
    structural=structural or structure_perturbation(conservation); components={"conservation":conservation,"structural":structural['destabilization_probability'],"interface":structural['interface_loss_probability'],"regulatory":regulatory,"splicing":splicing,"functional":functional_prior}; weights={"conservation":.18,"structural":.22,"interface":.12,"regulatory":.15,"splicing":.15,"functional":.18}; logit=-2+sum(4*weights[k]*components[k] for k in components); p=1/(1+math.exp(-logit)); radius=1.96*math.sqrt(p*(1-p)/max(calibration_n,1)); contrib={k:weights[k]*components[k] for k in components}; total=sum(contrib.values()); return {"pathogenic_probability":p,"attributions":{k:v/total for k,v in contrib.items()},"conformal_interval":[max(0,p-radius),min(1,p+radius)],"calibration_n":calibration_n}

def conformational_ensemble(ddg,states=None):
    states=states or {"active":0,"inactive":1.5,"misfolded":4}; energies={k:v+(ddg if k=='misfolded' else .2*ddg if k=='inactive' else 0) for k,v in states.items()}; w={k:math.exp(-v/.593) for k,v in energies.items()}; z=sum(w.values()); return {"energies":energies,"populations":{k:v/z for k,v in w.items()}}

def pathway_dynamics(hours=24,expression=1,drug_inhibition=0,feedback=.2):
    if hours<=0 or not 0<=drug_inhibition<=1: raise ValueError("invalid dynamics")
    def rhs(_t,y): signal,target,phenotype=y; return [expression*(1-drug_inhibition)-.5*signal-feedback*target,.8*signal-.3*target,.4*target-.2*phenotype]
    t=np.linspace(0,hours,121); sol=solve_ivp(rhs,(0,hours),[0,0,0],t_eval=t,rtol=1e-8,atol=1e-9); return {"time_h":sol.t.tolist(),"signal":sol.y[0].tolist(),"biomarker":sol.y[1].tolist(),"phenotype":sol.y[2].tolist()}

def counterfactual_variant(conservation=.5,interface=False,regulatory=.1,splicing=.1,condition=None):
    condition=condition or {}; structural=structure_perturbation(conservation,interface,condition.get('active_site',False),condition.get('buried',.5)); posterior=variant_posterior(conservation,structural,regulatory,splicing,condition.get('functional_prior',.5)); pathway=pathway_dynamics(expression=max(.05,1-posterior['pathogenic_probability']),drug_inhibition=condition.get('drug_inhibition',0)); return {"structural":structural,"posterior":posterior,"ensemble":conformational_ensemble(structural['ddg_kcal_mol']),"pathway":pathway,"phenotype_delta":pathway['phenotype'][-1]-pathway_dynamics()['phenotype'][-1]}

def outcome_aware_crispr(seq,desired='knockout',chromatin=.5,allele=None):
    design=design_guides(seq,background=seq,top_n=10); ranked=[]
    for g in design['guides']:
        specificity=1/(1+g['off_target_risk']); allele_score=1 if not allele else sum(a!=b for a,b in zip(g['guide'],allele))/20; phenotype=g['on_target']*(.5+.5*chromatin)*specificity; ranked.append({**g,"chromatin_score":chromatin,"allele_specificity":allele_score,"predicted_phenotype_score":phenotype,"desired_outcome":desired})
    return sorted(ranked,key=lambda x:-x['predicted_phenotype_score'])

def power_estimate(effect_size,variance=.25,power=.8):
    if effect_size<=0 or variance<=0 or not 0<power<1: raise ValueError("invalid power inputs")
    z=1.96+(.84 if power<=.8 else 1.28); return {"replicates_per_group":math.ceil(2*variance*z*z/effect_size**2),"effect_size":effect_size,"target_power":power}

def experimental_plan(symbol,effect_size=.5):
    return {"symbol":symbol,"controls":["unedited control","non-targeting guide","positive perturbation control"],"readouts":["qPCR","protein abundance assay","single-cell RNA-seq for network effects"],"power":power_estimate(effect_size),"status":"Study-design guidance requiring institutional review; not an executable protocol."}

def feedback_update(prior_probability,successes,total):
    if not 0<=prior_probability<=1 or not 0<=successes<=total: raise ValueError("invalid feedback")
    a=1+prior_probability*8+successes; b=1+(1-prior_probability)*8+total-successes; return {"alpha":a,"beta":b,"mean":a/(a+b),"std":math.sqrt(a*b/((a+b)**2*(a+b+1)))}

def gene_diagnostics(symbol,seq,variants=None):
    p=gene_profile(symbol,seq,variants=variants); d={"locus_length":float(p['locus']['length']),"gc_fraction":p['locus']['gc_content'],"protein_present":float(p['protein'] is not None),"protein_aa_length":float(p['protein']['aa_length'] if p['protein'] else 0),"protein_mw":float(p['protein']['molecular_weight_da'] if p['protein'] else 0),"enhancer_cluster_count":float(len(p['regulatory_landscape']['enhancer_clusters'])),"cpg_island_count":float(len(p['regulatory_landscape']['cpg_islands'])),"tf_motif_count":float(p['regulatory_landscape']['tf_motif_count']),"variant_count":float(len(p['variants'])),"crispr_target_count":float(len(p['crispr_targets'])),"pathway_count":float(len(p['pathway_links']))}
    for name,val in (("conservation",.5),("regulatory",.1),("splicing",.1)): d[f'baseline.{name}']=val
    return d

def digital_twin(symbol,seq,variants=None,condition=None):
    profile=gene_profile(symbol,seq,variants=variants); graph=molecular_graph(symbol,variants=variants,isoforms=['canonical']); cf=counterfactual_variant(condition=condition); return {"profile":profile,"causal_graph":graph,"counterfactual":cf,"crispr":outcome_aware_crispr(seq),"experimental_plan":experimental_plan(symbol),"diagnostics":gene_diagnostics(symbol,seq,variants),"model_status":"Transparent mechanistic/probabilistic models; no trained model and not clinically validated."}

# Variant-connected v2 overrides.
def _variant_features(variant):
    """Derive mechanistic severities from one normalized variant record."""
    variant=variant or {}; consequence=str(variant.get('consequence','')).lower(); coordinate=str(variant.get('variant','')); digits=''.join(c for c in coordinate if c.isdigit()); position=int(digits or variant.get('position',75)); splice=splice_outcome(consequence,position); synonymous='synonymous' in consequence; stop=any(x in consequence for x in ('nonsense','stop','frameshift')); missense='missense' in consequence
    conservation=float(variant.get('conservation',.1 if synonymous else .9 if stop else .65 if missense else .5)); regulatory=float(variant.get('regulatory',.05 if synonymous else .55 if 'regulatory' in consequence else .15)); splicing=float(variant.get('splicing',splice['splice_disruption'])); interface=bool(variant.get('interface',missense or stop)); active=bool(variant.get('active_site',stop)); functional=float(variant.get('functional_score',.05 if synonymous else .95 if stop else .7 if missense else .5))
    return {"consequence":consequence,"position":position,"synonymous":synonymous,"stop_or_frameshift":stop,"conservation":conservation,"regulatory":regulatory,"splicing":splicing,"interface":interface,"active_site":active,"functional_prior":functional,"splice_outcome":splice}


def pathway_dynamics(hours=24,expression=1,drug_inhibition=0,feedback=.2,gene='GENE',variant_effect=0):
    if hours<=0 or not 0<=drug_inhibition<=1: raise ValueError("invalid dynamics")
    gene=gene.upper(); biomarker_name={'TP53':'p53_targets','EGFR':'p_ERK','BRCA1':'DNA_repair_flux','CFTR':'chloride_transport'}.get(gene,f'{gene}_downstream_signal'); phenotype_name={'TP53':'apoptosis','EGFR':'proliferation','BRCA1':'genome_stability','CFTR':'epithelial_transport'}.get(gene,'cellular_function')
    drive=expression*(1-variant_effect)
    def rhs(_t,y): signal,target,phenotype=y; return [drive*(1-drug_inhibition)-.5*signal-feedback*target,.8*signal-.3*target,.4*target-.2*phenotype]
    t=np.linspace(0,hours,121); sol=solve_ivp(rhs,(0,hours),[0,0,0],t_eval=t,rtol=1e-8,atol=1e-9); return {"time_h":sol.t.tolist(),"signal":sol.y[0].tolist(),"biomarker":sol.y[1].tolist(),"phenotype":sol.y[2].tolist(),"biomarker_name":biomarker_name,"phenotype_name":phenotype_name,"gene":gene,"variant_effect":variant_effect}


def counterfactual_variant(conservation=.5,interface=False,regulatory=.1,splicing=.1,condition=None,gene='GENE',functional_prior=.5,active_site=False):
    condition=condition or {}; structural=structure_perturbation(conservation,interface,active_site or condition.get('active_site',False),condition.get('buried',.5)); posterior=variant_posterior(conservation,structural,regulatory,splicing,functional_prior); effect=posterior['pathogenic_probability']; pathway=pathway_dynamics(expression=1-splicing*.5,drug_inhibition=condition.get('drug_inhibition',0),gene=gene,variant_effect=effect*.7); baseline=pathway_dynamics(drug_inhibition=condition.get('drug_inhibition',0),gene=gene); return {"structural":structural,"posterior":posterior,"ensemble":conformational_ensemble(structural['ddg_kcal_mol']),"pathway":pathway,"phenotype_delta":pathway['phenotype'][-1]-baseline['phenotype'][-1],"condition":condition}


def outcome_aware_crispr(seq,desired='knockout',chromatin=.5,allele=None,nucleosome=.5):
    design=design_guides(seq,background=seq,top_n=10); ranked=[]
    for g in design['guides']:
        specificity=1/(1+g['off_target_risk']); allele_score=1 if not allele else sum(a!=b for a,b in zip(g['guide'],allele))/20; context=chromatin*(1-.5*nucleosome); phenotype=g['on_target']*(.5+.5*context)*specificity; guide=g['guide']; editable=[i+1 for i,b in enumerate(guide) if 4<=i+1<=8 and b in 'CA']; pbs=guide[-13:]; rtt=guide[-15:]; silent_pam_disruption={"recommended":g.get('pam','').endswith('GG'),"strategy":"synonymous PAM/seed change when coding context permits"}; ranked.append({**g,"chromatin_score":chromatin,"nucleosome_score":nucleosome,"allele_specificity":allele_score,"predicted_phenotype_score":phenotype,"desired_outcome":desired,"base_edit":{"window":[4,8],"editable_positions":editable,"bystander_count":max(0,len(editable)-1)},"prime_edit":{"pbs":pbs,"pbs_length":len(pbs),"rt_template":rtt,"rtt_length":len(rtt)},"silent_pam_disruption":silent_pam_disruption,"validation_assays":["amplicon sequencing","GUIDE-seq or orthogonal off-target assay"]})
    return sorted(ranked,key=lambda x:-x['predicted_phenotype_score'])


def experimental_plan(symbol,effect_size=.5):
    return {"symbol":symbol,"controls":["unedited control","non-targeting guide","positive perturbation control"],"readouts":["qPCR","protein abundance assay","single-cell RNA-seq for network effects"],"power":power_estimate(effect_size),"status":"Non-procedural study-design guidance only; omits reagents, conditions and execution steps. Institutional review required."}


def gene_diagnostics(symbol,seq,variants=None,counterfactual=None):
    p=gene_profile(symbol,seq,variants=variants); features=_variant_features((variants or [{}])[0]); cf=counterfactual or counterfactual_variant(features['conservation'],features['interface'],features['regulatory'],features['splicing'],gene=symbol,functional_prior=features['functional_prior'],active_site=features['active_site']); return {"locus_length":float(p['locus']['length']),"gc_fraction":p['locus']['gc_content'],"protein_present":float(p['protein'] is not None),"protein_aa_length":float(p['protein']['aa_length'] if p['protein'] else 0),"protein_mw":float(p['protein']['molecular_weight_da'] if p['protein'] else 0),"enhancer_cluster_count":float(len(p['regulatory_landscape']['enhancer_clusters'])),"cpg_island_count":float(len(p['regulatory_landscape']['cpg_islands'])),"tf_motif_count":float(p['regulatory_landscape']['tf_motif_count']),"variant_count":float(len(p['variants'])),"crispr_target_count":float(len(p['crispr_targets'])),"variant_splice_disruption":features['splicing'],"variant_nmd_probability":features['splice_outcome']['nmd_probability'],"variant_ddg":cf['structural']['ddg_kcal_mol'],"variant_pathogenic_probability":cf['posterior']['pathogenic_probability'],"variant_phenotype_delta":cf['phenotype_delta']}


def digital_twin(symbol,seq,variants=None,condition=None):
    variants=variants or []; profile=gene_profile(symbol,seq,variants=variants); graph=molecular_graph(symbol,variants=variants,isoforms=['canonical']); features=_variant_features(variants[0] if variants else None); cf=counterfactual_variant(features['conservation'],features['interface'],features['regulatory'],features['splicing'],condition,gene=symbol,functional_prior=features['functional_prior'],active_site=features['active_site']); return {"profile":profile,"causal_graph":graph,"variant_features":features,"counterfactual":cf,"crispr":outcome_aware_crispr(seq),"experimental_plan":experimental_plan(symbol),"diagnostics":gene_diagnostics(symbol,seq,variants,cf),"model_status":"Transparent mechanistic/probabilistic models; no trained model and not clinically validated."}
