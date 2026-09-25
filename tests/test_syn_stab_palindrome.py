"""Regression (BUG 49): palindromes are inverted repeats (reverse complement), not textual."""
from sugarcode.modules.syn_stab_ai.core import sequence_risk


def test_ecori_sites_counted():
    r = sequence_risk("TT" + "GAATTC" + "AA")
    assert r["palindrome_count"] >= 1


def test_textual_palindrome_not_counted():
    # GATTAG equals its plain reverse but is NOT a biological inverted repeat
    assert sequence_risk("TT" + "GATTAG" + "AA")["palindrome_count"] == 0


def test_no_sites_zero():
    assert sequence_risk("AAAAAACCCCCC")["palindrome_count"] == 0  # homopolymers: no inverted repeats
