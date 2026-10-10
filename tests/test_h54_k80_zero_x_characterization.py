"""H54: one literal current-code return, not model accuracy validation."""

import math

from sugarcode.bio.phylo import k80_distance


def test_one_transition_in_two_columns_returns_inf():
    assert k80_distance("AA", "AG") == math.inf
