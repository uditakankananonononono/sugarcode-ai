from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from scipy.integrate import solve_ivp


@dataclass
class Gate:
    """A regulated gene: inputs repress/activate its expression (Hill kinetics)."""
    name: str
    inputs: list[tuple[str, str]]  # (regulator, "repress"|"activate")
    logic: str = "AND"             # how multiple inputs combine
    basal: float = 0.01
    vmax: float = 1.0
    K: float = 0.5
    n: float = 2.0
    decay: float = 0.2


@dataclass
class Circuit:
    gates: list[Gate] = field(default_factory=list)
    name: str = "circuit"

    def gate(self, name: str) -> Gate:
        return next(g for g in self.gates if g.name == name)


def _hill_repress(x: float, K: float, n: float) -> float:
    return 1.0 / (1.0 + (x / K) ** n)


def _hill_activate(x: float, K: float, n: float) -> float:
    return (x / K) ** n / (1.0 + (x / K) ** n)


def _rates(y: np.ndarray, circuit: Circuit, external: dict[str, float]) -> np.ndarray:
    levels = {g.name: y[i] for i, g in enumerate(circuit.gates)}
    levels.update(external)
    dydt = np.zeros_like(y)
    for i, g in enumerate(circuit.gates):
        terms = []
        for reg, mode in g.inputs:
            x = levels.get(reg, 0.0)
            terms.append(_hill_repress(x, g.K, g.n) if mode == "repress"
                         else _hill_activate(x, g.K, g.n))
        if not terms:
            prod = g.vmax
        elif g.logic == "AND":
            prod = g.vmax * float(np.prod(terms))
        else:  # OR
            prod = g.vmax * (1.0 - float(np.prod([1 - t for t in terms])))
        dydt[i] = g.basal + prod - g.decay * y[i]
    return dydt


def simulate(circuit: Circuit, t_span: tuple[float, float] = (0, 100),
             external: dict[str, float] | None = None,
             y0: list[float] | None = None, n_points: int = 400) -> dict:
    external = external or {}
    y0 = y0 or [0.0] * len(circuit.gates)
    sol = solve_ivp(lambda t, y: _rates(y, circuit, external), t_span, y0,
                    t_eval=np.linspace(*t_span, n_points), rtol=1e-6, atol=1e-9)
    return {
        "circuit": circuit.name,
        "time": [round(float(t), 3) for t in sol.t],
        "series": {g.name: [round(float(v), 5) for v in sol.y[i]]
                   for i, g in enumerate(circuit.gates)},
        "steady_state": {g.name: round(float(sol.y[i][-1]), 4)
                         for i, g in enumerate(circuit.gates)},
        "converged": bool(np.allclose(sol.y[:, -1], sol.y[:, -2], atol=1e-4)),
    }


def logic_verify(circuit: Circuit, input_names: list[str],
                 output: str, levels: tuple[float, float] = (0.05, 3.0)) -> dict:
    """Truth-table verification of a combinatorial circuit by ODE steady states."""
    import itertools
    table = []
    for combo in itertools.product(levels, repeat=len(input_names)):
        ext = dict(zip(input_names, combo))
        r = simulate(circuit, (0, 200), external=ext, n_points=50)
        out = r["steady_state"][output]
        table.append({"inputs": {k: ("HIGH" if v > 1 else "LOW") for k, v in ext.items()},
                      "output": "HIGH" if out > 0.5 else "LOW",
                      "output_level": out})
    return {"output_gate": output, "truth_table": table}


def repressilator() -> Circuit:
    """Elowitz-Leibler repressilator: three-gene ring oscillator."""
    return Circuit(name="repressilator", gates=[
        Gate("LacI", [("TetR", "repress")], vmax=1.2, K=0.4, n=2.1),
        Gate("TetR", [("CI", "repress")], vmax=1.2, K=0.4, n=2.1),
        Gate("CI", [("LacI", "repress")], vmax=1.2, K=0.4, n=2.1),
    ])


def toggle_switch() -> Circuit:
    """Gardner-Collins bistable toggle switch."""
    return Circuit(name="toggle_switch", gates=[
        Gate("A", [("B", "repress")], vmax=1.5, K=0.5, n=2.5),
        Gate("B", [("A", "repress")], vmax=1.5, K=0.5, n=2.5),
    ])


def and_gate(input_a: str = "AraC", input_b: str = "AHL", output: str = "GFP") -> Circuit:
    return Circuit(name="and_gate", gates=[
        Gate(output, [(input_a, "activate"), (input_b, "activate")], logic="AND"),
    ])
