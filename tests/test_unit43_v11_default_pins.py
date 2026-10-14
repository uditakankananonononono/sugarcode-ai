"""Unit 43 v11: tests-only default/rounding pins for core.py. Hand-derived expectations, stubs record arguments."""
import pytest
from sugarcode.modules.virtual_cell import core


def _opt(obj, **fl):
    return {"status": "optimal", "objective": obj, "fluxes": fl}


def test_environment_default_conditions_exact_bounds(monkeypatch):
    seen = []
    def fake(model, objective=None, bounds_override=None):
        seen.append(bounds_override)
        return {"status": "optimal", "objective": 4.0, "fluxes": {}}
    monkeypatch.setattr(core, "fba", fake)
    r = core.environment_response(None)
    assert seen == [None, {}, {"GLC_UP": (0, 2)}]
    assert list(r["conditions"]) == ["standard", "glucose_limited"]
    assert seen[2]["GLC_UP"][0] == 0 and seen[2]["GLC_UP"][1] == 2


def _cell(monkeypatch, pf, ref):
    monkeypatch.setattr(core, "simulate_expression", lambda genes, ix, **kw: {
        "steady_state_protein": {"E": 1.0}, "steady_state_mrna": {"E": 1.0}, "method": "m", "protein_noise_cv": None})
    monkeypatch.setattr(core, "pfba", lambda model, bounds_override=None, **kw: pf)
    monkeypatch.setattr(core, "fba", lambda model, bounds_override=None, **kw: {"objective": ref})
    grn = {"genes": ["E"], "interactions": [], "enzyme_map": {"TCA": "E"}, "kcat": {"TCA": 0.5}}
    return core.simulate_cell(None, grn)


@pytest.mark.parametrize("ref,growth,ratio,pheno", [
    (0.5, 0.25, 0.5, "slow growth"), (1.0, 0.5, 0.5, "slow growth"), (0.25, 0.25, 1.0, "robust growth"),
    (1e-3, 5e-4, 0.5, "slow growth")])
def test_simulate_cell_small_positive_reference(monkeypatch, ref, growth, ratio, pheno):
    r = _cell(monkeypatch, _opt(growth, TCA=0.0), ref)
    assert r["growth_ratio_vs_reference"] == ratio and r["phenotype"] == pheno


def test_simulate_cell_ratio_four_decimals(monkeypatch):
    r = _cell(monkeypatch, _opt(1.0, TCA=0.0), 3.0)      # 1/3 -> 0.3333
    assert r["growth_ratio_vs_reference"] == 0.3333


def _report_stubs(monkeypatch):
    seen = {}
    def couple(model, genes, interactions, rules, initial=None, steps=12):
        seen["rules"] = rules; seen["initial"] = initial; return "C"
    monkeypatch.setattr(core, "couple_grn_metabolism", couple)
    monkeypatch.setattr(core, "simulate_growth", lambda m, hours=8.0, **k: "G")
    monkeypatch.setattr(core, "environment_response", lambda m, c=None: "E")
    monkeypatch.setattr(core, "perturbation_screen", lambda m, p=None: "P")
    monkeypatch.setattr(core, "simulate_cell", lambda m, *a, **k: "S")
    monkeypatch.setattr(core, "expression_perturbation_screen", lambda m, *a, **k: "X")
    return seen


def test_report_default_rules_resp_vs_oxphos(monkeypatch):
    seen = _report_stubs(monkeypatch)
    genes = ["a", "b", "c"]; ix = [("a", "b", 1)]
    core.virtual_cell_report(core.demo_model(), genes=genes, interactions=ix)       # has RESP, no OXPHOS
    assert seen["rules"] == {"RESP": "c"} and seen["initial"] == {"a": 1}
    core.virtual_cell_report(core.central_carbon_model(), genes=genes, interactions=ix)  # OXPHOS only
    assert seen["rules"] == {"OXPHOS": "c"}
    core.virtual_cell_report(core.central_carbon_model(), genes=genes, interactions=ix, reaction_rules={"TCA": "a"})
    assert seen["rules"] == {"TCA": "a"}


def test_expression_screen_rounding_fifth_digit(monkeypatch):
    def c(prot, gf, fl): return {"expression": {"steady_state_protein": prot}, "growth_flux": gf, "fluxes": fl}
    wt = c({"A": 1.0}, 3.0, {"r1": 1.0, "r2": 1.0})
    pert = c({"A": 1.0}, 1.0, {"r1": 1.123456, "r2": 1.0})
    monkeypatch.setattr(core, "simulate_cell", lambda model, grn=None, knockouts=None, overexpress=None: pert if knockouts else wt)
    model = type("M", (), {"reactions": ["r1", "r2"]})()
    row = core.expression_perturbation_screen(model, {"genes": ["A"]})["perturbations"][0]
    assert row["growth_ratio"] == 0.3333            # 1/3 at 4 dp
    assert row["flux_changes"] == {"r1": 0.1235}    # 0.123456 at 4 dp
    pert2 = c({"A": 1.3}, 3.0, {"r1": 1.0, "r2": 1.0})   # log2(2.3/2) = 0.201634 -> 0.2016
    monkeypatch.setattr(core, "simulate_cell", lambda model, grn=None, knockouts=None, overexpress=None: pert2 if knockouts else wt)
    row = core.expression_perturbation_screen(model, {"genes": ["A"]})["perturbations"][0]
    assert row["protein_log2fc"] == {"A": 0.2016}


def test_couple_repressed_gene_exact_bounds(monkeypatch):
    seen = {}
    def fake(model, objective=None, bounds_override=None):
        seen["b"] = bounds_override; return {"objective": 0.0, "status": "optimal", "fluxes": {}}
    monkeypatch.setattr(core, "fba", fake)
    m = core.demo_model()
    r = core.couple_grn_metabolism(m, ["G"], [], {"RESP": "G", "FERM": "G"}, {"G": 0})
    assert seen["b"] == {"RESP": (0.0, 0.0), "FERM": (0.0, 0.0)}
    assert r["disabled_reactions"] == ["FERM", "RESP"]
    r = core.couple_grn_metabolism(m, ["G"], [("G", "G", 1)], {"RESP": "G"}, {"G": 1})
    assert seen["b"] == {} and r["disabled_reactions"] == []
