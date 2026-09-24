from __future__ import annotations
from ..virtual_cell.core import MetabolicModel, fba

# Built-in reaction knowledge base (curated core metabolism subset)
REACTION_DB = [
    {"id": "R_HEX", "substrates": ["glucose"], "products": ["g6p"], "enzyme": "hexokinase", "ec": "2.7.1.1", "cofactors": ["ATP"]},
    {"id": "R_PGI", "substrates": ["g6p"], "products": ["f6p"], "enzyme": "phosphoglucose isomerase", "ec": "5.3.1.9", "cofactors": []},
    {"id": "R_PFK", "substrates": ["f6p"], "products": ["f1,6bp"], "enzyme": "phosphofructokinase", "ec": "2.7.1.11", "cofactors": ["ATP"]},
    {"id": "R_ALD", "substrates": ["f1,6bp"], "products": ["gap", "dhap"], "enzyme": "aldolase", "ec": "4.1.2.13", "cofactors": []},
    {"id": "R_TPI", "substrates": ["dhap"], "products": ["gap"], "enzyme": "triose-phosphate isomerase", "ec": "5.3.1.1", "cofactors": []},
    {"id": "R_GAPDH", "substrates": ["gap"], "products": ["1,3bpg"], "enzyme": "GAP dehydrogenase", "ec": "1.2.1.12", "cofactors": ["NAD+"]},
    {"id": "R_PGK", "substrates": ["1,3bpg"], "products": ["3pg"], "enzyme": "phosphoglycerate kinase", "ec": "2.7.2.3", "cofactors": ["ADP"]},
    {"id": "R_ENO", "substrates": ["3pg"], "products": ["pep"], "enzyme": "enolase (via 2pg)", "ec": "4.2.1.11", "cofactors": []},
    {"id": "R_PYK", "substrates": ["pep"], "products": ["pyruvate"], "enzyme": "pyruvate kinase", "ec": "2.7.1.40", "cofactors": ["ADP"]},
    {"id": "R_PDH", "substrates": ["pyruvate"], "products": ["acetyl-coa", "co2"], "enzyme": "pyruvate dehydrogenase", "ec": "1.2.4.1", "cofactors": ["CoA", "NAD+"]},
    {"id": "R_LDH", "substrates": ["pyruvate"], "products": ["lactate"], "enzyme": "lactate dehydrogenase", "ec": "1.1.1.27", "cofactors": ["NADH"]},
    {"id": "R_ADH", "substrates": ["acetyl-coa"], "products": ["ethanol"], "enzyme": "alcohol dehydrogenase (via acetaldehyde)", "ec": "1.1.1.1", "cofactors": ["NADH"]},
    {"id": "R_CS", "substrates": ["acetyl-coa"], "products": ["citrate"], "enzyme": "citrate synthase", "ec": "2.3.3.1", "cofactors": ["OAA"]},
    {"id": "R_ICL", "substrates": ["citrate"], "products": ["succinate", "glyoxylate"], "enzyme": "isocitrate lyase (glyoxylate shunt)", "ec": "4.1.3.1", "cofactors": []},
    {"id": "R_MLS", "substrates": ["glyoxylate", "acetyl-coa"], "products": ["malate"], "enzyme": "malate synthase", "ec": "2.3.3.9", "cofactors": []},
    {"id": "R_3HBD", "substrates": ["acetyl-coa", "acetyl-coa"], "products": ["3-hydroxybutyrate"], "enzyme": "thiolase + reductase", "ec": "2.3.1.9", "cofactors": ["NADPH"]},
    {"id": "R_PHA", "substrates": ["3-hydroxybutyrate"], "products": ["PHB_polymer"], "enzyme": "PHA synthase", "ec": "2.3.1.-", "cofactors": []},
]


