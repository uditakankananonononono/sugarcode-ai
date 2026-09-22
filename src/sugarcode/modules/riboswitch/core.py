from __future__ import annotations
import random

APTAMERS = {
    "theophylline": ("AUACUACCCUGGUGAGGAUUGAGGG", 0.32),  # seq, Kd uM
    "tetracycline": ("GGGAAUUCGGUACCGGUUCAGUAGCUG", 0.77),
    "adenine": ("UAUAAUCGCGUGGAUAUGGCACGCAAGUUUCUACC", 0.30),
    "SAM": ("UCUAUCAAGAGCUGGUGGAGGGACUGGCCCGCGAAACUC", 0.02),
}


def _fold_hairpin(stem5: str, loop: str, stem3: str) -> float:
    """Crude stability: GC-weighted stem pairing minus loop penalty."""
    gc = sum(1 for a, b in zip(stem5, stem3) if
             (a + b) in ("GC", "CG", "AU", "UA", "GU", "UG"))
    return round(gc * 1.8 - 0.5 * len(loop), 2)


def design_riboswitch(ligand: str, mode: str = "on", spacer: str = "AAGGAG",
                      seed: int = 42) -> dict:
    """Design a synthetic riboswitch: known aptamer + tuned expression platform.

    mode 'on': ligand binding exposes RBS (anti-sequester stem breaks).
    mode 'off': ligand binding stabilizes RBS-sequestering stem.
    Returns predicted dynamic range from stem energetics.
    """
    if ligand not in APTAMERS:
        raise KeyError(f"no aptamer for {ligand}; have {sorted(APTAMERS)}")
    if mode not in ("on", "off"):
        raise ValueError("mode must be 'on' or 'off'")
    rng = random.Random(seed)
    aptamer, kd = APTAMERS[ligand]
    apt_3p = aptamer[-6:]  # 3' end of aptamer participates in switching stem
    comp = {"A": "U", "U": "A", "G": "C", "C": "G"}
    antisense = "".join(comp[b] for b in apt_3p)
    if mode == "on":
        # sequester RBS in a stem broken by aptamer-ligand complex
        stem5 = antisense[:4] + spacer[-4:]
        stem3 = apt_3p[:4] + "".join(comp[b] for b in spacer[-4:])
        loop = "AAAU"
    else:
        stem5 = antisense
        stem3 = apt_3p
        loop = "UUUU"
    dG = _fold_hairpin(stem5, loop, stem3)
    kd_factor = max(0.5, 2.0 - kd)
    dyn_range = round((8.0 - 0.5 * dG) * kd_factor, 1) if mode == "on" \
        else round((5.0 + 0.4 * dG) * kd_factor, 1)
    dyn_range = max(1.2, min(50.0, dyn_range))
    seq = aptamer + loop.join(["", ""])[0:0] + stem5 + loop + stem3 + spacer
    return {
        "ligand": ligand, "mode": mode, "aptamer_Kd_uM": kd,
        "sequence": aptamer + stem5 + loop + stem3 + spacer,
        "components": {"aptamer": aptamer, "switching_stem5": stem5,
                       "loop": loop, "switching_stem3": stem3, "rbs_spacer": spacer},
        "stem_stability": dG,
        "predicted_dynamic_range_fold": dyn_range,
        "leakiness": round(1.0 / dyn_range, 3),
        "validation": ["in vitro transcription + ligand titration (Kd check)",
                       "cell-free TX-TL dose-response (dynamic range)",
                       "in vivo reporter curve in E. coli"],
    }

import math

def validate_rna(sequence: str, label: str="sequence") -> str:
    seq=sequence.upper().replace("T","U").replace(" ","")
    if not seq or set(seq)-set("ACGU"): raise ValueError(f"{label} must be a non-empty RNA sequence using A/C/G/U")
    return seq


