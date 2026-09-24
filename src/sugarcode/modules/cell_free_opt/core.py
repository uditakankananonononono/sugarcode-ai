from __future__ import annotations
import itertools

# response-surface priors (g/L yield at 4h, relative) for E. coli lysate CFPS
REAGENTS = {
    "mg_mm": {"range": (4, 20), "opt": 12, "cost_per_mmol": 0.05},
    "k_mm": {"range": (40, 200), "opt": 120, "cost_per_mmol": 0.02},
    "pep_mm": {"range": (0, 40), "opt": 20, "cost_per_mmol": 0.40},  # energy substrate
    "template_ng_ul": {"range": (2, 30), "opt": 12, "cost_per_ng": 0.001},
    "peg_pct": {"range": (0, 4), "opt": 2, "cost_per_pct": 0.01},
}


def _yield_model(mg, k, pep, tpl, peg) -> float:
    """Gaussian response surface around known optima, normalized to g/L."""
    import math
    def bell(x, opt, w):
        return math.exp(-((x - opt) / w) ** 2)
    y = (2.0 * bell(mg, 12, 5) * bell(k, 120, 50) * bell(pep, 20, 12)
         * bell(tpl, 12, 8) * bell(peg, 2, 1.5))
    return y  # g/L


def optimize_cfps(grid_step: int = 2) -> dict:
    """Grid search over reagent space for max yield under cost ceiling."""
    best = None
    # grids always include each reagent's documented optimum; otherwise some
    # steps (e.g. grid_step=2 for template: 2,6,10,14,...) never evaluate it
    mg_v = sorted(set(range(4, 21, grid_step)) | {REAGENTS["mg_mm"]["opt"]})
    k_v = sorted(set(range(40, 201, 2 * grid_step * 10)) | {REAGENTS["k_mm"]["opt"]})
    pep_v = sorted(set(range(0, 41, 2 * grid_step)) | {REAGENTS["pep_mm"]["opt"]})
    tpl_v = sorted(set(range(2, 31, grid_step * 2)) | {REAGENTS["template_ng_ul"]["opt"]})
    peg_v = sorted(set(range(0, 5, 1)) | {REAGENTS["peg_pct"]["opt"]})
    evaluated = 0
    for mg, k, pep, tpl, peg in itertools.product(mg_v, k_v, pep_v, tpl_v, peg_v):
        y = _yield_model(mg, k, pep, tpl, peg)
        evaluated += 1
        if best is None or y > best["yield_g_l"]:
            best = {"mg_mm": mg, "k_mm": k, "pep_mm": pep,
                    "template_ng_ul": tpl, "peg_pct": peg, "yield_g_l": round(y, 3)}
    best["conditions_evaluated"] = evaluated
    best["cost"] = cost_model(best)
    best["kinetics"] = kinetics(best)
    return best


def kinetics(conditions: dict, hours: float = 6.0, dt: float = 0.25) -> dict:
    """CFPS kinetic trace: rapid synthesis then resource-limited plateau."""
    import math
    vmax = conditions.get("yield_g_l", 1.5) / 2.0  # g/L/h initial
    tau = 2.0  # resource exhaustion timescale (h)
    t, series = 0.0, []
    produced = 0.0
    while t <= hours:
        rate = vmax * math.exp(-t / tau)
        produced += rate * dt
        series.append({"t_h": round(t, 2), "rate_g_l_h": round(rate, 4),
                       "cumulative_g_l": round(produced, 4)})
        t += dt
    return {"trajectory": series, "final_g_l": round(produced, 3),
            "plateau_time_h": round(3 * tau, 1)}


def cost_model(conditions: dict, reaction_ul: float = 15.0, n_reactions: int = 96) -> dict:
    """Reagent cost for a screening plate."""
    per_rxn = 0.0
    parts = {}
    parts["mg"] = conditions["mg_mm"] * REAGENTS["mg_mm"]["cost_per_mmol"] * reaction_ul / 1000
    parts["k"] = conditions["k_mm"] * REAGENTS["k_mm"]["cost_per_mmol"] * reaction_ul / 1000
    parts["pep"] = conditions["pep_mm"] * REAGENTS["pep_mm"]["cost_per_mmol"] * reaction_ul / 1000
    parts["template"] = conditions["template_ng_ul"] * REAGENTS["template_ng_ul"]["cost_per_ng"] * reaction_ul
    parts["lysate"] = 0.35  # per reaction, dominant cost
    per_rxn = sum(parts.values())
    return {"per_reaction_usd": round(per_rxn, 4),
            "plate_usd": round(per_rxn * n_reactions, 2),
            "breakdown": {k: round(v, 4) for k, v in parts.items()},
            "note": "lysate dominates; PEP energy substrate second - consider glucose-based energy"}

def batch_normalize(yields, controls):
    import statistics
    if len(yields)!=len(controls) or not yields: raise ValueError('paired non-empty yields and controls required')
    norm=[float(y)/float(c) for y,c in zip(yields,controls)]
    return {'normalized_yield':norm,'mean':statistics.mean(norm),'cv':statistics.pstdev(norm)/(statistics.mean(norm)+1e-12)}

def resource_sensitivity(conditions, fraction=0.1):
    base=_yield_model(conditions['mg_mm'],conditions['k_mm'],conditions['pep_mm'],conditions['template_ng_ul'],conditions['peg_pct']); out={}
    keys=['mg_mm','k_mm','pep_mm','template_ng_ul','peg_pct']
    for key in keys:
        c=dict(conditions); c[key]*=1+fraction
        y=_yield_model(c['mg_mm'],c['k_mm'],c['pep_mm'],c['template_ng_ul'],c['peg_pct'])
        out[key]=(y-base)/(base*fraction) if base else 0
    return {'baseline_g_l':base,'elasticity':out,'most_sensitive':max(out,key=lambda k:abs(out[k]))}

def pareto_conditions(candidates):
    keep=[]
    for c in candidates:
        dominated=any((o['yield_g_l']>=c['yield_g_l'] and o['cost_usd']<=c['cost_usd'] and (o['yield_g_l']>c['yield_g_l'] or o['cost_usd']<c['cost_usd'])) for o in candidates)
        if not dominated: keep.append(c)
    return sorted(keep,key=lambda x:x['cost_usd'])

def replicate_qc(values, max_cv=.15):
    import statistics
    mean=statistics.mean(values); cv=statistics.pstdev(values)/(mean+1e-12)
    return {'mean':mean,'cv':cv,'passes':cv<=max_cv,'n':len(values)}

def optimization_report(grid_step=2):
    out=optimize_cfps(grid_step); out['validation_scope']='Mechanistic response-surface heuristic; no trained production model and wet-lab validation is required.'; return out
