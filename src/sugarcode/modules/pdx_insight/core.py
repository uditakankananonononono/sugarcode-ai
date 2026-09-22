from __future__ import annotations
import numpy as _np
_trapz = getattr(_np, "trapezoid", None) or _np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
import math

DRIFT_RATES = {"mutation_retention": 0.98, "expression_drift": 0.05,
               "stroma_replacement": 0.15, "subclone_selection": 0.08}


def fidelity_assessment(patient_profile: dict, pdx_profile: dict,
                        passage: int = 3) -> dict:
    """Model Fidelity Index: how well the PDX still represents the patient.

    Compares mutation retention, expression correlation and stroma state;
    flags translational drift and proposes CRISPR restoration when needed.
    """
    p_mut = set(patient_profile.get("mutations", []))
    x_mut = set(pdx_profile.get("mutations", []))
    retention = len(p_mut & x_mut) / max(1, len(p_mut)) if p_mut else 1.0
    retention_adj = retention * (DRIFT_RATES["mutation_retention"] ** passage)
    p_expr = patient_profile.get("expression", {})
    x_expr = pdx_profile.get("expression", {})
    corr = _correlation(p_expr, x_expr)
    corr_adj = corr * (1 - DRIFT_RATES["expression_drift"]) ** passage
    stroma = min(1.0, DRIFT_RATES["stroma_replacement"] * passage)
    subclone = min(1.0, DRIFT_RATES["subclone_selection"] * passage)
    mfi = round(0.4 * retention_adj + 0.35 * corr_adj
                + 0.15 * (1 - stroma) + 0.10 * (1 - subclone), 3)
    drift_flags = []
    if retention_adj < 0.8:
        drift_flags.append("key driver mutations lost in PDX")
    if corr_adj < 0.7:
        drift_flags.append("expression program drifting from patient")
    if stroma > 0.4:
        drift_flags.append("human stroma largely replaced by mouse")
    restoration = _restoration(p_mut - x_mut) if p_mut - x_mut else None
    return {
        "passage": passage,
        "model_fidelity_index": mfi,
        "components": {"mutation_retention": round(retention_adj, 3),
                       "expression_correlation": round(corr_adj, 3),
                       "stroma_human_fraction": round(1 - stroma, 3),
                       "subclone_drift": round(subclone, 3)},
        "translational_drift": drift_flags,
        "verdict": ("high fidelity - results translate" if mfi > 0.8 else
                    "moderate - interpret with caution" if mfi > 0.6 else
                    "low fidelity - re-derive model from patient sample"),
        "crispr_restoration": restoration,
    }


def _correlation(a: dict, b: dict) -> float:
    genes = set(a) & set(b)
    if len(genes) < 2:
        return 0.5
    import math
    xa = [a[g] for g in genes]
    xb = [b[g] for g in genes]
    ma, mb = sum(xa) / len(xa), sum(xb) / len(xb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(xa, xb))
    va = math.sqrt(sum((x - ma) ** 2 for x in xa))
    vb = math.sqrt(sum((y - mb) ** 2 for y in xb))
    return cov / (va * vb) if va and vb else 0.5


def _restoration(lost: set) -> dict:
    return {"strategy": "CRISPR knock-in of lost driver mutations into PDX cells",
            "targets": sorted(lost),
            "method": "see CRISPR Opt for guide design",
            "note": "restores patient-relevant genotype before further passaging"}

# --- longitudinal multi-omic fidelity monitoring -----------------------------
def validate_profile(profile: dict, label: str="profile") -> dict:
    """Validate and normalize patient/PDX mutations, expression, CNV and methylation."""
    import math
    if not isinstance(profile,dict): raise ValueError(f"{label} must be a mapping")
    muts=profile.get("mutations",[]); expr=profile.get("expression",{}); cnv=profile.get("copy_number",{}); meth=profile.get("methylation",{})
    if not isinstance(muts,list) or not isinstance(expr,dict) or not isinstance(cnv,dict) or not isinstance(meth,dict): raise ValueError(f"{label} mutations/list and omics/mappings required")
    for name,data in (("expression",expr),("copy_number",cnv),("methylation",meth)):
        if any(not isinstance(v,(int,float)) or not math.isfinite(float(v)) for v in data.values()): raise ValueError(f"{label} {name} values must be finite numbers")
    return {"mutations":sorted(set(map(str,muts))),"expression":{str(k):float(v) for k,v in expr.items()},"copy_number":{str(k):float(v) for k,v in cnv.items()},"methylation":{str(k):float(v) for k,v in meth.items()}}