def nussinov_fold(sequence: str, *, min_loop: int=3) -> dict:
    """Compute an exact maximum-pair RNA secondary structure by dynamic programming."""
    seq=validate_rna(sequence); n=len(seq)
    if n>500: raise ValueError("sequence length must be <= 500")
    if min_loop<0: raise ValueError("min_loop must be non-negative")
    allowed={"AU","UA","GC","CG","GU","UG"}; dp=[[0]*n for _ in range(n)]; trace={}
    for span in range(1,n):
        for i in range(n-span):
            j=i+span; choices=[(dp[i+1][j] if i+1<=j else 0,("skip_i",i+1,j)),(dp[i][j-1] if i<=j-1 else 0,("skip_j",i,j-1))]
            if j-i>min_loop and seq[i]+seq[j] in allowed: choices.append(((dp[i+1][j-1] if i+1<=j-1 else 0)+1,("pair",i+1,j-1)))
            for k in range(i+1,j): choices.append((dp[i][k]+dp[k+1][j],("split",i,k,k+1,j)))
            best=max(choices,key=lambda x:x[0]); dp[i][j]=best[0]; trace[(i,j)]=best[1]
    pairs=[]
    def back(i,j):
        if i>=j:return
        action=trace[(i,j)]
        if action[0]=="skip_i":back(action[1],action[2])
        elif action[0]=="skip_j":back(action[1],action[2])
        elif action[0]=="pair":pairs.append((i,j));back(action[1],action[2])
        else:back(action[1],action[2]);back(action[3],action[4])
    if n>1: back(0,n-1)
    structure=["."]*n
    for i,j in pairs:structure[i]="(";structure[j]=")"
    gc=sum(seq[i]+seq[j] in {"GC","CG"} for i,j in pairs); energy=-3*gc-2*(len(pairs)-gc)
    return {"sequence":seq,"dot_bracket":"".join(structure),"pairs":[list(x) for x in sorted(pairs)],"pair_count":len(pairs),"paired_fraction":2*len(pairs)/n,"gc_pair_count":gc,"estimated_energy_kcal_mol":float(energy),"algorithm":"exact Nussinov dynamic programming"}


def response_curve(kd_uM: float, *, mode: str="on", hill: float=1.5, basal: float=.05, maximum: float=1, concentrations=None) -> dict:
    """Simulate equilibrium Hill response over supplied ligand concentrations."""
    import numpy as np
    if kd_uM<=0 or hill<=0 or not 0<=basal<maximum: raise ValueError("kd_uM and hill must be positive, with 0 <= basal < maximum")
    if mode not in {"on","off"}: raise ValueError("mode must be on or off")
    c=np.asarray(concentrations if concentrations is not None else np.logspace(-3,3,61)*kd_uM,float)
    if c.ndim!=1 or len(c)<2 or np.any(c<0): raise ValueError("concentrations must be a non-negative 1-D sequence with at least 2 values")
    occupancy=c**hill/(kd_uM**hill+c**hill); signal=basal+(maximum-basal)*(occupancy if mode=="on" else 1-occupancy)
    rows=[{"concentration_uM":float(x),"occupancy":float(o),"signal":float(s)} for x,o,s in zip(c,occupancy,signal)]
    return {"mode":mode,"kd_uM":kd_uM,"hill_coefficient":hill,"basal":basal,"maximum":maximum,"curve":rows,"ec50_uM":kd_uM,"dynamic_range":maximum/basal,"model_status":"mechanistic hermetic equilibrium response; no sensor performance claim"}


def optimize_switch(ligand: str, mode: str="on", *, candidates: int=24, seed: int=7) -> dict:
    """Search expression-platform stems for dynamic range and structural switching."""
    import random
    if ligand not in APTAMERS: raise ValueError(f"ligand must be one of {sorted(APTAMERS)}")
    if mode not in {"on","off"} or candidates<2: raise ValueError("mode must be on/off and candidates >= 2")
    rng=random.Random(seed); apt,kd=APTAMERS[ligand]; bases="ACGU"; rows=[]
    for k in range(candidates):
        stem="".join(rng.choice(bases) for _ in range(6)); comp="".join({"A":"U","U":"A","G":"C","C":"G"}[x] for x in reversed(stem)); loop="GAAA"; seq=apt+stem+loop+comp+"AAGGAG"; fold=nussinov_fold(seq); stability=-fold["estimated_energy_kcal_mol"]; accessibility=fold["dot_bracket"][-6:].count(".")/6; dyn=(1+stability/20)*(1+accessibility)*(1/(kd+.1)); leak=1/(1+stability); score=dyn-.5*leak-.02*abs(stability-35)
        rows.append({"sequence":seq,"stem":stem,"complement":comp,"score":score,"predicted_dynamic_range":dyn,"leakiness":leak,"rbs_accessibility":accessibility,"fold":fold})
    rows.sort(key=lambda x:(-x["score"],x["sequence"]))
    return {"ligand":ligand,"mode":mode,"ranking":rows,"selected":rows[0],"evaluated_candidates":len(rows),"search":"seeded sequence search with exact folding objective"}


