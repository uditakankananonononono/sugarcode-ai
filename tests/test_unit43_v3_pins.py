"""Unit 43 v3 pins for virtual_cell (PARTIAL). Expected values are closed-form / hand-derived; the SSA oracle is an
independent re-implementation of the textbook direct method inside this file (same numpy RNG calls, so streams align).
Where a literal comes from a recorded seeded run (marked REGRESSION) it pins current behaviour, it is not a derivation."""
import math
import re

import numpy as np
import pytest

from sugarcode.modules.virtual_cell import core as m


# ---------------------------------------------------------------- simulate_growth (L175-193)
# demo_model: GLC_UP u -> GLYC g=u, RESP r=g (NADH), ATP: 12g = 8b so b = 1.5 u, FERM f = b/6. So mu_flux = 1.5 * u.
def growth_oracle(glucose0, hours, dt, mu_per_flux):
    biomass, glucose, t, rows = 0.01, glucose0, 0.0, []
    while t <= hours and glucose > 0:
        u = min(10, glucose / max(biomass, 1e-9) / dt)
        flux_obj = 1.5 * u
        mu_h = flux_obj * mu_per_flux
        biomass += biomass * mu_h * dt
        glucose = max(0.0, glucose - u * biomass * 0.01 * dt)
        rows.append((round(t, 2), biomass, glucose, flux_obj, mu_h))
        t += dt
    return rows


@pytest.mark.parametrize("glucose0,hours,dt,mpf", [(10.0, .5, .25, .1), (0.01, .5, .25, .1), (0.01, 1.0, .5, .2), (3.0, .75, .25, .05)])
def test_multi_step_growth_matches_closed_form_recurrence(glucose0, hours, dt, mpf):
    r = m.simulate_growth(m.demo_model(), hours=hours, dt=dt, glucose0=glucose0, mu_per_flux=mpf)
    rows = growth_oracle(glucose0, hours, dt, mpf)
    assert len(r["trajectory"]) == len(rows) >= 3
    for got, (t, b, g, fo, mu) in zip(r["trajectory"], rows):
        assert got["t"] == t
        assert got["biomass"] == pytest.approx(round(b, 5), abs=1.1e-5)
        assert got["glucose"] == pytest.approx(round(g, 4), abs=1.1e-4)
        assert got["mu"] == pytest.approx(round(fo, 4), abs=1e-3)
        assert got["mu_per_h"] == pytest.approx(round(mu, 4), abs=1e-3)
        assert got["doubling_time_h"] == pytest.approx(round(math.log(2) / mu, 4), abs=1e-3)
    assert r["final_biomass"] == r["trajectory"][-1]["biomass"]
    assert r["mu_per_flux"] == mpf and r["model_objective"] == "BIOMASS"
    assert r["glucose_exhausted"] is False


def test_growth_hand_computed_glucose_limited_first_two_steps():
    # glucose0=0.01, B=0.01, dt=.25: u = 0.01/0.01/0.25 = 4 (< 10 cap); mu_flux = 6; mu_h = .6
    # B1 = .01*(1+.6*.25) = .0115 ; G1 = .01 - 4*.0115*.01*.25 = .009885
    # step 2: u = .009885/.0115/.25 = 3.43826..; mu_flux = 5.15739; B2 = .0115*(1+.515739*.25)
    r = m.simulate_growth(m.demo_model(), hours=.25, dt=.25, glucose0=.01)
    a, b = r["trajectory"]
    assert (a["t"], a["biomass"], a["glucose"], a["mu"], a["mu_per_h"]) == (0, .0115, .0099, 6, .6)
    u2 = .009885 / .0115 / .25
    assert (b["t"], b["mu"]) == (.25, round(1.5 * u2, 4))
    assert b["biomass"] == round(.0115 * (1 + 1.5 * u2 * .1 * .25), 5)
    assert b["doubling_time_h"] == round(math.log(2) / (1.5 * u2 * .1), 4)


def test_growth_uptake_cap_10_binds_when_glucose_plentiful():
    r = m.simulate_growth(m.demo_model(), hours=.5, dt=.25, glucose0=1000)
    assert [x["mu"] for x in r["trajectory"]] == [15, 15, 15]          # u = 10 each step, never glucose-limited
    assert [x["t"] for x in r["trajectory"]] == [0, .25, .5]            # t <= hours is inclusive
    assert r["trajectory"][1]["biomass"] == round(.01 * 1.375 * 1.375, 5)  # B *= 1 + 1.5*.25 each step


def test_growth_loop_runs_to_hours_inclusive_and_stops_after():
    assert len(m.simulate_growth(m.demo_model(), hours=.5, dt=.25)["trajectory"]) == 3
    assert len(m.simulate_growth(m.demo_model(), hours=.49, dt=.25)["trajectory"]) == 2
    assert len(m.simulate_growth(m.demo_model(), hours=.1, dt=.25)["trajectory"]) == 1


