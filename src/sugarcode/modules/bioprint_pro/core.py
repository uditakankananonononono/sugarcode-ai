from __future__ import annotations
import math

INKS = {
    "alginate_2pct": {"eta0": 150.0, "eta_inf": 0.5, "lambda_s": 2.0, "n": 0.55,
                      "crosslink": "ionic (CaCl2)", "k_crosslink_s": 0.8, "E0_kPa": 5.0},
    "gelma_10pct": {"eta0": 45.0, "eta_inf": 0.2, "lambda_s": 1.0, "n": 0.65,
                    "crosslink": "photo (UV, LAP)", "k_crosslink_s": 1.5, "E0_kPa": 12.0},
    "collagen_1pct": {"eta0": 8.0, "eta_inf": 0.05, "lambda_s": 0.5, "n": 0.8,
                      "crosslink": "thermal (37C)", "k_crosslink_s": 0.05, "E0_kPa": 1.5},
}


def _viscosity(ink: dict, shear: float) -> float:
    """Cross model: eta = eta_inf + (eta0 - eta_inf) / (1 + (lambda*shear)^n)."""
    return ink["eta_inf"] + (ink["eta0"] - ink["eta_inf"]) / (1 + (ink["lambda_s"] * shear) ** ink["n"])


def calibrate(ink_name: str, nozzle_mm: float = 0.4, target_speed_mm_s: float = 8.0) -> dict:
    """Printability window + crosslinking schedule + structural prediction."""
    if ink_name not in INKS:
        raise KeyError(f"unknown ink; have {sorted(INKS)}")
    ink = INKS[ink_name]
    radius = nozzle_mm / 2
    # pressure requirement from Hagen-Poiseuille with Cross viscosity at wall shear
    window = []
    for speed in (2, 4, 8, 12, 20):
        q = math.pi * radius ** 2 * speed  # mm^3/s
        # SI: Hagen-Poiseuille through an L=10mm needle
        q_m3, r_m, L_m = q * 1e-9, radius * 1e-3, 0.010
        shear = 4 * q_m3 / (math.pi * r_m ** 3)
        eta = _viscosity(ink, shear)
        p_kPa = round(8 * eta * L_m * q_m3 / (math.pi * r_m ** 4) / 1000, 1)
        printable = 5 <= p_kPa <= 250 and 0.05 <= eta <= 100
        window.append({"speed_mm_s": speed, "wall_shear_s-1": round(shear, 1),
                       "viscosity_Pa_s": round(eta, 3), "pressure_kPa": p_kPa,
                       "printable": printable})
    best = min((w for w in window if w["printable"]),
               key=lambda w: abs(w["speed_mm_s"] - target_speed_mm_s), default=None)
    # crosslinking: first-order conversion x(t) = 1 - exp(-kt)
    k = ink["k_crosslink_s"]
    t95 = round(-math.log(0.05) / k, 2) if k > 0 else None
    # modulus grows with conversion: E(t) = E0 * (1 + 9*x)
    x_print = 1 - math.exp(-k * 10)  # 10 s post-deposition
    E_kPa = round(ink["E0_kPa"] * (1 + 9 * x_print), 1)
    fidelity = round(min(1.0, x_print * 1.2) * (1.0 if best else 0.5), 2)
    return {
        "ink": ink_name, "nozzle_mm": nozzle_mm,
        "crosslink_chemistry": ink["crosslink"],
        "printability_window": window,
        "recommended": best,
        "crosslinking": {"rate_s-1": k, "t95_s": t95,
                         "conversion_at_10s": round(x_print, 3)},
        "structural_integrity": {"modulus_kPa_at_10s": E_kPa,
                                 "predicted_shape_fidelity": fidelity,
                                 "layer_adhesion": "good" if x_print < 0.95 else "risk of over-curing"},
        "visualization": {"type": "ink_rheology_curve",
                          "viscosity_vs_shear": [(round(s, 1), round(_viscosity(ink, s), 3))
                                                for s in (0.1, 1, 10, 100, 1000)]},
    }

