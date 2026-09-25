"""Regression (BUG 48): Chou-Fasman must use the 1978 breaker rule, not runaway extension."""
from collections import Counter
from sugarcode.modules.alpha_fold_ui import CF, chou_fasman

UBQ = "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"


def test_table_is_canonical_1978():
    assert CF["A"] == (142, 83, 66) and CF["V"] == (106, 170, 50) and CF["P"] == (57, 55, 152)


def test_polyalanine_helix_polyproline_glycine_coil():
    assert "".join(chou_fasman("AAAAAAAAAA")).count("H") >= 6
    assert "H" not in chou_fasman("PPGGPPGGPP") and "E" not in chou_fasman("PPGGPPGGPP")


def test_ubiquitin_not_runaway_helix():
    ss = "".join(chou_fasman(UBQ))
    comp = Counter(ss)
    # 1UBQ is one helix + five strands; the old per-residue extension gave 70/76 helix
    assert comp["H"] < 55
    # the real 23-34 helix is still found
    assert ss[22:34].count("H") >= 9