def test_growth_mu_zero_gives_none_doubling_time():
    mdl = m.demo_model()
    mdl.ub[mdl.rxn_index("BIOMASS")] = 0.0                              # biomass capped at 0 -> mu = 0
    r = m.simulate_growth(mdl, hours=.25, dt=.25)
    assert r["trajectory"][0]["mu"] == 0 and r["trajectory"][0]["doubling_time_h"] is None
    assert r["trajectory"][0]["biomass"] == .01 and r["trajectory"][0]["glucose"] == 10
    # documented behaviour: the dFBA step REPLACES the model's own GLC_UP bounds with (0, min(10, glucose/B/dt))
    mdl2 = m.demo_model(); mdl2.ub[0] = 1.0
    assert m.simulate_growth(mdl2, hours=.1, dt=.25)["trajectory"][0]["mu"] == 15


def test_growth_refusal_messages():
    for kw in ({"hours": 0}, {"dt": -1}, {"mu_per_flux": 0}):
        with pytest.raises(ValueError, match="^hours, dt and mu_per_flux must be positive$"):
            m.simulate_growth(m.demo_model(), **kw)
    with pytest.raises(ValueError, match="^glucose0 must be positive$"):
        m.simulate_growth(m.demo_model(), glucose0=-1)


# ---------------------------------------------------------------- regulatory_state (L198-225)
def traj(**kw):
    return m.regulatory_state(**kw)["trajectory"]


def test_boolean_two_gene_oscillator_never_converges():
    r = m.regulatory_state(["a", "b"], [("a", "b", 1), ("b", "a", 1)], initial={"a": 1}, steps=5)
    assert r["trajectory"] == [{"a": 1, "b": 0}, {"a": 0, "b": 1}, {"a": 1, "b": 0}, {"a": 0, "b": 1}, {"a": 1, "b": 0}, {"a": 0, "b": 1}]
    assert r["converged"] is False and r["steady_state"] == {"a": 0, "b": 1}


def test_boolean_chain_shifts_then_dies_and_breaks_on_first_repeat():
    ch = [("a", "b", 1), ("b", "c", 1)]
    r = m.regulatory_state(["a", "b", "c"], ch, initial={"a": 1}, steps=10)
    assert r["trajectory"] == [{"a": 1, "b": 0, "c": 0}, {"a": 0, "b": 1, "c": 0}, {"a": 0, "b": 0, "c": 1}, {"a": 0, "b": 0, "c": 0}, {"a": 0, "b": 0, "c": 0}]
    assert r["converged"] is True
    # boundary of the converged flag: the repeat is the last of steps+1 rows -> flag False; one more step -> True
    assert m.regulatory_state(["a", "b", "c"], ch, initial={"a": 1}, steps=4)["converged"] is False
    assert len(traj(genes=["a", "b", "c"], interactions=ch, initial={"a": 1}, steps=4)) == 5
    assert m.regulatory_state(["a", "b", "c"], ch, initial={"a": 1}, steps=5)["converged"] is True
    assert len(traj(genes=["a", "b", "c"], interactions=ch, initial={"a": 1}, steps=3)) == 4


def test_boolean_asymmetric_pair_exactly_at_threshold():
    ix = [("a", "c", .5), ("b", "c", .25)]
    g = ["a", "b", "c"]
    last = lambda ini, **k: m.regulatory_state(g, ix, initial=ini, steps=1, **k)["steady_state"]["c"]
    assert last({"a": 1}) == 1          # .5 >= .5  -> on exactly at threshold
    assert last({"b": 1}) == 0          # .25 < .5
    assert last({"a": 1, "b": 1}) == 1  # .75
    assert last({}) == 0
    assert last({"a": 1}, threshold=.5000001) == 0
    assert last({"b": 1}, threshold=.25) == 1
    assert last({"a": 1, "b": 1}, threshold=.75) == 1 and last({"a": 1, "b": 1}, threshold=.7500001) == 0
    assert last({"a": .5, "b": 1}) == 1  # .25 + .25 = .5


def test_boolean_fractional_initial_and_negative_weight_and_sum_of_sources():
    assert traj(genes=["a", "b"], interactions=[("a", "b", 1)], initial={"a": .5}, steps=1)[1]["b"] == 1
    assert traj(genes=["a", "b"], interactions=[("a", "b", 1)], initial={"a": .49}, steps=1)[1]["b"] == 0
    assert traj(genes=["a", "b"], interactions=[("a", "b", -1)], initial={"a": 1}, steps=1)[1] == {"a": 0, "b": 0}
    g = ["a", "b", "c"]
    ix = [("a", "c", 1), ("b", "c", -1)]                  # 1 - 1 = 0 < .5 ; one active repressor cancels the activator
    assert traj(genes=g, interactions=ix, initial={"a": 1, "b": 1}, steps=1)[1]["c"] == 0
    assert traj(genes=g, interactions=ix, initial={"a": 1}, steps=1)[1]["c"] == 1
    assert traj(genes=g, interactions=[("a", "c", 1)], initial={"a": 1}, steps=1)[1]["c"] == 1   # only edges INTO target count
    assert traj(genes=g, interactions=[("c", "a", 1)], initial={"a": 1}, steps=1)[1]["c"] == 0


