"""reward_decomposition: documented exact-match behavior of the specificity term (values unchanged)."""
from sugarcode.modules.crispr_muse.core import reward_decomposition

G = "GACGCATAAAGATGAGACGC"
ONE = "TTTT" + G + "TGG" + "TTTT"
TWO = ONE + "CCCCC" + G + "AGG" + "CCCC"
MM = ONE + "CCCCC" + "GACGCATAAAGATGAGACGA" + "TGG" + "CCCC"


def test_specificity_values_match_the_docstring():
    spec = {k: reward_decomposition(G, background=b)["components"]["specificity"] for k, b in (("one", ONE), ("two", TWO), ("mm", MM))}
    assert spec["one"] == 1 and spec["two"] == 1
    assert round(spec["mm"], 4) == 0.65


def test_docstring_states_the_behavior():
    doc = reward_decomposition.__doc__
    assert "two" in doc and "exact" in doc and "1.0" in doc and "0.65" in doc


def test_off_target_hits_count_exact_copies():
    assert reward_decomposition(G, background=TWO)["off_target_hits"] == 2
    assert reward_decomposition(G, background=MM)["off_target_hits"] == 2