def multiomic_fidelity(patient_profile: dict, pdx_profile: dict, passage: int=3) -> dict:
    """Calculate a transparent Model Fidelity Index from four omic layers."""
    import numpy as np
    _trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
    if not isinstance(passage,int) or passage<0: raise ValueError("passage must be a non-negative integer")
    p=validate_profile(patient_profile,"patient_profile"); x=validate_profile(pdx_profile,"pdx_profile")
    pm,xm=set(p["mutations"]),set(x["mutations"]); retained=pm&xm; lost=pm-xm; gained=xm-pm
    mutation=len(retained)/max(1,len(pm)) if pm else 1.
    def similarity(kind):
        genes=sorted(set(p[kind])&set(x[kind]))
        if not genes: return {"similarity":0.,"shared_features":0,"rmse":None,"correlation":None}
        a=np.array([p[kind][g] for g in genes]); b=np.array([x[kind][g] for g in genes]); rmse=float(np.sqrt(np.mean((a-b)**2))); scale=float(np.std(a)+np.mean(np.abs(a))+1e-12)
        corr=float(np.corrcoef(a,b)[0,1]) if len(a)>1 and np.std(a)>0 and np.std(b)>0 else 0.
        return {"similarity":float(max(0,min(1,(corr+1)/2*math.exp(-rmse/scale)))),"shared_features":len(genes),"rmse":rmse,"correlation":corr}
    expression=similarity("expression"); cnv=similarity("copy_number"); methylation=similarity("methylation")
    passage_penalty=math.exp(-.018*passage); raw=.35*mutation+.3*expression["similarity"]+.2*cnv["similarity"]+.15*methylation["similarity"]; mfi=raw*passage_penalty
    flags=[]
    if mutation<.8: flags.append("driver mutation retention below 80%")
    if expression["similarity"]<.7: flags.append("expression drift")
    if cnv["similarity"]<.7: flags.append("copy-number drift")
    if methylation["similarity"]<.7: flags.append("methylation drift")
    return {"passage":passage,"model_fidelity_index":round(mfi,8),"raw_multiomic_similarity":round(raw,8),"passage_penalty":round(passage_penalty,8),
      "components":{"mutation_retention":mutation,"expression":expression,"copy_number":cnv,"methylation":methylation},"retained_mutations":sorted(retained),"lost_mutations":sorted(lost),"gained_mutations":sorted(gained),"translational_drift":flags,
      "crispr_restoration":_restoration(lost) if lost else None,"model_status":"mechanistic hermetic multi-omic comparison; no translational or clinical claim"}


def longitudinal_drift(patient_profile: dict, passages: list[dict]) -> dict:
    """Track fidelity through serial passages and estimate threshold crossing."""
    import numpy as np
    if not isinstance(passages,list) or not passages: raise ValueError("passages must be a non-empty list")
    if any("passage" not in x or "profile" not in x for x in passages): raise ValueError("each passage requires passage and profile")
    rows=[multiomic_fidelity(patient_profile,x["profile"],int(x["passage"])) for x in passages]; rows.sort(key=lambda x:x["passage"])
    ps=np.array([x["passage"] for x in rows],float); m=np.array([x["model_fidelity_index"] for x in rows]); slope=float(np.polyfit(ps,m,1)[0]) if len(rows)>1 else 0.
    crossing=None
    if slope<0: crossing=float(ps[-1]+max(0,(m[-1]-.6)/-slope))
    return {"trajectory":rows,"fidelity_slope_per_passage":slope,"projected_mfi_0_6_passage":crossing,"current_drift_flags":rows[-1]["translational_drift"],"recommended_action":"re-derive or restore before further efficacy studies" if m[-1]<.6 else "continue monitoring at each passage"}


