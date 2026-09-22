from __future__ import annotations
import math

# Reference vehicle properties (literature-grounded defaults)
VEHICLES = {
    "LNP": {"cargo_kb": 6.0, "tissues": {"liver": 0.9, "spleen": 0.5, "lung": 0.4},
            "half_life_h": 12.0, "immunogenicity": 0.2, "repeat_dose": True},
    "AAV8": {"cargo_kb": 4.7, "tissues": {"liver": 0.85, "muscle": 0.6, "heart": 0.6},
             "half_life_h": 24 * 30.0, "immunogenicity": 0.5, "repeat_dose": False},
    "AAV9": {"cargo_kb": 4.7, "tissues": {"cns": 0.8, "heart": 0.7, "muscle": 0.65},
             "half_life_h": 24 * 30.0, "immunogenicity": 0.5, "repeat_dose": False},
    "AAV2": {"cargo_kb": 4.7, "tissues": {"retina": 0.9, "cns": 0.5},
             "half_life_h": 24 * 30.0, "immunogenicity": 0.4, "repeat_dose": False},
    "VLP-e": {"cargo_kb": 11.0, "tissues": {"liver": 0.6, "t_cell": 0.5, "eye": 0.4},
              "half_life_h": 24.0, "immunogenicity": 0.3, "repeat_dose": True},
    "PNP": {"cargo_kb": 20.0, "tissues": {"skin": 0.6, "tumor": 0.5, "lung": 0.5},
            "half_life_h": 48.0, "immunogenicity": 0.15, "repeat_dose": True},
}
PAYLOADS = {
    "SpCas9+gRNA": 5.5, "SaCas9+gRNA": 4.3, "base_editor+gRNA": 6.5,
    "prime_editor+pegRNA": 8.5, "Cas13+gRNA": 5.0, "gRNA_only": 0.2,
}


def recommend_vehicle(payload: str, tissue: str, repeat_dosing: bool = False) -> dict:
    """Rank delivery vehicles for a payload/tissue pair.

    Score = tropism * cargo_fit * (repeat-dose compatibility) - immunogenicity.
    """
    if payload not in PAYLOADS:
        raise KeyError(f"unknown payload {payload!r}; have {sorted(PAYLOADS)}")
    size = PAYLOADS[payload]
    ranked = []
    for name, v in VEHICLES.items():
        cargo_fit = 1.0 if size <= v["cargo_kb"] else max(0.0, 1 - (size - v["cargo_kb"]) / 5.0)
        tropism = v["tissues"].get(tissue, 0.1)
        dose_ok = 1.0 if (not repeat_dosing or v["repeat_dose"]) else 0.3
        score = (0.45 * tropism + 0.35 * cargo_fit + 0.2 * dose_ok) * (1 - 0.5 * v["immunogenicity"])
        ranked.append({"vehicle": name, "score": round(score, 4), "tropism": tropism,
                       "cargo_fit": round(cargo_fit, 3), "fits_cargo": size <= v["cargo_kb"],
                       "repeat_dose_ok": v["repeat_dose"],
                       "immunogenicity": v["immunogenicity"]})
    ranked.sort(key=lambda r: -r["score"])
    return {"payload": payload, "payload_kb": size, "tissue": tissue,
            "recommendation": ranked[0], "ranked": ranked}


def pk_model(vehicle: str, dose_ug: float = 100.0, hours: float = 96.0,
             dt: float = 1.0) -> dict:
    """One-compartment PK model: first-order elimination from plasma.

    C(t) = (D/Vd) * e^(-ke t); ke = ln2 / t_half. Returns concentration trace,
    Cmax, t_half and AUC (trapezoid).
    """
    if vehicle not in VEHICLES:
        raise KeyError(f"unknown vehicle {vehicle!r}")
    v = VEHICLES[vehicle]
    vd_l = 3.0  # plasma volume approximation (L, human-scaled per kg dose input)
    ke = math.log(2) / v["half_life_h"]
    c0 = dose_ug / vd_l
    ts, conc = [], []
    t = 0.0
    auc = 0.0
    prev = c0
    while t <= hours:
        c = c0 * math.exp(-ke * t)
        auc += (c + prev) / 2 * dt
        prev = c
        ts.append(round(t, 2))
        conc.append(round(c, 5))
        t += dt
    return {
        "vehicle": vehicle, "dose_ug": dose_ug,
        "half_life_h": v["half_life_h"], "elimination_ke": round(ke, 6),
        "cmax_ug_per_l": round(c0, 4),
        "auc_ug_h_per_l": round(auc, 3),
        "time_h": ts, "concentration_ug_per_l": conc,
    }


