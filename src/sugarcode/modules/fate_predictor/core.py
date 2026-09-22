from __future__ import annotations
import numpy as _np
_trapz = getattr(_np, "trapezoid", None) or _np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0

# Curated reprogramming knowledge (published protocols)
REPROGRAMMING_MAP = {
    ("fibroblast", "neuron"): {
        "tfs": ["ASCL1", "BRN2", "MYT1L"], "weeks": 3,
        "success_rate": 0.35, "reference": "Vierbuchen 2010"},
    ("fibroblast", "cardiomyocyte"): {
        "tfs": ["GATA4", "MEF2C", "TBX5"], "weeks": 4,
        "success_rate": 0.20, "reference": "Ieda 2010"},
    ("fibroblast", "hepatocyte"): {
        "tfs": ["HNF4A", "FOXA2", "HNF1A"], "weeks": 3,
        "success_rate": 0.25, "reference": "Huang 2011"},
    ("fibroblast", "ipsc"): {
        "tfs": ["OCT4", "SOX2", "KLF4", "MYC"], "weeks": 4,
        "success_rate": 0.01, "reference": "Takahashi-Yamanaka 2006"},
    ("b_cell", "macrophage"): {
        "tfs": ["CEBPA"], "weeks": 1,
        "success_rate": 0.80, "reference": "Xie 2004"},
    ("fibroblast", "endothelial"): {
        "tfs": ["ETV2", "FLI1", "ERG"], "weeks": 2,
        "success_rate": 0.30, "reference": "Morita 2015"},
}


def predict_reprogramming(source: str, target: str, delivery: str = "lentivirus") -> dict:
    """Predict TFs, protocol and success rate for a cell-fate conversion."""
    key = (source.lower(), target.lower())
    if key in REPROGRAMMING_MAP:
        r = REPROGRAMMING_MAP[key]
        known = True
    else:
        r = _infer(key)
        known = False
    delivery_factor = {"lentivirus": 1.0, "mRNA": 0.8, "episomal": 0.6,
                       "small_molecule": 0.5}.get(delivery, 0.7)
    rate = round(r["success_rate"] * delivery_factor, 3)
    return {
        "source": source, "target": target, "curated": known,
        "transcription_factors": r["tfs"],
        "estimated_success_rate": rate,
        "delivery": delivery,
        "protocol": _protocol(source, target, r["tfs"], r["weeks"], delivery),
        "duration_weeks": r["weeks"],
        "reference": r.get("reference", "inferred from lineage TF maps"),
        "validation": ["qPCR of source-marker silencing by week 1",
                       "immunostain for target markers at endpoint",
                       "functional assay (e.g. patch clamp for neurons)"],
    }


def _infer(key: tuple[str, str]) -> dict:
    core = {"neuron": ["ASCL1", "NEUROD1"], "cardiomyocyte": ["GATA4", "TBX5"],
            "hepatocyte": ["HNF4A", "FOXA2"], "beta_cell": ["PDX1", "NKX6.1"],
            "muscle": ["MYOD1"], "ipsc": ["OCT4", "SOX2", "KLF4", "MYC"]}
    tfs = core.get(key[1], ["OCT4", "SOX2"])
    return {"tfs": tfs, "weeks": 4, "success_rate": 0.05}


def _protocol(source: str, target: str, tfs: list[str], weeks: int, delivery: str) -> list[str]:
    return [
        f"culture {source} to 70% confluence",
        f"deliver {', '.join(tfs)} via {delivery} (MOI titrated)",
        "day 2: switch to induction media + small molecules as mapped",
        f"weeks 1-{weeks}: media changes every 2 days, monitor morphology",
        f"week {weeks}: score conversion by marker panel + function",
    ]

import math
CELL_MARKERS={"fibroblast":{"COL1A1":1,"VIM":.8},"neuron":{"MAP2":1,"RBFOX3":.9,"SYN1":.7},"cardiomyocyte":{"TNNT2":1,"MYH6":.8},"hepatocyte":{"ALB":1,"HNF4A":.9},"ipsc":{"POU5F1":1,"NANOG":.9},"endothelial":{"PECAM1":1,"VWF":.8},"macrophage":{"CD68":1,"CSF1R":.8},"b_cell":{"CD79A":1,"MS4A1":.8}}
TF_EFFECTS={"ASCL1":{"MAP2":.8,"RBFOX3":.6},"BRN2":{"SYN1":.7},"MYT1L":{"COL1A1":-.5},"GATA4":{"TNNT2":.6},"MEF2C":{"MYH6":.7},"TBX5":{"TNNT2":.5},"HNF4A":{"ALB":.8},"FOXA2":{"ALB":.5},"HNF1A":{"HNF4A":.6},"OCT4":{"POU5F1":.8},"SOX2":{"NANOG":.5},"KLF4":{"POU5F1":.4},"MYC":{"NANOG":.4},"ETV2":{"PECAM1":.8},"FLI1":{"VWF":.5},"ERG":{"PECAM1":.5},"CEBPA":{"CD68":.8,"MS4A1":-.5}}

