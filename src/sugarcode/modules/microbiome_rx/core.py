from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp

# generalized Lotka-Volterra community with metabolite exchange
SPECIES_TRAITS = {
    "Faecalibacterium": {"growth": 0.3, "consumes": ["acetate"], "produces": ["butyrate"]},
    "Bacteroides": {"growth": 0.4, "consumes": ["fiber"], "produces": ["acetate", "succinate"]},
    "Escherichia": {"growth": 0.6, "consumes": ["sugar", "oxygen"], "produces": ["lactate"]},
    "Lactobacillus": {"growth": 0.5, "consumes": ["sugar"], "produces": ["lactate"]},
    "Akkermansia": {"growth": 0.2, "consumes": ["mucin"], "produces": ["propionate"]},
    "Bifidobacterium": {"growth": 0.4, "consumes": ["fiber", "sugar"], "produces": ["acetate"]},
}
INTERACTIONS = {  # (consumer, producer-metabolite benefit)
    ("Faecalibacterium", "Bacteroides"): 0.3,   # cross-feeding on acetate
    ("Faecalibacterium", "Bifidobacterium"): 0.25,
    ("Escherichia", "Lactobacillus"): -0.1,     # niche competition
    ("Bacteroides", "Escherichia"): -0.2,
}


def simulate_community(initial: dict[str, float], days: float = 14,
                       diet: dict[str, float] | None = None,
                       antibiotic: str | None = None) -> dict:
    """gLV simulation of the community; diet shifts substrates, antibiotics
    impose differential death rates."""
    species = list(initial)
    x0 = np.array([initial[s] for s in species], dtype=float)
    diet = diet or {"fiber": 1.0, "sugar": 1.0}
    abx = {"amoxicillin": {"Bacteroides": 0.5, "Lactobacillus": 0.3, "Escherichia": 0.1},
           "ciprofloxacin": {"Escherichia": 0.7, "Bifidobacterium": 0.4}}.get(antibiotic or "", {})

    def rhs(t, x):
        dx = np.zeros_like(x)
        for i, s in enumerate(species):
            tr = SPECIES_TRAITS[s]
            g = tr["growth"] * np.mean([diet.get(c.rstrip('e') + 'e', diet.get(c, 0.5))
                                        for c in tr["consumes"]] or [0.5])
            interact = sum(INTERACTIONS.get((s, o), 0.0) * x[j]
                           for j, o in enumerate(species))
            death = abx.get(s, 0.0)
            dx[i] = x[i] * (g + interact - 0.1 * x[i].sum() / 5 - death)
        return dx

    ts = np.linspace(0, days, int(days * 4) + 1)
    sol = solve_ivp(rhs, (0, days), x0, t_eval=ts, rtol=1e-6)
    final = {s: round(float(max(sol.y[i][-1], 0)), 4) for i, s in enumerate(species)}
    total = sum(final.values()) or 1.0
    metabolites = _metabolites(species, final, diet)
    return {
        "days": days, "diet": diet, "antibiotic": antibiotic,
        "final_relative": {s: round(v / total, 3) for s, v in final.items()},
        "metabolite_flux": metabolites,
        "dysbiosis_shift": _shift(initial, final),
        "trajectory": {"t_d": [round(float(t), 2) for t in ts[::4]],
                       **{s: [round(float(v), 3) for v in sol.y[i][::4]]
                          for i, s in enumerate(species)}},
    }


def _metabolites(species, final, diet):
    flux = {}
    for s in species:
        for m in SPECIES_TRAITS[s]["produces"]:
            flux[m] = round(flux.get(m, 0) + final[s] * 0.5 * diet.get("fiber", 1.0), 3)
    return flux


def _shift(initial, final):
    i_tot = sum(initial.values()) or 1
    f_tot = sum(final.values()) or 1
    return {s: round(final.get(s, 0) / f_tot - initial.get(s, 0) / i_tot, 3) for s in initial}


def design_intervention(condition: str = "dysbiosis",
                        current_profile: dict[str, float] | None = None) -> dict:
    """Intervention to restore healthy metabolic function."""
    current_profile = current_profile or {"Faecalibacterium": 0.05, "Bacteroides": 0.2,
                                          "Escherichia": 0.4, "Lactobacillus": 0.1}
    baseline = simulate_community(current_profile, days=7)
    options = [
        {"intervention": "high-fiber diet (30g/d)", "diet": {"fiber": 2.0, "sugar": 0.5}},
        {"intervention": "inulin prebiotic", "diet": {"fiber": 1.6, "sugar": 0.8}},
        {"intervention": "low-sugar diet", "diet": {"fiber": 1.0, "sugar": 0.3}},
    ]
    scored = []
    for o in options:
        r = simulate_community(current_profile, days=7, diet=o["diet"])
        butyrate = r["metabolite_flux"].get("butyrate", 0)
        e_coli = r["final_relative"].get("Escherichia", 0)
        score = round(butyrate - 0.5 * e_coli, 3)
        scored.append({**o, "butyrate_flux": butyrate,
                       "escherichia_fraction": e_coli, "benefit_score": score})
    scored.sort(key=lambda x: -x["benefit_score"])
    return {
        "condition": condition,
        "baseline": {"metabolite_flux": baseline["metabolite_flux"],
                     "final_relative": baseline["final_relative"]},
        "interventions_ranked": scored,
        "recommended": scored[0],
        "rationale": "maximize butyrate producers while suppressing pro-inflammatory Enterobacteriaceae",
    }