def enhancement_features(optimization: dict, response: dict) -> dict:
    import numpy as np
    r=optimization["ranking"]; score=np.array([x["score"] for x in r]); dyn=np.array([x["predicted_dynamic_range"] for x in r]); leak=np.array([x["leakiness"] for x in r]); acc=np.array([x["rbs_accessibility"] for x in r]); pairs=np.array([x["fold"]["pair_count"] for x in r]); energy=np.array([x["fold"]["estimated_energy_kcal_mol"] for x in r]); curve=response["curve"]; c=np.array([x["concentration_uM"] for x in curve]); s=np.array([x["signal"] for x in curve]); o=np.array([x["occupancy"] for x in curve]); sel=r[0]
    out={"candidate_count":len(r),"selected_score":sel["score"],"selected_dynamic_range":sel["predicted_dynamic_range"],"selected_leakiness":sel["leakiness"],"selected_rbs_accessibility":sel["rbs_accessibility"],"selected_pair_count":sel["fold"]["pair_count"],"selected_paired_fraction":sel["fold"]["paired_fraction"],"selected_gc_pair_count":sel["fold"]["gc_pair_count"],"selected_energy_kcal_mol":sel["fold"]["estimated_energy_kcal_mol"],"score_min":float(score.min()),"score_max":float(score.max()),"score_range":float(np.ptp(score)),"score_margin":float(score[0]-score[1]),"dynamic_range_min":float(dyn.min()),"dynamic_range_max":float(dyn.max()),"dynamic_range_span":float(np.ptp(dyn)),"leakiness_min":float(leak.min()),"leakiness_max":float(leak.max()),"leakiness_span":float(np.ptp(leak)),"accessibility_min":float(acc.min()),"accessibility_max":float(acc.max()),"accessibility_span":float(np.ptp(acc)),"pair_count_min":int(pairs.min()),"pair_count_max":int(pairs.max()),"pair_count_span":int(np.ptp(pairs)),"energy_min":float(energy.min()),"energy_max":float(energy.max()),"energy_span":float(np.ptp(energy)),"curve_point_count":len(curve),"concentration_min_uM":float(c.min()),"concentration_max_uM":float(c.max()),"concentration_span_uM":float(np.ptp(c)),"signal_min":float(s.min()),"signal_max":float(s.max()),"signal_span":float(np.ptp(s)),"signal_initial":float(s[0]),"signal_terminal":float(s[-1]),"signal_auc_log_concentration":float(np.trapz(s,np.log10(np.maximum(c,1e-30)))),"occupancy_initial":float(o[0]),"occupancy_terminal":float(o[-1]),"occupancy_span":float(np.ptp(o)),"ec50_uM":response["ec50_uM"],"hill_coefficient":response["hill_coefficient"],"response_dynamic_range":response["dynamic_range"],"half_signal_nearest_concentration":float(c[np.argmin(abs(s-(s.min()+s.max())/2))]),"high_signal_point_count":int(np.sum(s>=s.min()+.8*np.ptp(s))),"low_signal_point_count":int(np.sum(s<=s.min()+.2*np.ptp(s))),"sequence_length":len(sel["sequence"]),"stem_gc_fraction":sum(x in "GC" for x in sel["stem"])/len(sel["stem"]),"fold_energy_per_pair":abs(sel["fold"]["estimated_energy_kcal_mol"])/max(sel["fold"]["pair_count"],1)}
    assert len(out)==50
    return out


def design_sensor(ligand: str, mode: str="on", *, candidates: int=24, hill: float=1.5) -> dict:
    """Return an optimized sequence, exact 2-D fold, dose response, and validation plan."""
    opt=optimize_switch(ligand,mode,candidates=candidates); kd=APTAMERS[ligand][1]; resp=response_curve(kd,mode=mode,hill=hill,basal=max(.01,opt["selected"]["leakiness"]/5)); diag=enhancement_features(opt,resp)
    return {"optimization":opt,"sequence":opt["selected"]["sequence"],"structure":opt["selected"]["fold"],"response":resp,"diagnostics":diag,"diagnostic_count":50,"validation":["confirm structure by chemical probing","measure ligand-binding Kd","run cell-free response curve","test selectivity against related metabolites"]}
