"""Unit 43 v6: tests-only pins for core.py mutant survivors (PARTIAL).
Oracles: hand-derived literals (steady-state algebra worked by hand), stubs with hand-computed expectations."""
import copy
import math
import numpy as np
import pytest
from sugarcode.modules.virtual_cell import core


# ---- central_carbon_model literal pins (independent of the code: copied from the module docstring/stoichiometry) ----
def test_central_carbon_model_literals():
    m = core.central_carbon_model()
    assert m.metabolites == ["GLC", "PYR", "NADH", "ATP", "LAC", "O2"]
    assert m.reactions == ["GLC_UP", "O2_UP", "GLYCOLYSIS", "TCA", "OXPHOS", "FERM", "LAC_OUT", "BIOMASS"]
    exp = [[1, 0, -1, 0, 0, 0, 0, 0],
           [0, 0, 2, -1, 0, -1, 0, -1],
           [0, 0, 2, 4, -1, -1, 0, -1],
           [0, 0, 2, 1, 2.5, 0, 0, -10],
           [0, 0, 0, 0, 0, 1, -1, 0],
           [0, 1, 0, 0, -0.5, 0, 0, 0]]
    assert m.S.tolist() == exp
    assert m.lb.tolist() == [0.0] * 8
    assert m.ub.tolist() == [10, 15, 1000, 1000, 1000, 1000, 1000, 1000]
    assert m.objective == "BIOMASS"


# hand solution: OXPHOS=5*TCA, ATP: 2g+13.5T=10B, O2 caps OXPHOS<=30 -> T=6, g=10, B=10.1, FERM=LAC_OUT=3.9
WT = {"GLC_UP": 10.0, "O2_UP": 15.0, "GLYCOLYSIS": 10.0, "TCA": 6.0, "OXPHOS": 30.0,
      "FERM": 3.9, "LAC_OUT": 3.9, "BIOMASS": 10.1}


def test_fba_and_pfba_wild_type_hand_values():
    m = core.central_carbon_model()
    f = core.fba(m)
    assert f["status"] == "optimal" and f["objective"] == 10.1
    for k, v in WT.items():
        assert f["fluxes"][k] == pytest.approx(v, abs=1e-6)
    p = core.pfba(m)
    assert p["objective"] == 10.1 and p["method"] == "pFBA"
    for k, v in WT.items():
        assert p["fluxes"][k] == pytest.approx(v, abs=1e-6)
    assert p["total_flux"] == pytest.approx(88.9, abs=1e-6)


def test_fba_rounding_is_six_places_and_infeasible_shape():
    m = core.central_carbon_model()
    # FERM knocked out: hand solution T=6, g=47/6, B=29/3 -> 9.666667 (6 dp), not 9.6666667
    f = core.fba(m, bounds_override={"FERM": (0.0, 0.0)})
    assert f["objective"] == 9.666667
    assert f["fluxes"]["GLC_UP"] == 7.833333
    p = core.pfba(m, bounds_override={"FERM": (0.0, 0.0)})
    assert p["fluxes"]["BIOMASS"] == 9.666667
    assert p["total_flux"] == 76.333333
    bad = core.fba(m, bounds_override={"GLC_UP": (5.0, 1.0)})
    assert bad["status"] == "infeasible" and bad["objective"] == 0.0
    assert bad["fluxes"] == {r: 0.0 for r in m.reactions}


def test_gene_knockout_oxphos_hand_values():
    r = core.gene_knockout(core.central_carbon_model(), "OXPHOS")
    # no respiration: T=0, B=0.2*g=2, FERM=18
    assert r["wild_type_objective"] == 10.1
    assert r["knockout_objective"] == 2.0
    assert r["growth_ratio"] == 0.198
    assert r["lethality"] == "impaired"
    assert r["rerouting"] == {"O2_UP": -15.0, "TCA": -6.0, "FERM": 14.1, "LAC_OUT": 14.1, "BIOMASS": -8.1}
    assert r["knockout_fluxes"]["OXPHOS"] == 0.0


