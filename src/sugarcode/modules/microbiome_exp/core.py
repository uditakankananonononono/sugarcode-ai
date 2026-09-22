from __future__ import annotations
import math
from collections import Counter

FUNCTIONAL_POTENTIAL = {
    "Faecalibacterium": ["butyrate production", "anti-inflammatory"],
    "Bacteroides": ["polysaccharide degradation", "bile acid metabolism"],
    "Lactobacillus": ["lactate production", "pathogen exclusion"],
    "Akkermansia": ["mucin degradation", "barrier support"],
    "Escherichia": ["pro-inflammatory potential", "vitamin K"],
    "Bifidobacterium": ["acetate production", "infant gut health"],
    "Clostridium": ["butyrate production (cluster IV)", "spore formation"],
    "Prevotella": ["fiber fermentation", "propionate production"],
}
DISEASE_ASSOCIATIONS = {
    "low_diversity": ["IBD", "obesity", "c.diff risk"],
    "Faecalibacterium_depleted": ["Crohn's disease"],
    "Escherichia_blooms": ["inflammation", "dysbiosis"],
    "Akkermansia_depleted": ["metabolic syndrome"],
}


def analyze_16s(counts: dict[str, int], metadata: dict | None = None) -> dict:
    """Taxonomic profile from genus-level read counts.

    Computes alpha diversity (Shannon, Simpson, richness), distributions,
    functional potential summary and disease-state correlations.
    """
    if not counts or sum(counts.values()) <= 0:
        raise ValueError("empty count table")
    total = sum(counts.values())
    rel = {g: c / total for g, c in counts.items()}
    shannon = -sum(p * math.log(p) for p in rel.values() if p > 0)
    simpson = 1 - sum(p ** 2 for p in rel.values())
    richness = len(counts)
    dominant = sorted(rel, key=rel.get, reverse=True)[:5]
    functions = {}
    for g, p in rel.items():
        if g in FUNCTIONAL_POTENTIAL and p > 0.01:
            for f in FUNCTIONAL_POTENTIAL[g]:
                functions[f] = functions.get(f, 0) + p
    flags = []
    if shannon < 1.5:
        flags.append({"flag": "low_diversity", "associations": DISEASE_ASSOCIATIONS["low_diversity"]})
    if rel.get("Faecalibacterium", 0) < 0.01:
        flags.append({"flag": "Faecalibacterium_depleted",
                      "associations": DISEASE_ASSOCIATIONS["Faecalibacterium_depleted"]})
    if rel.get("Escherichia", 0) > 0.2:
        flags.append({"flag": "Escherichia_blooms",
                      "associations": DISEASE_ASSOCIATIONS["Escherichia_blooms"]})
    if rel.get("Akkermansia", 0) < 0.005:
        flags.append({"flag": "Akkermansia_depleted",
                      "associations": DISEASE_ASSOCIATIONS["Akkermansia_depleted"]})
    return {
        "total_reads": total,
        "alpha_diversity": {"shannon": round(shannon, 3), "simpson": round(simpson, 3),
                            "richness": richness},
        "relative_abundance": {g: round(p, 4) for g, p in
                               sorted(rel.items(), key=lambda kv: -kv[1])},
        "dominant_genera": dominant,
        "functional_potential": {f: round(v, 3) for f, v in
                                 sorted(functions.items(), key=lambda kv: -kv[1])},
        "disease_correlations": flags,
        "publication_trend_link": "profile comparable against published cohort studies",
        "metadata": metadata or {},
    }

import numpy as np

def validate_count_table(table: dict[str,dict[str,int]]) -> dict:
    if not isinstance(table,dict) or len(table)<2: raise ValueError("count table must contain at least two samples")
    out={}
    for sample,counts in table.items():
        if not isinstance(counts,dict) or not counts or any(not isinstance(v,int) or v<0 for v in counts.values()) or sum(counts.values())<=0: raise ValueError(f"sample {sample!r} requires non-negative integer counts with positive total")
        out[str(sample)]={str(k):v for k,v in counts.items()}
    return out