def validate_conversion(source: str, target: str, delivery: str) -> dict:
    if source not in CELL_MARKERS: raise ValueError(f"unsupported source {source!r}; choose {sorted(CELL_MARKERS)}")
    if target not in CELL_MARKERS: raise ValueError(f"unsupported target {target!r}; choose {sorted(CELL_MARKERS)}")
    if source==target: raise ValueError("source and target must differ")
    if delivery not in {"lentivirus","mRNA","episomal","small_molecule"}: raise ValueError("delivery must be lentivirus, mRNA, episomal, or small_molecule")
    return {"source":source,"target":target,"delivery":delivery}


def optimize_tf_set(source: str, target: str, *, max_factors: int=4) -> dict:
    """Exactly optimize TF subsets for target activation and source silencing."""
    import itertools
    validate_conversion(source,target,"mRNA")
    candidates=sorted({tf for tf,effects in TF_EFFECTS.items() if set(effects)&(set(CELL_MARKERS[target])|set(CELL_MARKERS[source]))})
    if not candidates: candidates=list(_infer((source,target))["tfs"])
    scored=[]
    for size in range(1,min(max_factors,len(candidates))+1):
        for combo in itertools.combinations(candidates,size):
            target_gain=sum(max(0,TF_EFFECTS.get(tf,{}).get(g,0))*w for tf in combo for g,w in CELL_MARKERS[target].items()); source_loss=sum(max(0,-TF_EFFECTS.get(tf,{}).get(g,0))*w for tf in combo for g,w in CELL_MARKERS[source].items()); burden=.08*size**1.5; score=target_gain+source_loss-burden
            scored.append({"factors":list(combo),"score":score,"target_activation":target_gain,"source_silencing":source_loss,"burden":burden,"factor_count":size})
    scored.sort(key=lambda x:(-x["score"],x["factor_count"],x["factors"]))
    return {"ranking":scored,"selected":scored[0],"evaluated_subsets":len(scored),"solver":"exact_subset_enumeration"}


def simulate_trajectory(source: str, target: str, factors: list[str], *, days: float=28, sample_hours: float=12, delivery: str="mRNA") -> dict:
    """Solve source, transitional, target, and stress cell-state ODEs."""
    import numpy as np
    _trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
    from scipy.integrate import solve_ivp
    validate_conversion(source,target,delivery)
    if not factors or any(x not in TF_EFFECTS for x in factors): raise ValueError("factors must be a non-empty supported TF list")
    if days<=0 or sample_hours<=0: raise ValueError("days and sample_hours must be positive")
    strength={"lentivirus":1.,"mRNA":.8,"episomal":.6,"small_molecule":.5}[delivery]; selected=set(factors); activation=sum(max(0,v) for tf in selected for g,v in TF_EFFECTS[tf].items() if g in CELL_MARKERS[target]); burden=.03*len(factors)**1.5
    def rhs(_,y):
        src,transition,target_state,stress=y; conversion=.02*strength*activation*max(src,0); maturation=.035*max(transition,0)*math.exp(-max(stress,0)); recovery=.02*max(stress,0)
        return [-conversion,conversion-maturation-.01*max(stress,0)*max(transition,0),maturation-.005*max(target_state,0),burden*max(src+transition,0)-recovery]
    times=np.arange(0,days*24+1e-9,sample_hours); times=np.unique(np.append(times,days*24)); sol=solve_ivp(rhs,(0,days*24),[1,0,0,0],t_eval=times,method="BDF",rtol=1e-8,atol=1e-9)
    if not sol.success: raise RuntimeError(sol.message)
    rows=[{"hour":float(t),"source_fraction":max(0,float(s)),"transition_fraction":max(0,float(tr)),"target_fraction":max(0,float(ta)),"stress":max(0,float(st))} for t,s,tr,ta,st in zip(sol.t,*sol.y)]
    return {"source":source,"target":target,"factors":factors,"delivery":delivery,"trajectory":rows,"terminal_target_fraction":rows[-1]["target_fraction"],"solver":{"method":"BDF","nfev":sol.nfev,"success":sol.success},"model_status":"mechanistic hermetic state-transition ODE; no regenerative or clinical success claim"}