def test_gene_knockout_ferm_viable_and_glyc_lethal_hand_values():
    m = core.central_carbon_model()
    r = core.gene_knockout(m, "FERM")
    assert r["knockout_objective"] == 9.666667
    assert r["growth_ratio"] == 0.9571
    assert r["lethality"] == "viable"
    assert r["rerouting"] == {"GLC_UP": -2.1667, "GLYCOLYSIS": -2.1667, "LAC_OUT": -3.9, "BIOMASS": -0.4333}
    g = core.gene_knockout(m, "GLYCOLYSIS")
    assert g["knockout_objective"] == 0.0 and g["growth_ratio"] == 0.0
    assert g["lethality"] == "lethal" and g["rerouting"] == {} and g["knockout_fluxes"] is None
    with pytest.raises(ValueError, match="unknown reaction"):
        core.gene_knockout(m, "NOPE")


# ---- gene_knockout thresholds/rounding via stubbed pfba (hand arithmetic) ----
def _ko(monkeypatch, wt_obj, ko_obj, wt_fl, ko_fl, reaction="X"):
    def fake(model, objective=None, bounds_override=None, optimum_fraction=1.0):
        if bounds_override is None:
            return {"objective": wt_obj, "fluxes": wt_fl}
        return {"objective": ko_obj, "fluxes": ko_fl}
    monkeypatch.setattr(core, "pfba", fake)
    model = type("M", (), {"reactions": ["X", "Y", "Z"]})()
    return core.gene_knockout(model, reaction)


@pytest.mark.parametrize("wt,ko,label", [(100.0, 0.99, "lethal"), (100.0, 1.0, "impaired"),
                                          (100.0, 69.99, "impaired"), (100.0, 70.0, "viable")])
def test_lethality_boundaries(monkeypatch, wt, ko, label):
    r = _ko(monkeypatch, wt, ko, {"X": 0.0, "Y": 1.0, "Z": 1.0}, {"X": 0.0, "Y": 1.0, "Z": 1.0})
    assert r["lethality"] == label


def test_gene_knockout_zero_and_small_wild_type_and_negative_ko(monkeypatch):
    fl = {"X": 0.0, "Y": 1.0, "Z": 1.0}
    r = _ko(monkeypatch, 0.0, 0.0, fl, fl)
    assert r["growth_ratio"] == 0.0 and r["lethality"] == "lethal"
    r = _ko(monkeypatch, 0.5, 0.5, fl, fl)
    assert r["growth_ratio"] == 1.0 and r["lethality"] == "viable"
    r = _ko(monkeypatch, 10.0, -1.0, fl, fl)
    assert r["knockout_objective"] == 0.0 and math.copysign(1, r["knockout_objective"]) == 1.0
    assert math.copysign(1, r["growth_ratio"]) == 1.0


def test_gene_knockout_rounding_and_rerouting_filter(monkeypatch):
    r = _ko(monkeypatch, 3.0, 1.0, {"X": 0, "Y": 1.0, "Z": 1.0},
            {"X": 0, "Y": 1.123456, "Z": 1.0})
    assert r["growth_ratio"] == 0.3333 and r["knockout_objective"] == 1.0
    assert r["rerouting"] == {"Y": 0.1235}
    r = _ko(monkeypatch, 3.0, 0.1234567, {"X": 0, "Y": 1.0, "Z": 1.0}, {"X": 0, "Y": 1.0, "Z": 1.0})
    assert r["knockout_objective"] == 0.123457
    # |diff| 2**-20 (< 1e-6) dropped, 2**-19 (> 1e-6) kept; the knocked-out reaction itself is excluded
    r = _ko(monkeypatch, 3.0, 3.0, {"X": 0.0, "Y": 1.0, "Z": 1.0},
            {"X": 5.0, "Y": 1.0 + 2.0 ** -20, "Z": 1.0 + 2.0 ** -19})
    assert list(r["rerouting"]) == ["Z"]
    # -2e-6 rounds to -0.0 at 4 dp; reported as +0.0
    r = _ko(monkeypatch, 3.0, 3.0, {"X": 0, "Y": 1.0, "Z": 1.0}, {"X": 0, "Y": 1.0 - 2e-6, "Z": 1.0})
    assert r["rerouting"] == {"Y": 0.0} and math.copysign(1, r["rerouting"]["Y"]) == 1.0


