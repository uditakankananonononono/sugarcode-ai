"""Unit 43 v7: tests-only pins for the remaining core.py survivors (PARTIAL).
Oracles: hand algebra and stubs with hand arithmetic; nothing mirrors module code."""
import math
import numpy as np
import pytest
from sugarcode.modules.virtual_cell import core


# ---- demo_model ----
def test_demo_model_literals_and_hand_fba():
    m = core.demo_model()
    assert m.metabolites == ["GLC_int", "PYR", "ATP", "NADH"]
    assert m.reactions == ["GLC_UP", "GLYCOLYSIS", "RESP", "FERM", "BIOMASS", "LAC_OUT"]
    assert m.S.tolist() == [[1, -1, 0, 0, 0, 0], [0, 2, -1, -1, -0.5, 0],
                            [0, 2, 10, 0, -8, 0], [0, 2, -2, 0, 0, 0]]
    assert m.lb.tolist() == [0] * 6 and m.ub.tolist() == [10, 1000, 1000, 1000, 1000, 1000]
    # hand: NADH -> RESP=g ; ATP -> 12g=8B -> B=1.5g=15 ; PYR -> FERM=g/4=2.5
    p = core.pfba(m)
    assert p["objective"] == 15.0
    assert p["fluxes"] == {"GLC_UP": 10.0, "GLYCOLYSIS": 10.0, "RESP": 10.0, "FERM": 2.5,
                           "BIOMASS": 15.0, "LAC_OUT": 0.0}
    assert p["total_flux"] == 47.5
    # half optimum: B>=7.5 -> g=5 -> total 23.75
    h = core.pfba(m, optimum_fraction=0.5)
    assert h["fluxes"]["BIOMASS"] == 7.5 and h["total_flux"] == 23.75
    for bad in (0, -0.1, 1.0001):
        with pytest.raises(ValueError, match="optimum_fraction must be in"):
            core.pfba(m, optimum_fraction=bad)
    assert core.pfba(m, optimum_fraction=1)["objective"] == 15.0


def test_pfba_reversible_flux_split():
    # A + B = 0 balance (S=[1,1]); maximise A in [-5,5] -> A=5, B=-5, total |v| = 10
    m = core.MetabolicModel(["M"], ["A", "B"], np.array([[1.0, 1.0]]), np.array([-5.0, -5.0]),
                            np.array([5.0, 5.0]), objective="A")
    p = core.pfba(m)
    assert p["fluxes"] == {"A": 5.0, "B": -5.0} and p["total_flux"] == 10.0
    q = core.pfba(m, objective="B")
    assert q["fluxes"] == {"A": -5.0, "B": 5.0}


# ---- simulate_growth validation / defaults ----
@pytest.mark.parametrize("kw,msg", [({"hours": 0}, "must be positive"), ({"dt": 0}, "must be positive"),
                                    ({"mu_per_flux": 0}, "must be positive"),
                                    ({"glucose0": 0}, "glucose0 must be positive"),
                                    ({"hours": -1}, "must be positive"), ({"dt": -1}, "must be positive"),
                                    ({"glucose0": -1}, "glucose0 must be positive")])
def test_growth_rejects_nonpositive(kw, msg):
    m = type("M", (), {"objective": "B"})()
    with pytest.raises(ValueError, match=msg):
        core.simulate_growth(m, **kw)


def test_growth_missing_uptake_flux_means_no_depletion(monkeypatch):
    monkeypatch.setattr(core, "fba", lambda *a, **k: {"objective": 2.0, "fluxes": {}})
    m = type("M", (), {"objective": "B"})()
    r = core.simulate_growth(m, hours=0.0001, glucose0=10.0)
    assert r["trajectory"][0]["glucose"] == 10.0


# ---- regulatory_state ----
def test_regulatory_steady_state_and_converged_flag():
    osc = core.regulatory_state(["A", "B"], [("A", "B", 1), ("B", "A", 1)], {"A": 1})
    assert osc["steady_state"] == {"A": 1.0, "B": 0.0}      # row 12 of the period-2 cycle (even index)
    assert osc["trajectory"][1] == {"A": 0.0, "B": 1.0}
    chain = core.regulatory_state(["A", "B"], [("A", "B", 1)], {"A": 1})
    # t0 (1,0) t1 (0,1) t2 (0,0) t3 (0,0) -> converged at row 3
    assert chain["trajectory"] == [{"A": 1.0, "B": 0.0}, {"A": 0.0, "B": 1.0}, {"A": 0.0, "B": 0.0},
                                   {"A": 0.0, "B": 0.0}]
    assert chain["steady_state"] == {"A": 0.0, "B": 0.0} and chain["converged"] is True
    # v9: converging exactly on the last allowed step is reported converged=True
    edge = core.regulatory_state(["A", "B"], [], {"A": 1}, steps=2)
    assert edge["trajectory"][-1] == edge["trajectory"][-2] and edge["converged"] is True


