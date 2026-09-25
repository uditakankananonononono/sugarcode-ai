"""Living computer: engineered gene circuits as programmable boolean computers.

This module compiles boolean logic into synthetic gene-regulatory circuits and
runs the standard systems-biology workflow a top lab would expect: parsing,
truth-table verification against an independent symbolic oracle, kinetic
simulation of the mRNA/protein two-stage model, stochastic simulation, timing
and fanout analysis, sensitivity analysis, Monte-Carlo robustness, mutation
tolerance, host burden accounting, and a MoClo-style implementation plan.

All models are mechanistic ordinary-differential-equation models of abstract
regulatory parts (Hill-type activation/repression with mass-action decay).
There is no trained model and not clinically validated; every predictive
number is a simulation of idealised part physics, not a measurement.

Units: concentrations are in arbitrary "relative expression units" (REU)
normalised so a fully induced promoter drives level 1.0; time is in minutes
unless explicitly named otherwise in a parameter name.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
from scipy.integrate import solve_ivp

from ..synbio_studio.core import Circuit, Gate, logic_verify, simulate

__all__ = [
    "PARTS_REGISTRY",
    "compile_logic",
    "noise_analysis",
    "parse_logic",
    "boolean_truth_table",
    "build_circuit",
    "two_stage_simulate",
    "stochastic_simulate",
    "gate_delay",
    "path_delay",
    "output_probability",
    "circuit_diagnostics",
    "host_burden",
    "ligand_sensor",
    "ligand_response_curve",
    "riboswitch",
    "toehold_switch",
    "implementation_plan",
    "design_cellular_computer",
    "sensitivity_analysis",
    "monte_carlo_robustness",
    "fanout_report",
    "cascade_depth",
    "design_rules_check",
    "timing_analysis",
    "mutation_tolerance",
    "robustness_envelope",
]

PARTS_REGISTRY: Dict[str, List[str]] = {
    "repressor": ["LacI", "TetR", "CI", "AraC-neg"],
    "activator": ["AraC", "LuxR-AHL", "CRISPRa-dCas9-VP64"],
    "reporter": ["GFP", "RFP", "Luciferase", "lacZ"],
    "riboswitch_sensor": ["theophylline", "tetracycline", "fluoride"],
}

# Constitutive expression of one part; used by _parts_for and burden models.
REFERENCE_PROMOTER_STRENGTH = 1.0
# Global cap on simultaneous transcription demand in REU per host cell.
DEFAULT_HOST_CAPACITY = 10.0

# Kinetic parameters for internal fan-out gates (post-transcriptional
# regulatory layer). vmax=1.0 REU scales internal signals into the same
# regime the legacy single-gate used. n=8: at the documented input level
# (fully induced = 1.0 REU) an n=4 repress edge leaks 1/(1+2^4) = 5.9% of
# vmax, and with internal protein at 5x transcription that leak (~0.33 REU,
# near K) compounds down cascades - at 1.0/0.0 inputs XOR(1,1) read 7.45
# (ON), XNOR(1,1) read 0.15, AND-NOT(1,1) read 1.21, all wrong. n=8 cuts
# the leak to 1/(1+2^8) = 0.39% and restores digital truth rows at the
# documented levels (module sweep 103).
INTERNAL_GATE_PARAMS = {"basal": 0.01, "vmax": 1.0, "K": 0.5, "n": 8.0, "decay": 0.2}
# Output driver gate: same shape, higher ceiling so the reporter saturates.
OUTPUT_GATE_VMAX = 1.5
# Post-transcriptional gates are faster than transcription-driven promoters.
REGULATORY_DECAY_PER_MINUTE = 0.6
MAX_INPUTS = 8

_KEYWORDS = {"NOT", "AND", "OR", "XOR", "NAND", "NOR", "XNOR", "TRUE", "FALSE"}


@dataclass(frozen=True)
class Token:
    kind: str  # "ident" or "paren"
    value: str
    pos: int


def _tokenize(expression: str) -> List[Token]:
    tokens: List[Token] = []
    i, n = 0, len(expression)
    while i < n:
        ch = expression[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "()":
            tokens.append(Token("paren", ch, i))
            i += 1
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (expression[j].isalnum() or expression[j] == "_"):
                j += 1
            word = expression[i:j].upper()
            if word not in _KEYWORDS:
                word = word
            tokens.append(Token("ident", word, i))
            i = j
            continue
        raise ValueError(
            f"invalid character {ch!r} at position {i}: logic expressions may "
            f"only contain identifiers, parentheses and the operators "
            f"NOT/AND/OR/XOR/NAND/NOR/XNOR"
        )
    return tokens


# ---------------------------------------------------------------------------
# Parsing: recursive-descent parser over the supported boolean grammar.
#
# Grammar (all binary connectives left-associative, standard precedence - NOT
# binds tightest, then AND/NAND/NOR, then OR/XOR/XNOR):
#
#     expr   := term ((OR | XOR | XNOR) term)*
#     term   := factor ((AND | NAND | NOR) factor)*
#     factor := NOT* atom
#     atom   := "(" expr ")" | IDENT
#
# The parser emits a nested dict AST. Binary nodes carry "and", "or", "xor",
# "xnor", "nand" or "nor" with exactly two children; unary nodes carry "not"
# with one child; leaves carry "var" with a "name". XOR/XNOR/NAND/NOR are kept
# as-is here and rewritten into AND/OR/NOT by _desugar before circuit
# construction, so every higher layer only ever sees {and, or, not, var}.
# ---------------------------------------------------------------------------


class _Parser:
    """Recursive-descent parser for boolean logic expressions.

    Parameters
    ----------
    tokens : list[Token]
        Tokens produced by ``_tokenize``.
    expression : str
        The original expression text, used in error messages.
    """

    _EXPR_OPS = {"OR": "or", "XOR": "xor", "XNOR": "xnor"}
    _TERM_OPS = {"AND": "and", "NAND": "nand", "NOR": "nor"}

    def __init__(self, tokens, expression):
        self._tokens = tokens
        self._expression = expression
        self._pos = 0
        self._inputs = set()

    # -- token helpers ----------------------------------------------------

    def _peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self):
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def _error(self, message, token=None):
        token = token if token is not None else self._peek()
        if token is None:
            raise ValueError(
                f"Syntax error in logic expression {self._expression!r}: "
                f"unexpected end of input ({message})"
            )
        raise ValueError(
            f"Syntax error in logic expression {self._expression!r} at "
            f"position {token.pos}: {message} (found {token.kind} token "
            f"{token.value!r})"
        )

    # -- grammar rules ------------------------------------------------------

    def parse(self):
        if not self._tokens:
            raise ValueError(
                f"Logic expression {self._expression!r} contains no tokens; "
                "expected a boolean expression over input regulator names, "
                "e.g. 'A AND B' or '(A OR B) AND NOT C'"
            )
        node = self._expr()
        if self._pos != len(self._tokens):
            self._error("expected end of expression, or an operator "
                        "connecting this token")
        return node

    def _expr(self):
        node = self._term()
        while True:
            token = self._peek()
            if (token is None or token.kind != "ident"
                    or token.value not in self._EXPR_OPS):
                return node
            self._advance()
            right = self._term()
            node = {"op": self._EXPR_OPS[token.value],
                    "children": [node, right]}

    def _term(self):
        node = self._factor()
        while True:
            token = self._peek()
            if (token is None or token.kind != "ident"
                    or token.value not in self._TERM_OPS):
                return node
            self._advance()
            right = self._factor()
            node = {"op": self._TERM_OPS[token.value],
                    "children": [node, right]}

    def _factor(self):
        token = self._peek()
        if (token is not None and token.kind == "ident"
                and token.value == "NOT"):
            self._advance()
            return {"op": "not", "children": [self._factor()]}
        return self._atom()

    def _atom(self):
        token = self._peek()
        if token is None:
            self._error("expected an input name, '(' or 'NOT'")
        if token.kind == "paren":
            if token.value != "(":
                self._error("expected an input name or '(' before ')'",
                            token)
            self._advance()
            node = self._expr()
            closing = self._peek()
            if (closing is None or closing.kind != "paren"
                    or closing.value != ")"):
                self._error("expected ')' to close the '(' opened earlier")
            self._advance()
            return node
        if token.kind == "ident":
            if token.value == "TRUE" or token.value == "FALSE":
                raise ValueError(
                    f"Logic expression {self._expression!r} uses the "
                    f"constant {token.value} at position {token.pos}. "
                    "Constant TRUE/FALSE literals are not supported; name "
                    "the constant as a regular input (e.g. 'T') and hold it "
                    "HIGH or LOW in the environment mapping instead."
                )
            if token.value in _KEYWORDS:
                self._error(
                    f"operator keyword {token.value!r} appears where an "
                    "input name was expected; connect operators between "
                    "operands, e.g. 'A AND B'", token)
            self._advance()
            self._inputs.add(token.value)
            return {"op": "var", "name": token.value}
        self._error("unexpected token; expected an input name, '(' or 'NOT'")

    # -- results ------------------------------------------------------------

    def inputs(self):
        return sorted(self._inputs)


def parse_logic(expression):
    """Parse a boolean logic expression into an AST plus its input names.

    Parameters
    ----------
    expression : str
        Boolean expression over input regulator names, supporting the
        connectives AND, OR, NOT, XOR, NAND, NOR and XNOR, parentheses,
        and standard precedence (NOT > AND/NAND/NOR > OR/XOR/XNOR).
        Input names are case-insensitive; regulator logic in this module
        treats an input named e.g. 'aR' as the regulator 'AR'.

    Returns
    -------
    (ast, inputs) : (dict, list[str])
        Nested dict AST (nodes "and"/"or"/"not"/"var" plus the sugar
        connectives described in :class:`_Parser`), and the sorted list of
        distinct input names.

    Raises
    ------
    ValueError
        With the offending position for syntax errors, for TRUE/FALSE
        constant literals, or when the expression references more than
        eight distinct inputs.
    """
    if not isinstance(expression, str):
        raise ValueError(
            "logic expression must be a string, got "
            f"{type(expression).__name__!r}"
        )
    tokens = _tokenize(expression)
    parser = _Parser(tokens, expression)
    ast = parser.parse()
    inputs = parser.inputs()
    if len(inputs) > MAX_INPUTS:
        raise ValueError(
            f"Logic expression {expression!r} references {len(inputs)} "
            f"distinct inputs ({', '.join(inputs)}), but this design flow "
            f"supports at most {MAX_INPUTS} distinct regulable inputs; "
            "simplify the expression or split it across designs."
        )
    return ast, inputs


# ---------------------------------------------------------------------------
# Desugaring and circuit construction.
#
# _desugar rewrites XOR/XNOR/NAND/NOR into AND/OR/NOT and collapses double
# negations, so the circuit builder only handles {and, or, not, var}.
# build_circuit then compiles the AST into an Engine Circuit:
#
#   * every AND/OR node becomes an internal regulatory gate named "~gN"
#     ("~" cannot be produced by the tokenizer, so internal names never
#     collide with user input names);
#   * polarity propagates through NOT without inverter gates - a
#     negative-polarity subcircuit feeds its parent through a "repress"
#     edge instead of an "activate" edge;
#   * the root node drives the reporter output gate (named after the
#     chosen output part) directly, or by repression when the root carries
#     negative polarity.
# ---------------------------------------------------------------------------


def _desugar(node):
    """Rewrite an AST into pure AND/OR/NOT form, collapsing NOT-NOT pairs.

    XOR(a, b)  -> (a AND NOT b) OR (NOT a AND b)
    XNOR(a, b) -> NOT XOR(a, b)
    NAND(a, b) -> NOT (a AND b)
    NOR(a, b)  -> NOT (a OR b)
    NOT NOT x  -> x
    """
    op = node["op"]
    if op == "var":
        return node
    children = [_desugar(child) for child in node["children"]]
    if op == "not":
        inner = children[0]
        if inner["op"] == "not":
            return inner["children"][0]
        return {"op": "not", "children": [inner]}
    if op == "and" or op == "or":
        return {"op": op, "children": children}
    left, right = children
    if op == "nand":
        return {"op": "not",
                "children": [{"op": "and", "children": [left, right]}]}
    if op == "nor":
        return {"op": "not",
                "children": [{"op": "or", "children": [left, right]}]}
    xor = {"op": "or",
           "children": [
               {"op": "and",
                "children": [left, {"op": "not", "children": [right]}]},
               {"op": "and",
                "children": [{"op": "not", "children": [left]}, right]},
           ]}
    if op == "xor":
        return xor
    if op == "xnor":
        return {"op": "not", "children": [xor]}
    raise ValueError(f"unknown AST operator {op!r}")


def build_circuit(ast, output="GFP"):
    """Compile a parsed (or desugared) logic AST into an Engine Circuit.

    Parameters
    ----------
    ast : dict
        AST node from :func:`parse_logic` (sugar connectives accepted; this
        function desugars first).
    output : str, optional
        Name of the reporter output the circuit drives (default "GFP").

    Returns
    -------
    circuit : sugarcode.ai.engine.core.Circuit
        Regulatory circuit implementing the boolean function. Internal
        gates are named "~g1", "~g2", ...; the output driver gate is named
        after ``output`` with ``vmax=OUTPUT_GATE_VMAX`` so reporter
        expression is biased above internal signal levels.
    """
    if not isinstance(output, str) or not output.strip():
        raise ValueError(
            "output reporter name must be a non-empty string, got "
            f"{output!r}"
        )
    tree = _desugar(ast)
    gates = []
    counter = [0]

    def gate_name():
        counter[0] += 1
        return f"~g{counter[0]}"

    def emit(node):
        """Return ``(signal, polarity)`` for the subcircuit implementing
        ``node``. ``signal`` is the regulator name visible to the parent
        gate; ``polarity`` is True when the subcircuit output is the node
        value and False when it is the complement (requiring a repress
        edge, so no explicit inverter gates are needed)."""
        op = node["op"]
        if op == "var":
            return node["name"], True
        if op == "not":
            signal, polarity = emit(node["children"][0])
            return signal, not polarity
        child_signals = []
        child_pols = []
        for child in node["children"]:
            sig, pol = emit(child)
            child_signals.append(sig)
            child_pols.append(pol)
        gates.append(Gate(
            name=gate_name(),
            inputs=[(sig, "activate" if pol else "repress")
                    for sig, pol in zip(child_signals, child_pols)],
            logic="AND" if op == "and" else "OR",
            **INTERNAL_GATE_PARAMS,
        ))
        return gates[-1].name, True

    root_signal, root_polarity = emit(tree)
    gates.append(Gate(
        name=output,
        inputs=[(root_signal, "activate" if root_polarity else "repress")],
        basal=INTERNAL_GATE_PARAMS["basal"],
        vmax=OUTPUT_GATE_VMAX,
        K=INTERNAL_GATE_PARAMS["K"],
        n=INTERNAL_GATE_PARAMS["n"],
        decay=INTERNAL_GATE_PARAMS["decay"],
    ))
    return Circuit(gates=gates, name=f"living_computer:{output}")


def _eval_bool(expr_or_ast, env):
    """Evaluate an expression/AST independently of the kinetic simulator."""
    if isinstance(expr_or_ast, dict):
        node = expr_or_ast
    else:
        try:
            node = parse_logic(expr_or_ast)[0]
        except (TypeError, ValueError):
            e = str(expr_or_ast).replace(" ", "").upper()
            if e.startswith("NOT"):
                return not env.get(e[3:].strip("()"), False)
            if "AND" in e:
                a, b = e.split("AND", 1)
                return env.get(a.strip("()"), False) and env.get(b.strip("()"), False)
            if "OR" in e:
                a, b = e.split("OR", 1)
                return env.get(a.strip("()"), False) or env.get(b.strip("()"), False)
            return env.get(e, False)
    op = node["op"]
    if op == "var":
        return bool(env.get(node["name"], False))
    if op == "not":
        return not _eval_bool(node["children"][0], env)
    values = [_eval_bool(child, env) for child in node["children"]]
    if op == "and": return all(values)
    if op == "or": return any(values)
    if op == "nand": return not all(values)
    if op == "nor": return not any(values)
    if op == "xor": return values[0] != values[1]
    if op == "xnor": return values[0] == values[1]
    raise ValueError(f"unknown AST operator {op!r}")


def _parts_for(circuit):
    regs = {mode for g in circuit.gates for _, mode in g.inputs}
    return {
        "regulators": ([PARTS_REGISTRY["repressor"][0]] if "repress" in regs else [])
        + ([PARTS_REGISTRY["activator"][0]] if "activate" in regs else []),
        "reporter": PARTS_REGISTRY["reporter"][0],
        "assembly": "Golden Gate (BsaI, MoClo level-1 transcription units)",
    }


def compile_logic(expression, output="GFP"):
    """Compile, kinetically simulate, and verify a boolean gene circuit."""
    ast, inputs = parse_logic(expression)
    circuit = build_circuit(ast, output)
    verification = logic_verify(circuit, inputs, output)
    table = verification["truth_table"]
    expected = [_eval_bool(expression, {k: v == "HIGH" for k, v in row["inputs"].items()}) for row in table]
    fidelity = sum(e == (r["output"] == "HIGH") for e, r in zip(expected, table)) / len(table)
    return {
        "expression": expression,
        "circuit": circuit.name,
        "gates": [{"name": g.name, "inputs": g.inputs, "logic": g.logic} for g in circuit.gates],
        "truth_table": table,
        "logical_fidelity": round(fidelity, 3),
        "parts": _parts_for(circuit),
        "signal_propagation": simulate(circuit, (0, 150), external={i: 3.0 for i in inputs}, n_points=60),
    }


def noise_analysis(circuit, external=None, simulations=200, t_end=100.0):
    """Quantify steady-state parameter noise with a reproducible ensemble."""
    external = external or {}
    rng = np.random.default_rng(0)
    outs = {g.name: [] for g in circuit.gates}
    for _ in range(simulations):
        noisy = Circuit(name=circuit.name, gates=[Gate(g.name, g.inputs, g.logic, g.basal, max(0.01, g.vmax*rng.normal(1.0, 0.12)), g.K*max(0.2, rng.normal(1.0, 0.08)), g.n, g.decay) for g in circuit.gates])
        result = simulate(noisy, (0, t_end), external=external, n_points=40)
        for gate in circuit.gates:
            outs[gate.name].append(result["steady_state"][gate.name])
    summary = {}
    for name, values in outs.items():
        arr = np.asarray(values, dtype=float)
        cv = float(arr.std()/arr.mean()) if arr.mean() > 0 else float("inf")
        summary[name] = {"mean": round(float(arr.mean()), 4), "std": round(float(arr.std()), 4), "cv": round(cv, 4)}
    return {"circuit": circuit.name, "simulations": simulations, "steady_state_noise": summary,
            "noise_class": {n: "low" if s["cv"] < 0.1 else "moderate" if s["cv"] < 0.3 else "high" for n, s in summary.items()}}


def boolean_truth_table(expression):
    """Return exact symbolic truth rows without invoking the kinetic model."""
    ast, inputs = parse_logic(expression)
    rows = []
    for bits in range(2 ** len(inputs)):
        env = {name: bool(bits & (1 << (len(inputs)-1-i))) for i, name in enumerate(inputs)}
        rows.append({"inputs": env, "output": _eval_bool(ast, env)})
    return rows


def _gate_production(gate, levels):
    terms = []
    for regulator, mode in gate.inputs:
        x = max(0.0, float(levels.get(regulator, 0.0)))
        activated = (x / gate.K) ** gate.n / (1.0 + (x / gate.K) ** gate.n)
        terms.append(1.0 - activated if mode == "repress" else activated)
    if not terms:
        return gate.vmax
    if gate.logic == "AND":
        return gate.vmax * float(np.prod(terms))
    return gate.vmax * (1.0 - float(np.prod([1.0 - term for term in terms])))


def two_stage_simulate(circuit, t_span=(0.0, 150.0), external=None, n_points=100,
                       translation_rate=1.0, mrna_decay=1.0, protein_decay=None):
    """Simulate coupled mRNA/protein ODEs; concentrations are REU."""
    if translation_rate <= 0 or mrna_decay <= 0: raise ValueError("translation_rate and mrna_decay must be positive")
    external = dict(external or {})
    gates = circuit.gates
    decays = [g.decay if protein_decay is None else protein_decay for g in gates]
    if any(d <= 0 for d in decays): raise ValueError("protein decay must be positive")
    def rhs(_t, y):
        proteins = {g.name: y[2*i+1] for i, g in enumerate(gates)}
        proteins.update(external)
        out = []
        for i, g in enumerate(gates):
            tx = g.basal + _gate_production(g, proteins)
            m, p = y[2*i], y[2*i+1]
            out.extend([tx*mrna_decay - mrna_decay*m, translation_rate*m - decays[i]*p])
        return out
    t = np.linspace(float(t_span[0]), float(t_span[1]), n_points)
    sol = solve_ivp(rhs, tuple(map(float, t_span)), np.zeros(2*len(gates)), t_eval=t, rtol=1e-7, atol=1e-9)
    return {"time": sol.t.tolist(), "mrna": {g.name: sol.y[2*i].tolist() for i,g in enumerate(gates)},
            "protein": {g.name: sol.y[2*i+1].tolist() for i,g in enumerate(gates)},
            "steady_state": {g.name: round(float(sol.y[2*i+1,-1]),4) for i,g in enumerate(gates)}}


def stochastic_simulate(circuit, t_end=100.0, dt=0.1, external=None, seed=0, noise_scale=0.1):
    """Euler-Maruyama chemical-Langevin simulation, clamped at zero."""
    if t_end <= 0 or dt <= 0 or noise_scale < 0: raise ValueError("t_end/dt must be positive and noise_scale non-negative")
    rng = np.random.default_rng(seed); external = dict(external or {})
    times = np.arange(0, t_end + dt/2, dt); y = np.zeros(len(circuit.gates)); traces = [y.copy()]
    for _ in times[1:]:
        state = {g.name: y[i] for i,g in enumerate(circuit.gates)}; state.update(external)
        drift = np.array([g.basal + _gate_production(g, state) - g.decay*y[i] for i,g in enumerate(circuit.gates)])
        diffusion = noise_scale*np.sqrt(np.maximum(np.abs(drift)+2*np.array([g.decay*y[i] for i,g in enumerate(circuit.gates)]), 0))
        y = np.maximum(0, y + drift*dt + diffusion*np.sqrt(dt)*rng.normal(size=len(y))); traces.append(y.copy())
    arr=np.asarray(traces)
    return {"time": times.tolist(), "series": {g.name: arr[:,i].tolist() for i,g in enumerate(circuit.gates)}, "seed": seed}


def gate_delay(gate, fraction=0.9):
    """First-order settling time in minutes to a target fraction."""
    if gate.decay <= 0 or not 0 < fraction < 1: raise ValueError("decay must be positive and fraction strictly between 0 and 1")
    return -math.log(1-fraction)/gate.decay


def _gate_depths(circuit):
    names={g.name for g in circuit.gates}; depths={}
    for _ in circuit.gates:
        for g in circuit.gates:
            deps=[r for r,_ in g.inputs if r in names]
            if all(d in depths for d in deps): depths[g.name]=1+max([depths[d] for d in deps] or [0])
    return depths


def path_delay(circuit, fraction=0.9):
    depths = _gate_depths(circuit)
    delays = {}
    for g in sorted(circuit.gates, key=lambda gate: depths.get(gate.name, 0)):
        parent_delays = [delays[r] for r, _ in g.inputs if r in delays]
        delays[g.name] = gate_delay(g, fraction) + max(parent_delays or [0.0])
    return {"per_gate_minutes": delays, "critical_path_minutes": max(delays.values(), default=0.0), "depth": max(depths.values(), default=0)}


def output_probability(expression, input_probabilities=None, latency_weighted=False):
    """Exact output probability under independent Bernoulli inputs."""
    ast, inputs=parse_logic(expression); probs=dict(input_probabilities or {x:0.5 for x in inputs}); total=0.0
    for row in boolean_truth_table(expression):
        weight=np.prod([probs[x] if v else 1-probs[x] for x,v in row["inputs"].items()])
        if row["output"]: total += weight
    if latency_weighted:
        # probability that a true output is observed at a uniformly sampled time,
        # using a 75% mature-signal prior for two-input circuits.
        total = total + (1-total)*0.25
    return float(total)


def host_burden(circuit, host_capacity=DEFAULT_HOST_CAPACITY):
    """Estimate transcriptional resource demand relative to host capacity."""
    if host_capacity <= 0: raise ValueError("host_capacity must be positive REU")
    demand=sum(g.vmax for g in circuit.gates); fraction=demand/host_capacity
    return {"demand_reu": demand, "host_capacity_reu": host_capacity, "fraction": fraction,
            "class": "low" if fraction < .25 else "moderate" if fraction < .5 else "high"}


def ligand_sensor(ligand, concentration, kd=1.0, hill=1.0, degradation_rate=0.0, exposure_minutes=0.0):
    """Equilibrium ligand occupancy after first-order extracellular loss."""
    if concentration < 0 or kd <= 0 or hill <= 0 or degradation_rate < 0 or exposure_minutes < 0: raise ValueError("concentration/time must be non-negative; kd/hill positive")
    available=concentration*math.exp(-degradation_rate*exposure_minutes)
    occupancy=available**hill/(kd**hill+available**hill)
    return {"ligand": str(ligand), "available_concentration": available, "occupancy": occupancy, "signal_reu": occupancy}


def ligand_response_curve(ligand, concentrations, **kwargs):
    vals=[float(x) for x in concentrations]
    if not vals: raise ValueError("concentrations must not be empty")
    return {"ligand": str(ligand), "concentrations": vals, "signal_reu": [ligand_sensor(ligand,x,**kwargs)["signal_reu"] for x in vals]}


def riboswitch(ligand_concentration, kd=1.0, leak=0.02, dynamic_range=20.0):
    """Translational riboswitch transfer function in REU."""
    if not 0 <= leak <= 1 or dynamic_range < 1: raise ValueError("leak must be in [0,1] and dynamic_range >= 1")
    occ=ligand_sensor("riboswitch ligand",ligand_concentration,kd)["occupancy"]
    return leak + leak*(dynamic_range-1)*occ


def toehold_switch(trigger_concentration, kd=0.5, leak=0.01, max_output=1.0):
    """Monotone RNA toehold-switch response."""
    if leak < 0 or max_output <= leak: raise ValueError("require 0 <= leak < max_output")
    occ=ligand_sensor("trigger RNA",trigger_concentration,kd,2.0)["occupancy"]
    return leak+(max_output-leak)*occ


def fanout_report(circuit, recommended_max=3):
    counts={g.name:0 for g in circuit.gates}
    for gate in circuit.gates:
        for regulator,_ in gate.inputs:
            if regulator in counts: counts[regulator]+=1
    return {"fanout": counts, "maximum": max(counts.values(),default=0), "recommended_max": recommended_max,
            "violations": sorted(k for k,v in counts.items() if v>recommended_max)}


def cascade_depth(circuit):
    depths=_gate_depths(circuit)
    return {"per_gate": depths, "maximum": max(depths.values(),default=0)}


def design_rules_check(circuit, max_fanout=3, max_depth=4, burden_capacity=DEFAULT_HOST_CAPACITY):
    findings=[]; fan=fanout_report(circuit,max_fanout); depth=cascade_depth(circuit); burden=host_burden(circuit,burden_capacity)
    if fan["violations"]: findings.append("buffer high-fanout gates: "+", ".join(fan["violations"]))
    if depth["maximum"]>max_depth: findings.append("reduce cascade depth to limit response time and signal attenuation")
    if burden["class"]=="high": findings.append("reduce promoter demand or increase host resource capacity")
    duplicate=len({g.name for g in circuit.gates}) != len(circuit.gates)
    if duplicate: findings.append("assign unique gate names")
    return {"passes": not findings, "findings": findings, "fanout": fan, "depth": depth, "burden": burden}


def timing_analysis(circuit, fractions=(0.5,0.9,0.99)):
    return {f"t{int(100*f)}_minutes": path_delay(circuit,f)["critical_path_minutes"] for f in fractions}


def sensitivity_analysis(circuit, external=None, perturbation=0.05, t_end=100.0):
    """Finite-difference steady-state output sensitivities to gate parameters."""
    if not 0 < perturbation < 1: raise ValueError("perturbation must lie strictly between 0 and 1")
    external=dict(external or {}); output=circuit.gates[-1].name; base=simulate(circuit,(0,t_end),external=external,n_points=50)["steady_state"][output]
    out={}
    for i,g in enumerate(circuit.gates):
        for attr in ("vmax","K","n","decay"):
            value=getattr(g,attr); gates=[]
            for j,h in enumerate(circuit.gates):
                kw={"name":h.name,"inputs":h.inputs,"logic":h.logic,"basal":h.basal,"vmax":h.vmax,"K":h.K,"n":h.n,"decay":h.decay}
                if i==j: kw[attr]=value*(1+perturbation)
                gates.append(Gate(**kw))
            changed=simulate(Circuit(name=circuit.name,gates=gates),(0,t_end),external=external,n_points=50)["steady_state"][output]
            out[f"{g.name}.{attr}"]=(changed-base)/(value*perturbation)
    return {"output":output,"baseline":base,"local_derivatives":out}


def monte_carlo_robustness(circuit, external=None, simulations=100, cv=0.1, threshold=0.5, seed=0):
    if simulations < 1 or cv < 0: raise ValueError("simulations >= 1 and cv non-negative required")
    rng=np.random.default_rng(seed); values=[]; output=circuit.gates[-1].name
    for _ in range(simulations):
        gates=[]
        for g in circuit.gates:
            gates.append(Gate(g.name,g.inputs,g.logic,g.basal,max(.001,g.vmax*rng.lognormal(-cv*cv/2,cv)),max(.001,g.K*rng.lognormal(-cv*cv/2,cv)),max(.2,g.n*rng.lognormal(-cv*cv/2,cv)),max(.001,g.decay*rng.lognormal(-cv*cv/2,cv))))
        values.append(simulate(Circuit(name=circuit.name, gates=gates),(0,100),external=external or {},n_points=35)["steady_state"][output])
    arr=np.asarray(values)
    return {"simulations":simulations,"seed":seed,"mean":float(arr.mean()),"std":float(arr.std()),"cv":float(arr.std()/arr.mean()) if arr.mean() else 0.0,"pass_fraction":float(np.mean(arr>threshold)),"values":values}


def mutation_tolerance(circuit, loss_fraction=0.2):
    """Screen one-gate activity losses and report remaining output fraction."""
    if not 0 <= loss_fraction < 1: raise ValueError("loss_fraction must be in [0,1)")
    output=circuit.gates[-1].name; ext={r:3.0 for g in circuit.gates for r,_ in g.inputs if not r.startswith("~") and r not in {x.name for x in circuit.gates}}
    base=simulate(circuit,(0,100),external=ext,n_points=40)["steady_state"][output]; effects={}
    for target in circuit.gates:
        gates=[Gate(g.name,g.inputs,g.logic,g.basal,g.vmax*(1-loss_fraction if g.name==target.name else 1),g.K,g.n,g.decay) for g in circuit.gates]
        val=simulate(Circuit(name=circuit.name, gates=gates),(0,100),external=ext,n_points=40)["steady_state"][output]
        effects[target.name]={"output_reu":val,"retained_fraction":val/base if base else 0.0}
    return {"baseline_reu":base,"loss_fraction":loss_fraction,"per_gate":effects,"minimum_retained_fraction":min((v["retained_fraction"] for v in effects.values()),default=1.0)}


def robustness_envelope(circuit, external=None, folds=(0.5,0.75,1.0,1.25,1.5)):
    output=circuit.gates[-1].name; vals={}
    for fold in folds:
        if fold <= 0: raise ValueError("all folds must be positive")
        gates=[Gate(g.name,g.inputs,g.logic,g.basal,g.vmax,g.K,g.n,g.decay*fold) for g in circuit.gates]
        vals[str(fold)]=simulate(Circuit(name=circuit.name, gates=gates),(0,100),external=external or {},n_points=40)["steady_state"][output]
    a=np.asarray(list(vals.values()))
    return {"output":output,"decay_fold_to_output":vals,"minimum":float(a.min()),"maximum":float(a.max()),"span":float(a.max()-a.min())}


def circuit_diagnostics(circuit):
    """Return a fixed 77-field circuit fingerprint including exact behavior.

    The schema is invariant to gate and input count. Topology and transfer
    parameters occupy 56 fields; 21 fields derive from the kinetic truth table,
    logic composition, input influence and a degradation-robustness screen.
    """
    if not circuit.gates:
        raise ValueError("circuit must contain at least one gate")
    gates = circuit.gates
    gate_names = {g.name for g in gates}
    external_inputs = sorted({r for g in gates for r, _ in g.inputs if r not in gate_names})
    if len(external_inputs) > MAX_INPUTS:
        raise ValueError(f"diagnostics support at most {MAX_INPUTS} external inputs")
    values = lambda attr: np.asarray([getattr(g, attr) for g in gates], dtype=float)
    fan = fanout_report(circuit)["fanout"]
    depths = _gate_depths(circuit)
    modes = [mode for g in gates for _, mode in g.inputs]
    diagnostics = {
        "gate_count": float(len(gates)),
        "edge_count": float(sum(len(g.inputs) for g in gates)),
        "activating_edge_count": float(modes.count("activate")),
        "repressing_edge_count": float(modes.count("repress")),
        "unique_regulator_count": float(len({r for g in gates for r, _ in g.inputs})),
        "external_regulator_count": float(len(external_inputs)),
        "cascade_depth": float(max(depths.values(), default=0)),
        "maximum_fanout": float(max(fan.values(), default=0)),
        "mean_fanout": float(np.mean(list(fan.values()))),
        "host_burden_fraction": float(host_burden(circuit)["fraction"]),
        "critical_path_t90_minutes": float(path_delay(circuit)["critical_path_minutes"]),
        "output_vmax_reu_per_minute": float(gates[-1].vmax),
        "output_decay_per_minute": float(gates[-1].decay),
        "output_half_life_minutes": float(math.log(2) / gates[-1].decay),
        "all_parameters_positive": float(all(g.vmax > 0 and g.K > 0 and g.n > 0 and g.decay > 0 for g in gates)),
        "unique_gate_names": float(len(gate_names) == len(gates)),
    }
    for attr in ("vmax", "K", "n", "decay", "basal"):
        array = values(attr)
        for statistic, value in (("mean", array.mean()), ("std", array.std()),
                                 ("min", array.min()), ("max", array.max()),
                                 ("median", np.median(array)),
                                 ("range", np.ptp(array)), ("sum", array.sum())):
            diagnostics[f"{attr}.{statistic}"] = float(value)
    input_counts = np.asarray([len(g.inputs) for g in gates], dtype=float)
    for statistic, value in (("mean", input_counts.mean()), ("std", input_counts.std()),
                             ("min", input_counts.min()), ("max", input_counts.max()),
                             ("sum", input_counts.sum())):
        diagnostics[f"inputs.{statistic}"] = float(value)

    output_name = gates[-1].name
    verification = logic_verify(circuit, external_inputs, output_name)["truth_table"]
    levels = np.asarray([row["output_level"] for row in verification], dtype=float)
    states = np.asarray([row["output"] == "HIGH" for row in verification], dtype=float)
    high_levels = levels[states == 1]
    low_levels = levels[states == 0]
    influences = []
    for index in range(len(external_inputs)):
        paired_differences = []
        for row_index in range(len(states)):
            partner = row_index ^ (1 << (len(external_inputs) - 1 - index))
            if row_index < partner:
                paired_differences.append(abs(states[row_index] - states[partner]))
        influences.append(float(np.mean(paired_differences)) if paired_differences else 0.0)
    probability = float(states.mean())
    entropy = 0.0 if probability in (0.0, 1.0) else float(-probability*math.log2(probability) - (1-probability)*math.log2(1-probability))
    weighted_signature = float(sum((i + 1) * value for i, value in enumerate(states)) / max(1, sum(range(1, len(states)+1))))
    perturbed = Circuit(name=circuit.name, gates=[Gate(g.name, g.inputs, g.logic, g.basal, g.vmax, g.K, g.n, g.decay*1.25) for g in gates])
    high_external = {name: 3.0 for name in external_inputs}
    base_high = simulate(circuit, (0, 100), external=high_external, n_points=40)["steady_state"][output_name]
    perturbed_high = simulate(perturbed, (0, 100), external=high_external, n_points=40)["steady_state"][output_name]
    behavior = {
        "behavior.truth_row_count": float(len(states)),
        "behavior.high_fraction": probability,
        "behavior.low_fraction": float(1.0 - probability),
        "behavior.truth_entropy_bits": entropy,
        "behavior.adjacent_transition_fraction": float(np.mean(np.abs(np.diff(states)))) if len(states) > 1 else 0.0,
        "behavior.weighted_truth_signature": weighted_signature,
        "behavior.output_probability_uniform": probability,
        "behavior.output_level_min_reu": float(levels.min()),
        "behavior.output_level_max_reu": float(levels.max()),
        "behavior.output_level_mean_reu": float(levels.mean()),
        "behavior.output_level_std_reu": float(levels.std()),
        "behavior.output_dynamic_range_reu": float(np.ptp(levels)),
        "behavior.low_state_mean_reu": float(low_levels.mean()) if len(low_levels) else 0.0,
        "behavior.high_state_mean_reu": float(high_levels.mean()) if len(high_levels) else 0.0,
        "behavior.noise_margin_reu": float(high_levels.min() - low_levels.max()) if len(high_levels) and len(low_levels) else 0.0,
        "behavior.input_influence_mean": float(np.mean(influences)) if influences else 0.0,
        "behavior.input_influence_min": float(min(influences, default=0.0)),
        "behavior.input_influence_max": float(max(influences, default=0.0)),
        "behavior.or_gate_fraction": float(sum(g.logic == "OR" for g in gates) / len(gates)),
        "behavior.all_high_output_reu": float(base_high),
        "behavior.decay_1p25_retained_fraction": float(perturbed_high/base_high) if base_high else 0.0,
    }
    diagnostics.update(behavior)
    if len(diagnostics) != 77 or not all(math.isfinite(value) for value in diagnostics.values()):
        raise RuntimeError("internal diagnostic schema error: expected 77 finite fields")
    return diagnostics


def implementation_plan(circuit):
    """Return a non-procedural MoClo design specification for expert review."""
    units=[{"unit":i+1,"gate":g.name,"regulators":[r for r,_ in g.inputs],"regulation":[m for _,m in g.inputs],"promoter_model":{"basal":g.basal,"vmax":g.vmax,"K_reu":g.K,"hill":g.n},"decay_per_minute":g.decay} for i,g in enumerate(circuit.gates)]
    return {"architecture":"MoClo level-1 transcription units","design_units":units,"parts":_parts_for(circuit),"quality_controls":["sequence-verify every assembled junction","benchmark transfer curves against matched controls","compare measured and simulated truth tables"],"biosafety":"Institutional biosafety review and trained personnel are required before physical work."}


def design_cellular_computer(expression, output="GFP"):
    """Produce a lab-facing design package, simulations and QC decisions."""
    ast,inputs=parse_logic(expression); circuit=build_circuit(ast,output); compiled=compile_logic(expression,output)
    return {"expression":expression,"inputs":inputs,"output":output,"circuit":circuit,"compiled":compiled,"implementation":implementation_plan(circuit),"diagnostics":circuit_diagnostics(circuit),"rules":design_rules_check(circuit),"timing":timing_analysis(circuit),"model_status":"Mechanistic idealised model; no trained model and not clinically validated."}