def test_boolean_refusal_messages_exact():
    with pytest.raises(ValueError, match="^genes must be a non-empty unique list$"):
        m.regulatory_state([], [])
    with pytest.raises(ValueError, match="^genes must be a non-empty unique list$"):
        m.regulatory_state(["a", "a"], [])
    with pytest.raises(ValueError, match="^steps must be at least 1$"):
        m.regulatory_state(["a"], [], steps=0)
    m.regulatory_state(["a"], [], steps=1)
    with pytest.raises(ValueError, match=re.escape("interaction references unknown genes: ['x', 'y']")):
        m.regulatory_state(["a"], [("x", "a", 1), ("a", "y", 1)])
    with pytest.raises(ValueError, match=re.escape("initial references unknown genes: ['z']")):
        m.regulatory_state(["a"], [], initial={"z": 1})
    with pytest.raises(ValueError, match="initial Boolean states must be within"):
        m.regulatory_state(["a"], [], initial={"a": 1.0000001})
    m.regulatory_state(["a"], [], initial={"a": 0}); m.regulatory_state(["a"], [], initial={"a": 1})


# ---------------------------------------------------------------- _validate_grn (L311-319) one case per refusal
G = ["a", "b"]


@pytest.mark.parametrize("genes,inter,inputs,msg", [
    ([], [], None, "^genes must be a non-empty unique list$"),
    (["a", "a"], [], None, "^genes must be a non-empty unique list$"),
    (G, [("x", "b", 1)], None, re.escape("interaction references unknown genes: ['x']")),
    (G, [("a", "y", 1)], None, re.escape("interaction references unknown genes: ['y']")),
    (G, [], {"q": 1}, re.escape("interaction references unknown genes: ['q']")),
    (G, [("a", "b", 1)], {"z": 1, "q": 1}, re.escape("interaction references unknown genes: ['q', 'z']")),
    (G, [("a", "b")], None, "^interactions must be .regulator, target, sign. with non-zero sign$"),
    (G, [("a", "b", 1, 9)], None, "^interactions must be .regulator, target, sign. with non-zero sign$"),
    (G, [("a", "b", 0)], None, "^interactions must be .regulator, target, sign. with non-zero sign$"),
    (G, [("a", "b", 0.0)], None, "^interactions must be .regulator, target, sign. with non-zero sign$"),
    (G, [("a", "b", 1), ("b", "a", 0)], None, "^interactions must be .regulator, target, sign. with non-zero sign$"),
])
def test_validate_grn_each_refusal(genes, inter, inputs, msg):
    with pytest.raises(ValueError, match=msg):
        m._validate_grn(genes, inter, inputs)
    with pytest.raises(ValueError, match=msg):                 # simulate_expression reaches it first
        m.simulate_expression(genes, inter, inputs=inputs)


def test_validate_grn_accepts_valid_and_signs_any_nonzero():
    assert m._validate_grn(G, [("a", "b", 1), ("b", "a", -1), ("a", "a", .001)], {"a": 1}) is None
    assert m._validate_grn(G, [], None) is None and m._validate_grn(["a"], [], {}) is None


# ---------------------------------------------------------------- _transcription_rates (L322-338)
def rates(genes, inter, protein, inputs=None, ko=(), oe=None, params=None):
    par = m._expr_params(genes, params)
    return m._transcription_rates(genes, inter, par, np.array(protein, float), inputs or {}, set(ko), oe or {})


def test_rates_two_activators_multiply_hill_terms_hand_computed():
    # K=50, n=2: p=50 -> x=1 -> .5 ; p=100 -> x=4 -> .8 ; f = .4 ; rate = .05 + 1*.4
    r = rates(["a", "b", "c"], [("a", "c", 1), ("b", "c", 1)], [50, 100, 0])
    assert r[2] == pytest.approx(.45) and r[0] == pytest.approx(1.05) and r[1] == pytest.approx(1.05)   # no regulators: f=1


def test_rates_repressor_times_activator_hand_computed():
    # activator p=50 -> .5 ; repressor p=100 -> 1/(1+4) = .2 ; f = .1 ; rate = .15
    r = rates(["a", "b", "c"], [("a", "c", 1), ("b", "c", -1)], [50, 100, 0])
    assert r[2] == pytest.approx(.15)
    r = rates(["a", "b"], [("a", "b", -.5)], [0, 0])      # float negative sign is a repressor; zero protein -> 1/(1+0)
    assert r[1] == pytest.approx(1.05)
    r = rates(["a", "b"], [("a", "b", .5)], [0, 0])       # float positive sign activates; zero protein -> 0
    assert r[1] == pytest.approx(.05)


def test_rates_custom_K_n_vmax_basal_per_gene():
    par = {"b": {"K": 10, "n": 3, "vmax": 2, "basal": .1}}
    r = rates(["a", "b"], [("a", "b", 1)], [20, 0], params=par)     # x = 2^3 = 8 -> 8/9
    assert r[1] == pytest.approx(.1 + 2 * 8 / 9)
    r = rates(["a", "b"], [("a", "b", -1)], [10, 0], params=par)    # x = 1 -> .5
    assert r[1] == pytest.approx(.1 + 2 * .5)
    r = rates(["a", "b"], [("a", "b", 1)], [30, 0], params={"b": {"K": 10, "n": 1}})   # x = 3 -> .75, vmax 1, basal .05
    assert r[1] == pytest.approx(.05 + .75)


