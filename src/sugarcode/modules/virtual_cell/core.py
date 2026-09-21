from __future__ import annotations
import numpy as np
from scipy.optimize import linprog


class MetabolicModel:
    """Stoichiometric metabolic model (S v = 0, lb <= v <= ub)."""

    def __init__(self, metabolites: list[str], reactions: list[str],
                 S: np.ndarray, lb: np.ndarray, ub: np.ndarray,
                 objective: str = "BIOMASS"):
        self.metabolites = metabolites
        self.reactions = reactions
        self.S = np.asarray(S, dtype=float)
        self.lb = np.asarray(lb, dtype=float)
        self.ub = np.asarray(ub, dtype=float)
        self.objective = objective
        assert self.S.shape == (len(metabolites), len(reactions))

    def rxn_index(self, name: str) -> int:
        return self.reactions.index(name)


def demo_model() -> MetabolicModel:
    """A compact central-carbon model: glucose -> glycolysis -> biomass.

    Metabolites: GLC, PYR, ATP, NADH, BIOMASS_precursors, EXT
    Reactions: uptake, glycolysis, respiration, fermentation, biomass, drain.
    """
    mets = ["GLC_int", "PYR", "ATP", "NADH"]
    rxns = ["GLC_UP", "GLYCOLYSIS", "RESP", "FERM", "BIOMASS", "LAC_OUT"]
    S = np.array([
        # GLC_UP GLYC RESP FERM BIOMASS LAC_OUT
        [1,      -1,   0,   0,    0,      0],   # GLC_int
        [0,       2,  -1,  -1,   -0.5,    0],   # PYR
        [0,       2,  10,   0,   -8,      0],   # ATP
        [0,       2,  -2,   0,    0,      0],   # NADH
    ])
    lb = np.array([0, 0, 0, 0, 0, 0])
    ub = np.array([10, 1000, 1000, 1000, 1000, 1000])
    return MetabolicModel(mets, rxns, S, lb, ub)


def fba(model: MetabolicModel, objective: str | None = None,
        bounds_override: dict[str, tuple[float, float]] | None = None) -> dict:
    """Flux balance analysis maximizing the objective reaction."""
    obj_name = objective or model.objective
    c = np.zeros(len(model.reactions))
    c[model.rxn_index(obj_name)] = -1.0  # maximize -> minimize negative
    lb = model.lb.copy()
    ub = model.ub.copy()
    for name, (lo, hi) in (bounds_override or {}).items():
        i = model.rxn_index(name)
        lb[i], ub[i] = lo, hi
    res = linprog(c, A_eq=model.S, b_eq=np.zeros(len(model.metabolites)),
                  bounds=list(zip(lb, ub)), method="highs")
    if not res.success:
        return {"status": "infeasible", "objective": 0.0,
                "fluxes": {r: 0.0 for r in model.reactions}}
    fluxes = {r: round(float(v), 6) for r, v in zip(model.reactions, res.x)}
    return {"status": "optimal", "objective": round(float(-res.fun), 6),
            "objective_reaction": obj_name, "fluxes": fluxes}


def gene_knockout(model: MetabolicModel, reaction: str,
                  objective: str | None = None) -> dict:
    """Simulate a gene knockout by zeroing its reaction's bounds."""
    wt = fba(model, objective)
    ko = fba(model, objective, {reaction: (0.0, 0.0)})
    ratio = ko["objective"] / wt["objective"] if wt["objective"] > 0 else 0.0
    return {
        "knocked_out": reaction,
        "wild_type_objective": wt["objective"],
        "knockout_objective": ko["objective"],
        "growth_ratio": round(ratio, 4),
        "lethality": "lethal" if ratio < 0.01 else "impaired" if ratio < 0.7 else "viable",
        "rerouting": {r: round(ko["fluxes"][r] - wt["fluxes"][r], 4)
                      for r in model.reactions
                      if abs(ko["fluxes"][r] - wt["fluxes"][r]) > 1e-6},
    }


def simulate_growth(model: MetabolicModel, hours: float = 8.0,
                    dt: float = 0.25, glucose0: float = 10.0) -> dict:
    """Dynamic FBA: stepwise biomass accumulation with substrate depletion."""
    uptake_i = model.rxn_index("GLC_UP") if "GLC_UP" in model.reactions else 0
    biomass = 0.01  # gDW/L seed
    glucose = glucose0
    t, series = 0.0, []
    while t <= hours and glucose > 0:
        sol = fba(model, bounds_override={"GLC_UP": (0, min(10, glucose / max(biomass, 1e-9) / dt))})
        mu = sol["objective"]
        uptake = sol["fluxes"].get("GLC_UP", 0.0)
        biomass += biomass * mu * 0.1 * dt
        glucose = max(0.0, glucose - uptake * biomass * 0.01 * dt)
        series.append({"t": round(t, 2), "biomass": round(biomass, 5),
                       "glucose": round(glucose, 4), "mu": round(mu, 4)})
        t += dt
    return {"model_objective": model.objective, "trajectory": series,
            "final_biomass": series[-1]["biomass"], "glucose_exhausted": glucose <= 0}
