"""Module 116 phage_tx: library anchors vs literature (T7 latent 17 min - Wikipedia;
T4 LPS/OmpC receptor - J Bacteriol 151(2):718), optimizer vs brute force, edge cases."""
import itertools, math
import pytest
from sugarcode.modules.phage_tx import (PHAGE_LIBRARY, evolve_cocktail, match_phages,
                                        optimize_cocktail, design_phage_therapy)
from sugarcode.modules.phage_tx.core import RESISTANCE_MECHANISMS, RECEPTOR_REDUNDANCY

ECOLI_SUSC = {"T4": .9, "T7": .8, "lambda_vir": .7}


def test_library_references_are_live():
    used = {sp["receptor"] for sp in PHAGE_LIBRARY.values()}
    for key, vals in RECEPTOR_REDUNDANCY.items():
        assert key in used  # "OmpC" key was dead - no phage uses it standalone
        for v in vals:
            assert v in RESISTANCE_MECHANISMS


def test_optimizer_matches_brute_force():
    hits = [n for n, s in PHAGE_LIBRARY.items() if "Escherichia_coli" in s["targets"] and s["burst"] > 0]
    best = max(
        ((1 - (esc := math.prod(1 - ECOLI_SUSC.get(x, 0) for x in c)))
         + .25 * len({PHAGE_LIBRARY[x]["receptor"].split("/")[0] for x in c}) / len(c)
         - .4 * esc - .03 * len(c), c)
        for sz in range(1, 4) for c in itertools.combinations(hits, sz))
    r = optimize_cocktail("Escherichia_coli", ECOLI_SUSC, max_phages=3)
    assert r["selected"]["score"] == round(best[0], 8) and set(r["selected"]["cocktail"]) == set(best[1])


def test_evolve_cocktail_rejects_zero_rounds():
    with pytest.raises(ValueError):
        evolve_cocktail("Escherichia_coli", rounds=0)


def test_design_uses_selected_latent_periods():
    r = design_phage_therapy("Escherichia_coli", ECOLI_SUSC, {"hours": 6})
    selected = r["optimization"]["selected"]["cocktail"]
    expect = sum(PHAGE_LIBRARY[x]["latent_min"] for x in selected) / len(selected) / 60
    assert r["simulation"]["parameters"]["latent_h"] == pytest.approx(expect)  # was always 0.5
    r2 = design_phage_therapy("Escherichia_coli", ECOLI_SUSC, {"hours": 6, "latent_h": 0.25})
    assert r2["simulation"]["parameters"]["latent_h"] == 0.25  # user value wins


def test_literature_anchors():
    assert PHAGE_LIBRARY["T7"]["latent_min"] == 17  # T7 life cycle 17 min at 37 C
    assert PHAGE_LIBRARY["T4"]["receptor"] == "LPS/OmpC"
    assert match_phages("Staphylococcus_aureus")["best"]["phage"] == "K"
