from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp

# Minimal gene-program modules (JCVI-syn3.0 flavored categories)
GENE_MODULES = {
    "replication": {"rate": 0.02, "atp_cost": 4},
    "transcription": {"rate": 0.1, "atp_cost": 2},
    "translation": {"rate": 0.2, "atp_cost": 4},
    "metabolism": {"rate": 0.5, "atp_cost": 0},   # produces ATP
    "membrane": {"rate": 0.05, "atp_cost": 1},
    "division": {"rate": 0.01, "atp_cost": 3},
}


def simulate_minimal_cell(gene_set: list[str], hours: float = 10.0,
                          glucose: float = 10.0) -> dict:
    """ODE simulation of a minimal cell: ATP budget, mass growth, division.

    State: [mass, atp, glucose_int]. Missing modules create specific failure
    phenotypes (no metabolism -> ATP crash; no division -> filamentation).
    """
    missing = [m for m in GENE_MODULES if m not in gene_set]
    active = {m: GENE_MODULES[m] for m in gene_set if m in GENE_MODULES}

    def rhs(t, y):
        mass, atp, glc = y
        uptake = active.get("metabolism", {"rate": 0})["rate"] * glc
        atp_in = 8 * uptake if "metabolism" in active else 0.0
        atp_out = sum(m["atp_cost"] * m["rate"] * mass for m in active.values())
        growth = active.get("translation", {"rate": 0})["rate"] * atp * 0.01 * (glc > 0.01)
        return [growth, atp_in - atp_out, -uptake]

    y0 = [1.0, 5.0, glucose]
    ts = np.linspace(0, hours, 200)
    sol = solve_ivp(rhs, (0, hours), y0, t_eval=ts, rtol=1e-6)
    mass = sol.y[0]
    divisions = []
    cell_count = 1
    if "division" in active:
        threshold = 2.0
        for i, m in enumerate(mass):
            if m >= threshold * cell_count:
                divisions.append({"t_h": round(float(ts[i]), 2), "generation": cell_count})
                cell_count += 1
    logs = _behavior_log(active, missing, sol, divisions)
    return {
        "gene_set": gene_set, "missing_modules": missing,
        "trajectory": {"t_h": [round(float(t), 2) for t in ts],
                       "mass": [round(float(m), 4) for m in sol.y[0]],
                       "atp": [round(float(a), 4) for a in sol.y[1]],
                       "glucose": [round(float(g), 4) for g in sol.y[2]]},
        "divisions": divisions,
        "final_cells": cell_count,
        "emergent_behaviors": logs,
        "viable": "metabolism" in active and sol.y[1][-1] > 0.1,
        "summary": _summary(active, missing, cell_count, sol),
    }


def _behavior_log(active, missing, sol, divisions):
    out = []
    if "metabolism" not in active:
        out.append("ATP depletion: cell cannot sustain macromolecular synthesis")
    if "division" not in active:
        out.append("filamentation: growth without division (mass accumulates)")
    if divisions:
        out.append(f"self-propagation emerged: {len(divisions)} division events")
    if "metabolism" in active and sol.y[2][-1] <= 0.01:
        out.append("substrate exhaustion: stationary phase reached")
    if not out:
        out.append("balanced growth maintained")
    return out


def _summary(active, missing, cells, sol) -> str:
    if "metabolism" not in active:
        return "non-viable: no energy module"
    return (f"minimal cell with {len(active)} gene modules grew to "
            f"{cells} cell(s); final ATP {sol.y[1][-1]:.2f} a.u.")