# ---- environment_response (stubbed fba, hand ratios) ----
def _env_stub(monkeypatch, table, baseline):
    def fake(model, objective=None, bounds_override=None):
        if bounds_override is None:
            return {"status": "optimal", "objective": baseline, "fluxes": {}}
        return table[tuple(sorted(bounds_override))]
    monkeypatch.setattr(core, "fba", fake)


def test_environment_response_phenotype_edges_and_rounding(monkeypatch):
    def res(o, st="optimal"):
        return {"status": st, "objective": o, "fluxes": {"x": o}}
    table = {("a",): res(0.99), ("b",): res(1.0), ("c",): res(69.99), ("d",): res(70.0),
             ("e",): res(100.0 / 3.0), ("f",): res(0.0, "infeasible"), (): res(5.0)}
    _env_stub(monkeypatch, table, 100.0)
    conds = {"a": {"a": 1}, "b": {"b": 1}, "c": {"c": 1}, "d": {"d": 1}, "e": {"e": 1}, "f": {"f": 1}}
    out = core.environment_response(None, conds)["conditions"]
    assert out["a"]["phenotype"] == "no growth"
    assert out["b"]["phenotype"] == "slow growth" and out["b"]["growth_ratio"] == 0.01
    assert out["c"]["phenotype"] == "slow growth"
    assert out["d"]["phenotype"] == "robust growth" and out["d"]["growth_ratio"] == 0.7
    assert out["e"]["growth_ratio"] == 0.333333
    assert out["f"]["phenotype"] == "infeasible - contradictory bounds, no steady-state solution"
    assert out["f"]["status"] == "infeasible"
    assert out["a"]["fluxes"] == {"x": 0.99}


def test_environment_response_zero_baseline_and_defaults(monkeypatch):
    _env_stub(monkeypatch, {("x",): {"status": "optimal", "objective": 0.0, "fluxes": {}}}, 0.0)
    r = core.environment_response(None, {"z": {"x": 1}})
    assert r["conditions"]["z"]["growth_ratio"] == 0.0 and r["conditions"]["z"]["phenotype"] == "no growth"
    monkeypatch.undo()
    # default conditions on the demo model, hand: GLC_UP<=2 -> B = 1.5*2 = 3 -> ratio 0.2
    d = core.environment_response(core.demo_model())
    assert d["baseline_growth"] == 15.0 and list(d["conditions"]) == ["standard", "glucose_limited"]
    assert d["conditions"]["standard"]["growth"] == 15.0 and d["conditions"]["standard"]["growth_ratio"] == 1.0
    assert d["conditions"]["glucose_limited"]["growth"] == 3.0
    assert d["conditions"]["glucose_limited"]["growth_ratio"] == 0.2
    assert d["conditions"]["glucose_limited"]["phenotype"] == "slow growth"


# ---- couple_grn_metabolism / perturbation_screen ----
def test_couple_grn_hand_values_and_errors():
    m = core.demo_model()
    on = core.couple_grn_metabolism(m, ["G"], [("G", "G", 1)], {"RESP": "G"}, {"G": 1})
    assert on["disabled_reactions"] == [] and on["predicted_growth"] == 15.0
    off = core.couple_grn_metabolism(m, ["G"], [], {"RESP": "G"}, {"G": 0})
    assert off["disabled_reactions"] == ["RESP"] and off["predicted_growth"] == 0.0   # no RESP -> NADH balance forces g=0
    assert off["metabolic"]["fluxes"]["RESP"] == 0.0
    with pytest.raises(ValueError, match="unknown reaction"):
        core.couple_grn_metabolism(m, ["G"], [], {"NOPE": "G"}, {"G": 1})
    with pytest.raises(ValueError, match="unknown regulatory gene"):
        core.couple_grn_metabolism(m, ["G"], [], {"RESP": "H"}, {"G": 1})
    osc = core.couple_grn_metabolism(m, ["A", "B"], [("A", "B", 1), ("B", "A", 1)], {"RESP": "A"}, {"A": 1})
    assert len(osc["regulatory"]["trajectory"]) == 13      # default steps=12