# --- specification-complete multiphysics biofabrication -----------------------
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import differential_evolution


def carreau_yasuda(shear,eta0=150,eta_inf=.5,lam=2,n=.55,a=2):
    shear=np.asarray(shear,float); return eta_inf+(eta0-eta_inf)*(1+(lam*shear)**a)**((n-1)/a)


def oldroyd_b_extrusion(pressure_kpa,nozzle_mm,length_mm=10,ink="alginate_2pct",cells=500,seed=5):
    """Axisymmetric pressure flow with the Cross/Carreau viscosity solved
    self-consistently with the flow it produces (fixed point of
    q = pi r^4 dp / (8 eta(4q/(pi r^3)) L)). The elastic shear stress is
    Giesekus-family: an Oldroyd-B fluid has constant shear viscosity and
    cannot shear-thin."""
    p=INKS[ink]; r=nozzle_mm*1e-3/2; dp=pressure_kpa*1000; L=length_mm*1e-3
    # BUG 57 fix: the old code evaluated eta once at a guessed shear
    # (dp*r/(2*L*eta0)) - for these shear-thinning inks that overestimated
    # viscosity ~4x and underestimated the flow rate ~4.4x. F(q) = q - flow(q)
    # is monotone increasing (flow grows sublinearly, bounded by the
    # eta_inf Newtonian rate), so bisection converges to the unique root.
    def _flow(qq):
        return math.pi * r ** 4 * dp / (8 * _viscosity(p, 4 * qq / (math.pi * r ** 3)) * L)
    q_lo, q_hi = 1e-15, math.pi * r ** 4 * dp / (8 * p["eta_inf"] * L)
    for _ in range(200):
        q_mid = 0.5 * (q_lo + q_hi)
        if _flow(q_mid) > q_mid:
            q_lo = q_mid
        else:
            q_hi = q_mid
        if q_hi - q_lo < 1e-18 * max(q_hi, 1e-30):
            break
    q = 0.5 * (q_lo + q_hi)
    eta = _viscosity(p, 4 * q / (math.pi * r ** 3))
    velocity=q/(np.pi*r*r); shear=4*velocity/r
    solvent=.2*eta; polymer=max(eta-solvent,0); relaxation=p["lambda_s"]
    stress=solvent*shear+polymer*shear/(1+(relaxation*shear)**2)**.5
    rng=np.random.default_rng(seed); radial=r*np.sqrt(rng.random(cells)); local_shear=4*velocity*radial/r**2
    exposure=length_mm*1e-3/max(velocity,1e-12); viability=np.exp(-.004*local_shear*exposure)
    return {"flow_rate_mm3_s":float(q*1e9),"velocity_mm_s":float(velocity*1e3),"wall_shear_s-1":float(shear),
            "shear_stress_Pa":float(stress),"Weissenberg":float(relaxation*shear),"Reynolds":float(1000*velocity*2*r/max(eta,1e-12)),
            "cell_radial_position_mm":(radial*1e3).tolist(),"cell_viability":viability.tolist(),"mean_viability":float(viability.mean()),
            "viscosity_Pa_s_at_wall":float(eta),
            "constitutive_model":("Giesekus-style elastic shear stress with Carreau-Yasuda viscosity - "
                                  "an Oldroyd-B fluid has constant shear viscosity and cannot shear-thin")}


