"""Protein properties: hand-computed cases + Biopython oracle cross-check.

Tables are vendored from the published sets (Bjellqvist 1993 pKas,
Guruprasad 1990 DIWV, Kyte-Doolittle 1982, Gill & von Hippel 1989) - the
oracle tests verify the vendored values and formulas against Biopython
1.88, which embeds the same published tables.
"""
import pytest

from sugarcode.bio.proteinprops import (molecular_weight,
                                        extinction_coefficient,
                                        instability_index, aromaticity,
                                        gravy, charge_at_ph,
                                        isoelectric_point, protein_summary)

INSULIN_B = "FVNQHLCGSHLVEALYLVCGERGFFYTPKT"
UBIQUITIN = ("MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRT"
             "LSDYNIQKESTLHLVLRLRGG")
ALL20 = "ACDEFGHIKLMNPQRSTVWY"


def test_molecular_weight_hand_computed():
    # 2 x Ala(89.0932) - 1 x water(18.0153)
    assert molecular_weight("AA") == pytest.approx(160.1711)
    assert molecular_weight("A") == pytest.approx(89.0932)     # no bonds
    with pytest.raises(ValueError, match="empty"):
        molecular_weight("")
    with pytest.raises(ValueError, match="non-standard"):
        molecular_weight("ACDX")
    with pytest.raises(ValueError, match="non-standard"):
        molecular_weight("ACDU")          # selenocysteine out of scope


def test_extinction_coefficient_cystine_pairs():
    assert extinction_coefficient("WYCC") == {"reduced": 6990,
                                              "oxidized": 7115}
    # odd cysteine stays reduced (Gill & von Hippel count pairs)
    assert extinction_coefficient("WYC") == {"reduced": 6990,
                                             "oxidized": 6990}
    assert extinction_coefficient("AAA") == {"reduced": 0, "oxidized": 0}


def test_instability_index_hand_computed():
    assert instability_index("AA") == 5.0            # (10/2) x DIWV[AA]=1.0
    # (10/3) x (DIWV[AC] + DIWV[CA]) = (10/3) x (44.94 + 1.0)
    assert instability_index("ACA") == pytest.approx(10 * 45.94 / 3)


def test_aromaticity_and_gravy():
    assert aromaticity("FY") == 1.0
    assert aromaticity("AA") == 0.0
    assert gravy("AV") == 3.0                        # (1.8 + 4.2) / 2
    assert gravy("RR") == -4.5


def test_charge_and_pi_bounds():
    with pytest.raises(ValueError, match="pH"):
        charge_at_ph("AA", 15)
    # fully acidic peptide: negative at neutral pH, pI at the lower bound
    assert charge_at_ph("DDDD", 7.0) < 0
    assert isoelectric_point("DDDD") < 4.5
    # fully basic: positive, pI at the upper bound
    assert isoelectric_point("RRRR") > 11.0
    # pI is where the net charge crosses zero
    pi = isoelectric_point(ALL20)
    assert abs(charge_at_ph(ALL20, pi)) < 0.05
    assert 6.0 < pi < 7.5


def test_terminal_pka_adjustments():
    # N-terminal Ala uses pKa 7.59, not the default 7.5: a peptide starting
    # with A has a slightly higher pI than the same peptide starting with G
    # (in-range pI so the bisection resolves the difference).
    assert isoelectric_point("AAAK") > isoelectric_point("GAAK")


def test_summary_shape():
    s = protein_summary(INSULIN_B)
    assert s["length"] == 30
    assert s["instability_prediction"] in ("stable", "unstable")
    assert s["extinction_oxidized"] >= s["extinction_reduced"]
    assert set(s) == {"length", "molecular_weight", "extinction_reduced",
                      "extinction_oxidized", "isoelectric_point",
                      "instability_index", "instability_prediction",
                      "aromaticity", "gravy"}


# ------------------------- oracle: Biopython 1.88 -------------------------

oracle = pytest.importorskip("Bio", reason="Biopython oracle not installed")
from Bio.SeqUtils.ProtParam import ProteinAnalysis          # noqa: E402
from Bio.SeqUtils.IsoelectricPoint import IsoelectricPoint  # noqa: E402


@pytest.mark.parametrize("seq", [INSULIN_B, UBIQUITIN, ALL20, "MKDDDDEEEE"])
def test_against_biopython_oracle(seq):
    pa = ProteinAnalysis(seq)
    assert molecular_weight(seq) == pytest.approx(pa.molecular_weight(),
                                                  abs=1e-6)
    red, oxi = pa.molar_extinction_coefficient()
    mine = extinction_coefficient(seq)
    assert mine["reduced"] == red and mine["oxidized"] == oxi
    assert instability_index(seq) == pytest.approx(pa.instability_index())
    assert aromaticity(seq) == pytest.approx(pa.aromaticity())
    assert gravy(seq) == pytest.approx(pa.gravy())
    assert isoelectric_point(seq) == pytest.approx(IsoelectricPoint(seq).pi(),
                                                   abs=0.01)
