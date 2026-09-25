"""Digital-contract validation for living_computer (module 103).

BUG 73: INTERNAL_GATE_PARAMS n=4 leaked 1/(1+2^4)=5.9% of vmax through every
repress edge at the documented input level (fully induced = 1.0 REU); with
internal protein at 5x transcription the leak (~0.33 REU, near K=0.5)
compounded down cascades. At 1.0/0.0 inputs, before the fix: XOR(1,1)=7.45
(ON, should be OFF), XNOR(1,1)=0.148 (OFF, should be ON), AND-NOT(1,1)=1.21
(OFF above the 0.5 threshold), 3-input XOR had 3 wrong rows - identical on
the two-stage and single-stage engines. The compile_logic verify path masked
it by testing only at HIGH=3.0 (leak 0.08%). n=8 cuts the leak to 0.39%.
These tests pin the truth table at the documented 1.0/0.0 levels on BOTH
simulation engines.
"""
import itertools
import pytest
from sugarcode.modules.living_computer import core as lc
from sugarcode.modules.synbio_studio.core import simulate

# expressions that were wrong at 1.0/0.0 before BUG 73, plus controls
EXPRS = ["A XOR B", "A XNOR B", "A AND NOT B", "A XOR B XOR C",
         "A AND B", "A OR B", "NOT A", "(A OR B) AND (C OR D)"]
HIGH, LOW, THRESHOLD = 1.0, 0.0, 0.5


def _rows(expr):
    ast, inputs = lc.parse_logic(expr)
    c = lc.build_circuit(ast)
    for bits in itertools.product([0, 1], repeat=len(inputs)):
        env = dict(zip(inputs, bits))
        ext = {v: (HIGH if b else LOW) for v, b in env.items()}
        want = bool(lc._eval_bool(ast, {k: bool(b) for k, b in env.items()}))
        yield c, ext, want


@pytest.mark.parametrize("expr", EXPRS)
def test_two_stage_truth_table_at_documented_levels(expr):
    for c, ext, want in _rows(expr):
        ss = lc.two_stage_simulate(c, t_span=(0, 400), external=ext,
                                   n_points=10)["steady_state"]["GFP"]
        assert (ss > THRESHOLD) == want, (expr, ext, ss, want)


@pytest.mark.parametrize("expr", EXPRS)
def test_single_stage_truth_table_at_documented_levels(expr):
    for c, ext, want in _rows(expr):
        ss = simulate(c, (0, 400), external=ext, n_points=50)["steady_state"]["GFP"]
        assert (ss > THRESHOLD) == want, (expr, ext, ss, want)


def test_on_off_margins_at_documented_levels():
    for expr in EXPRS:
        on, off = [], []
        for c, ext, want in _rows(expr):
            ss = lc.two_stage_simulate(c, t_span=(0, 400), external=ext,
                                       n_points=10)["steady_state"]["GFP"]
            (on if want else off).append(ss)
        if on and off:
            assert min(on) > 5 * max(off), (expr, min(on), max(off))


def test_repress_leak_bound():
    # a single repress edge at a fully induced 1.0 REU input leaks < 0.5%
    g = lc.Gate(name="GFP", inputs=[("A", "repress")], logic="AND",
                basal=0.01, vmax=1.5, K=0.5, n=lc.INTERNAL_GATE_PARAMS["n"],
                decay=0.2)
    assert lc._gate_production(g, {"A": 1.0}) / 1.5 < 0.005
