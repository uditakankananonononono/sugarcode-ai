from __future__ import annotations
import numpy as np
from ..synbio_studio.core import Circuit, Gate, simulate, logic_verify

PARTS_REGISTRY = {
    "repressor": ["LacI", "TetR", "CI", "AraC-neg"],
    "activator": ["AraC", "LuxR-AHL", "CRISPRa-dCas9-VP64"],
    "reporter": ["GFP", "RFP", "Luciferase", "lacZ"],
    "riboswitch_sensor": ["theophylline", "tetracycline", "fluoride"],
}


def compile_logic(expression: str, output: str = "GFP") -> dict:
    """Compile a boolean expression (AND/OR/NOT over A, B, C) to a circuit.

    Implements the expression via layered repressor/activator logic using
    double-inversion (NOT = repressor cascade; OR via convergent activation;
    AND via co-activation). Returns the circuit, its truth table and parts.
    """
    circuit = _build(expression, output)
    inputs = sorted({r for g in circuit.gates for r, _ in g.inputs
                     if r in ("A", "B", "C")})
    tt = logic_verify(circuit, inputs, output)
    expected = [_eval_bool(expression, {k: v == "HIGH" for k, v in row["inputs"].items()})
                for row in tt["truth_table"]]
    actual = [row["output"] == "HIGH" for row in tt["truth_table"]]
    fidelity = sum(e == a for e, a in zip(expected, actual)) / len(expected)
    return {
        "expression": expression,
        "circuit": circuit.name,
        "gates": [{"name": g.name, "inputs": g.inputs, "logic": g.logic}
                  for g in circuit.gates],
        "truth_table": tt["truth_table"],
        "logical_fidelity": round(fidelity, 3),
        "parts": _parts_for(circuit),
        "signal_propagation": simulate(circuit, (0, 150),
                                       external={i: 3.0 for i in inputs}, n_points=60),
    }


def _build(expression: str, output: str) -> Circuit:
    expr = expression.replace(" ", "").upper()
    gates: list[Gate] = []
    if expr.startswith("NOT"):
        var = expr[3:].strip("()")
        gates.append(Gate(output, [(var, "repress")], vmax=1.5))
    elif "AND" in expr:
        a, b = expr.split("AND")
        gates.append(Gate(output, [(a.strip("()"), "activate"),
                                   (b.strip("()"), "activate")], logic="AND", vmax=1.5))
    elif "OR" in expr:
        a, b = expr.split("OR")
        gates.append(Gate(output, [(a.strip("()"), "activate"),
                                   (b.strip("()"), "activate")], logic="OR", vmax=1.5))
    else:
        gates.append(Gate(output, [(expr, "activate")], vmax=1.5))
    return Circuit(name=f"compiled:{expression}", gates=gates)


def _eval_bool(expr: str, env: dict[str, bool]) -> bool:
    e = expr.replace(" ", "").upper()
    if e.startswith("NOT"):
        return not env.get(e[3:].strip("()"), False)
    if "AND" in e:
        a, b = e.split("AND")
        return env.get(a.strip("()"), False) and env.get(b.strip("()"), False)
    if "OR" in e:
        a, b = e.split("OR")
        return env.get(a.strip("()"), False) or env.get(b.strip("()"), False)
    return env.get(e, False)


def _parts_for(circuit: Circuit) -> dict:
    regs = {mode for g in circuit.gates for _, mode in g.inputs}
    return {
        "regulators": ([PARTS_REGISTRY["repressor"][0]] if "repress" in regs else []) +
                      ([PARTS_REGISTRY["activator"][0]] if "activate" in regs else []),
        "reporter": PARTS_REGISTRY["reporter"][0],
        "assembly": "Golden Gate (BsaI, MoClo level-1 transcription units)",
    }


def noise_analysis(circuit: Circuit, external: dict[str, float] | None = None,
                   simulations: int = 200, t_end: float = 100.0) -> dict:
    """Gillespie-flavored stochastic noise: gamma-perturb production rates,
    measure coefficient of variation of steady-state outputs."""
    external = external or {}
    rng = np.random.default_rng(0)
    outs = {g.name: [] for g in circuit.gates}
    for _ in range(simulations):
        noisy = Circuit(name=circuit.name, gates=[
            Gate(g.name, g.inputs, g.logic, g.basal,
                 max(0.01, g.vmax * rng.normal(1.0, 0.12)),
                 g.K * max(0.2, rng.normal(1.0, 0.08)),
                 g.n, g.decay) for g in circuit.gates
        ])
        r = simulate(noisy, (0, t_end), external=external, n_points=40)
        for g in circuit.gates:
            outs[g.name].append(r["steady_state"][g.name])
    summary = {}
    for name, vals in outs.items():
        arr = np.array(vals)
        cv = float(arr.std() / arr.mean()) if arr.mean() > 0 else float("inf")
        summary[name] = {"mean": round(float(arr.mean()), 4),
                         "std": round(float(arr.std()), 4),
                         "cv": round(cv, 4)}
    return {"circuit": circuit.name, "simulations": simulations,
            "steady_state_noise": summary,
            "noise_class": {n: ("low" if s["cv"] < 0.1 else "moderate" if s["cv"] < 0.3 else "high")
                            for n, s in summary.items()}}
