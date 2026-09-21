from sugarcode.modules.virtual_cell import demo_model, fba, gene_knockout, simulate_growth


def test_fba_optimal_growth():
    m = demo_model()
    r = fba(m)
    assert r["status"] == "optimal"
    assert r["objective"] > 0
    assert r["fluxes"]["GLC_UP"] > 0


def test_knockout_lethality_call():
    m = demo_model()
    ko = gene_knockout(m, "GLYCOLYSIS")
    assert ko["knockout_objective"] < ko["wild_type_objective"]
    assert ko["lethality"] in ("lethal", "impaired", "viable")


def test_growth_simulation():
    m = demo_model()
    r = simulate_growth(m, hours=2.0)
    assert r["trajectory"] and r["final_biomass"] > 0