def design_pathway(target: str, source: str = "glucose", max_steps: int = 10) -> dict:
    """BFS over the reaction graph: shortest substrate->product route to target.

    Returns the reaction sequence with enzymes, cofactor budget and an
    FBA-ready stoichiometric scaffold for the host.
    """
    target = target.lower()
    source = source.lower()
    # Fixpoint reachability in waves: a reaction fires only when ALL its substrates
    # are reachable (single-substrate BFS stranded multi-substrate reactions like
    # malate synthase without their co-substrate branch).
    prev: dict[str, dict] = {}
    fire_round: dict[str, int] = {}
    seen = {source}
    changed = True
    round_ = 0
    while changed and target not in seen:
        changed = False
        new_seen: set[str] = set()
        for rxn in REACTION_DB:
            if all(x.lower() in seen for x in rxn["substrates"]):
                if rxn["id"] not in fire_round:
                    fire_round[rxn["id"]] = round_
                for prod in rxn["products"]:
                    pl = prod.lower()
                    if pl not in seen and pl not in new_seen:
                        new_seen.add(pl)
                        prev[pl] = rxn
                        changed = True
        seen |= new_seen
        round_ += 1
    if target not in seen:
        return {"target": target, "found": False,
                "note": f"no route in built-in reaction DB ({len(REACTION_DB)} reactions)",
                "suggestion": "extend REACTION_DB with heterologous steps for this target"}
    # Back-walk every substrate so branched routes include each co-substrate's supply.
    path: list[dict] = []
    needed = [target]
    while needed:
        node = needed.pop()
        if node == source or node not in prev:
            continue
        rxn = prev[node]
        if any(r["id"] == rxn["id"] for r in path):
            continue
        path.append(rxn)
        needed.extend(x.lower() for x in rxn["substrates"] if x.lower() != source)
    # Closure: add DB reactions that recycle a dead-end byproduct of the route back
    # into a metabolite the route consumes (e.g. triose-phosphate isomerase turning
    # aldolase's DHAP into GAP). Without this the second triose was discarded and
    # every glucose-derived molar yield came out at half the textbook value.
    added = True
    while added:
        added = False
        made = {p.lower() for r in path for p in r["products"]}
        used = {x.lower() for r in path for x in r["substrates"]} | {source}
        dead = made - used - {target}
        for rxn in REACTION_DB:
            if any(r["id"] == rxn["id"] for r in path):
                continue
            subs = {x.lower() for x in rxn["substrates"]}
            prods = {x.lower() for x in rxn["products"]}
            if subs and subs <= dead and prods and prods <= (used | {target}):
                path.append(rxn)
                added = True
    # Topological order: by the wave in which each reaction first became fireable.
    order = {r["id"]: i for i, r in enumerate(REACTION_DB)}
    path.sort(key=lambda r: (fire_round.get(r["id"], len(REACTION_DB)), order[r["id"]]))
    cofactors: dict[str, int] = {}
    for r in path:
        for c in r["cofactors"]:
            cofactors[c] = cofactors.get(c, 0) + 1
    return {
        "target": target, "source": source, "found": True,
        "steps": len(path),
        "route": [{"step": i + 1, "reaction": r["id"], "enzyme": r["enzyme"],
                   "ec": r["ec"], "substrates": r["substrates"],
                   "products": r["products"], "cofactors": r["cofactors"]}
                  for i, r in enumerate(path)],
        "cofactor_budget": cofactors,
        "enzymes_to_clone": sorted({r["enzyme"] for r in path}),
        "feasibility": _feasibility(path, cofactors),
    }


def _feasibility(path: list[dict], cofactors: dict) -> dict:
    atp_cost = cofactors.get("ATP", 0)
    red_need = cofactors.get("NADH", 0) + cofactors.get("NADPH", 0)
    score = 1.0 / (1 + 0.15 * len(path) + 0.1 * atp_cost + 0.05 * red_need)
    return {
        "score": round(score, 3),
        "atp_steps": atp_cost, "redox_steps": red_need,
        "verdict": "tractable in standard chassis" if score > 0.4 else
                   "feasible with cofactor balancing engineering",
        "balancing_suggestions": (["overexpress pathway enzymes at bottleneck steps",
                                   "consider compartmentalization for toxic intermediates"]
                                  if red_need or atp_cost else ["route is redox/ATP light"]),
    }


def bottleneck_analysis(path: list[dict], enzyme_kcat: dict[str, float] | None = None) -> dict:
    """Rank pathway steps by kinetic bottleneck risk.

    Uses kcat priors per enzyme class; low kcat x high cofactor demand = risk.
    """
    defaults = {"kinase": 100.0, "dehydrogenase": 50.0, "isomerase": 200.0,
                "synthase": 20.0, "lyase": 30.0, "transferase": 80.0}
    enzyme_kcat = enzyme_kcat or {}
    scored = []
    for i, r in enumerate(path):
        kcat = None
        for cls, v in defaults.items():
            if cls in r["enzyme"]:
                kcat = enzyme_kcat.get(r["enzyme"], v)
        kcat = kcat or enzyme_kcat.get(r["enzyme"], 40.0)
        demand = 1 + len(r["cofactors"])
        risk = demand / kcat
        scored.append({"step": i + 1, "reaction": r.get("id") or r.get("reaction"), "enzyme": r["enzyme"],
                       "kcat_s": kcat, "risk": round(risk, 4)})
    scored.sort(key=lambda x: -x["risk"])
    return {"ranked_bottlenecks": scored,
            "top_bottleneck": scored[0] if scored else None,
            "mitigation": f"overexpress {scored[0]['enzyme']} or find a faster ortholog"
            if scored else "empty pathway"}

import math
import numpy as np
from scipy.optimize import linprog
from scipy.integrate import solve_ivp

