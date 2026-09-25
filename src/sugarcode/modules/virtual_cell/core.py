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


def central_carbon_model() -> MetabolicModel:
    """Central-carbon model with alternative routes, so knockouts can reroute.

    GLYCOLYSIS: GLC -> 2 PYR + 2 NADH + 2 ATP;  TCA: PYR -> 4 NADH + ATP;
    OXPHOS: NADH + 0.5 O2 -> 2.5 ATP;  FERM: PYR + NADH -> LAC (lactate);
    BIOMASS: PYR + NADH + 10 ATP.  Uptake caps: glucose 10, O2 15.
    With O2 limiting, the optimum overflows to lactate; without respiration the
    cell reroutes all NADH through fermentation (anaerobic growth ~20% of WT).
    ``demo_model()`` is kept unchanged for backward compatibility.
    """
    mets = ["GLC", "PYR", "NADH", "ATP", "LAC", "O2"]
    rxns = ["GLC_UP", "O2_UP", "GLYCOLYSIS", "TCA", "OXPHOS", "FERM", "LAC_OUT", "BIOMASS"]
    S = np.array([
        # GLC_UP O2_UP GLYC TCA OXPHOS FERM LAC_OUT BIOMASS
        [1,      0,    -1,   0,   0,     0,   0,      0],    # GLC
        [0,      0,     2,  -1,   0,    -1,   0,     -1],    # PYR
        [0,      0,     2,   4,  -1,    -1,   0,     -1],    # NADH
        [0,      0,     2,   1,   2.5,   0,   0,    -10],    # ATP
        [0,      0,     0,   0,   0,     1,  -1,      0],    # LAC
        [0,      1,     0,   0,  -0.5,   0,   0,      0],    # O2
    ], dtype=float)
    lb = np.zeros(len(rxns))
    ub = np.array([10, 15, 1000, 1000, 1000, 1000, 1000, 1000], dtype=float)
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
        return {"status": "infeasible", "objective": 0.0, "objective_reaction": obj_name,
                "fluxes": {r: 0.0 for r in model.reactions}}
    fluxes = {r: round(float(v), 6) for r, v in zip(model.reactions, res.x)}
    return {"status": "optimal", "objective": round(float(-res.fun), 6),
            "objective_reaction": obj_name, "fluxes": fluxes}


def pfba(model: MetabolicModel, objective: str | None = None,
         bounds_override: dict[str, tuple[float, float]] | None = None,
         optimum_fraction: float = 1.0) -> dict:
    """Parsimonious FBA: fix the objective at its optimum, then minimise total flux.

    FBA optima are often degenerate; pFBA picks the unique minimal-enzyme-cost
    flux distribution, so flux differences between conditions are meaningful.
    """
    if not 0 < optimum_fraction <= 1:
        raise ValueError("optimum_fraction must be in (0, 1]")
    first = fba(model, objective, bounds_override)
    if first["status"] != "optimal":
        return first
    obj_name = objective or model.objective
    lb = model.lb.copy(); ub = model.ub.copy()
    for name, (lo, hi) in (bounds_override or {}).items():
        i = model.rxn_index(name); lb[i], ub[i] = lo, hi
    j = model.rxn_index(obj_name)
    lb[j] = max(lb[j], first["objective"] * optimum_fraction - 1e-9)
    n = len(model.reactions)
    # split v = vp - vn so |v| is linear for reversible reactions
    c = np.ones(2 * n)
    A_eq = np.hstack([model.S, -model.S])
    bounds = [(max(0.0, l), max(0.0, u)) for l, u in zip(lb, ub)] + \
             [(max(0.0, -u), max(0.0, -l)) for l, u in zip(lb, ub)]
    res = linprog(c, A_eq=A_eq, b_eq=np.zeros(len(model.metabolites)), bounds=bounds, method="highs")
    if not res.success:
        # honest fallback: the caller asked for pFBA and gets plain FBA - say so
        return {**first, "method": "fba", "pfba_stage": "failed: %s" % res.message}
    v = res.x[:n] - res.x[n:]
    fluxes = {r: round(float(x), 6) + 0.0 for r, x in zip(model.reactions, v)}
    return {"status": "optimal", "objective": first["objective"], "objective_reaction": obj_name,
            "fluxes": fluxes, "total_flux": round(float(np.abs(v).sum()), 6), "method": "pFBA"}