def enhancement_features(longitudinal: dict) -> dict:
    """Compute 50 passage- and multi-omic-derived diagnostics."""
    import numpy as np
    r=longitudinal["trajectory"]; p=np.array([x["passage"] for x in r]); m=np.array([x["model_fidelity_index"] for x in r]); raw=np.array([x["raw_multiomic_similarity"] for x in r]); mut=np.array([x["components"]["mutation_retention"] for x in r]); ex=np.array([x["components"]["expression"]["similarity"] for x in r]); cn=np.array([x["components"]["copy_number"]["similarity"] for x in r]); me=np.array([x["components"]["methylation"]["similarity"] for x in r]); lost=np.array([len(x["lost_mutations"]) for x in r]); gained=np.array([len(x["gained_mutations"]) for x in r])
    out={"passage_count":len(r),"first_passage":int(p[0]),"last_passage":int(p[-1]),"passage_span":int(p[-1]-p[0]),"initial_mfi":float(m[0]),"current_mfi":float(m[-1]),"mfi_absolute_change":float(m[-1]-m[0]),"mfi_relative_change":float((m[-1]-m[0])/max(abs(m[0]),1e-12)),"mfi_minimum":float(m.min()),"mfi_maximum":float(m.max()),"mfi_range":float(np.ptp(m)),"mfi_slope":longitudinal["fidelity_slope_per_passage"],"raw_similarity_initial":float(raw[0]),"raw_similarity_current":float(raw[-1]),"raw_similarity_change":float(raw[-1]-raw[0]),"mutation_retention_initial":float(mut[0]),"mutation_retention_current":float(mut[-1]),"mutation_retention_change":float(mut[-1]-mut[0]),"expression_similarity_initial":float(ex[0]),"expression_similarity_current":float(ex[-1]),"expression_similarity_change":float(ex[-1]-ex[0]),"cnv_similarity_initial":float(cn[0]),"cnv_similarity_current":float(cn[-1]),"cnv_similarity_change":float(cn[-1]-cn[0]),"methylation_similarity_initial":float(me[0]),"methylation_similarity_current":float(me[-1]),"methylation_similarity_change":float(me[-1]-me[0]),"lost_mutations_initial":int(lost[0]),"lost_mutations_current":int(lost[-1]),"lost_mutations_change":int(lost[-1]-lost[0]),"gained_mutations_initial":int(gained[0]),"gained_mutations_current":int(gained[-1]),"gained_mutations_change":int(gained[-1]-gained[0]),"current_drift_flag_count":len(r[-1]["translational_drift"]),"passages_below_high_fidelity":int(np.sum(m<.8)),"passages_below_minimum_fidelity":int(np.sum(m<.6)),"monotonic_fidelity_decline":bool(np.all(np.diff(m)<=0)),"largest_single_passage_drop":float(max(0,-np.diff(m).min())) if len(m)>1 else 0.,"mean_mfi":float(m.mean()),"mfi_auc_by_passage":float(_trapz(m,p)) if len(m)>1 else 0.,"projected_threshold_passage":longitudinal["projected_mfi_0_6_passage"],"current_passage_penalty":r[-1]["passage_penalty"],"current_retained_mutation_count":len(r[-1]["retained_mutations"]),"current_lost_mutation_count":len(r[-1]["lost_mutations"]),"current_gained_mutation_count":len(r[-1]["gained_mutations"]),"current_expression_shared_features":r[-1]["components"]["expression"]["shared_features"],"current_cnv_shared_features":r[-1]["components"]["copy_number"]["shared_features"],"current_methylation_shared_features":r[-1]["components"]["methylation"]["shared_features"],"restoration_target_count":len(r[-1]["lost_mutations"]),"fidelity_decision_margin":float(m[-1]-.6)}
    assert len(out)==50
    return out


def monitor_pdx(patient_profile: dict, passages: list[dict]) -> dict:
    """Build a scientist-actionable longitudinal PDX fidelity report."""
    trend=longitudinal_drift(patient_profile,passages); diag=enhancement_features(trend)
    return {"longitudinal":trend,"diagnostics":diag,"diagnostic_count":50,"restoration_plan":trend["trajectory"][-1]["crispr_restoration"],"quality_actions":["verify sample identity by STR","review human/mouse read disambiguation","confirm drifted drivers orthogonally","repeat drug response only within predefined fidelity gate"],"model_status":"mechanistic hermetic fidelity monitoring; no preclinical translation claim"}
