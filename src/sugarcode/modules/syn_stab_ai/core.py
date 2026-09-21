from __future__ import annotations
from ..stability_ai.core import stability_forecast


def evaluate_circuit_stability(circuit: dict) -> dict:
    """Circuit-level evolutionary stability: burden from expression load,
    failure risk per gate, generation-resolved forecast."""
    n_gates = circuit.get("n_gates", 3)
    expression = circuit.get("expression_level", 0.5)
    mode = circuit.get("mode", "plasmid")
    size_kb = circuit.get("size_kb", 4.0 * n_gates / 3)
    burden = min(1.0, 0.25 * n_gates * expression)
    fc = stability_forecast({"mode": mode, "burden": burden, "size_kb": size_kb,
                             "toxic": circuit.get("toxic", False)},
                            generations=circuit.get("generations", 200))
    return {
        "circuit": circuit,
        "estimated_burden": round(burden, 3),
        "forecast": fc,
        "circuit_failure_risk": round(1 - fc["trajectory"][-1]["functional_fraction"], 3),
        "dominant_risk": ("mutational drift" if mode == "genomic" else "plasmid loss + burden selection"),
    }


def suggest_stabilization(circuit: dict) -> dict:
    """Genetic modifications to increase functional half-life."""
    ev = evaluate_circuit_stability(circuit)
    suggestions = []
    if circuit.get("mode", "plasmid") == "plasmid":
        suggestions.append({"change": "integrate circuit into genome",
                            "expected_half_life_gain": "5-20x",
                            "mechanism": "removes segregational loss"})
    if ev["estimated_burden"] > 0.4:
        suggestions.append({"change": "swap to weaker promoter / tune RBS",
                            "expected_half_life_gain": "2-4x",
                            "mechanism": "lowers burden, weakens selection against circuit"})
    suggestions.append({"change": "remove repetitive parts; diversify promoters/terminators",
                        "expected_half_life_gain": "1.5-3x",
                        "mechanism": "suppresses homologous-recombination deletions"})
    suggestions.append({"change": "add toxin-antitoxin or addiction module",
                        "expected_half_life_gain": "2-5x",
                        "mechanism": "cells losing the circuit die"})
    return {"evaluation": ev, "suggestions": suggestions}
