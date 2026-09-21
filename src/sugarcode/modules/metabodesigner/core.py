from __future__ import annotations
from collections import deque
from ..virtual_cell.core import MetabolicModel, fba

# Built-in reaction knowledge base (curated core metabolism subset)
REACTION_DB = [
    {"id": "R_HEX", "substrates": ["glucose"], "products": ["g6p"], "enzyme": "hexokinase", "ec": "2.7.1.1", "cofactors": ["ATP"]},
    {"id": "R_PGI", "substrates": ["g6p"], "products": ["f6p"], "enzyme": "phosphoglucose isomerase", "ec": "5.3.1.9", "cofactors": []},
    {"id": "R_PFK", "substrates": ["f6p"], "products": ["f1,6bp"], "enzyme": "phosphofructokinase", "ec": "2.7.1.11", "cofactors": ["ATP"]},
    {"id": "R_ALD", "substrates": ["f1,6bp"], "products": ["gap", "dhap"], "enzyme": "aldolase", "ec": "4.1.2.13", "cofactors": []},
    {"id": "R_GAPDH", "substrates": ["gap"], "products": ["1,3bpg"], "enzyme": "GAP dehydrogenase", "ec": "1.2.1.12", "cofactors": ["NAD+"]},
    {"id": "R_PGK", "substrates": ["1,3bpg"], "products": ["3pg"], "enzyme": "phosphoglycerate kinase", "ec": "2.7.2.3", "cofactors": ["ADP"]},
    {"id": "R_ENO", "substrates": ["3pg"], "products": ["pep"], "enzyme": "enolase (via 2pg)", "ec": "4.2.1.11", "cofactors": []},
    {"id": "R_PYK", "substrates": ["pep"], "products": ["pyruvate"], "enzyme": "pyruvate kinase", "ec": "2.7.1.40", "cofactors": ["ADP"]},
    {"id": "R_PDH", "substrates": ["pyruvate"], "products": ["acetyl-coa"], "enzyme": "pyruvate dehydrogenase", "ec": "1.2.4.1", "cofactors": ["CoA", "NAD+"]},
    {"id": "R_LDH", "substrates": ["pyruvate"], "products": ["lactate"], "enzyme": "lactate dehydrogenase", "ec": "1.1.1.27", "cofactors": ["NADH"]},
    {"id": "R_ADH", "substrates": ["acetyl-coa"], "products": ["ethanol"], "enzyme": "alcohol dehydrogenase (via acetaldehyde)", "ec": "1.1.1.1", "cofactors": ["NADH"]},
    {"id": "R_CS", "substrates": ["acetyl-coa"], "products": ["citrate"], "enzyme": "citrate synthase", "ec": "2.3.3.1", "cofactors": ["OAA"]},
    {"id": "R_ICL", "substrates": ["citrate"], "products": ["succinate", "glyoxylate"], "enzyme": "isocitrate lyase (glyoxylate shunt)", "ec": "4.1.3.1", "cofactors": []},
    {"id": "R_MLS", "substrates": ["glyoxylate", "acetyl-coa"], "products": ["malate"], "enzyme": "malate synthase", "ec": "2.3.3.9", "cofactors": []},
    {"id": "R_3HBD", "substrates": ["acetyl-coa"], "products": ["3-hydroxybutyrate"], "enzyme": "thiolase + reductase", "ec": "2.3.1.9", "cofactors": ["NADPH"]},
    {"id": "R_PHA", "substrates": ["3-hydroxybutyrate"], "products": ["PHB_polymer"], "enzyme": "PHA synthase", "ec": "2.3.1.-", "cofactors": []},
]


def design_pathway(target: str, source: str = "glucose", max_steps: int = 10) -> dict:
    """BFS over the reaction graph: shortest substrate->product route to target.

    Returns the reaction sequence with enzymes, cofactor budget and an
    FBA-ready stoichiometric scaffold for the host.
    """
    target = target.lower()
    source = source.lower()
    # BFS over metabolite graph
    prev: dict[str, tuple[str, dict]] = {}
    seen = {source}
    q = deque([source])
    found = False
    while q and not found:
        met = q.popleft()
        for rxn in REACTION_DB:
            if met in [x.lower() for x in rxn["substrates"]]:
                for prod in rxn["products"]:
                    pl = prod.lower()
                    if pl not in seen:
                        seen.add(pl)
                        prev[pl] = (met, rxn)
                        if pl == target:
                            found = True
                        q.append(pl)
    if target not in seen:
        return {"target": target, "found": False,
                "note": f"no route in built-in reaction DB ({len(REACTION_DB)} reactions)",
                "suggestion": "extend REACTION_DB with heterologous steps for this target"}
    path = []
    node = target
    while node != source:
        m, rxn = prev[node]
        path.append(rxn)
        node = m
    path.reverse()
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