def test_perturbation_screen_central_model_hand_order():
    m = core.central_carbon_model()
    r = core.perturbation_screen(m)
    assert r["wild_type_growth"] == 10.1
    assert [x["knocked_out"] for x in r["perturbations"]] == [
        "BIOMASS", "GLC_UP", "GLYCOLYSIS", "O2_UP", "OXPHOS", "TCA", "FERM", "LAC_OUT"]
    assert r["essential_reactions"] == ["BIOMASS", "GLC_UP", "GLYCOLYSIS"]
    one = core.perturbation_screen(m, ["FERM"])
    assert [x["knocked_out"] for x in one["perturbations"]] == ["FERM"] and one["essential_reactions"] == []
    with pytest.raises(ValueError, match="unknown reactions"):
        core.perturbation_screen(m, ["FERM", "NOPE"])


# ---- DEMO_GRN literal and expression params ----
def test_demo_grn_literal():
    assert core.DEMO_GRN["genes"] == ["glucose_sensor", "resp_regulator", "glycolysis_enzyme", "resp_enzyme", "ferm_enzyme"]
    assert core.DEMO_GRN["interactions"] == [("glucose_sensor", "glycolysis_enzyme", 1),
                                             ("glucose_sensor", "resp_regulator", 1),
                                             ("resp_regulator", "resp_enzyme", 1),
                                             ("resp_regulator", "ferm_enzyme", -1)]
    assert core.DEMO_GRN["inputs"] == {"glucose_sensor": 1.0}
    assert core.DEMO_GRN["kcat"] == {"GLYCOLYSIS": 0.2, "TCA": 0.15, "OXPHOS": 0.6, "FERM": 0.5}
    assert core.DEMO_GRN["enzyme_map"] == {"GLYCOLYSIS": "glycolysis_enzyme", "TCA": "resp_enzyme",
                                           "OXPHOS": "resp_enzyme", "FERM": "ferm_enzyme"}


@pytest.mark.parametrize("k", ["mrna_decay", "protein_decay", "K", "n"])
def test_expr_params_positive_required(k):
    for bad in (0, -1):
        with pytest.raises(ValueError, match=f"{k} for 'g' must be positive"):
            core._expr_params(["g"], {"g": {k: bad}})
    assert core._expr_params(["g"], {"g": {k: 1e-9}})["g"][k] == 1e-9


@pytest.mark.parametrize("k", ["basal", "vmax", "translation"])
def test_expr_params_nonnegative(k):
    with pytest.raises(ValueError, match="must be non-negative"):
        core._expr_params(["g"], {"g": {k: -1e-9}})
    assert core._expr_params(["g"], {"g": {k: 0}})["g"][k] == 0


def test_ssa_zero_propensity_stops_without_error():
    r = core.simulate_expression(["A"], [], method="gillespie", points=5, hours=10.0,
                                 params={"A": {"basal": 0.0, "vmax": 0.0}}, seed=1)
    assert r["ssa_events"] == 0 and r["protein"]["A"] == [0.0] * 5 and r["mrna"]["A"] == [0.0] * 5
    assert r["time_h"] == [0.0, 2.5, 5.0, 7.5, 10.0]


# ---- simulate_cell (stubbed expression/pfba/fba) ----
GRN = {"genes": ["E"], "interactions": [], "enzyme_map": {"TCA": "E"}, "kcat": {"TCA": 0.5}, "inputs": {"s": 1.0}}


def _cell_stubs(monkeypatch, protein, pf, ref=10.0, unc=7.0):
    seen = {}
    def expr(genes, interactions, **kw):
        seen["expr"] = (genes, kw)
        return {"steady_state_protein": {"E": protein}, "steady_state_mrna": {"E": 1.0}, "method": "m",
                "protein_noise_cv": None}
    def pfba(model, bounds_override=None, **kw):
        seen["bounds"] = bounds_override; seen["nrx"] = len(model.reactions); return pf
    def fba(model, bounds_override=None, **kw):
        return {"objective": ref if bounds_override is None else unc}
    monkeypatch.setattr(core, "simulate_expression", expr)
    monkeypatch.setattr(core, "pfba", pfba)
    monkeypatch.setattr(core, "fba", fba)
    return seen


def _opt(obj, **fl):
    return {"status": "optimal", "objective": obj, "fluxes": fl}


