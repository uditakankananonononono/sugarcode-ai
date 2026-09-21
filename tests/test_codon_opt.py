from sugarcode.modules.codon_opt import optimize, tasep_simulate, metabolic_load


def test_optimize_improves_cai():
    r = optimize("MKTLLLGAAVVVGGGDES", host="ecoli_k12")
    assert r["cai_after"] >= r["cai_before"]
    assert 0.2 < r["gc_content"] < 0.8
    assert r["chi_score"] >= 0
    assert r["tasep"]["codons"] == 18


def test_tasep_produces_output():
    r = tasep_simulate("ATG" + "GCT" * 40 + "TAA")
    assert r["proteins_completed"] >= 1
    assert 0 < r["mean_density"] < 1


def test_metabolic_load_burden_class():
    r = metabolic_load("ATG" + "AAA" * 300, copies=500)
    assert r["burden_class"] in ("low", "moderate", "high")
    assert r["fba_constraint_row"]["stoichiometry"]["ATP"] < 0
