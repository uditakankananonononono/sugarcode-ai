import pytest

from sugarcode.modules.microbiome_exp import analyze_16s
from sugarcode.modules.microbiome_rx import simulate_community, design_intervention
from sugarcode.modules.micro_tx import pair_therapeutic
from sugarcode.modules.microaiverse import cultivation_plan
from sugarcode.modules.riboswitch import design_riboswitch
from sugarcode.modules.phage_tx import match_phages, evolve_cocktail
from sugarcode.modules.phage_designer import design_fiber, design_lysin

GUT = {"Faecalibacterium": 1500, "Bacteroides": 3000, "Lactobacillus": 800,
       "Akkermansia": 200, "Escherichia": 400, "Bifidobacterium": 600}


def test_16s_diversity_metrics():
    r = analyze_16s(GUT)
    assert r["alpha_diversity"]["richness"] == 6
    assert 0.0 < r["alpha_diversity"]["shannon"] < 2.5
    assert abs(sum(r["relative_abundance"].values()) - 1.0) < 0.01
    assert r["dominant_genera"][0] == "Bacteroides"
    assert r["functional_potential"]  # butyrate etc.


def test_16s_dysbiosis_flags():
    dysbiotic = {"Escherichia": 9000, "Bacteroides": 500}
    r = analyze_16s(dysbiotic)
    flags = {f["flag"] for f in r["disease_correlations"]}
    assert "low_diversity" in flags
    assert "Escherichia_blooms" in flags
    assert "Faecalibacterium_depleted" in flags


def test_16s_rejects_empty():
    with pytest.raises(ValueError):
        analyze_16s({})


def test_community_simulation_antibiotic_kills_target():
    init = {"Bacteroides": 1.0, "Escherichia": 1.0, "Lactobacillus": 1.0}
    base = simulate_community(init, days=7)
    abx = simulate_community(init, days=7, antibiotic="ciprofloxacin")
    assert abx["final_relative"]["Escherichia"] < base["final_relative"]["Escherichia"]


def test_community_metabolites_present():
    init = {"Faecalibacterium": 1.0, "Bacteroides": 1.0}
    r = simulate_community(init, days=7, diet={"fiber": 2.0, "sugar": 0.5})
    assert "butyrate" in r["metabolite_flux"]
    assert r["dysbiosis_shift"]


def test_intervention_ranks_options():
    r = design_intervention("dysbiosis")
    assert len(r["interventions_ranked"]) >= 2
    assert r["recommended"]["benefit_score"] >= r["interventions_ranked"][-1]["benefit_score"]


def test_micro_tx_pairs_strain_prebiotic():
    r = pair_therapeutic("IBD")
    assert len(r["pairs"]) >= 1
    for p in r["pairs"]:
        assert p["strain"] and p["prebiotic"] and p["rationale"]
    assert "community_simulation" in r


def test_micro_tx_unknown_indication():
    with pytest.raises(KeyError):
        pair_therapeutic("hangnail")


def test_microaiverse_syntroph_needs_partner():
    r = cultivation_plan("Candidatus_X", lifestyle="syntroph",
                         genome_gaps=["vitamin_B12", "amino_acid_biosynthesis"])
    assert r["coculture_partners"]  # gaps force cross-feeding
    assert r["media_recipe"]["supplements"]
    assert 0.0 < r["predicted_success"] <= 1.0


def test_microaiverse_unknown_lifestyle():
    with pytest.raises(KeyError):
        cultivation_plan("X", lifestyle="cloud_dweller")


def test_riboswitch_on_vs_off():
    on = design_riboswitch("theophylline", mode="on")
    off = design_riboswitch("theophylline", mode="off")
    assert on["ligand"] == "theophylline"
    assert on["predicted_dynamic_range_fold"] >= 1.2
    assert on["predicted_dynamic_range_fold"] != off["predicted_dynamic_range_fold"]
    assert on["leakiness"] == pytest.approx(1.0 / on["predicted_dynamic_range_fold"], abs=1e-3)


def test_riboswitch_unknown_ligand():
    with pytest.raises(KeyError):
        design_riboswitch("coffee", mode="on")


def test_phage_match_ecoli():
    r = match_phages("Escherichia_coli")
    assert r["best"]["phage"] == "T4"  # highest burst among lytic E. coli phages
    assert all("resistance_risk" in m for m in r["matches"])


def test_phage_match_unknown_pathogen():
    with pytest.raises(KeyError):
        match_phages("Vampirovibrio")


def test_cocktail_suppresses_escape():
    single = match_phages("Escherichia_coli")
    r = evolve_cocktail("Escherichia_coli", rounds=3)
    assert len(r["cocktail"]) >= 1
    assert r["final_escape_rate"] < 0.5
    assert len(r["receptor_coverage"]) >= 1


def test_fiber_retargeting():
    r = design_fiber("LamB")
    assert r["predicted_binding_nM"] == 8
    assert r["predicted_adsorption_rate"] > 0.5
    assert r["off_target_risk"] == "low"


def test_fiber_unknown_receptor():
    with pytest.raises(KeyError):
        design_fiber("madeup_receptor")


def test_lysin_gram_negative_needs_strategy():
    pos = design_lysin("gram+", domains=["CHAP", "amidase"])
    neg = design_lysin("gram-", domains=["amidase"])
    assert pos["outer_membrane_strategy"] == "not needed (gram+)"
    assert "permeabil" in neg["outer_membrane_strategy"].lower() or "Artilysin" in neg["outer_membrane_strategy"]
    assert 0.0 < neg["predicted_potency"] <= 1.0