def test_simulate_cell_defaults_rounding_and_caps(monkeypatch):
    seen = _cell_stubs(monkeypatch, 4.246912, _opt(3.14159, TCA=1.0))
    r = core.simulate_cell(None, GRN)
    genes, kw = seen["expr"]
    assert kw["hours"] == 48.0 and kw["method"] == "ode" and kw["seed"] == 7 and kw["inputs"] == {"s": 1.0}
    assert seen["nrx"] == 8 and seen["bounds"] == {"TCA": (0.0, pytest.approx(2.123456))}
    assert r["enzyme_flux_caps"] == {"TCA": 2.1235}
    assert r["growth_flux"] == 3.14159 and r["growth_rate_per_h"] == 0.3142      # 0.314159 -> 4 dp
    assert r["growth_ratio_vs_reference"] == 0.3142 and r["phenotype"] == "slow growth"
    assert r["growth_without_enzyme_limits"] == 10.0 - 3.0     # no environment: fba(model, {}) path -> stub 7.0
    assert r["enzyme_limited_reactions"] == []
    assert r["perturbation"] == {"knockouts": [], "overexpress": {}, "environment": {}, "inputs": {"s": 1.0}}
    r2 = core.simulate_cell(None, GRN, mu_per_flux=0.5)
    assert r2["growth_rate_per_h"] == 1.5708


def test_simulate_cell_environment_merge_and_inputs(monkeypatch):
    seen = _cell_stubs(monkeypatch, 4.0, _opt(5.0, TCA=1.0, GLC_UP=2.0))
    env = {"TCA": (0.5, 1.5), "GLC_UP": (0.25, 2.0)}
    r = core.simulate_cell(None, GRN, environment=env, inputs={"s": 0.5, "t": 1.0}, knockouts=["E", "E"],
                           overexpress={"E": 2.0})
    assert seen["bounds"] == {"TCA": (0.5, 1.5), "GLC_UP": (0.25, 2.0)}     # TCA cap (0,2) intersected with env
    assert r["perturbation"]["inputs"] == {"s": 0.5, "t": 1.0} and r["perturbation"]["knockouts"] == ["E", "E"]
    assert r["perturbation"]["environment"] == env and r["perturbation"]["overexpress"] == {"E": 2.0}
    assert r["growth_without_enzyme_limits"] == 7.0
    assert r["enzyme_flux_caps"]["GLC_UP"] == 2.0
    assert seen["expr"][1]["inputs"] == {"s": 0.5, "t": 1.0}
    with pytest.raises(ValueError, match="unknown reaction"):
        core.simulate_cell(None, GRN, environment={"NOPE": (0, 1)})


def test_simulate_cell_limiting_reactions(monkeypatch):
    # hi = 0.5*1.0 = 0.5 (<1, so tolerance scale is 1): 0.5e-6 below the cap counts, 1.5e-6 does not
    _cell_stubs(monkeypatch, 1.0, _opt(1.0, TCA=0.5 - 0.5e-6, GLC_UP=2.0))
    r = core.simulate_cell(None, GRN, environment={"GLC_UP": (0, 2)})
    assert r["enzyme_limited_reactions"] == ["TCA"]          # GLC_UP is capped but not enzyme-mapped
    _cell_stubs(monkeypatch, 1.0, _opt(1.0, TCA=0.5 - 1.5e-6))
    assert core.simulate_cell(None, GRN)["enzyme_limited_reactions"] == []
    # hi = 2000 -> tolerance 1e-6*2000 = 2e-3
    _cell_stubs(monkeypatch, 4000.0, _opt(1.0, TCA=1000.0 - 1e-3))
    g = dict(GRN, kcat={"TCA": 0.5})
    assert core.simulate_cell(None, g)["enzyme_limited_reactions"] == ["TCA"]
    _cell_stubs(monkeypatch, 4000.0, {"status": "infeasible", "objective": 0.0, "fluxes": {}})
    r = core.simulate_cell(None, GRN)
    assert r["enzyme_limited_reactions"] == [] and r["status"] == "infeasible"


def test_simulate_cell_zero_reference_and_negative_growth(monkeypatch):
    _cell_stubs(monkeypatch, 1.0, _opt(-2.0, TCA=0.0), ref=0.0)
    r = core.simulate_cell(None, GRN)
    assert r["growth_flux"] == 0.0 and math.copysign(1, r["growth_flux"]) == 1.0
    assert r["growth_ratio_vs_reference"] == 0.0 and r["phenotype"] == "no growth"
    _cell_stubs(monkeypatch, 1.0, _opt(2.0, TCA=0.0), ref=0.0)
    r = core.simulate_cell(None, GRN)
    assert r["growth_ratio_vs_reference"] == 0.0 and r["phenotype"] == "no growth"
    _cell_stubs(monkeypatch, 1.0, _opt(2.0, TCA=0.0), ref=4.0)
    assert core.simulate_cell(None, GRN)["growth_ratio_vs_reference"] == 0.5
    assert core.simulate_cell(None, GRN)["phenotype"] == "slow growth"