# ---- expression_perturbation_screen via stubbed simulate_cell ----
def _cell(prot, gf, fl):
    return {"expression": {"steady_state_protein": prot}, "growth_flux": gf, "fluxes": fl}


def _screen(monkeypatch, wt, perts, genes, **kw):
    def fake(model, grn=None, knockouts=None, overexpress=None):
        if not knockouts and not overexpress:
            return wt
        g = (knockouts or list(overexpress))[0]
        return perts[g]
    monkeypatch.setattr(core, "simulate_cell", fake)
    model = type("M", (), {"reactions": ["r1", "r2"]})()
    return core.expression_perturbation_screen(model, {"genes": genes}, **kw)


def test_expression_screen_hand_values(monkeypatch):
    wt = _cell({"A": 1.0, "B": 3.0, "C": 0.0}, 100.0, {"r1": 1.0, "r2": 2.0})
    perts = {
        # B: (1+1)/(3+1)=1/2 -> -1 ; A: (0+1)/(1+1) -> -1 ; C: (0.41421356237+1)/(0+1) -> log2 = 0.5
        "A": _cell({"A": 0.0, "B": 1.0, "C": 0.41421356237}, 50.0, {"r1": 1.5, "r2": 2.0}),
        # B knockout: growth 1.0/100 = 0.01 exactly -> flux_changes kept; B 3.0 -> 0.5 : log2(1.5/4)=-1.415
        "B": _cell({"A": 1.0, "B": 0.0, "C": 0.5}, 1.0, {"r1": 1.0 + 2.0 ** -19, "r2": 2.0 - 2e-6}),
        # C: growth 0.99/100 -> <0.01 -> no flux changes; negative growth clamps
        "C": _cell({"A": 1.0, "B": 3.0, "C": 0.0}, 0.99, {"r1": 9.0, "r2": 9.0}),
    }
    out = _screen(monkeypatch, wt, perts, ["A", "B", "C"])
    assert out["wild_type"] == {"growth_flux": 100.0, "protein": {"A": 1.0, "B": 3.0, "C": 0.0}}
    rows = {r["gene"]: r for r in out["perturbations"]}
    a = rows["A"]
    assert a["protein_log2fc"] == {"A": -1.0, "B": -1.0, "C": 0.5}
    assert a["downstream_changed"] == ["B", "C"]          # |0.5| included (>=), self excluded
    assert a["growth_ratio"] == 0.5 and a["phenotype"] == "slow growth"
    assert a["flux_changes"] == {"r1": 0.5}
    assert a["perturbation"] == "knockout"
    b = rows["B"]
    assert b["protein_log2fc"]["C"] == round(math.log2(1.5 / 1.0), 4) == 0.585
    assert b["protein_log2fc"]["B"] == -2.0
    assert b["growth_ratio"] == 0.01 and b["phenotype"] == "slow growth"
    assert list(b["flux_changes"]) == ["r1", "r2"] or list(b["flux_changes"]) == ["r1"]
    assert "r1" in b["flux_changes"]
    assert b["flux_changes"].get("r2", 0.0) == 0.0 and math.copysign(1, b["flux_changes"].get("r2", 0.0)) == 1.0
    c = rows["C"]
    assert c["growth_ratio"] == 0.99 / 100 and False or c["growth_ratio"] == 0.0099
    assert c["phenotype"] == "no growth" and c["flux_changes"] == {}
    assert [r["gene"] for r in out["perturbations"]] == ["C", "B", "A"]  # sorted by growth ratio


