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
            if reg not in levels:
                raise KeyError(f"gate {g.name!r} regulates on {reg!r}, which is neither a circuit gate nor an external input (was: silently 0.0)")
            if mode not in ("repress", "activate"):
                raise ValueError(f"gate {g.name!r}: unknown regulation mode {mode!r} (was: silently treated as 'activate')")
            x = levels[reg]
            terms.append(_hill_repress(x, g.K, g.n) if mode == "repress"
                         else _hill_activate(x, g.K, g.n))
        if not terms:
            prod = g.vmax
        elif g.logic == "AND":
            prod = g.vmax * float(np.prod(terms))
        elif g.logic == "OR":
            prod = g.vmax * (1.0 - float(np.prod([1 - t for t in terms])))
        else:
            raise ValueError(f"gate {g.name!r}: unknown logic {g.logic!r} (was: silently treated as 'OR')")
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
        # last-quarter peak-to-peak amplitude: nonzero means the 'steady_state'
        # above is a point on a limit cycle, not a settled fixed point
        "amplitude_last_quarter": {g.name: round(float(np.ptp(sol.y[i][-len(sol.t)//4:])), 4)
                                   for i, g in enumerate(circuit.gates)},
        "oscillating": bool(any(np.ptp(sol.y[i][-len(sol.t)//4:]) > 1e-2
                                for i in range(len(circuit.gates)))),
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
    """Elowitz-Leibler repressilator: three-gene ring oscillator.

    Recalibrated n 2.1 -> 3.0: with n=2.1 the ring converges to the symmetric
    fixed point (last-quarter amplitude 0.002), contradicting 'oscillator'.
    Sustained oscillation needs loop cooperativity n>2 with sufficient gain;
    at n=3.0 the last-quarter amplitude is 2.77 (verified). Note: symmetric
    initial conditions stay symmetric by construction - break symmetry in y0
    to observe the limit cycle."""
    return Circuit(name="repressilator", gates=[
        Gate("LacI", [("TetR", "repress")], vmax=1.2, K=0.4, n=3.0),
        Gate("TetR", [("CI", "repress")], vmax=1.2, K=0.4, n=3.0),
        Gate("CI", [("LacI", "repress")], vmax=1.2, K=0.4, n=3.0),
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