def test_rates_input_clamp_knockout_precedence_and_overexpression():
    g = ["a", "b"]
    inter = [("b", "a", 1)]
    # clamped input: vmax * input * oe, ignores regulators and basal
    assert rates(g, inter, [0, 1e9], inputs={"a": .25}, params={"a": {"vmax": 4}})[0] == pytest.approx(1.0)
    assert rates(g, inter, [0, 0], inputs={"a": .25}, params={"a": {"vmax": 4}}, oe={"a": 3})[0] == pytest.approx(3.0)
    assert rates(g, inter, [0, 0], inputs={"a": 0})[0] == 0                  # clamp at 0 gives 0, not basal
    assert rates(g, inter, [0, 0], inputs={"a": 1}, ko=["a"])[0] == 0        # knockout beats the clamp
    # unclamped: overexpression multiplies basal + vmax*f together
    assert rates(g, inter, [0, 50], oe={"a": 2})[0] == pytest.approx(2 * (.05 + .5))
    assert rates(["a", "b"], [("a", "b", 1)], [50, 0], oe={"b": 2})[1] == pytest.approx(2 * (.05 + .5))
    assert rates(["a", "b"], [("a", "b", 1)], [50, 0], oe={"b": 0})[1] == 0
    assert rates(g, [], [0, 0], ko=["b"])[1] == 0 and rates(g, [], [0, 0], ko=["b"])[0] == pytest.approx(1.05)


def test_rates_negative_protein_clamped_to_zero_and_rate_vector_shape():
    r = rates(["a", "b"], [("a", "b", 1)], [-50, 0])
    assert r.shape == (2,) and r[1] == pytest.approx(.05)                  # max(p, 0): x = 0, activation 0
    r = rates(["a", "b"], [("a", "b", -1)], [-50, 0])
    assert r[1] == pytest.approx(1.05)                                      # repression 1/(1+0) = 1, not 1/(1+1)


# ---------------------------------------------------------------- simulate_expression SSA (L374-408)
def ssa_oracle(genes, interactions, par, inputs, ko, oe, hours, points, seed):
    n = len(genes)
    rng = np.random.default_rng(seed)
    times = np.linspace(0, hours, points)
    mm = np.zeros(n); pp = np.zeros(n); t = 0.0; k = 0
    M = np.zeros((n, points)); P = np.zeros((n, points)); ev = 0
    dm = np.array([par[g]["mrna_decay"] for g in genes]); dp = np.array([par[g]["protein_decay"] for g in genes])
    kt = np.array([par[g]["translation"] for g in genes])
    while k < points:
        tx = m._transcription_rates(genes, interactions, par, pp, inputs, ko, oe)
        props = np.concatenate([tx, dm * mm, kt * mm, dp * pp]); tot = props.sum()
        dt = rng.exponential(1 / tot) if tot > 0 else np.inf
        while k < points and times[k] <= t + dt:
            M[:, k] = mm; P[:, k] = pp; k += 1
        if not np.isfinite(dt):
            break
        t += dt
        r = rng.choice(4 * n, p=props / tot)
        g, kind = r % n, r // n
        (mm, mm, pp, pp)[kind][g] += (1, -1, 1, -1)[kind]
        ev += 1
    return times, M, P, ev