def test_expression_screen_zero_wt_growth_and_negative_pert(monkeypatch):
    wt = _cell({"A": 1.0}, 0.0, {"r1": 1.0, "r2": 1.0})
    perts = {"A": _cell({"A": 0.0}, 5.0, {"r1": 1.0, "r2": 1.0})}
    out = _screen(monkeypatch, wt, perts, ["A"])
    assert out["perturbations"][0]["growth_ratio"] == 0.0
    wt = _cell({"A": 1.0}, 0.5, {"r1": 1.0, "r2": 1.0})
    perts = {"A": _cell({"A": 1.0}, 0.5, {"r1": 1.0, "r2": 1.0})}
    out = _screen(monkeypatch, wt, perts, ["A"])
    assert out["perturbations"][0]["growth_ratio"] == 1.0
    perts = {"A": _cell({"A": 1.0}, -3.0, {"r1": 1.0, "r2": 1.0})}
    r = _screen(monkeypatch, wt, perts, ["A"])["perturbations"][0]
    assert r["growth_ratio"] == 0.0 and math.copysign(1, r["growth_ratio"]) == 1.0


def test_expression_screen_overexpress_label(monkeypatch):
    wt = _cell({"A": 1.0}, 10.0, {"r1": 1.0, "r2": 1.0})
    perts = {"A": _cell({"A": 3.0}, 10.0, {"r1": 1.0, "r2": 1.0})}
    r = _screen(monkeypatch, wt, perts, ["A"], overexpress_factor=2)["perturbations"][0]
    assert r["perturbation"] == "overexpress x2" and r["protein_log2fc"] == {"A": 1.0}


# ---- virtual_cell_report default wiring ----
def test_report_default_wiring(monkeypatch):
    seen = {}
    def couple(model, genes, interactions, rules, initial=None, steps=12):
        seen["couple"] = (genes, interactions, rules, initial); return "C"
    def growth(model, hours=8.0, **kw):
        seen["hours"] = hours; return "G"
    monkeypatch.setattr(core, "couple_grn_metabolism", couple)
    monkeypatch.setattr(core, "simulate_growth", growth)
    monkeypatch.setattr(core, "environment_response", lambda m, c=None: "E")
    monkeypatch.setattr(core, "perturbation_screen", lambda m, p=None: "P")
    monkeypatch.setattr(core, "simulate_cell", lambda m, *a, **k: "S")
    monkeypatch.setattr(core, "expression_perturbation_screen", lambda m, *a, **k: "X")
    out = core.virtual_cell_report()
    assert seen["couple"] == (["carbon_sensor", "respiration_gene"],
                              [("carbon_sensor", "carbon_sensor", 1), ("carbon_sensor", "respiration_gene", 1)],
                              {"OXPHOS": "respiration_gene"}, {"carbon_sensor": 1})
    assert seen["hours"] == 2
    assert out["baseline"]["objective"] == 10.1
    assert out["limitations"] == ["predictions depend on model bounds, kcat values and network assumptions",
                                  "no wet-lab validation was performed"]
    assert [out[k] for k in ("regulatory_metabolic_coupling", "environment", "growth", "perturbation_screen",
                             "expression_coupled_cell", "expression_knockout_screen")] == ["C", "E", "G", "P", "S", "X"]


# ---- kcat boundary, growth, regulatory defaults, SSA ----
def test_kcat_boundary():
    m = core.central_carbon_model()
    for bad in (0, -1, -1e-9):
        with pytest.raises(ValueError, match="must be positive"):
            core.expression_to_bounds(m, {"E": 1.0}, {"TCA": "E"}, {"TCA": bad})
    with pytest.raises(ValueError, match="must be positive"):
        core.expression_to_bounds(m, {"E": 1.0}, {"TCA": "E"}, {})
    b = core.expression_to_bounds(m, {"E": 2.0}, {"TCA": "E"}, {"TCA": 0.5})
    assert b == {"TCA": (0.0, 1.0)}
    b = core.expression_to_bounds(m, {"E": 2000.0}, {"TCA": "E"}, {"TCA": 1.0})
    assert b == {"TCA": (0.0, 1000.0)}


def _fake_fba(rec):
    def fake(model, objective=None, bounds_override=None):
        rec.append(bounds_override)
        return {"objective": 2.0, "fluxes": {"GLC_UP": 1.0}}
    return fake