def crosslink_reaction_diffusion(kind="ionic",seconds=60,size_mm=2,points=41):
    """1D finite-difference diffusion-reaction gelation and stiffness PDE."""
    x=np.linspace(0,size_mm,points); dx=x[1]-x[0]; D={"ionic":.008,"photo":.02,"enzymatic":.004}[kind]; k={"ionic":.8,"photo":1.5,"enzymatic":.08}[kind]
    dt=min(.05,.4*dx*dx/D); c=np.zeros(points); gel=np.zeros(points); history=[]; t=0
    while t<seconds:
        c[[0,-1]]=1; lap=np.zeros_like(c); lap[1:-1]=(c[:-2]-2*c[1:-1]+c[2:])/dx**2
        c=np.clip(c+dt*(D*lap-k*c*(1-gel)),0,1); gel=np.clip(gel+dt*k*c*(1-gel),0,1); t+=dt
        if len(history)<100 and int(t/dt)%max(1,int(seconds/dt/100))==0: history.append(gel.copy().tolist())
    stiffness=2+48*gel**2
    return {"position_mm":x.tolist(),"conversion":gel.tolist(),"stiffness_kPa":stiffness.tolist(),"concentration":c.tolist(),
            "heterogeneity_CV":float(stiffness.std()/stiffness.mean()),"anisotropy":float((stiffness.max()-stiffness.min())/stiffness.mean()),
            "history":history,"chemistry":kind,"diffusion_mm2_s":D,"rate_s-1":k}


def scaffold_mechanics(crosslink,load_kpa=10,seconds=3600,porosity=.35):
    """Nonlinear poro-viscoelastic finite-element chain under physiological load."""
    E=np.asarray(crosslink["stiffness_kPa"])*(1-porosity)**2; n=len(E); strain=load_kpa/np.maximum(E,1e-6); tau=300*(1+E/E.mean()); relaxed=strain*(.35+.65*np.exp(-seconds/tau))
    pressure=load_kpa*np.exp(-np.linspace(0,3,n)/(1+porosity)); shear=np.gradient(pressure)
    buckling=E*np.pi**2/(12*max(n,1)**2)
    return {"element_modulus_kPa":E.tolist(),"instantaneous_strain":strain.tolist(),"relaxed_strain":relaxed.tolist(),
            "pore_pressure_kPa":pressure.tolist(),"interelement_shear":shear.tolist(),"buckling_load_kPa":buckling.tolist(),
            "max_strain":float(relaxed.max()),"safety_factor":float(np.min(buckling)/(load_kpa+1e-12)),"model":"nonlinear poro-viscoelastic FE chain"}


def maturation_pathway(viability,stiffness,days=28):
    """ODE cell growth, matrix deposition, oxygen limitation, and differentiation."""
    def rhs(_,y):
        cells,ecm,oxygen,diff=y; mech=np.exp(-abs(stiffness-15)/20); return [.18*cells*(1-cells/5)*oxygen-.03*cells,.12*cells*mech-.02*ecm,.25*(1-oxygen)-.08*cells*oxygen,.1*mech*cells*(1-diff)-.02*diff]
    t=np.linspace(0,days,113); y=solve_ivp(rhs,(0,days),[max(viability,.01),0,1,0],t_eval=t,rtol=1e-8,atol=1e-10).y
    return {"day":t.tolist(),"cell_density":y[0].tolist(),"ECM":y[1].tolist(),"oxygen":y[2].tolist(),"differentiation":y[3].tolist()}