def enhancement_features(optimization: dict, simulation: dict) -> dict:
    import numpy as np
    rank=optimization["ranking"]; scores=np.array([x["score"] for x in rank]); act=np.array([x["target_activation"] for x in rank]); sil=np.array([x["source_silencing"] for x in rank]); burden=np.array([x["burden"] for x in rank]); r=simulation["trajectory"]; t=np.array([x["hour"] for x in r]); S=np.array([x["source_fraction"] for x in r]); T=np.array([x["transition_fraction"] for x in r]); F=np.array([x["target_fraction"] for x in r]); X=np.array([x["stress"] for x in r]); sel=optimization["selected"]
    out={"subsets_evaluated":optimization["evaluated_subsets"],"selected_factor_count":sel["factor_count"],"selected_score":sel["score"],"selected_target_activation":sel["target_activation"],"selected_source_silencing":sel["source_silencing"],"selected_burden":sel["burden"],"score_min":float(scores.min()),"score_max":float(scores.max()),"score_range":float(np.ptp(scores)),"score_margin":float(scores[0]-scores[1]) if len(scores)>1 else 0.0,"activation_min":float(act.min()),"activation_max":float(act.max()),"activation_range":float(np.ptp(act)),"silencing_min":float(sil.min()),"silencing_max":float(sil.max()),"silencing_range":float(np.ptp(sil)),"burden_min":float(burden.min()),"burden_max":float(burden.max()),"duration_h":float(t[-1]),"timepoint_count":len(t),"initial_source_fraction":float(S[0]),"terminal_source_fraction":float(S[-1]),"source_fraction_change":float(S[-1]-S[0]),"source_half_loss_hour":float(t[np.argmax(S<=.5)]) if np.any(S<=.5) else float(t[-1]),"source_auc":float(_trapz(S,t)),"initial_transition_fraction":float(T[0]),"terminal_transition_fraction":float(T[-1]),"peak_transition_fraction":float(T.max()),"peak_transition_hour":float(t[T.argmax()]),"transition_auc":float(_trapz(T,t)),"initial_target_fraction":float(F[0]),"terminal_target_fraction":float(F[-1]),"target_fraction_change":float(F[-1]-F[0]),"peak_target_fraction":float(F.max()),"peak_target_hour":float(t[F.argmax()]),"target_auc":float(_trapz(F,t)),"target_ten_percent_hour":float(t[np.argmax(F>=.1)]) if np.any(F>=.1) else float(t[-1]),"target_half_max_hour":float(t[np.argmax(F>=F.max()/2)]),"initial_stress":float(X[0]),"terminal_stress":float(X[-1]),"peak_stress":float(X.max()),"peak_stress_hour":float(t[X.argmax()]),"stress_auc":float(_trapz(X,t)),"conversion_efficiency":float(F[-1]/max(1-S[-1],1e-12)),"target_to_stress_ratio":float(F[-1]/max(X[-1],1e-12)),"source_target_crossing_hour":float(t[np.argmax(F>=S)]) if np.any(F>=S) else float(t[-1]),"solver_evaluations":simulation["solver"]["nfev"],"trajectory_mass_terminal":float(S[-1]+T[-1]+F[-1]),"maturation_fraction":float(F[-1]/max(F[-1]+T[-1],1e-12)),"residual_source_burden":float(S[-1]*(1+X[-1]))}
    assert len(out)==50
    return out


def design_reprogramming(source: str, target: str, *, delivery: str="mRNA", days: float=28) -> dict:
    """Return an optimized, simulated, and lab-reviewable reprogramming protocol."""
    validate_conversion(source,target,delivery); opt=optimize_tf_set(source,target); factors=opt["selected"]["factors"]; sim=simulate_trajectory(source,target,factors,days=days,delivery=delivery); diag=enhancement_features(opt,sim)
    return {"optimization":opt,"simulation":sim,"diagnostics":diag,"diagnostic_count":50,"protocol":_protocol(source,target,factors,max(1,round(days/7)),delivery),"validation":["track source-marker silencing","measure target marker panel","run target-specific functional assay","screen genomic integrity and residual vector"]}