def cohort_analysis(table: dict[str,dict[str,int]], metadata: dict[str,dict]|None=None) -> dict:
    """Compute alpha/beta diversity, distributions, functions, and disease associations."""
    table=validate_count_table(table); metadata=metadata or {}; taxa=sorted({t for x in table.values() for t in x}); samples=sorted(table); X=np.array([[table[s].get(t,0) for t in taxa] for s in samples],float); totals=X.sum(1); P=X/totals[:,None]
    alpha=[]
    for s,p,total in zip(samples,P,totals):
        nz=p[p>0]; sh=-float(np.sum(nz*np.log(nz))); simp=1-float(np.sum(p*p)); richness=int(np.sum(p>0)); even=sh/math.log(richness) if richness>1 else 0; alpha.append({"sample":s,"reads":int(total),"shannon":sh,"simpson":simp,"richness":richness,"pielou_evenness":even})
    bray=np.zeros((len(samples),len(samples)))
    for i in range(len(samples)):
        for j in range(len(samples)): bray[i,j]=np.sum(abs(P[i]-P[j]))/max(np.sum(P[i]+P[j]),1e-12)
    centered=-.5*(bray**2-bray.mean(0)[None,:]-bray.mean(1)[:,None]+bray.mean() ); vals,vec=np.linalg.eigh(centered); order=np.argsort(vals)[::-1]; coords=vec[:,order[:2]]*np.sqrt(np.maximum(vals[order[:2]],0))
    funcs={s:{f:sum(P[i,j] for j,t in enumerate(taxa) if f in FUNCTIONAL_POTENTIAL.get(t,[])) for f in {z for t in taxa for z in FUNCTIONAL_POTENTIAL.get(t,[])}} for i,s in enumerate(samples)}
    flags={s:analyze_16s(table[s],metadata.get(s))["disease_correlations"] for s in samples}
    return {"samples":samples,"taxa":taxa,"relative_abundance":{s:{t:float(P[i,j]) for j,t in enumerate(taxa)} for i,s in enumerate(samples)},"alpha_diversity":alpha,"bray_curtis":bray.tolist(),"ordination":{"method":"classical PCoA","coordinates":{s:coords[i].tolist() for i,s in enumerate(samples)},"eigenvalues":vals[order[:2]].tolist()},"functional_potential":funcs,"disease_correlations":flags,"model_status":"descriptive hermetic 16S statistics; associations are not diagnoses"}

def differential_abundance(table: dict[str,dict[str,int]], metadata: dict[str,dict], group_key: str) -> dict:
    """Estimate group log2 fold changes with permutation p-values."""
    table=validate_count_table(table); samples=sorted(table); groups=[metadata.get(s,{}).get(group_key) for s in samples]
    if any(g is None for g in groups) or len(set(groups))!=2: raise ValueError("metadata must define exactly two groups for every sample")
    labels=sorted(set(groups)); taxa=sorted({t for x in table.values() for t in x}); X=np.array([[table[s].get(t,0) for t in taxa] for s in samples],float); P=(X+.5)/(X.sum(1,keepdims=True)+.5*len(taxa)); rng=np.random.default_rng(7); rows=[]
    # Explicit convention: alphabetical first group is comparison/numerator,
    # second group is reference/denominator. Thus disease-vs-healthy is positive
    # for a disease-enriched taxon in the standard labels used by this module.
    comparison,reference=labels[0],labels[1]; mask=np.array(groups)==comparison
    for j,t in enumerate(taxa):
        effect=float(np.log2(P[mask,j].mean()/P[~mask,j].mean())); null=[]
        for _ in range(500):
            pm=rng.permutation(mask); null.append(np.log2(P[pm,j].mean()/P[~pm,j].mean()))
        pv=(1+sum(abs(x)>=abs(effect) for x in null))/501; rows.append({"taxon":t,"group_reference":reference,"group_comparison":comparison,"log2_fold_change":effect,"permutation_p":pv})
    rows.sort(key=lambda x:(x["permutation_p"],-abs(x["log2_fold_change"])))
    return {"results":rows,"permutations":500,"group_key":group_key}

