from __future__ import annotations
import random

PRODUCTS = {
    "insulin": {"pathway": ["proinsulin expression", "proteolytic maturation", "secretion"],
                "product_type": "protein", "atp_cost": "high", "difficulty": 0.6},
    "artemisinin_precursor": {"pathway": ["MVA pathway", "FPP synthesis", "amorphadiene synthase",
                                          "P450 oxidation"],
                              "product_type": "metabolite", "atp_cost": "very high", "difficulty": 0.85},
    "vanillin": {"pathway": ["tyrosine synthesis", "deamination", "hydroxylation", "methylation"],
                 "product_type": "metabolite", "atp_cost": "medium", "difficulty": 0.4},
    "spider_silk": {"pathway": ["repetitive protein expression", "secretion/spinning"],
                    "product_type": "protein", "atp_cost": "very high", "difficulty": 0.75},
    "butanol": {"pathway": ["acetyl-CoA", "acetoacetyl-CoA", "butyryl-CoA", "butanol"],
                "product_type": "metabolite", "atp_cost": "medium", "difficulty": 0.45},
}
CHASSIS = {
    "E_coli": {"protein": 0.9, "metabolite": 0.8, "atp_budget": 0.7, "ease": 0.95},
    "S_cerevisiae": {"protein": 0.8, "metabolite": 0.9, "atp_budget": 0.8, "ease": 0.85},
    "CHO": {"protein": 0.95, "metabolite": 0.3, "atp_budget": 0.9, "ease": 0.4},
    "B_subtilis": {"protein": 0.75, "metabolite": 0.7, "atp_budget": 0.6, "ease": 0.8},
}


def run_wizard(goal: str, parts_max: int = 8, seed: int = 42) -> dict:
    """Guided multi-step design: pathway, chassis scoring, assembly plan,
    stochastic yield simulation, feasibility with confidence intervals."""
    if goal not in PRODUCTS:
        raise KeyError(f"goal {goal!r} unknown; catalog: {sorted(PRODUCTS)}")
    rng = random.Random(seed)
    spec = PRODUCTS[goal]
    steps = spec["pathway"]
    # chassis scoring
    scored = []
    for c, props in CHASSIS.items():
        fit = (0.4 * props[spec["product_type"]] + 0.25 * props["atp_budget"]
               + 0.2 * props["ease"] - 0.15 * spec["difficulty"])
        scored.append({"chassis": c, "score": round(fit, 3)})
    scored.sort(key=lambda s: -s["score"])
    chassis = scored[0]
    # assembly plan by part count
    n_parts = len(steps) + 2  # promoter + terminator
    assembly = ("Golden Gate" if n_parts <= 10 else "Gibson")
    overhangs = [f"O{i}" for i in range(1, n_parts)] if assembly == "Golden Gate" else None
    # stochastic yield simulation (Gillespie-flavored Monte Carlo)
    base_yield = max(0.05, 0.9 - spec["difficulty"] - 0.05 * (n_parts - 4))
    runs = [max(0.0, base_yield * (1 + rng.gauss(0, 0.25))) for _ in range(200)]
    runs.sort()
    ci = (round(runs[5], 3), round(runs[195], 3))
    mean_yield = round(sum(runs) / len(runs), 3)
    feasibility = round(min(1.0, mean_yield * chassis["score"] / 0.5), 2)
    uncertainties = []
    if spec["atp_cost"] in ("high", "very high"):
        uncertainties.append("ATP/redox burden may cap titer - run Virtual Cell FBA before build")
    if spec["difficulty"] > 0.6:
        uncertainties.append("multi-enzyme balancing unresolved - promoter library recommended")
    return {
        "goal": goal,
        "steps": {
            "1_goal": spec,
            "2_pathway": steps,
            "3_chassis_ranking": scored,
            "4_selected_chassis": chassis,
            "5_assembly": {"method": assembly, "parts": n_parts, "overhangs": overhangs},
            "6_yield_simulation": {"mean_titer_fraction": mean_yield,
                                   "90pct_CI": ci, "n_monte_carlo": 200},
        },
        "feasibility_score": feasibility,
        "verdict": "go" if feasibility > 0.45 else "redesign needed",
        "uncertainties": uncertainties,
        "suggested_experiments": ["promoter strength library on rate-limiting step",
                                  "chassis head-to-head at small scale",
                                  "metabolite assay at 24/48/72 h"],
    }