def gene_knockout(model: MetabolicModel, reaction: str,
                  objective: str | None = None) -> dict:
    """Simulate a knockout by zeroing its reaction's bounds.

    Rerouting is the parsimonious-flux difference (knockout - wild type) and is
    reported only when the knockout still supports growth; a lethal knockout
    has no steady-state flux to reroute.
    """
    if reaction not in model.reactions:
        raise ValueError(f"unknown reaction {reaction!r}")
    wt = pfba(model, objective)
    ko = pfba(model, objective, {reaction: (0.0, 0.0)})
    ko_obj = max(0.0, ko["objective"]) + 0.0
    ratio = ko_obj / wt["objective"] if wt["objective"] > 0 else 0.0
    lethality = "lethal" if ratio < 0.01 else "impaired" if ratio < 0.7 else "viable"
    rerouting = {}
    if lethality != "lethal":
        rerouting = {r: round(ko["fluxes"][r] - wt["fluxes"][r], 4) + 0.0
                     for r in model.reactions
                     if r != reaction and abs(ko["fluxes"][r] - wt["fluxes"][r]) > 1e-6}
    return {
        "knocked_out": reaction,
        "wild_type_objective": wt["objective"],
        "knockout_objective": round(ko_obj, 6),
        "growth_ratio": round(ratio, 4) + 0.0,
        "lethality": lethality,
        "rerouting": rerouting,
        "knockout_fluxes": ko["fluxes"] if lethality != "lethal" else None,
        "rerouting_basis": "pFBA flux difference, knockout minus wild type, excluding the knocked-out reaction",
    }


def simulate_growth(model: MetabolicModel, hours: float = 8.0,
                    dt: float = 0.25, glucose0: float = 10.0,
                    mu_per_flux: float = 0.1) -> dict:
    """Dynamic FBA: stepwise biomass accumulation with substrate depletion.

    The FBA objective is in model flux units; ``mu_per_flux`` converts it to a
    specific growth rate in 1/h (default 0.1, i.e. the demo optimum of 15 flux
    units = 1.5 /h). ``mu_per_h`` in each row is that physical growth rate.
    """
    if hours <= 0 or dt <= 0 or mu_per_flux <= 0:
        raise ValueError("hours, dt and mu_per_flux must be positive")
    if glucose0 <= 0:
        raise ValueError("glucose0 must be positive")
    biomass = 0.01  # gDW/L seed
    glucose = glucose0
    t, series = 0.0, []
    while t <= hours and glucose > 0:
        sol = fba(model, bounds_override={"GLC_UP": (0, min(10, glucose / max(biomass, 1e-9) / dt))})
        flux_obj = sol["objective"]
        mu_h = flux_obj * mu_per_flux
        uptake = sol["fluxes"].get("GLC_UP", 0.0)
        biomass += biomass * mu_h * dt
        glucose = max(0.0, glucose - uptake * biomass * 0.01 * dt)
        series.append({"t": round(t, 2), "biomass": round(biomass, 5),
                       "glucose": round(glucose, 4), "mu": round(flux_obj, 4),
                       "mu_per_h": round(mu_h, 4),
                       "doubling_time_h": round(float(np.log(2) / mu_h), 4) if mu_h > 0 else None})
        t += dt
    return {"model_objective": model.objective, "trajectory": series,
            "final_biomass": series[-1]["biomass"], "glucose_exhausted": glucose <= 0,
            "units": {"mu": "objective flux units", "mu_per_h": "1/h", "biomass": "gDW/L"},
            "mu_per_flux": mu_per_flux}


def regulatory_state(genes, interactions, initial=None, steps=12, threshold=0.5):
    """Deterministic synchronous Boolean GRN simulation."""
    if not genes or len(set(genes)) != len(genes):
        raise ValueError("genes must be a non-empty unique list")
    if steps < 1:
        raise ValueError("steps must be at least 1")
    unknown = {x for e in interactions for x in e[:2]} - set(genes)
    if unknown:
        raise ValueError(f"interaction references unknown genes: {sorted(unknown)}")
    unknown_initial = set(initial or {}) - set(genes)
    if unknown_initial:
        raise ValueError(f"initial references unknown genes: {sorted(unknown_initial)}")
    bad_initial = {g: v for g, v in (initial or {}).items() if not 0 <= float(v) <= 1}
    if bad_initial:
        raise ValueError(f"initial Boolean states must be within [0, 1]: {bad_initial}")
    state = {g: float((initial or {}).get(g, 0.0)) for g in genes}
    trajectory = [{g: round(v, 6) for g, v in state.items()}]
    for _ in range(steps):
        nxt = {}
        for target in genes:
            incoming = [(source, float(weight)) for source, dest, weight in interactions if dest == target]
            signal = sum(state[source] * weight for source, weight in incoming)
            nxt[target] = 1.0 if signal >= threshold else 0.0
        state = nxt
        trajectory.append({g: round(v, 6) for g, v in state.items()})
        if len(trajectory) >= 2 and trajectory[-1] == trajectory[-2]:
            break
    return {"genes": list(genes), "trajectory": trajectory, "steady_state": trajectory[-1],
            "converged": len(trajectory) < steps + 1, "model_status": "computational prediction; requires experimental validation"}