def test_simulate_growth_exhausted_path_hand_values(monkeypatch):
    rec = []
    monkeypatch.setattr(core, "fba", _fake_fba(rec))
    m = type("M", (), {"objective": "BIOMASS"})()
    r = core.simulate_growth(m, glucose0=1e-5)
    # cap = 1e-5/0.01/0.25 = 0.004 ; biomass 0.01*(1+0.2*0.25)=0.0105 ; glucose -> max(0, 1e-5-2.625e-5)=0
    assert rec[0]["GLC_UP"] == (0, pytest.approx(0.004))
    assert len(r["trajectory"]) == 1 and r["glucose_exhausted"] is True
    row = r["trajectory"][0]
    assert row == {"t": 0.0, "biomass": 0.0105, "glucose": 0.0, "mu": 2.0, "mu_per_h": 0.2,
                   "doubling_time_h": 3.4657}
    assert r["final_biomass"] == 0.0105 and r["mu_per_flux"] == 0.1
    assert r["model_objective"] == "BIOMASS"


def test_simulate_growth_defaults_and_inclusive_end(monkeypatch):
    assert core.simulate_growth.__defaults__ == (8.0, 0.25, 10.0, 0.1)
    rec = []
    monkeypatch.setattr(core, "fba", _fake_fba(rec))
    m = type("M", (), {"objective": "BIOMASS"})()
    r = core.simulate_growth(m, hours=0.5)
    assert [x["t"] for x in r["trajectory"]] == [0.0, 0.25, 0.5]
    assert r["glucose_exhausted"] is False
    assert rec[0]["GLC_UP"] == (0, 10)          # min(10, 10/0.01/0.25=4000)
    assert r["final_biomass"] == pytest.approx(0.01 * 1.05 ** 3, abs=6e-6)
    full = core.simulate_growth(m)
    assert len(full["trajectory"]) == 33        # t = 0, 0.25, ..., 8.0 inclusive


def test_simulate_growth_mu_zero_has_no_doubling(monkeypatch):
    monkeypatch.setattr(core, "fba", lambda *a, **k: {"objective": 0.0, "fluxes": {}})
    m = type("M", (), {"objective": "B"})()
    r = core.simulate_growth(m, hours=0.25)
    assert r["trajectory"][0]["doubling_time_h"] is None and r["trajectory"][0]["mu_per_h"] == 0.0


def test_regulatory_defaults_and_threshold_equality():
    assert core.regulatory_state.__defaults__ == (None, 12, 0.5)
    r = core.regulatory_state(["A", "B"], [("A", "B", 0.5)], {"A": 1})
    assert r["trajectory"][1] == {"A": 0.0, "B": 1.0}       # signal exactly 0.5 >= 0.5 fires
    r = core.regulatory_state(["A", "B"], [("A", "B", 0.4999)], {"A": 1})
    assert r["trajectory"][1] == {"A": 0.0, "B": 0.0}
    osc = core.regulatory_state(["A", "B"], [("A", "B", 1), ("B", "A", 1)], {"A": 1})
    assert len(osc["trajectory"]) == 13 and osc["converged"] is False   # default steps=12


def test_ssa_points_boundary_and_reproducibility():
    g = ["A"]
    one = core.simulate_expression(g, [], method="gillespie", points=1, hours=5.0, seed=3)
    assert one["ssa_events"] == 1 and one["time_h"] == [0.0]  # characterization: one event fires after the final sample is stored
    assert one["protein"] == {"A": [0.0]} and one["mrna"] == {"A": [0.0]}
    a = core.simulate_expression(g, [], method="gillespie", points=9, hours=48.0, seed=5)
    b = core.simulate_expression(g, [], method="gillespie", points=9, hours=48.0, seed=5)
    assert a == b and a["seed"] == 5 and a["ssa_events"] >= 1
    assert a["mrna"]["A"][0] == 0.0 and a["protein"]["A"][0] == 0.0   # t=0 sample is the empty initial state
    assert len(a["time_h"]) == 9 and a["time_h"][-1] == 48.0
    d = core.simulate_expression(g, [], points=97)
    assert d["seed"] is None and d["ssa_events"] is None
