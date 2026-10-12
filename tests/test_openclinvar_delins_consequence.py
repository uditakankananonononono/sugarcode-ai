"""delins consequence is derived from the net length change of the edit."""
import pytest

from sugarcode.modules.openclinvar.core import _consequence_from_hgvs, interpret_variant


@pytest.mark.parametrize("variant,expected", [
    ("c.1_3delinsA", "frameshift"),        # 3 replaced by 1: net -2
    ("c.1_3delinsAAAA", "frameshift"),     # 3 replaced by 4: net +1
    ("c.2delinsAAAA", "inframe_indel"),    # 1 replaced by 4: net +3
    ("c.1_6delinsA", "frameshift"),        # 6 replaced by 1: net -5
    ("c.1_6delinsAAA", "inframe_indel"),   # 6 replaced by 3: net -3
    ("c.1_3delinsAGT", "inframe_indel"),   # net 0: existing label kept
    ("c.2delinsAT", "frameshift"),         # 1 replaced by 2: net +1
])
def test_delins_consequence_follows_net_length_change(variant, expected):
    assert _consequence_from_hgvs(variant) == expected
    assert interpret_variant("BRCA1", variant)["consequence"] == expected


@pytest.mark.parametrize("variant,expected", [
    ("c.1_3del", "inframe_indel"),
    ("c.1_2del", "frameshift"),
    ("c.4_5dup", "frameshift"),
    ("c.4_6dup", "inframe_indel"),
    ("c.4_5insAAA", "inframe_indel"),
    ("c.4_5insAA", "frameshift"),
])
def test_non_delins_indel_labels_unchanged(variant, expected):
    assert _consequence_from_hgvs(variant) == expected
