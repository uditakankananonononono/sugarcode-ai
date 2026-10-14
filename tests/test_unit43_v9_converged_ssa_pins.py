"""Unit 43 v9 (PARTIAL): regulatory_state converged fix pins, SSA tie/propensity pins. Hand-derived."""
import numpy as np
import pytest
from sugarcode.modules.virtual_cell import core

CH = [("a", "b", 1), ("b", "c", 1), ("c", "d", 1)]   # a one-hot token shifts right then dies


@pytest.mark.parametrize("steps", [1, 2, 3, 4, 5, 6, 7])
def test_converged_chain_each_step_boundary(steps):
    # rows: t0 1000, t1 0100, t2 0010, t3 0001, t4 0000, t5 0000 (first repeat at row 5 = step 5)
    r = core.regulatory_state(["a", "b", "c", "d"], CH, initial={"a": 1}, steps=steps)
    assert len(r["trajectory"]) == min(steps + 1, 6)
    assert r["converged"] is (steps >= 5)


@pytest.mark.parametrize("steps", [1, 2, 3, 4])
def test_fixed_point_reached_exactly_at_step(steps):
    # token starts `steps-1` places before the end: fixed point (all zero) is reached by the repeat on step `steps`
    genes = ["g%d" % i for i in range(steps)]
    ch = [(genes[i], genes[i + 1], 1) for i in range(steps - 1)]
    r = core.regulatory_state(genes, ch, initial={"g0": 1}, steps=steps)
    assert r["trajectory"][-1] == {g: 0.0 for g in genes}
    if steps == 1:
        assert r["trajectory"] == [{"g0": 1.0}, {"g0": 0.0}] and r["converged"] is False  # last two differ
    # one more step reaches the repeat
    r2 = core.regulatory_state(genes, ch, initial={"g0": 1}, steps=steps + 1)
    assert r2["converged"] is True and len(r2["trajectory"]) == steps + 2


def test_converged_when_already_fixed_for_each_steps():
    for steps in (1, 2, 3, 4):
        r = core.regulatory_state(["a"], [], steps=steps)
        assert r["converged"] is True and r["trajectory"] == [{"a": 0.0}, {"a": 0.0}]
    r = core.regulatory_state(["a"], [("a", "a", 1)], initial={"a": 1}, steps=1)
    assert r["converged"] is True and r["trajectory"] == [{"a": 1.0}, {"a": 1.0}]


def test_converged_false_for_oscillator_at_each_steps():
    for steps in (1, 2, 3, 4):
        r = core.regulatory_state(["a", "b"], [("a", "b", 1), ("b", "a", 1)], initial={"a": 1}, steps=steps)
        assert r["converged"] is False and len(r["trajectory"]) == steps + 1


# ---- SSA: tie between sample time and event time; sub-unit propensity ----
class _Rng:
    def __init__(self, dt): self.dt = dt
    def exponential(self, scale): return self.dt
    def choice(self, n, p): return 0


def test_ssa_sample_time_equal_to_event_time_is_recorded_before_the_event(monkeypatch):
    monkeypatch.setattr(core.np.random, "default_rng", lambda seed: _Rng(1.0))
    r = core.simulate_expression(["A"], [], method="gillespie", points=2, hours=1.0)
    assert r["time_h"] == [0.0, 1.0]
    assert r["mrna"]["A"] == [0.0, 0.0]          # t==1.0 sample is taken before the event at t==1.0
    assert r["ssa_events"] == 1


def test_ssa_propensity_below_one_still_fires():
    r = core.simulate_expression(["A"], [], method="gillespie", points=50, hours=400.0, seed=2,
                                 params={"A": {"basal": 0.5, "vmax": 0.0, "mrna_decay": 0.5, "translation": 0.0,
                                               "protein_decay": 0.5}})
    assert r["ssa_events"] > 10 and max(r["mrna"]["A"]) >= 1.0