def _bp_diagnostics(flow,cross,mech,mat,params):
    v=np.array(flow["cell_viability"]); E=np.array(cross["stiffness_kPa"]); strain=np.array(mech["relaxed_strain"]); o=np.array(mat["oxygen"]); cells=np.array(mat["cell_density"]); ecm=np.array(mat["ECM"]); diff=np.array(mat["differentiation"])
    d={"flow_rate":flow["flow_rate_mm3_s"],"extrusion_velocity":flow["velocity_mm_s"],"wall_shear":flow["wall_shear_s-1"],"shear_stress":flow["shear_stress_Pa"],"Weissenberg":flow["Weissenberg"],"Reynolds":flow["Reynolds"],
    "mean_cell_viability":float(v.mean()),"minimum_cell_viability":float(v.min()),"apoptotic_fraction":float((v<.5).mean()),"high_stress_fraction":float((v<.8).mean()),"viability_uniformity":float(1-v.std()),
    "gel_conversion_mean":float(np.mean(cross["conversion"])),"gel_conversion_min":float(np.min(cross["conversion"])),"stiffness_mean":float(E.mean()),"stiffness_min":float(E.min()),"stiffness_max":float(E.max()),"stiffness_gradient":float(np.max(np.abs(np.gradient(E)))),"stiffness_heterogeneity":cross["heterogeneity_CV"],"structural_anisotropy":cross["anisotropy"],
    "max_relaxed_strain":float(strain.max()),"mean_relaxed_strain":float(strain.mean()),"strain_uniformity":float(1-strain.std()),"safety_factor":mech["safety_factor"],"minimum_buckling_load":float(np.min(mech["buckling_load_kPa"])),"peak_pore_pressure":float(np.max(mech["pore_pressure_kPa"])),"peak_interelement_shear":float(np.max(np.abs(mech["interelement_shear"]))),
    "final_cell_density":float(cells[-1]),"cell_expansion_fold":float(cells[-1]/cells[0]),"peak_cell_density":float(cells.max()),"final_ECM":float(ecm[-1]),"ECM_accumulation":float(ecm[-1]-ecm[0]),"final_oxygen":float(o[-1]),"minimum_oxygen":float(o.min()),"hypoxia_fraction":float((o<.2).mean()),"final_differentiation":float(diff[-1]),"peak_differentiation":float(diff.max()),
    "pressure_kPa":params[0],"nozzle_mm":params[1],"crosslink_seconds":params[2],"porosity":params[3],"load_kPa":params[4],"resolution_proxy":float(1/params[1]),"throughput_resolution_product":float(flow["flow_rate_mm3_s"]/params[1]),"shape_fidelity":float(np.exp(-cross["heterogeneity_CV"]-strain.max())),"layer_stability":float(np.exp(-strain.max())*min(1,mech["safety_factor"])),"maturation_stability":float(np.exp(-np.std(cells[-10:]))),
    "oxygen_delivery_efficiency":float(o.mean()),"ECM_per_surviving_cell":float(ecm[-1]/max(cells[-1],1e-12)),"mechanical_resilience":float(mech["safety_factor"]/(1+strain.max())),"cell_mechanical_tradeoff":float(v.mean()/(1+strain.max())),"overall_print_score":float(v.mean()*np.exp(-cross["heterogeneity_CV"]-strain.max())*(1-o.min()+1)/2)}
    assert len(d)>=50; return d


def simulate_bioprint(params=(100,.4,30,.35,10),ink="alginate_2pct",chemistry="ionic"):
    pressure,nozzle,seconds,porosity,load=params; flow=oldroyd_b_extrusion(pressure,nozzle,ink=ink); cross=crosslink_reaction_diffusion(chemistry,seconds); mech=scaffold_mechanics(cross,load,porosity=porosity); mat=maturation_pathway(flow["mean_viability"],np.mean(cross["stiffness_kPa"])); diag=_bp_diagnostics(flow,cross,mech,mat,params)
    return {"extrusion":flow,"crosslinking":cross,"mechanics":mech,"maturation":mat,"diagnostics":diag,"enhancement_feature_count":len(diag),"model_status":"mechanistic multiphysics simulation; no trained model and not clinically validated"}


def optimize_print(ink="alginate_2pct",chemistry="ionic",seed=5):
    """Evolutionary global optimization of pressure, nozzle, cure, porosity, load."""
    def obj(x):
        r=simulate_bioprint(x,ink,chemistry); d=r["diagnostics"]; return -(d["overall_print_score"]-.02*x[0]/250-.1*max(0,.8-d["mean_cell_viability"]))
    res=differential_evolution(obj,[(20,200),(.2,.8),(5,90),(.15,.65),(2,25)],seed=seed,popsize=5,maxiter=5,polish=False)
    sim=simulate_bioprint(res.x,ink,chemistry); return {"parameters":{"pressure_kPa":float(res.x[0]),"nozzle_mm":float(res.x[1]),"crosslink_seconds":float(res.x[2]),"porosity":float(res.x[3]),"load_kPa":float(res.x[4])},"objective":float(-res.fun),"simulation":sim,"solver":"differential evolution"}