def environment_response(model, conditions=None):
    """Run FBA across named environmental bounds and report growth phenotypes."""
    conditions = conditions or {"standard": {}, "glucose_limited": {"GLC_UP": (0, 2)}}
    if not conditions:
        raise ValueError("conditions must be a non-empty mapping")
    results = {}
    baseline = fba(model)["objective"]
    for name, bounds in conditions.items():
        sol = fba(model, bounds_override=bounds)
        ratio = sol["objective"] / baseline if baseline else 0.0
        phenotype = ("infeasible - contradictory bounds, no steady-state solution" if sol["status"] != "optimal"
                     else "no growth" if ratio < .01 else "slow growth" if ratio < .7 else "robust growth")
        results[name] = {"growth": sol["objective"], "growth_ratio": round(ratio, 6),
                         "status": sol["status"], "phenotype": phenotype,
                         "fluxes": sol["fluxes"]}
    return {"baseline_growth": baseline, "conditions": results,
            "model_status": "computational prediction; requires experimental validation"}


def couple_grn_metabolism(model, genes, interactions, reaction_rules, initial=None, steps=12):
    """Couple steady GRN states to metabolic reaction availability."""
    grn = regulatory_state(genes, interactions, initial, steps)
    bounds = {}
    for reaction, gene in reaction_rules.items():
        if reaction not in model.reactions:
            raise ValueError(f"unknown reaction {reaction!r}")
        if gene not in grn["steady_state"]:
            raise ValueError(f"unknown regulatory gene {gene!r}")
        if grn["steady_state"][gene] < .5:
            bounds[reaction] = (0.0, 0.0)
    solution = fba(model, bounds_override=bounds)
    return {"regulatory": grn, "disabled_reactions": sorted(bounds), "metabolic": solution,
            "predicted_growth": solution["objective"], "model_status": "computational prediction; requires experimental validation"}


def perturbation_screen(model, perturbations=None):
    """Rank reaction knockouts by predicted growth impact."""
    names = list(perturbations or model.reactions)
    unknown = set(names) - set(model.reactions)
    if unknown:
        raise ValueError(f"unknown reactions: {sorted(unknown)}")
    rows = [gene_knockout(model, name) for name in names]
    rows.sort(key=lambda x: (x["growth_ratio"], x["knocked_out"]))
    return {"wild_type_growth": fba(model)["objective"], "perturbations": rows,
            "essential_reactions": [x["knocked_out"] for x in rows if x["lethality"] == "lethal"],
            "model_status": "computational prediction; requires experimental validation"}


# ---------------------------------------------------------------------------
# Gene-expression layer: Hill-function transcription -> mRNA -> protein
# ---------------------------------------------------------------------------

DEMO_GRN = {
    "genes": ["glucose_sensor", "resp_regulator", "glycolysis_enzyme", "resp_enzyme", "ferm_enzyme"],
    # (regulator, target, sign): +1 activates, -1 represses
    "interactions": [("glucose_sensor", "glycolysis_enzyme", 1), ("glucose_sensor", "resp_regulator", 1),
                     ("resp_regulator", "resp_enzyme", 1), ("resp_regulator", "ferm_enzyme", -1)],
    "inputs": {"glucose_sensor": 1.0},
    # reaction -> enzyme protein whose level caps that reaction (ub = kcat * protein)
    # for central_carbon_model(): TCA and OXPHOS share the respiratory enzyme pool
    "enzyme_map": {"GLYCOLYSIS": "glycolysis_enzyme", "TCA": "resp_enzyme", "OXPHOS": "resp_enzyme",
                   "FERM": "ferm_enzyme"},
    "kcat": {"GLYCOLYSIS": 0.2, "TCA": 0.15, "OXPHOS": 0.6, "FERM": 0.5},
}

_EXPR_DEFAULTS = {"basal": 0.05, "vmax": 1.0, "K": 50.0, "n": 2.0,
                  "mrna_decay": 0.5, "translation": 5.0, "protein_decay": 0.1}