def enhancement_features(cohort: dict, differential: dict) -> dict:
    A=cohort["alpha_diversity"]; sh=np.array([x["shannon"] for x in A]); si=np.array([x["simpson"] for x in A]); ri=np.array([x["richness"] for x in A]); ev=np.array([x["pielou_evenness"] for x in A]); reads=np.array([x["reads"] for x in A]); b=np.array(cohort["bray_curtis"]); d=differential["results"]; fc=np.array([x["log2_fold_change"] for x in d]); pv=np.array([x["permutation_p"] for x in d]); out={"sample_count":len(A),"taxon_count":len(cohort["taxa"]),"read_total":int(reads.sum()),"read_min":int(reads.min()),"read_max":int(reads.max()),"read_range":int(np.ptp(reads)),"shannon_min":float(sh.min()),"shannon_max":float(sh.max()),"shannon_mean":float(sh.mean()),"shannon_range":float(np.ptp(sh)),"simpson_min":float(si.min()),"simpson_max":float(si.max()),"simpson_mean":float(si.mean()),"simpson_range":float(np.ptp(si)),"richness_min":int(ri.min()),"richness_max":int(ri.max()),"richness_mean":float(ri.mean()),"richness_range":int(np.ptp(ri)),"evenness_min":float(ev.min()),"evenness_max":float(ev.max()),"evenness_mean":float(ev.mean()),"evenness_range":float(np.ptp(ev)),"bray_mean":float(b[np.triu_indices(len(b),1)].mean()),"bray_min":float(b[np.triu_indices(len(b),1)].min()),"bray_max":float(b.max()),"bray_range":float(b.max()-b[np.triu_indices(len(b),1)].min()),"pcoa_axis1_eigenvalue":cohort["ordination"]["eigenvalues"][0],"pcoa_axis2_eigenvalue":cohort["ordination"]["eigenvalues"][1],"function_count":len({f for x in cohort["functional_potential"].values() for f in x}),"disease_flag_total":sum(len(x) for x in cohort["disease_correlations"].values()),"disease_flagged_sample_count":sum(bool(x) for x in cohort["disease_correlations"].values()),"differential_taxa_count":len(d),"log2fc_min":float(fc.min()),"log2fc_max":float(fc.max()),"log2fc_range":float(np.ptp(fc)),"maximum_absolute_log2fc":float(np.max(abs(fc))),"positive_log2fc_count":int(np.sum(fc>0)),"negative_log2fc_count":int(np.sum(fc<0)),"minimum_permutation_p":float(pv.min()),"p_below_0_05_count":int(np.sum(pv<.05)),"p_below_0_1_count":int(np.sum(pv<.1)),"top_taxon_absolute_log2fc":abs(d[0]["log2_fold_change"]),"top_taxon_p":d[0]["permutation_p"],"relative_abundance_nonzero_count":sum(v>0 for x in cohort["relative_abundance"].values() for v in x.values()),"relative_abundance_zero_count":sum(v==0 for x in cohort["relative_abundance"].values() for v in x.values()),"samples_per_taxon_mean":sum(sum(v>0 for v in x.values()) for x in cohort["relative_abundance"].values())/len(cohort["taxa"]),"reads_per_taxon_mean":reads.sum()/len(cohort["taxa"]),"ordination_coordinate_span_axis1":float(np.ptp([x[0] for x in cohort["ordination"]["coordinates"].values()])),"ordination_coordinate_span_axis2":float(np.ptp([x[1] for x in cohort["ordination"]["coordinates"].values()])),"diversity_decision_margin":float(sh.mean()-1.5)}
    assert len(out)==50; return out

def analyze_16s_cohort(table,metadata,group_key):
    cohort=cohort_analysis(table,metadata); diff=differential_abundance(table,metadata,group_key); diag=enhancement_features(cohort,diff)
    return {"cohort":cohort,"differential":diff,"diagnostics":diag,"diagnostic_count":50,"actions":["review read-depth and negative controls","confirm differential taxa by qPCR","validate functions with shotgun metagenomics","treat disease links as hypotheses"]}
