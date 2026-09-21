from __future__ import annotations
import math


def stability_forecast(construct: dict, generations: int = 200) -> dict:
    """Simulate construct loss: plasmid segregational loss + mutational drift.

    construct: {"mode": "plasmid"|"genomic", "burden": 0..1, "size_kb": float,
                "toxic": bool}
    Plasmid loss modeled per generation (loss rate grows with burden);
    mutational inactivation as Poisson process over functional target size.
    """
    mode = construct.get("mode", "plasmid")
    burden = min(max(construct.get("burden", 0.3), 0.0), 1.0)
    size_kb = construct.get("size_kb", 5.0)
    toxic = construct.get("toxic", False)

    loss_rate = (0.002 if mode == "plasmid" else 0.00005) * (1 + 4 * burden)
    mut_rate_per_kb = 1e-4 * (2.0 if toxic else 1.0)
    func_fraction = 1.0
    series = []
    for g in range(0, generations + 1, 10):
        plasmid_retention = (1 - loss_rate) ** g
        mut_survival = math.exp(-mut_rate_per_kb * size_kb * g)
        func = plasmid_retention * mut_survival
        series.append({"generation": g, "functional_fraction": round(func, 4)})
    half_life = next((s["generation"] for s in series if s["functional_fraction"] < 0.5),
                     generations)
    final = series[-1]["functional_fraction"]
    score = round(final * 100, 1)
    return {
        "construct": construct,
        "trajectory": series,
        "functional_half_life_generations": half_life,
        "stability_score": score,
        "failure_modes": _failure_modes(mode, burden, toxic),
        "stability_class": "robust" if score > 80 else "moderate" if score > 50 else "fragile",
    }


def _failure_modes(mode: str, burden: float, toxic: bool) -> list[str]:
    out = []
    if mode == "plasmid":
        out.append("segregational plasmid loss without selection")
    if burden > 0.5:
        out.append("metabolic burden selects for expression-loss mutants")
    if toxic:
        out.append("product toxicity drives suppressor mutations")
    out.append("mutational drift in cargo region over long passaging")
    return out