def stoichiometric_matrix(route):
 mets=sorted({m for r in route for m in r['substrates']+r['products']}); S=np.zeros((len(mets),len(route)))
 for j,r in enumerate(route):
  for m in r['substrates']:S[mets.index(m),j]-=1
  for m in r['products']:S[mets.index(m),j]+=1
 return {'metabolites':mets,'reactions':[r.get('reaction',r.get('id')) for r in route],'matrix':S.tolist()}
def pathway_flux(route,target,source,upper=10):
 sm=stoichiometric_matrix(route); S=np.asarray(sm['matrix']); internal=[i for i,m in enumerate(sm['metabolites']) if m not in (source,target) and np.any(S[i]<0)]; c=np.zeros(len(route)); c[-1]=-1; res=linprog(c,A_eq=S[internal] if internal else None,b_eq=np.zeros(len(internal)) if internal else None,bounds=[(0,upper)]*len(route),method='highs'); return {'success':bool(res.success),'fluxes':res.x.tolist() if res.success else [],'objective_flux':float(-res.fun) if res.success else 0,'stoichiometry':sm}
def thermodynamics(route,dg_by_reaction=None):
 dg_by_reaction=dg_by_reaction or {}; vals=[float(dg_by_reaction.get(r.get('reaction',r.get('id')),-5+len(r.get('cofactors',[])))) for r in route]; return {'step_dg':vals,'total_dg':sum(vals),'uphill_steps':[i+1 for i,v in enumerate(vals) if v>0],'feasible':sum(vals)<0}
def carbon_redox(route):
 cof=[c for r in route for c in r.get('cofactors',[])]; return {'atp_demand':cof.count('ATP'),'nadh_demand':cof.count('NADH'),'nadph_demand':cof.count('NADPH'),'carbon_efficiency_proxy':1/(1+.1*len(route))}
def intermediate_risk(route,concentrations=None):
 concentrations=concentrations or {}; out=[]
 for r in route:
  for p in r['products']: out.append({'metabolite':p,'concentration':concentrations.get(p,1),'reactivity_risk':min(1,.1*concentrations.get(p,1)+.2*('aldehyde' in p))})
 return sorted(out,key=lambda x:-x['reactivity_risk'])
def dynamic_pathway(kcats,initial_substrate=10,hours=20):
 k=np.asarray(kcats,float); n=len(k)
 def rhs(t,y):
  rates=k*y[:-1]/(1+y[:-1]); dy=np.zeros(n+1); dy[0]=-rates[0]
  for i in range(1,n):dy[i]=rates[i-1]-rates[i]
  dy[-1]=rates[-1]; return dy
 t=np.linspace(0,hours,201); s=solve_ivp(rhs,(0,hours),[initial_substrate]+[0]*n,t_eval=t,rtol=1e-8,atol=1e-9); return {'time_h':t.tolist(),'concentrations':s.y.tolist(),'product_final':float(s.y[-1,-1])}
def chassis_rank(requirements):
 chassis={'e_coli':{'oxygen':.5,'secretion':.2,'glycosylation':0,'scale':1},'yeast':{'oxygen':.7,'secretion':.7,'glycosylation':1,'scale':.8},'mammalian':{'oxygen':.8,'secretion':1,'glycosylation':1,'scale':.2}}; rows=[]
 for name,p in chassis.items(): rows.append({'chassis':name,'score':sum(1-abs(p[k]-v) for k,v in requirements.items())/len(requirements)})
 return sorted(rows,key=lambda x:-x['score'])
def pathway_report(target,source='glucose'):
 d=design_pathway(target,source); route=d.get('route',[]); return {**d,'flux':pathway_flux(route,target,source) if route else None,'thermodynamics':thermodynamics(route),'balances':carbon_redox(route),'intermediate_risks':intermediate_risk(route),'bottlenecks':bottleneck_analysis(route),'model_status':'Curated reaction graph, LP and explicit kinetics; not live KEGG/MetaCyc and no learned enzyme model.'}
def metabolic_diagnostics(r):
 return {'step_count':float(r['steps']),'feasibility_score':r['feasibility']['score'],'objective_flux':r['flux']['objective_flux'],'total_dg':r['thermodynamics']['total_dg'],'uphill_steps':float(len(r['thermodynamics']['uphill_steps'])),'atp_demand':float(r['balances']['atp_demand']),'nadh_demand':float(r['balances']['nadh_demand']),'nadph_demand':float(r['balances']['nadph_demand']),'carbon_efficiency':r['balances']['carbon_efficiency_proxy'],'intermediate_count':float(len(r['intermediate_risks'])),'max_intermediate_risk':max((x['reactivity_risk'] for x in r['intermediate_risks']),default=0),'bottleneck_risk':r['bottlenecks']['top_bottleneck']['risk'] if r['bottlenecks']['top_bottleneck'] else 0}
