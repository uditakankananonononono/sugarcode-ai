"""Module 117 protein_painter: active-site placement identities, MW against average masses, edge contracts."""
import random
import pytest
from sugarcode.modules.protein_painter import (codon_optimize, design_protein,
                                               molecular_weight, clean_protein)
from sugarcode.modules.protein_painter.core import _design_sequence, FOLD_TEMPLATES


def test_active_site_never_truncated_or_terminal_only():
    # left-heavy coil run: old code placed only "H" of the HDE triad
    seq, pos, complete = _design_sequence("CCCCCC" + "H" * 26, "HDE", random.Random(0))
    assert complete and len(pos) == 3
    for i, aa in zip(pos, "HDE"):
        assert seq[i] == aa
    # default enzyme template keeps the full triad and reports it
    r = design_protein("catalyze redox", seed=3)
    assert r["best"]["active_site_placement_complete"]
    assert len(r["best"]["active_site_residues"]) == len(FOLD_TEMPLATES["enzyme"]["active"])


def test_length_and_candidates_validated():
    with pytest.raises(ValueError):
        design_protein("enzyme", length=0)
    with pytest.raises(ValueError):
        design_protein("enzyme", candidates=0)
    r = design_protein("enzyme", length=60, seed=1)
    assert len(r["best"]["sequence"]) == 60


def test_unknown_host_rejected():
    with pytest.raises(KeyError):
        codon_optimize("AAAA", "mystery_host")
    assert codon_optimize("ACDE") == "GCGTGCGATGAA"
    assert codon_optimize("ACDE", host="yeast") == "GCTTGTGACGAG"


def test_molecular_weight_matches_average_masses():
    # GGG: 3*57.0519 + 18.0153 = 189.171; A: 89.0932 (ExPASy average convention)
    assert molecular_weight("GGG") == pytest.approx(189.171, abs=0.01)
    assert molecular_weight("A") == pytest.approx(89.0932, abs=0.01)


def test_clean_protein_contract():
    assert clean_protein("ac-def!") == "ACDEF"
    with pytest.raises(ValueError):
        clean_protein("123")