@pytest.mark.parametrize("seed", [0, 1, 7, 12345])
def test_ssa_matches_independent_direct_method(seed):
    genes = ["a", "b"]; inter = [("a", "b", 1)]
    r = m.simulate_expression(genes, inter, inputs={"a": 1.0}, method="gillespie", hours=4, points=9, seed=seed)
    par = m._expr_params(genes, None)
    times, M, P, ev = ssa_oracle(genes, inter, par, {"a": 1.0}, set(), {}, 4, 9, seed)
    assert r["ssa_events"] == ev and r["seed"] == seed and r["method"] == "exact Gillespie SSA"
    assert r["time_h"] == [round(float(x), 4) for x in times]
    for i, g in enumerate(genes):
        assert r["mrna"][g] == [float(x) for x in M[i]] and r["protein"][g] == [float(x) for x in P[i]]
    tail = max(1, 9 // 4)
    for i, g in enumerate(genes):
        sp, sm = P[i, -tail:], M[i, -tail:]
        assert r["steady_state_protein"][g] == round(float(sp.mean()), 4)
        assert r["steady_state_mrna"][g] == round(float(sm.mean()), 4)
        assert r["protein_noise_cv"][g] == (round(float(sp.std() / sp.mean()), 4) if sp.mean() > 0 else 0.0)
    assert ev > 0 and r["inputs"] == {"a": 1.0} and r["knockouts"] == [] and r["overexpress"] == {}


def test_ssa_counts_are_integers_nonnegative_and_grid_filled_to_the_end():
    r = m.simulate_expression(["g"], [], inputs={"g": 1}, method="gillespie", hours=3, points=7, seed=3)
    assert len(r["time_h"]) == 7 and r["time_h"][0] == 0 and r["time_h"][-1] == 3
    assert r["mrna"]["g"][0] == 0 and r["protein"]["g"][0] == 0                  # grid point t=0 is the empty initial state
    assert all(v == int(v) and v >= 0 for v in r["mrna"]["g"] + r["protein"]["g"])
    assert r["ssa_events"] >= 1


REG_SEED7 = (9, [0.0, 0.0, 0.0, 1.0, 1.0], [0.0, 0.0, 0.0, 4.0, 5.0])


def test_ssa_regression_literals_seed7():
    # REGRESSION: literals recorded from the current code at seed 7 (the oracle test above is the derivation).
    r = m.simulate_expression(["g"], [], inputs={"g": 1}, method="gillespie", hours=2, points=5, seed=7)
    assert (r["ssa_events"], r["mrna"]["g"], r["protein"]["g"]) == REG_SEED7


def test_ssa_same_seed_same_result_different_seed_different():
    a = m.simulate_expression(["g"], [], inputs={"g": 1}, method="gillespie", hours=6, points=13, seed=5)
    b = m.simulate_expression(["g"], [], inputs={"g": 1}, method="gillespie", hours=6, points=13, seed=5)
    c = m.simulate_expression(["g"], [], inputs={"g": 1}, method="gillespie", hours=6, points=13, seed=6)
    assert a == b and a != c and c["seed"] == 6


def test_ssa_default_seed_is_7_and_ode_has_no_seed_events_or_cv():
    d = m.simulate_expression(["g"], [], inputs={"g": 1}, method="gillespie", hours=2, points=5)
    assert d["seed"] == 7 and d == m.simulate_expression(["g"], [], inputs={"g": 1}, method="gillespie", hours=2, points=5, seed=7)
    o = m.simulate_expression(["g"], [], hours=2, points=5)
    assert o["seed"] is None and o["ssa_events"] is None and o["protein_noise_cv"] is None and o["method"] == "LSODA ODE"


def test_ssa_zero_rates_exhaust_grid_with_zero_events_and_cv_zero_branch():
    r = m.simulate_expression(["a", "b"], [], inputs={"a": 0, "b": 0}, params={"a": {"basal": 0}, "b": {"basal": 0}},
                              knockouts=["a", "b"], method="gillespie", hours=2, points=9)
    assert r["ssa_events"] == 0 and r["protein_noise_cv"] == {"a": 0.0, "b": 0.0}
    assert r["steady_state_protein"] == {"a": 0.0, "b": 0.0} and r["steady_state_mrna"] == {"a": 0.0, "b": 0.0}
    assert len(r["time_h"]) == 9 and r["mrna"]["a"] == [0.0] * 9


def test_ssa_knockout_and_overexpress_flow_into_events():
    base = dict(method="gillespie", hours=4, points=9, seed=2)
    ko = m.simulate_expression(["g"], [], knockouts=["g"], **base)
    assert ko["ssa_events"] == 0 and ko["knockouts"] == ["g"] and ko["mrna"]["g"] == [0.0] * 9
    par = m._expr_params(["g"], None)
    for oe in ({"g": 3.0}, {"g": 0.0}):
        r = m.simulate_expression(["g"], [], overexpress=oe, **base)
        _, M, P, ev = ssa_oracle(["g"], [], par, {}, set(), oe, 4, 9, 2)
        assert r["ssa_events"] == ev and r["overexpress"] == oe and r["protein"]["g"] == [float(x) for x in P[0]]


def test_expression_refusals_and_method_messages():
    with pytest.raises(ValueError, match=re.escape("perturbation references unknown genes: ['x']")):
        m.simulate_expression(["g"], [], knockouts=["x"])
    with pytest.raises(ValueError, match=re.escape("perturbation references unknown genes: ['y']")):
        m.simulate_expression(["g"], [], overexpress={"y": 1})
    with pytest.raises(ValueError, match="^overexpression factors must be non-negative$"):
        m.simulate_expression(["g"], [], overexpress={"g": -.001})
    m.simulate_expression(["g"], [], overexpress={"g": 0}, points=3)
    with pytest.raises(ValueError, match="^hours must be positive$"):
        m.simulate_expression(["g"], [], hours=0)
    with pytest.raises(ValueError, match="^method must be 'ode' or 'gillespie'$"):
        m.simulate_expression(["g"], [], method="euler")


def test_ode_tail_mean_steady_state_over_last_quarter():
    # unregulated gene, hours long enough that the tail mean ~ steady state q/dm = 2.1 and q*kt/(dm*dp) = 105 (a.u.)
    r = m.simulate_expression(["g"], [], hours=200, points=9)
    tail = max(1, 9 // 4)
    assert r["steady_state_protein"]["g"] == round(float(np.mean(r["protein"]["g"][-tail:])), 4)
    assert r["steady_state_mrna"]["g"] == pytest.approx(2.1, abs=1e-3)
    assert r["steady_state_protein"]["g"] == pytest.approx(105.0, abs=.05)
    assert r["inputs"] == {} and r["knockouts"] == [] and r["units"]["time"] == "h"


# ---------------------------------------------------------------- expression_to_bounds / _phenotype (L418-431)
def test_expression_to_bounds_refusals_exact():
    mdl = m.demo_model()
    with pytest.raises(ValueError, match=re.escape("unknown reaction 'NOPE'")):
        m.expression_to_bounds(mdl, {"e": 1}, {"NOPE": "e"}, {"NOPE": 1})
    with pytest.raises(ValueError, match=re.escape("enzyme 'x' has no protein level")):
        m.expression_to_bounds(mdl, {"e": 1}, {"GLC_UP": "x"}, {"GLC_UP": 1})
    for kc in ({}, {"GLC_UP": 0}, {"GLC_UP": -1}, {"OTHER": 1}):
        with pytest.raises(ValueError, match=re.escape("kcat for 'GLC_UP' must be positive")):
            m.expression_to_bounds(mdl, {"e": 1}, {"GLC_UP": "e"}, kc)
    assert m.expression_to_bounds(mdl, {"e": 1}, {}, {}) == {}


def test_expression_to_bounds_cap_lb_ub_and_types():
    mdl = m.demo_model()
    b = m.expression_to_bounds(mdl, {"e": 1, "f": 4}, {"GLC_UP": "e", "RESP": "f"}, {"GLC_UP": .5, "RESP": .25})
    assert b == {"GLC_UP": (0.0, .5), "RESP": (0.0, 1.0)}
    assert all(isinstance(x, float) for lo_hi in b.values() for x in lo_hi)
    assert m.expression_to_bounds(mdl, {"e": 20}, {"GLC_UP": "e"}, {"GLC_UP": .5})["GLC_UP"] == (0.0, 10.0)    # ub 10 caps
    assert m.expression_to_bounds(mdl, {"e": 20}, {"GLC_UP": "e"}, {"GLC_UP": .5001})["GLC_UP"] == (0.0, 10.0)
    assert m.expression_to_bounds(mdl, {"e": 19}, {"GLC_UP": "e"}, {"GLC_UP": .5})["GLC_UP"] == (0.0, 9.5)
    assert m.expression_to_bounds(mdl, {"e": 0}, {"GLC_UP": "e"}, {"GLC_UP": 5})["GLC_UP"] == (0.0, 0.0)
    mdl2 = m.MetabolicModel(["x"], ["A", "B"], np.array([[1, -1]]), np.array([2, 0]), np.array([9, 9]))
    assert m.expression_to_bounds(mdl2, {"e": 100}, {"A": "e"}, {"A": 1})["A"] == (2.0, 9.0)   # lb kept
    assert m.expression_to_bounds(mdl2, {"e": 1}, {"A": "e"}, {"A": 1})["A"] == (2.0, 1.0)     # cap below lb is passed through as given


def test_phenotype_exact_thresholds_and_extremes():
    assert [m._phenotype(x) for x in (0, .0099999, .01, .0100001, .6999999, .7, 1.0, 3.0)] == [
        "no growth", "no growth", "slow growth", "slow growth", "slow growth", "robust growth", "robust growth", "robust growth"]
    assert m._phenotype(-1) == "no growth"


# ---------------------------------------------------------------- pfba (L105-129) optimum_fraction + reference objective
# demo_model: g=u=GLC_UP=GLYC=RESP=2b/3, FERM = b/6, total = 19b/6. b >= fraction*opt.
@pytest.mark.parametrize("frac,b", [(1.0, 15.0), (.5, 7.5), (.2, 3.0)])
def test_pfba_optimum_fraction_demo_hand_derived(frac, b):
    r = m.pfba(m.demo_model(), optimum_fraction=frac)
    g = 2 * b / 3
    assert r["fluxes"] == {"GLC_UP": round(g, 6), "GLYCOLYSIS": round(g, 6), "RESP": round(g, 6), "FERM": round(b / 6, 6),
                           "BIOMASS": round(b, 6), "LAC_OUT": 0}
    assert r["total_flux"] == round(19 * b / 6, 6) and r["method"] == "pFBA" and r["status"] == "optimal"
    assert r["objective"] == 15 and r["objective_reaction"] == "BIOMASS"      # stage-1 reference, never the relaxed growth


def test_pfba_fraction_boundaries_and_message():
    for bad in (0, -1, 1.0000001, 2, float("nan")):
        with pytest.raises(ValueError, match=re.escape("optimum_fraction must be in (0, 1]")):
            m.pfba(m.demo_model(), optimum_fraction=bad)
    assert m.pfba(m.demo_model(), optimum_fraction=1)["objective"] == 15
    assert m.pfba(m.demo_model(), optimum_fraction=1e-9)["status"] == "optimal"


def test_pfba_alternate_objective_and_bounds_override():
    r = m.pfba(m.demo_model(), objective="FERM")           # FERM = b/6 max at b = 15 -> 2.5 ; total = 19*15/6
    assert r["objective"] == 2.5 and r["objective_reaction"] == "FERM"
    assert r["fluxes"]["BIOMASS"] == 15 and r["total_flux"] == 47.5
    r = m.pfba(m.demo_model(), bounds_override={"GLC_UP": (0, 6)})     # u = 6 -> b = 9
    assert r["objective"] == 9 and r["fluxes"]["GLC_UP"] == 6 and r["fluxes"]["BIOMASS"] == 9 and r["total_flux"] == 28.5
    r = m.pfba(m.demo_model(), bounds_override={"GLC_UP": (0, 6)}, optimum_fraction=.5)
    assert r["objective"] == 9 and r["fluxes"]["BIOMASS"] == 4.5 and r["total_flux"] == 14.25


def test_pfba_flux_values_have_no_negative_zero_and_infeasible_returns_first():
    r = m.pfba(m.demo_model())
    assert all(math.copysign(1.0, v) > 0 for v in r["fluxes"].values())
    bad = m.pfba(m.demo_model(), bounds_override={"GLC_UP": (5, 1)})
    assert bad["status"] == "infeasible" and bad["objective"] == 0 and "method" not in bad


def test_pfba_stage2_lower_bound_uses_relaxed_objective_floor_not_rounded():
    # optimum of the custom model is 1/3 (not representable at 6 dp); fraction 1 must still be feasible and report 0.333333
    mdl = m.MetabolicModel(["x"], ["UP", "BIOMASS"], np.array([[1, -3]]), np.array([0, 0]), np.array([1, 10]))
    r = m.pfba(mdl)
    assert r["status"] == "optimal" and r["objective"] == round(1 / 3, 6) and r["fluxes"]["BIOMASS"] == round(1 / 3, 6)
    assert r["fluxes"]["UP"] == 1.0 and r["total_flux"] == round(4 / 3, 6)


# ---------------------------------------------------------------- second round: gaps found by the first mutation run
def test_growth_low_glucose_uptake_below_one_unit_and_row_rounding():
    # glucose0=.001: u = .001/.01/.25 = .4 < 1 (a lower bound of 1 on GLC_UP would make the LP infeasible); mu = 1.5*.4 = .6
    r = m.simulate_growth(m.demo_model(), hours=.25, dt=.25, glucose0=.001)
    a = r["trajectory"][0]
    assert a["mu"] == .6 and a["mu_per_h"] == .06 and a["biomass"] == round(.01 * (1 + .06 * .25), 5)
    assert a["glucose"] == round(.001 - .4 * a["biomass"] * .01 * .25, 4)


def test_growth_rounding_digits_exact():
    # dt=.125: t = 0, .125 -> round(t, 2) gives 0.12 (banker's/float), 3 digits would give .125
    r = m.simulate_growth(m.demo_model(), hours=.125, dt=.125, mu_per_flux=.123456)
    assert [x["t"] for x in r["trajectory"]] == [0, .12]
    a = r["trajectory"][0]
    mu_h = 15 * .123456                                   # 1.85184
    assert a["mu"] == 15 and a["mu_per_h"] == round(mu_h, 4) == 1.8518
    assert a["doubling_time_h"] == round(math.log(2) / mu_h, 4)
    assert a["biomass"] == round(.01 * (1 + mu_h * .125), 5)


def test_boolean_default_steps_is_12_and_initial_rounded_to_6_digits():
    r = m.regulatory_state(["a", "b"], [("a", "b", 1), ("b", "a", 1)], initial={"a": 1})
    assert len(r["trajectory"]) == 13 and r["converged"] is False
    t0 = m.regulatory_state(["a"], [], initial={"a": .1234567}, steps=1)["trajectory"][0]
    assert t0 == {"a": .123457}


def test_boolean_out_of_range_initial_message_exact():
    with pytest.raises(ValueError) as e:
        m.regulatory_state(["a", "b"], [], initial={"a": 2, "b": .5})
    assert str(e.value) == "initial Boolean states must be within [0, 1]: {'a': 2}"
    with pytest.raises(ValueError) as e:
        m.regulatory_state(["a"], [], initial={"a": -.5})
    assert str(e.value) == "initial Boolean states must be within [0, 1]: {'a': -0.5}"


def test_rates_zero_sign_called_directly_is_treated_as_repressor():
    # simulate_expression refuses sign 0 in _validate_grn; direct callers get the repressor branch (float(sign) > 0 is False)
    r = rates(["a", "b"], [("a", "b", 0)], [100, 0])          # x = 4: repressor 1/5 = .2 (an activator would give .8)
    assert r[1] == pytest.approx(.05 + .2)


def test_expression_defaults_hours_48_points_97():
    r = m.simulate_expression(["g"], [])
    assert len(r["time_h"]) == 97 and r["time_h"][0] == 0 and r["time_h"][1] == .5 and r["time_h"][-1] == 48
    assert r["seed"] is None and r["method"] == "LSODA ODE"


def test_expression_time_grid_and_values_are_rounded_to_4_digits():
    r = m.simulate_expression(["g"], [], hours=1, points=4)
    assert r["time_h"] == [0, .3333, .6667, 1]
    for key in ("mrna", "protein"):
        assert all(round(v, 4) == v for v in r[key]["g"])
    q = 2.1
    assert r["mrna"]["g"][1] == round(q * (1 - math.exp(-.5 / 3)), 4)
    assert r["mrna"]["g"][3] == round(q * (1 - math.exp(-.5)), 4)
    assert all(round(v, 4) == v for v in r["steady_state_mrna"].values())


def test_ode_two_independent_genes_closed_form_each():
    # n = 2 (n = 1 hides state-vector size errors through broadcasting). Gene A default, gene B custom, no interactions.
    par = {"b": {"basal": .2, "vmax": 0, "mrna_decay": 1.0, "translation": 2.0, "protein_decay": .25}}
    r = m.simulate_expression(["a", "b"], [], hours=3, points=4, params=par)
    for t, ma, pa, mb, pb in zip(r["time_h"], r["mrna"]["a"], r["protein"]["a"], r["mrna"]["b"], r["protein"]["b"]):
        # constant tx q, mrna decay dm, translation k, protein decay dp: m = q/dm (1-e^{-dm t}), p = (k q/dm)[(1-e^{-dp t})/dp - (e^{-dp t}-e^{-dm t})/(dm-dp)]
        for (q, dm, k, dp), mm, pp in (((1.05, .5, 5.0, .1), ma, pa), ((.2, 1.0, 2.0, .25), mb, pb)):
            em = q / dm * (1 - math.exp(-dm * t))
            ep = k * q / dm * ((1 - math.exp(-dp * t)) / dp - (math.exp(-dp * t) - math.exp(-dm * t)) / (dm - dp))
            assert mm == pytest.approx(em, abs=2e-4) and pp == pytest.approx(ep, abs=2e-4)


def test_ode_regulated_two_gene_chain_matches_independent_rk4():
    # a clamped at input 1 (rate vmax=1), b activated by a's protein with K=5, n=2 ; RK4 with h=.001 as oracle
    par = {"a": {"mrna_decay": 1, "protein_decay": .5, "translation": 2}, "b": {"K": 5, "n": 2, "basal": .1, "vmax": 3, "mrna_decay": .7, "protein_decay": .3, "translation": 1.5}}
    r = m.simulate_expression(["a", "b"], [("a", "b", 1)], inputs={"a": 1}, params=par, hours=4, points=5)

    def f(y):
        ma, mb, pa, pb = y
        x = (max(pa, 0) / 5) ** 2
        txb = .1 + 3 * (x / (1 + x))
        return np.array([1 * 1 - 1 * ma, txb - .7 * mb, 2 * ma - .5 * pa, 1.5 * mb - .3 * pb])
    y = np.zeros(4); h = .001; out = [y.copy()]
    for _ in range(4):
        for _ in range(1000):
            k1 = f(y); k2 = f(y + h / 2 * k1); k3 = f(y + h / 2 * k2); k4 = f(y + h * k3)
            y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        out.append(y.copy())
    for i, o in enumerate(out):
        assert r["mrna"]["a"][i] == pytest.approx(o[0], abs=3e-4) and r["mrna"]["b"][i] == pytest.approx(o[1], abs=3e-4)
        assert r["protein"]["a"][i] == pytest.approx(o[2], abs=3e-4) and r["protein"]["b"][i] == pytest.approx(o[3], abs=3e-4)
    assert r["protein"]["b"][-1] > .5                                    # the activation path is actually exercised


def test_ssa_cv_branch_with_small_positive_tail_mean():
    # low-count regime: protein decays fast so the tail mean is in (0, 1]; oracle must agree, and one seed must hit that branch
    par = {"g": {"protein_decay": 30.0, "translation": 6.0, "mrna_decay": 2.0}}
    hit = 0
    for seed in range(40):
        r = m.simulate_expression(["g"], [], inputs={"g": 1}, params=par, method="gillespie", hours=20, points=40, seed=seed)
        p = np.array(r["protein"]["g"][-10:])
        if 0 < p.mean() < 1:
            hit += 1
            assert r["protein_noise_cv"]["g"] == round(float(p.std() / p.mean()), 4) and r["protein_noise_cv"]["g"] > 0
    assert hit >= 1


def test_steady_state_tail_is_last_point_when_fewer_than_four_points():
    # tail = max(1, points // 4): with 3 points only the LAST point counts (not a whole-array mean)
    r = m.simulate_expression(["g"], [], hours=4, points=3)
    assert r["steady_state_protein"]["g"] == r["protein"]["g"][-1] != r["protein"]["g"][0]
    assert r["steady_state_mrna"]["g"] == r["mrna"]["g"][-1]
    r = m.simulate_expression(["g"], [], hours=4, points=8)       # 8 // 4 = 2 -> mean of the last two
    assert r["steady_state_mrna"]["g"] == round((r["mrna"]["g"][-1] + r["mrna"]["g"][-2]) / 2, 4)