def _expr_params(genes, params):
    out = {}
    for g in genes:
        gp = dict(_EXPR_DEFAULTS); gp.update((params or {}).get(g, {}))
        for k in ("mrna_decay", "protein_decay", "K", "n"):
            if gp[k] <= 0:
                raise ValueError(f"{k} for {g!r} must be positive")
        if gp["basal"] < 0 or gp["vmax"] < 0 or gp["translation"] < 0:
            raise ValueError(f"rates for {g!r} must be non-negative")
        out[g] = gp
    return out


def _validate_grn(genes, interactions, inputs):
    if not genes or len(set(genes)) != len(genes):
        raise ValueError("genes must be a non-empty unique list")
    unknown = ({x for e in interactions for x in e[:2]} | set(inputs or {})) - set(genes)
    if unknown:
        raise ValueError(f"interaction references unknown genes: {sorted(unknown)}")
    for e in interactions:
        if len(e) != 3 or float(e[2]) == 0:
            raise ValueError("interactions must be (regulator, target, sign) with non-zero sign")


def _transcription_rates(genes, interactions, par, protein, inputs, knockouts, overexpress):
    idx = {g: k for k, g in enumerate(genes)}
    rates = np.zeros(len(genes))
    for g in genes:
        if g in knockouts:
            continue
        if g in inputs:  # externally clamped signal: fraction of max transcription
            rates[idx[g]] = par[g]["vmax"] * float(inputs[g]) * overexpress.get(g, 1.0)
            continue
        f = 1.0
        for src, dst, sign in interactions:
            if dst != g:
                continue
            x = (max(protein[idx[src]], 0.0) / par[g]["K"]) ** par[g]["n"]
            f *= x / (1 + x) if float(sign) > 0 else 1 / (1 + x)
        rates[idx[g]] = (par[g]["basal"] + par[g]["vmax"] * f) * overexpress.get(g, 1.0)
    return rates