def delivery_blueprint(payload: str, tissue: str, dose_ug: float = 100.0) -> dict:
    """Full delivery blueprint: vehicle choice + PK trace + composition spec."""
    rec = recommend_vehicle(payload, tissue)
    veh = rec["recommendation"]["vehicle"]
    pk = pk_model(veh, dose_ug)
    return {
        **rec,
        "pk": pk,
        "composition": _composition(veh, payload, dose_ug),
        "dose_response": [
            {"dose_ug": d, "cmax": pk_model(veh, d, hours=4)["cmax_ug_per_l"]}
            for d in (25.0, 50.0, 100.0, 200.0, 400.0)
        ],
    }


def _composition(veh: str, payload: str, dose_ug: float) -> dict:
    if veh == "LNP":
        return {"ionizable_lipid": "SM-102-class, 50 mol%", "helper": "DSPC 10 mol%",
                "cholesterol": "38.5 mol%", "peg_lipid": "1.5 mol%",
                "n_p_ratio": 6.0, "payload": payload, "dose_ug": dose_ug}
    if veh.startswith("AAV"):
        return {"capsid": veh, "genome": f"ssDNA {payload} expression cassette",
                "vp_particles": "1e13 vg/kg typical", "dose_ug": dose_ug}
    return {"particle": veh, "payload": payload, "dose_ug": dose_ug}

# Transparent mechanistic extensions; no trained toxicity or efficacy model.
import numpy as np
from scipy.integrate import solve_ivp

RECEPTOR_TROPISM={"liver":{"ASGPR":.9,"LDLR":.8},"t_cell":{"CD3":.8,"CD7":.7},"cns":{"AAVR":.75},"muscle":{"AAVR":.65},"lung":{"ICAM1":.6}}

def payload_architecture(payload, promoter='tissue_specific', nls_count=2):
    if payload not in PAYLOADS or nls_count<0: raise ValueError('invalid payload architecture')
    size=PAYLOADS[payload]; aav_fit=size<=4.7
    return {"payload":payload,"size_kb":size,"aav_fit":aav_fit,"split_required":not aav_fit,"split_strategy":None if aav_fit else "dual-vector intein/reconstitution concept","promoter":promoter,"nls_count":nls_count,"status":"architecture-level, non-procedural"}

def receptor_uptake(tissue, receptor_expression, vehicle='LNP', kd=0.3):
    if kd<=0: raise ValueError('kd must be positive')
    atlas=RECEPTOR_TROPISM.get(tissue,{})
    scores={cell:{"uptake_probability":max(0,min(1,float(expr)/(float(expr)+kd)*max(atlas.values(),default=.2))),"receptor_expression":float(expr)} for cell,expr in receptor_expression.items()}
    return {"tissue":tissue,"vehicle":vehicle,"cell_subtypes":scores,"atlas_receptors":atlas}

def lnp_biophysics(size_nm=90,zeta_mv=5,pka=6.4,peg_mol_pct=1.5):
    if size_nm<=0 or peg_mol_pct<0: raise ValueError('invalid particle properties')
    size_score=math.exp(-((size_nm-90)/45)**2); ionization=1/(1+10**(7.2-pka)); fusion=size_score*(.4+.6*ionization); escape=fusion*math.exp(-peg_mol_pct/8); clearance=min(1,.15+abs(zeta_mv)/80+peg_mol_pct/12)
    return {"size_nm":size_nm,"zeta_mv":zeta_mv,"pka":pka,"peg_mol_pct":peg_mol_pct,"fusion_probability":fusion,"endosomal_escape_probability":escape,"relative_clearance":clearance}

