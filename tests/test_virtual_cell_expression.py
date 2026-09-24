import numpy as np
import pytest
from sugarcode.modules.virtual_cell import (DEMO_GRN, central_carbon_model, demo_model, expression_perturbation_screen,
                                            expression_to_bounds, fba, gene_knockout, pfba, simulate_cell,
                                            simulate_expression, simulate_growth, virtual_cell_report)

G, I, IN = DEMO_GRN["genes"], DEMO_GRN["interactions"], DEMO_GRN["inputs"]


def test_expression_ode_matches_analytic_steady_state():
    # single constitutive gene: p* = translation * basal-plus-vmax / (mrna_decay * protein_decay)
    r = simulate_expression(["g"], [], hours=200, points=201)
    assert r["steady_state_protein"]["g"] == pytest.approx(5 * 1.05 / (0.5 * 0.1), rel=1e-3)
    assert r["steady_state_mrna"]["g"] == pytest.approx(1.05 / 0.5, rel=1e-3)
    assert len(r["protein"]["g"]) == len(r["time_h"]) == 201


def test_activation_and_repression_are_directional():
    r = simulate_expression(G, I, inputs=IN)
    p = r["steady_state_protein"]
    off = simulate_expression(G, I, inputs=IN, knockouts=["resp_regulator"])["steady_state_protein"]
    assert off["resp_regulator"] == 0
    assert off["resp_enzyme"] < p["resp_enzyme"] / 5      # loses its activator
    assert off["ferm_enzyme"] > p["ferm_enzyme"] * 2      # loses its repressor
    over = simulate_expression(G, I, inputs=IN, overexpress={"glycolysis_enzyme": 2})["steady_state_protein"]
    assert over["glycolysis_enzyme"] == pytest.approx(2 * p["glycolysis_enzyme"], rel=1e-3)


def test_gillespie_is_seeded_and_reports_noise():
    a = simulate_expression(G, I, inputs=IN, method="gillespie", seed=3, hours=24)
    b = simulate_expression(G, I, inputs=IN, method="gillespie", seed=3, hours=24)
    assert a["protein"] == b["protein"] and a["ssa_events"] > 100
    assert all(v >= 0 for v in a["protein_noise_cv"].values())
    assert all(float(x).is_integer() for x in a["protein"]["glucose_sensor"])


def test_knockout_rerouting_is_real_flux_delta_not_negated_wild_type():
    m = central_carbon_model()
    wt = pfba(m)["fluxes"]
    ko = gene_knockout(m, "OXPHOS")
    assert ko["lethality"] == "impaired"
    assert ko["rerouting"]["FERM"] > 0 and ko["rerouting"]["LAC_OUT"] > 0      # fermentation takes over
    assert ko["rerouting"]["FERM"] != pytest.approx(-wt["FERM"])
    assert all(abs(x) < 1e-6 for x in m.S @ np.array(list(ko["knockout_fluxes"].values())))
    lethal = gene_knockout(m, "GLYCOLYSIS")
    assert lethal["lethality"] == "lethal" and lethal["rerouting"] == {} and lethal["knockout_objective"] == 0
    assert str(lethal["growth_ratio"]) == "0.0"


def test_expression_changes_flux_and_growth():
    wt = simulate_cell()
    assert wt["phenotype"] == "robust growth" and wt["growth_flux"] > 0
    ko = simulate_cell(knockouts=["resp_regulator"])
    assert ko["expression"]["steady_state_protein"]["resp_enzyme"] < 10
    assert ko["growth_flux"] < wt["growth_flux"] * 0.5 and "OXPHOS" in ko["enzyme_limited_reactions"]
    assert ko["fluxes"]["FERM"] > wt["fluxes"]["FERM"]          # derepressed fermentation carries NADH
    low = simulate_cell(inputs={"glucose_sensor": 0.3})
    assert low["growth_flux"] < wt["growth_flux"]
    starved = simulate_cell(environment={"GLC_UP": (0, 2)})
    assert starved["phenotype"] == "slow growth"


def test_expression_screen_reports_system_wide_effects():
    s = expression_perturbation_screen()
    rows = {r["gene"]: r for r in s["perturbations"]}
    assert rows["glycolysis_enzyme"]["phenotype"] == "no growth" and rows["glycolysis_enzyme"]["flux_changes"] == {}
    assert set(rows["glucose_sensor"]["downstream_changed"]) >= {"glycolysis_enzyme", "resp_regulator"}
    assert rows["ferm_enzyme"]["phenotype"] == "robust growth"
    assert s["perturbations"][0]["growth_ratio"] <= s["perturbations"][-1]["growth_ratio"]


def test_growth_rate_has_physical_units():
    r = simulate_growth(central_carbon_model(), hours=1)
    row = r["trajectory"][0]
    assert row["mu_per_h"] == pytest.approx(row["mu"] * 0.1) and row["doubling_time_h"] > 0
    assert r["units"]["mu_per_h"] == "1/h"


def test_report_includes_expression_layer_and_legacy_model_unchanged():
    r = virtual_cell_report()
    assert r["expression_coupled_cell"]["expression"]["steady_state_protein"]
    assert r["expression_knockout_screen"]["perturbations"]
    assert fba(demo_model())["objective"] == 15.0


def test_expression_validation():
    with pytest.raises(ValueError, match="unknown genes"):
        simulate_expression(["a"], [("b", "a", 1)])
    with pytest.raises(ValueError, match="perturbation"):
        simulate_expression(["a"], [], knockouts=["z"])
    with pytest.raises(ValueError, match="method"):
        simulate_expression(["a"], [], method="magic")
    with pytest.raises(ValueError, match="unknown reaction"):
        expression_to_bounds(central_carbon_model(), {"e": 1}, {"FAKE": "e"}, {"FAKE": 1})
    with pytest.raises(ValueError, match="unknown reaction"):
        gene_knockout(central_carbon_model(), "FAKE")