def simulate_expression(genes, interactions, *, inputs=None, params=None, hours=48.0,
                        knockouts=(), overexpress=None, method="ode", seed=7, points=97):
    """Simulate mRNA and protein expression for a regulatory network.

    Transcription of each gene = basal + vmax * prod(Hill terms of its regulators'
    protein levels); activators use x^n/(1+x^n), repressors 1/(1+x^n), x = P/K.
    dm/dt = tx - mrna_decay*m;  dp/dt = translation*m - protein_decay*p.
    ``method='ode'`` integrates deterministically (LSODA); ``method='gillespie'``
    runs the exact stochastic simulation algorithm on molecule counts.
    ``knockouts`` silence transcription; ``overexpress`` multiplies it.
    ``inputs`` clamp signal genes (e.g. an environmental sensor) at a fraction of vmax.
    """
    from scipy.integrate import solve_ivp
    inputs = dict(inputs or {}); overexpress = dict(overexpress or {}); knockouts = set(knockouts)
    _validate_grn(genes, interactions, inputs)
    bad = (knockouts | set(overexpress)) - set(genes)
    if bad:
        raise ValueError(f"perturbation references unknown genes: {sorted(bad)}")
    if any(v < 0 for v in overexpress.values()):
        raise ValueError("overexpression factors must be non-negative")
    if hours <= 0:
        raise ValueError("hours must be positive")
    if method not in {"ode", "gillespie"}:
        raise ValueError("method must be 'ode' or 'gillespie'")
    par = _expr_params(genes, params); n = len(genes)
    dm = np.array([par[g]["mrna_decay"] for g in genes]); dp = np.array([par[g]["protein_decay"] for g in genes])
    ktl = np.array([par[g]["translation"] for g in genes])
    times = np.linspace(0, hours, points)
    if method == "ode":
        def rhs(_, y):
            m, p = y[:n], y[n:]
            tx = _transcription_rates(genes, interactions, par, p, inputs, knockouts, overexpress)
            return np.concatenate([tx - dm * m, ktl * m - dp * p])
        sol = solve_ivp(rhs, (0, hours), np.zeros(2 * n), t_eval=times, method="LSODA", rtol=1e-8, atol=1e-10)
        if not sol.success:
            raise RuntimeError(sol.message)
        M, P = sol.y[:n], sol.y[n:]
        events = None
    else:
        rng = np.random.default_rng(seed)
        m = np.zeros(n); p = np.zeros(n); t = 0.0; k = 0
        M = np.zeros((n, points)); P = np.zeros((n, points)); events = 0
        while k < points:
            tx = _transcription_rates(genes, interactions, par, p, inputs, knockouts, overexpress)
            props = np.concatenate([tx, dm * m, ktl * m, dp * p]); total = props.sum()
            dt = rng.exponential(1 / total) if total > 0 else np.inf
            while k < points and times[k] <= t + dt:
                M[:, k] = m; P[:, k] = p; k += 1
            if not np.isfinite(dt):
                break
            t += dt
            r = rng.choice(4 * n, p=props / total); g = r % n; kind = r // n
            if kind == 0: m[g] += 1
            elif kind == 1: m[g] -= 1
            elif kind == 2: p[g] += 1
            else: p[g] -= 1
            events += 1
    tail = max(1, points // 4)
    steady_p = {g: round(float(P[i, -tail:].mean()), 4) for i, g in enumerate(genes)}
    steady_m = {g: round(float(M[i, -tail:].mean()), 4) for i, g in enumerate(genes)}
    noise = {g: round(float(P[i, -tail:].std() / P[i, -tail:].mean()), 4) if P[i, -tail:].mean() > 0 else 0.0
             for i, g in enumerate(genes)} if method == "gillespie" else None
    return {"genes": list(genes), "method": "LSODA ODE" if method == "ode" else "exact Gillespie SSA",
            "time_h": [round(float(x), 4) for x in times],
            "mrna": {g: [round(float(v), 4) for v in M[i]] for i, g in enumerate(genes)},
            "protein": {g: [round(float(v), 4) for v in P[i]] for i, g in enumerate(genes)},
            "steady_state_mrna": steady_m, "steady_state_protein": steady_p,
            "protein_noise_cv": noise, "ssa_events": events, "seed": seed if method == "gillespie" else None,
            "knockouts": sorted(knockouts), "overexpress": overexpress, "inputs": inputs,
            "units": {"time": "h", "mrna": "molecules/cell (a.u.)", "protein": "molecules/cell (a.u.)"},
            "model_status": "mechanistic Hill-function expression model; parameters are user-set, not fitted"}


def expression_to_bounds(model, protein_levels, enzyme_map, kcat):
    """Cap each enzyme-catalysed reaction at kcat * enzyme protein level."""
    bounds = {}
    for rxn, enzyme in enzyme_map.items():
        if rxn not in model.reactions:
            raise ValueError(f"unknown reaction {rxn!r}")
        if enzyme not in protein_levels:
            raise ValueError(f"enzyme {enzyme!r} has no protein level")
        if kcat.get(rxn, 0) <= 0:
            raise ValueError(f"kcat for {rxn!r} must be positive")
        i = model.rxn_index(rxn)
        cap = kcat[rxn] * max(protein_levels[enzyme], 0.0)
        bounds[rxn] = (float(model.lb[i]), float(min(model.ub[i], cap)))
    return bounds


def _phenotype(ratio):
    return "no growth" if ratio < .01 else "slow growth" if ratio < .7 else "robust growth"


def simulate_cell(model=None, grn=None, *, knockouts=(), overexpress=None, environment=None,
                  inputs=None, params=None, hours=48.0, method="ode", seed=7, mu_per_flux=0.1):
    """Multi-scale step: regulatory network -> protein expression -> flux caps -> growth.

    ``environment`` is FBA bounds (e.g. {"GLC_UP": (0, 2)}); ``inputs`` override the
    GRN's clamped signal genes. Returns protein expression, the enzyme-limited
    flux distribution (pFBA), growth in flux units and 1/h, and the phenotype call.
    """
    model = model or central_carbon_model(); grn = grn or DEMO_GRN
    sig = dict(grn.get("inputs", {})); sig.update(inputs or {})
    expr = simulate_expression(grn["genes"], grn["interactions"], inputs=sig, params=params, hours=hours,
                               knockouts=knockouts, overexpress=overexpress, method=method, seed=seed)
    bounds = expression_to_bounds(model, expr["steady_state_protein"], grn["enzyme_map"], grn["kcat"])
    for rxn, b in (environment or {}).items():
        if rxn not in model.reactions:
            raise ValueError(f"unknown reaction {rxn!r}")
        lo, hi = bounds.get(rxn, b)
        bounds[rxn] = (max(lo, b[0]), min(hi, b[1]))
    flux = pfba(model, bounds_override=bounds)
    unconstrained = fba(model, bounds_override=environment or {})["objective"]
    reference = fba(model)["objective"]  # unperturbed, standard medium, no enzyme limits
    growth = max(0.0, flux["objective"]) + 0.0
    limiting = [r for r, (lo, hi) in bounds.items() if r in grn["enzyme_map"]
                and flux["status"] == "optimal" and hi - flux["fluxes"][r] < 1e-6 * max(1, hi)]
    return {"expression": {"steady_state_protein": expr["steady_state_protein"],
                           "steady_state_mrna": expr["steady_state_mrna"], "method": expr["method"],
                           "protein_noise_cv": expr["protein_noise_cv"]},
            "enzyme_flux_caps": {r: round(b[1], 4) for r, b in bounds.items()},
            "fluxes": flux["fluxes"], "status": flux["status"],
            "growth_flux": growth, "growth_rate_per_h": round(growth * mu_per_flux, 4),
            "growth_ratio_vs_reference": round(growth / reference, 4) if reference > 0 else 0.0,
            "growth_without_enzyme_limits": unconstrained,
            "enzyme_limited_reactions": sorted(limiting),
            "phenotype": _phenotype(growth / reference if reference > 0 else 0.0),
            "perturbation": {"knockouts": sorted(knockouts), "overexpress": dict(overexpress or {}),
                             "environment": dict(environment or {}), "inputs": sig},
            "model_status": "mechanistic expression + constraint-based flux prediction; requires experimental validation"}


def expression_perturbation_screen(model=None, grn=None, genes=None, *, overexpress_factor=None):
    """Knock out (or overexpress) each gene and report system-wide expression and growth changes."""
    model = model or central_carbon_model(); grn = grn or DEMO_GRN
    targets = list(genes or grn["genes"])
    bad = set(targets) - set(grn["genes"])
    if bad:
        raise ValueError(f"unknown genes: {sorted(bad)}")
    wt = simulate_cell(model, grn)
    rows = []
    for g in targets:
        pert = simulate_cell(model, grn, overexpress={g: overexpress_factor}) if overexpress_factor \
            else simulate_cell(model, grn, knockouts=[g])
        wp, pp = wt["expression"]["steady_state_protein"], pert["expression"]["steady_state_protein"]
        lfc = {h: round(float(np.log2((pp[h] + 1) / (wp[h] + 1))), 4) for h in grn["genes"]}
        ratio = max(0.0, pert["growth_flux"] / wt["growth_flux"]) + 0.0 if wt["growth_flux"] > 0 else 0.0
        rows.append({"gene": g, "perturbation": f"overexpress x{overexpress_factor}" if overexpress_factor else "knockout",
                     "protein_log2fc": lfc,
                     "downstream_changed": sorted(h for h, v in lfc.items() if h != g and abs(v) >= 0.5),
                     "growth_ratio": round(ratio, 4), "phenotype": _phenotype(ratio),
                     # a non-growing cell has no steady-state flux, so there is nothing to reroute
                     "flux_changes": {} if ratio < 0.01 else
                     {r: round(pert["fluxes"][r] - wt["fluxes"][r], 4) + 0.0 for r in model.reactions
                      if abs(pert["fluxes"][r] - wt["fluxes"][r]) > 1e-6}})
    rows.sort(key=lambda r: (r["growth_ratio"], r["gene"]))
    return {"wild_type": {"growth_flux": wt["growth_flux"], "protein": wt["expression"]["steady_state_protein"]},
            "perturbations": rows, "model_status": "computational prediction; requires experimental validation"}


def virtual_cell_report(model=None, genes=None, interactions=None, reaction_rules=None, conditions=None):
    """End-to-end multi-scale cell hypothesis report."""
    model = model or central_carbon_model()
    genes = genes or ["carbon_sensor", "respiration_gene"]
    interactions = interactions or [("carbon_sensor", "carbon_sensor", 1), ("carbon_sensor", "respiration_gene", 1)]
    initial = {genes[0]: 1}
    coupled = couple_grn_metabolism(model, genes, interactions, reaction_rules or {("RESP" if "RESP" in model.reactions else "OXPHOS"): genes[-1]}, initial)
    return {"baseline": fba(model), "regulatory_metabolic_coupling": coupled,
            "environment": environment_response(model, conditions), "growth": simulate_growth(model, hours=2),
            "perturbation_screen": perturbation_screen(model),
            "expression_coupled_cell": simulate_cell(model),
            "expression_knockout_screen": expression_perturbation_screen(model),
            "limitations": ["predictions depend on model bounds, kcat values and network assumptions",
                            "no wet-lab validation was performed"]}