def compartment_pk(vehicle,dose_ug=100,hours=96,tissue='liver'):
    if vehicle not in VEHICLES or dose_ug<=0: raise ValueError('invalid vehicle/dose')
    trop=VEHICLES[vehicle]['tissues'].get(tissue,.1); ke=math.log(2)/VEHICLES[vehicle]['half_life_h']; kup=.03+.12*trop; kout=.04
    def rhs(t,y): return [-(ke+kup)*y[0]+kout*y[1],kup*y[0]-kout*y[1],ke*y[0]]
    t=np.linspace(0,hours,97); sol=solve_ivp(rhs,(0,hours),[dose_ug/3,0,0],t_eval=t,rtol=1e-8,atol=1e-10)
    return {"time_h":t.tolist(),"plasma_ug_l":sol.y[0].tolist(),"target_ug_l":sol.y[1].tolist(),"cleared_ug_l":sol.y[2].tolist(),"target_auc":float(np.trapz(sol.y[1],t)),"mass_balance_error":float(np.max(abs(sol.y.sum(0)-dose_ug/3)))}

def immune_risk(vehicle,cpg_fraction=0,rna_uridine_fraction=.25,preexisting_antibody=.1):
    if min(cpg_fraction,rna_uridine_fraction,preexisting_antibody)<0: raise ValueError('risk inputs must be nonnegative')
    viral=1 if vehicle.startswith('AAV') else 0; innate=min(1,.5*cpg_fraction+.4*rna_uridine_fraction+.2*VEHICLES[vehicle]['immunogenicity']); adaptive=min(1,viral*(.55*preexisting_antibody+.45*VEHICLES[vehicle]['immunogenicity'])); return {"innate_activation":innate,"adaptive_risk":adaptive,"complement_risk":min(1,.15+VEHICLES[vehicle]['immunogenicity']*.5),"overall":max(innate,adaptive),"status":"relative mechanistic risk, not clinical prediction"}

def expression_kinetics(payload,vehicle,hours=168):
    arch=payload_architecture(payload); hl=24 if vehicle=='LNP' else 240; t=np.linspace(0,hours,85); active=(1-np.exp(-t/8))*np.exp(-math.log(2)*t/hl); off_target_burden=np.trapz(active,t)*(1+.08*arch['nls_count']); return {"time_h":t.tolist(),"relative_activity":active.tolist(),"active_auc":float(np.trapz(active,t)),"off_target_exposure_proxy":float(off_target_burden)}

def optimize_delivery(payload,tissue,receptor_expression=None,repeat_dosing=False):
    base=recommend_vehicle(payload,tissue,repeat_dosing); ranked=[]
    for row in base['ranked']:
        immune=immune_risk(row['vehicle']); uptake=receptor_uptake(tissue,receptor_expression or {'target':.7},row['vehicle']); cell=np.mean([x['uptake_probability'] for x in uptake['cell_subtypes'].values()]); benefit=row['score']*cell; ranked.append({**row,"cell_uptake":cell,"immune_risk":immune['overall'],"benefit_risk":benefit/(.1+immune['overall'])})
    ranked.sort(key=lambda x:-x['benefit_risk']); return {"payload":payload,"tissue":tissue,"ranked":ranked,"recommendation":ranked[0],"payload_architecture":payload_architecture(payload),"validation":["biodistribution qPCR","cell-subtype uptake assay","cytokine and complement panel","editing and off-target time course"],"model_status":"Transparent PK/biophysical scoring; no trained toxicity model and not clinically validated."}

def cargo_diagnostics(payload,tissue,vehicle='LNP'):
    arch=payload_architecture(payload); bio=lnp_biophysics() if vehicle=='LNP' else {"fusion_probability":0,"endosomal_escape_probability":0,"relative_clearance":0}; imm=immune_risk(vehicle); pk=compartment_pk(vehicle,100,24,tissue); trop=VEHICLES[vehicle]['tissues'].get(tissue,.1)
    return {"payload_kb":arch['size_kb'],"cargo_capacity_kb":VEHICLES[vehicle]['cargo_kb'],"cargo_margin_kb":VEHICLES[vehicle]['cargo_kb']-arch['size_kb'],"tropism":trop,"half_life_h":VEHICLES[vehicle]['half_life_h'],"immunogenicity":VEHICLES[vehicle]['immunogenicity'],"innate_risk":imm['innate_activation'],"adaptive_risk":imm['adaptive_risk'],"fusion_probability":bio['fusion_probability'],"escape_probability":bio['endosomal_escape_probability'],"relative_clearance":bio['relative_clearance'],"target_auc":pk['target_auc'],"mass_balance_error":pk['mass_balance_error'],"repeat_dose_compatible":float(VEHICLES[vehicle]['repeat_dose'])}
